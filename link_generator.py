import pandas as pd
import urllib.parse
import os

def generate_custom_links(input_csv, base_url):
    if not os.path.exists(input_csv):
        print(f"❌ Erro: O arquivo {input_csv} não foi encontrado.")
        return

    # Carrega os leads
    df = pd.read_csv(input_csv)
    
    # Filtra apenas quem tem telefone
    df = df[df['Telefone'] != "Não encontrado"].copy()
    
    output_lines = []

    print(f"🔗 Gerando links ultra-personalizados para {len(df)} leads...")

    for index, row in df.iterrows():
        # 1. Limpeza do Nome da Empresa
        nome_bruto = str(row['Empresa'])
        nome_limpo = nome_bruto.split('-')[0].split('|')[0].strip()
        nome_limpo = " ".join(nome_limpo.split()[:4]) 

        # 2. Captura de Bairro e Nicho de acordo com o csv
        # Se o scraper não tiver essas colunas, usa valores padrão inteligentes
        bairro = "Belo Horizonte"
        if "Santo Agostinho" in nome_bruto: bairro = "Santo Agostinho"
        elif "Lourdes" in nome_bruto: bairro = "Lourdes"
        elif "Savassi" in nome_bruto: bairro = "Savassi"

        nicho = "especialistas em estética" # Padrão

        # 3. Montagem dos Parâmetros da URL
        params = {
            "empresa": nome_limpo,
            "local": bairro,
            "segmento": nicho
        }
        
        # O urlencode gera a string: ?empresa=...&local=...&segmento=...
        query_string = urllib.parse.urlencode(params)
        link_personalizado = f"{base_url}?{query_string}"
        
        # Formata a saída para o arquivo de texto
        telefone = str(row['Telefone'])
        linha = (f"Empresa: {nome_limpo}\n"
                 f"Bairro: {bairro}\n"
                 f"WhatsApp: {telefone}\n"
                 f"Link: {link_personalizado}\n"
                 f"{'-'*30}")
        output_lines.append(linha)

    # Salva em um TXT
    with open("lista_para_whatsapp.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))

    print(f"✅ Sucesso! {len(output_lines)} links gerados em 'lista_para_whatsapp.txt'")

if __name__ == "__main__":
    # URL da Landing Page (ou Local para teste)  -> colocar em um .env depois
    MINHA_URL = "http://127.0.0.1:8000/index.html" 
    
    # Nome do arquivo que o Scraper gerou
    ARQUIVO_LEADS = "leads_clinica_de_estetica.csv" 
    
    generate_custom_links(ARQUIVO_LEADS, MINHA_URL)