import os
import re
import pandas as pd
import urllib.parse
from datetime import datetime

ARQUIVO_LEADS = "leads_santo_agostinho_belo_horizonte.csv"
SITE_PREVIEW_BASE = "http://127.0.0.1:8000/index.html"


def limpar_nome_empresa(nome_bruto: str) -> str:
    nome = str(nome_bruto).strip()

    # separações mais comuns
    nome = re.split(r"\s+\|\s+|\s+-\s+", nome)[0].strip()

    # remove caudas muito genéricas
    pads_remover = [
        r"\bBelo Horizonte\b.*$",
        r"\bBH\b.*$",
        r"\bMG\b.*$",
        r"\bSanto Agostinho\b.*$",
        r"\bSavassi\b.*$",
        r"\bLourdes\b.*$",
        r"\bBotox\b.*$",
        r"\bUltraformer\b.*$",
        r"\bEmagrecimento\b.*$",
        r"\bDepilação a Laser\b.*$",
        r"\bHarmonização Facial\b.*$",
        r"\bTricologia\b.*$",
    ]

    for padrao in pads_remover:
        nome = re.sub(padrao, "", nome, flags=re.IGNORECASE).strip(" -_|,:")

    nome = re.sub(r"\s+", " ", nome).strip(" -_|,:")

    # fallback simples
    if len(nome) < 4:
        nome = str(nome_bruto).strip()

    # limita tamanho visual
    palavras = nome.split()
    if len(palavras) > 5:
        nome = " ".join(palavras[:5])

    # remove nome genérico demais
    if nome.lower() in {"estética", "clinica", "clínica", "spa"}:
        nome = str(nome_bruto).split("-")[0].strip()

    return nome.strip(" -_|,:")


def detectar_bairro(nome: str, site: str = "") -> str:
    texto = f"{nome} {site}".lower()

    if "santo agostinho" in texto:
        return "Santo Agostinho"
    if "savassi" in texto:
        return "Savassi"
    if "lourdes" in texto:
        return "Lourdes"
    if "belvedere" in texto:
        return "Belvedere"
    return "Belo Horizonte"


def normalizar_telefone(valor: str) -> str:
    digits = re.sub(r"\D", "", str(valor))
    if digits.startswith("55") and len(digits) > 11:
        digits = digits[2:]
    if digits.startswith("0") and len(digits) >= 11:
        digits = digits[1:]
    return digits


def score_lead(nome: str, telefone: str, site: str = "") -> int:
    score = 0
    nome_low = nome.lower()
    tel = normalizar_telefone(telefone)
    site_low = str(site).lower()

    if len(tel) in (10, 11):
        score += 2

    if site and site_low not in {"n/a", "nan", ""}:
        score += 2

    if any(b in nome_low for b in ["savassi", "lourdes", "belvedere", "santo agostinho"]):
        score += 2

    if any(k in nome_low for k in ["clínica", "clinica", "laser", "spa", "derma", "estética", "estetica"]):
        score += 2

    if len(nome.split()) >= 2:
        score += 1

    if len(nome) < 5:
        score -= 2

    return max(score, 0)


def gerar_link_preview(base_url: str, empresa: str, bairro: str, segmento: str) -> str:
    params = {
        "empresa": empresa,
        "local": bairro,
        "segmento": segmento
    }
    return f"{base_url}?{urllib.parse.urlencode(params)}"


def generate_custom_links(input_csv=ARQUIVO_LEADS, base_url=SITE_PREVIEW_BASE):
    if not os.path.exists(input_csv):
        print(f"❌ Erro: arquivo não encontrado -> {input_csv}")
        return

    df = pd.read_csv(input_csv).copy()

    for col in ["Empresa", "Telefone", "Site", "Data_Captura"]:
        if col not in df.columns:
            df[col] = ""

    df["Telefone"] = df["Telefone"].astype(str)
    df = df[df["Telefone"].str.strip() != ""].copy()
    df = df[df["Telefone"].str.lower() != "não encontrado"].copy()

    data_tratamento = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sufixo = datetime.now().strftime("%Y%m%d_%H%M")

    saida = []

    for _, row in df.iterrows():
        empresa_original = str(row["Empresa"]).strip()
        empresa_contato = limpar_nome_empresa(empresa_original)
        telefone = normalizar_telefone(row["Telefone"])
        site = str(row.get("Site", "")).strip()
        data_captura = str(row.get("Data_Captura", "")).strip()

        bairro = detectar_bairro(empresa_original, site)
        segmento = "clínicas de estética"
        prioridade = score_lead(empresa_contato, telefone, site)

        link = gerar_link_preview(
            base_url=base_url,
            empresa=empresa_contato,
            bairro=bairro,
            segmento=segmento
        )

        saida.append({
            "Empresa_Original": empresa_original,
            "Empresa_Contato": empresa_contato,
            "Telefone": telefone,
            "Bairro": bairro,
            "Site": "" if site.lower() in {"nan", "n/a"} else site,
            "Segmento": segmento,
            "Link": link,
            "Prioridade": prioridade,
            "Pronto_Para_Enviar": "SIM" if prioridade >= 5 else "REVISAR",
            "Data_Captura": data_captura,
            "Data_Tratamento": data_tratamento
        })

    df_saida = pd.DataFrame(saida)
    df_saida = df_saida.sort_values(
        by=["Pronto_Para_Enviar", "Prioridade", "Empresa_Contato"],
        ascending=[True, False, True]
    ).reset_index(drop=True)

    arquivo_datado = f"leads_tratados_para_envio_{sufixo}.csv"
    arquivo_estavel = "leads_tratados_para_envio.csv"

    df_saida.to_csv(arquivo_datado, index=False, encoding="utf-8-sig")
    df_saida.to_csv(arquivo_estavel, index=False, encoding="utf-8-sig")

    print("✅ Arquivos gerados:")
    print(f"- {arquivo_datado}")
    print(f"- {arquivo_estavel}")


if __name__ == "__main__":
    generate_custom_links()