import os
from datetime import datetime
import pandas as pd

CRM_FILE = "meu_crm_estetica.csv"
BASE_TRATADA = "leads_tratados_para_envio.csv"

COLUNAS_CRM = [
    "Empresa",
    "Telefone",
    "Bairro",
    "Site",
    "Prioridade",
    "Status",
    "Ultimo_Contato",
    "Observacao",
    "Link",
    "Caminho_Print",
    "Mensagem",
    "Data_Captura",
    "Data_Entrada_CRM",
]


def criar_ou_carregar_crm(csv_base=BASE_TRATADA):
    if os.path.exists(CRM_FILE):
        df = pd.read_csv(CRM_FILE)
        print("✅ CRM carregado com sucesso.")
        return df

    if not os.path.exists(csv_base):
        raise FileNotFoundError(f"Arquivo base não encontrado: {csv_base}")

    df_base = pd.read_csv(csv_base).copy()
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for col in [
        "Empresa_Contato", "Telefone", "Bairro", "Site", "Prioridade",
        "Link", "Data_Captura"
    ]:
        if col not in df_base.columns:
            df_base[col] = ""

    df = pd.DataFrame({
        "Empresa": df_base["Empresa_Contato"],
        "Telefone": df_base["Telefone"],
        "Bairro": df_base["Bairro"],
        "Site": df_base["Site"],
        "Prioridade": df_base["Prioridade"],
        "Status": "Novo",
        "Ultimo_Contato": "",
        "Observacao": "",
        "Link": df_base["Link"],
        "Caminho_Print": "",
        "Mensagem": "",
        "Data_Captura": df_base["Data_Captura"],
        "Data_Entrada_CRM": agora,
    })

    df = df[COLUNAS_CRM]
    df.to_csv(CRM_FILE, index=False, encoding="utf-8-sig")

    arquivo_backup = f"meu_crm_estetica_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    df.to_csv(arquivo_backup, index=False, encoding="utf-8-sig")

    print(f"🚀 CRM criado com {len(df)} leads.")
    print(f"💾 Backup: {arquivo_backup}")
    return df


def atualizar_status(empresa_nome, novo_status, obs=""):
    if not os.path.exists(CRM_FILE):
        raise FileNotFoundError("CRM ainda não existe.")

    df = pd.read_csv(CRM_FILE)

    idx = df[df["Empresa"].astype(str).str.contains(empresa_nome, case=False, na=False)].index

    if idx.empty:
        print("❌ Empresa não encontrada no CRM.")
        return

    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    df.loc[idx, "Status"] = novo_status
    df.loc[idx, "Observacao"] = obs
    df.loc[idx, "Ultimo_Contato"] = agora

    df.to_csv(CRM_FILE, index=False, encoding="utf-8-sig")
    print(f"✅ Status atualizado: {empresa_nome} -> {novo_status}")


if __name__ == "__main__":
    crm = criar_ou_carregar_crm()
    print("\nResumo do funil:")
    print(crm["Status"].value_counts(dropna=False))