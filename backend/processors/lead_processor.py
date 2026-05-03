import re
import urllib.parse
from datetime import datetime

class LeadProcessor:
    """
    Responsável por limpar e processar leads brutos.
    Suas funções originais do link_generator.py, agora organizadas em classe.
    """
    
    def __init__(self):
        self.pads_remover = [
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
    
    def limpar_nome_empresa(self, nome_bruto: str) -> str:
        """
        Limpa o nome da empresa removendo informações geográficas
        e mantendo apenas o nome comercial principal.
        Mantive sua lógica original que funciona bem.
        """
        nome = str(nome_bruto).strip()
        
        # Separações mais comuns
        nome = re.split(r"\s+\|\s+|\s+-\s+", nome)[0].strip()
        
        # Remove caudas genéricas
        for padrao in self.pads_remover:
            nome = re.sub(padrao, "", nome, flags=re.IGNORECASE).strip(" -_|,:")
        
        nome = re.sub(r"\s+", " ", nome).strip(" -_|,:")
        
        # Fallback simples
        if len(nome) < 4:
            nome = str(nome_bruto).strip()
        
        # Limita tamanho visual
        palavras = nome.split()
        if len(palavras) > 5:
            nome = " ".join(palavras[:5])
        
        # Remove nome genérico
        if nome.lower() in {"estética", "clinica", "clínica", "spa"}:
            nome = str(nome_bruto).split("-")[0].strip()
        
        return nome.strip(" -_|,:")
    
    def detectar_bairro(self, nome: str, site: str = "") -> str:
        """Detecta o bairro baseado no nome e site"""
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
    
    def normalizar_telefone(self, valor: str) -> str:
        """Normaliza o telefone removendo caracteres não numéricos"""
        digits = re.sub(r"\D", "", str(valor))
        if digits.startswith("55") and len(digits) > 11:
            digits = digits[2:]
        if digits.startswith("0") and len(digits) >= 11:
            digits = digits[1:]
        return digits
    
    def score_lead(self, nome: str, telefone: str, site: str = "") -> int:
        """Calcula a prioridade do lead baseado em critérios de qualidade"""
        score = 0
        nome_low = nome.lower()
        tel = self.normalizar_telefone(telefone)
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
    
    def gerar_link_landing(self, empresa: str, bairro: str, segmento: str) -> str:
            params = {
                "empresa": empresa,
                "local": bairro,
                "segmento": segmento
            }
            return f"http://127.0.0.1:8000/landing.html?{urllib.parse.urlencode(params)}"

    def gerar_link_preview(self, empresa: str, bairro: str, segmento: str) -> str:
        params = {
            "empresa": empresa,
            "local": bairro,
            "segmento": segmento
        }
        return f"http://127.0.0.1:8000/preview_print.html?{urllib.parse.urlencode(params)}"
    
    
    def montar_mensagem_whatsapp(self, nome_empresa: str, bairro: str, segmento: str = "clínicas de estética") -> str:
        """Monta a mensagem persuasiva para WhatsApp (sem ser spam)"""
        
        # Personaliza saudação baseado no horário
        from datetime import datetime
        hora = datetime.now().hour
        if hora < 12:
            saudacao = "Bom dia"
        elif hora < 18:
            saudacao = "Boa tarde"
        else:
            saudacao = "Boa noite"
        
        return (
            f"{saudacao}! Tudo bem? 🦷✨\n\n"
            f"Meu nome é [SEU NOME] e eu criei uma demonstração personalizada de como "
            f"um benefício odontológico poderia funcionar para a equipe da *{nome_empresa}*.\n\n"
            f"Preparei especialmente para clínicas em *{bairro}* — "
            f"é uma proposta simples, com valores a partir de R$ 26,90 por pessoa, "
            f"e que pode ajudar na retenção da equipe.\n\n"
            f"Montei uma visualização rápida pra vocês verem como ficaria.\n\n"
            f"👇 Segue o print da apresentação personalizada abaixo.\n"
            f"Se fizer sentido, podemos conversar rapidinho."
        )
    
    def processar_lead_bruto(self, dados_brutos: dict) -> dict:
        """
        Processa um lead bruto e retorna um dicionário limpo e pontuado.
        Esta é a função principal que seu pipeline vai chamar.
        """
        empresa_original = str(dados_brutos.get('nome', '')).strip()
        telefone_bruto = str(dados_brutos.get('telefone', ''))
        site = str(dados_brutos.get('site', '')).strip()
        
        empresa_contato = self.limpar_nome_empresa(empresa_original)
        telefone = self.normalizar_telefone(telefone_bruto)
        bairro = self.detectar_bairro(empresa_original, site)
        segmento = 'clínicas de estética'
        prioridade = self.score_lead(empresa_contato, telefone, site)
        
        return {
            'empresa_original': empresa_original,
            'empresa_contato': empresa_contato,
            'telefone': telefone,
            'bairro': bairro,
            'site': '' if site.lower() in {'nan', 'n/a'} else site,
            'segmento': segmento,
            'prioridade': prioridade,
            'pronto_para_enviar': 'SIM' if prioridade >= 5 else 'REVISAR',
            'link_landing': self.gerar_link_landing(empresa_contato, bairro, segmento),
            'link_preview': self.gerar_link_preview(empresa_contato, bairro, segmento),
            'mensagem_whatsapp': self.montar_mensagem_whatsapp(empresa_contato, bairro),
        }