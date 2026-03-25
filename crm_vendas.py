import pandas as pd
import os

def criar_ou_carregar_crm(csv_leads):
    crm_file = "meu_crm_estetica.csv"
    
    if os.path.exists(crm_file):
        df_crm = pd.read_csv(crm_file)
        print("✅ CRM carregado com sucesso.")
    else:
        # Se não existe, cria a partir do seu arquivo de leads do scraper
        df_leads = pd.read_csv(csv_leads)
        df_crm = df_leads[['Empresa', 'Telefone']].copy()
        df_crm['Status'] = 'Novo' # Status iniciais: Novo, Contatado, Visualizou, Agendado, Fechado
        df_crm['Ultimo_Contato'] = '-'
        df_crm['Observacao'] = '-'
        df_crm.to_csv(crm_file, index=False)
        print(f"🚀 CRM criado com {len(df_crm)} leads.")
    
    return df_crm

def atualizar_status(empresa_nome, novo_status, obs="-"):
    crm_file = "meu_crm_estetica.csv"
    df = pd.read_csv(crm_file)
    
    # Busca parcial pelo nome da empresa
    idx = df[df['Empresa'].str.contains(empresa_nome, case=False)].index
    
    if not idx.empty:
        df.loc[idx, 'Status'] = novo_status
        df.loc[idx, 'Observacao'] = obs
        from datetime import datetime
        df.loc[idx, 'Ultimo_Contato'] = datetime.now().strftime("%d/%m/%Y")
        df.to_csv(crm_file, index=False)
        print(f"✅ Status de '{empresa_nome}' atualizado para '{novo_status}'.")
    else:
        print("❌ Empresa não encontrada no CRM.")

# --- MODO DE USO ---
if __name__ == "__main__":
    # 1. Cria o banco de dados se ele não existir
    meu_crm = criar_ou_carregar_crm("leads_clinica_de_estetica.csv")
    
    # 2. Exemplo de uso
    # atualizar_status("Bella", "Contatado", "Mandei o link personalizado")
    
    print("\nResumo do seu Funil:")
    print(meu_crm['Status'].value_counts())