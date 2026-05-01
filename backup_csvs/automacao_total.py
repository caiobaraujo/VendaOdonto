import os
import re
import time
import random
import urllib.parse
import pandas as pd
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


SITE_PREVIEW_BASE = "http://127.0.0.1:8000/preview_print.html"
SITE_LANDING_BASE = "http://127.0.0.1:8000/index.html"

ARQUIVO_BASE = "leads_tratados_para_envio.csv"
CRM_FILE = "meu_crm_estetica.csv"
PASTA_PRINTS = "prints_personalizados"

if not os.path.exists(PASTA_PRINTS):
    os.makedirs(PASTA_PRINTS)


def slug_seguro(texto: str) -> str:
    texto = re.sub(r"[^\wÀ-ÿ\s-]", "", str(texto)).strip()
    texto = re.sub(r"\s+", "_", texto)
    return texto[:80]


def configurar_navegador_mobile():
    chrome_options = Options()
    mobile_emulation = {"deviceName": "iPhone 12 Pro"}
    chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--window-size=430,932")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--log-level=3")

    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)


def gerar_link(base_url: str, empresa: str, bairro: str, segmento: str) -> str:
    params = {
        "empresa": empresa,
        "local": bairro,
        "segmento": segmento
    }
    return f"{base_url}?{urllib.parse.urlencode(params)}"


def montar_mensagem_inicial(nome_empresa: str, bairro: str) -> str:
    return (
        f"Olá! Tudo bem?\n\n"
        f"Eu montei uma visualização de site personalizada no nome da {nome_empresa}, "
        f"pensando em uma proposta de benefício odontológico para a equipe da clínica em {bairro}.\n\n"
        f"Já deixei a prévia pronta na imagem aqui embaixo para vocês verem primeiro.\n"
        f"Se acharem interessante, eu explico rapidinho como funciona."
    )


def esperar_nome_personalizado(driver, nome_empresa: str, timeout=10):
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.ID, "empresa-nome"))
        )

        def texto_ok(drv):
            try:
                el = drv.find_element(By.ID, "empresa-nome")
                txt = el.text.strip().lower()
                alvo = nome_empresa.strip().lower()
                return alvo in txt or txt == alvo
            except Exception:
                return False

        WebDriverWait(driver, timeout).until(texto_ok)
        return True
    except Exception:
        return False


def tirar_print(driver, url, caminho_img, nome_empresa):
    print(f"🌐 Abrindo preview: {url}")
    driver.get(url)
    driver.execute_script("window.scrollTo(0, 0);")

    ok = esperar_nome_personalizado(driver, nome_empresa, timeout=10)
    time.sleep(random.uniform(1.2, 2.2))

    if not ok:
        print(f"⚠️ Nome da clínica não confirmou no DOM para: {nome_empresa}")

    driver.save_screenshot(caminho_img)


def carregar_ou_criar_crm():
    if os.path.exists(CRM_FILE):
        return pd.read_csv(CRM_FILE)
    raise FileNotFoundError(
        "CRM não encontrado. Rode primeiro o crm_vendas.py para criar o arquivo meu_crm_estetica.csv"
    )


def atualizar_crm_pos_geracao(df_crm, empresa, link_landing, caminho_print, mensagem):
    idx = df_crm[df_crm["Empresa"].astype(str).str.lower() == str(empresa).lower()].index
    if not idx.empty:
        df_crm.loc[idx, "Link"] = link_landing
        df_crm.loc[idx, "Caminho_Print"] = caminho_print
        df_crm.loc[idx, "Mensagem"] = mensagem
    return df_crm


def processar_esteira(limite_por_execucao=15):
    if not os.path.exists(ARQUIVO_BASE):
        raise FileNotFoundError(
            "Arquivo leads_tratados_para_envio.csv não encontrado. Rode primeiro o link_generator.py"
        )

    df = pd.read_csv(ARQUIVO_BASE).copy()

    df = df[df["Pronto_Para_Enviar"] == "SIM"].copy()
    df = df.sort_values(
        by=["Prioridade", "Empresa_Contato"],
        ascending=[False, True]
    ).head(limite_por_execucao)

    if df.empty:
        print("⚠️ Nenhum lead pronto para envio.")
        return

    driver = configurar_navegador_mobile()
    df_crm = carregar_ou_criar_crm()

    lista_envio = []
    data_geracao = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sufixo = datetime.now().strftime("%Y%m%d_%H%M")

    print(f"🚀 Preparando {len(df)} leads para revisão/envio...")

    for _, row in df.iterrows():
        nome = str(row["Empresa_Contato"]).strip()
        bairro = str(row["Bairro"]).strip()
        telefone = re.sub(r"\D", "", str(row["Telefone"]))
        segmento = str(row.get("Segmento", "clínicas de estética")).strip()
        data_captura = str(row.get("Data_Captura", "")).strip()

        link_preview = gerar_link(
            base_url=SITE_PREVIEW_BASE,
            empresa=nome,
            bairro=bairro,
            segmento=segmento
        )

        link_landing = gerar_link(
            base_url=SITE_LANDING_BASE,
            empresa=nome,
            bairro=bairro,
            segmento=segmento
        )

        nome_img = f"{slug_seguro(nome)}.png"
        caminho_img = os.path.join(PASTA_PRINTS, nome_img)

        print(f"📸 Gerando print para: {nome}")
        tirar_print(driver, link_preview, caminho_img, nome)

        mensagem = montar_mensagem_inicial(nome, bairro)

        lista_envio.append({
            "Empresa": nome,
            "Telefone": telefone,
            "Bairro": bairro,
            "Prioridade": row["Prioridade"],
            "Link_Preview": link_preview,
            "Link_Landing": link_landing,
            "Caminho_Print": caminho_img,
            "Mensagem": mensagem,
            "Status_Envio": "REVISAR_ANTES_DE_ENVIAR",
            "Data_Captura": data_captura,
            "Data_Geracao_Print": data_geracao
        })

        df_crm = atualizar_crm_pos_geracao(
            df_crm=df_crm,
            empresa=nome,
            link_landing=link_landing,
            caminho_print=caminho_img,
            mensagem=mensagem
        )

        time.sleep(random.uniform(1.0, 2.0))

    driver.quit()

    df_final = pd.DataFrame(lista_envio)
    arquivo_datado = f"esteira_pronta_para_envio_{sufixo}.csv"
    arquivo_estavel = "esteira_pronta_para_envio.csv"

    df_final.to_csv(arquivo_datado, index=False, encoding="utf-8-sig")
    df_final.to_csv(arquivo_estavel, index=False, encoding="utf-8-sig")
    df_crm.to_csv(CRM_FILE, index=False, encoding="utf-8-sig")

    print("\n✅ Tudo pronto.")
    print("Arquivos gerados/atualizados:")
    print(f"- {arquivo_datado}")
    print(f"- {arquivo_estavel}")
    print("- meu_crm_estetica.csv")
    print(f"- pasta {PASTA_PRINTS}/")


if __name__ == "__main__":
    processar_esteira(limite_por_execucao=15)