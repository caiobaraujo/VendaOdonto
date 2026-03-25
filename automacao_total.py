import pandas as pd
import urllib.parse
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

MINHA_URL_BASE = "http://127.0.0.1:8000/index.html" # mudar para produção
ARQUIVO_LEADS = "leads_clinica_de_estetica.csv"
PASTA_PRINTS = "prints_personalizados"

if not os.path.exists(PASTA_PRINTS):
    os.makedirs(PASTA_PRINTS)

def configurar_navegador_mobile():
    chrome_options = Options()
    # Simula um iPhone 12 para o print ficar com cara de celular
    mobile_emulation = { "deviceName": "iPhone 12 Pro" }
    chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)
    chrome_options.add_argument("--headless") # Roda sem abrir a janela 
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def processar_esteira():
    # 1. Carregar Leads
    df = pd.read_csv(ARQUIVO_LEADS)
    df = df[df['Telefone'] != "Não encontrado"].copy()
    
    driver = configurar_navegador_mobile()
    lista_envio = []

    print(f"🚀 Iniciando automação para {len(df)} leads...")

    for index, row in df.iterrows():
        # Limpeza do Nome
        nome_bruto = str(row['Empresa'])
        nome_limpo = nome_bruto.split('-')[0].split('|')[0].strip()
        nome_limpo = " ".join(nome_limpo.split()[:4])
        
        # Lógica de Bairro 
        bairro = "Belo Horizonte"
        if "Santo Agostinho" in nome_bruto: bairro = "Santo Agostinho"
        elif "Lourdes" in nome_bruto: bairro = "Lourdes"
        
        # 2. Gerar URL Personalizada
        params = {
            "empresa": nome_limpo,
            "local": bairro,
            "segmento": "especialistas em estética"
        }
        url_final = f"{MINHA_URL_BASE}?{urllib.parse.urlencode(params)}"
        
        # 3. Tirar Print Realista
        print(f"📸 Gerando print para: {nome_limpo}...")
        driver.get(url_final)
        time.sleep(2) # Espera o JS carregar o nome
        
        nome_arquivo_img = f"{nome_limpo.replace(' ', '_')}.png"
        caminho_img = os.path.join(PASTA_PRINTS, nome_arquivo_img)
        driver.save_screenshot(caminho_img)
        
        # 4. Preparar Mensagem de WhatsApp
        msg = (
            f"Olá pessoal da {nome_limpo}! Tudo bem?\n\n"
            f"Notei o padrão de vocês no bairro {bairro} e desenhei uma "
            f"condição exclusiva para o time de vocês na SulAmérica Odonto.\n\n"
            f"Fica apenas R$ 26,90 por pessoa. Montei esse resumo personalizado:\n"
            f"🔗 {url_final}"
        )
        
        lista_envio.append({
            "Empresa": nome_limpo,
            "Telefone": row['Telefone'],
            "Link": url_final,
            "Caminho_Print": caminho_img,
            "Mensagem": msg
        })

    driver.quit()
    
    # 5. Salvar Tabela de Controle (CRM)
    df_final = pd.DataFrame(lista_envio)
    df_final.to_csv("esteira_pronta_para_envio.csv", index=False)
    print("\n✅ TUDO PRONTO! Prints salvos e planilha de envio gerada.")

    # --- PARTE DE ENVIO AUTOMÁTICO (COMENTADA) ---
    """
    import pywhatkit as kit
    for item in lista_envio:
        # kit.send_whats_image(item['Telefone'], item['Caminho_Print'], item['Mensagem'])
        # time.sleep(10) # Intervalo de segurança
    """

if __name__ == "__main__":
    processar_esteira()