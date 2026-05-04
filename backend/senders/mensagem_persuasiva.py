"""
Gerador de mensagens persuasivas para WhatsApp
"""
from datetime import datetime

class MensagemPersuasiva:
    
    def __init__(self, base_url="http://127.0.0.1:5001"):
        self.base_url = base_url
    
    def gerar_mensagem_completa(self, dados_lead: dict) -> str:
        """Mensagem SEM link do print (print vai como imagem separada)"""
        empresa = dados_lead.get('empresa_contato', 'sua clínica')
        bairro = dados_lead.get('bairro', 'Belo Horizonte')
        link_landing = dados_lead.get('link_landing', '')
        
        hora = datetime.now().hour
        if hora < 12:
            saudacao = "Bom dia"
            emoji = "☀️"
        elif hora < 18:
            saudacao = "Boa tarde"
            emoji = "🌤️"
        else:
            saudacao = "Boa noite"
            emoji = "🌙"
        
        mensagem = (
            f"{saudacao}! Tudo bem? {emoji}\n\n"
            f"Sou corretor(a) da SulAmérica Odonto e preparei uma "
            f"*apresentação personalizada* para a *{empresa}*.\n\n"
            f"🌐 *Site personalizado:* {link_landing}\n\n"
            f"É uma proposta de benefício odontológico pensada para "
            f"clínicas aqui em *{bairro}*, a partir de R$ 26,90 por vida.\n\n"
            f"Não é propaganda genérica — montei essa visualização "
            f"especificamente para vocês, porque acredito que faça sentido "
            f"para o setor de estética.\n\n"
            f"Se acharem interessante, podemos conversar rapidinho. "
            f"Sem compromisso! 😊\n\n"
            f"📸 Vou enviar o print da apresentação na sequência."
        )
        
        return mensagem.strip()
    
    def gerar_mensagem_curta(self, dados_lead: dict) -> str:
        """Versão direta"""
        empresa = dados_lead.get('empresa_contato', 'sua clínica')
        bairro = dados_lead.get('bairro', 'Belo Horizonte')
        link_landing = dados_lead.get('link_landing', '')
        
        hora = datetime.now().hour
        saudacao = "Bom dia" if hora < 12 else "Boa tarde" if hora < 18 else "Boa noite"
        
        return (
            f"{saudacao}! Tudo bem?\n\n"
            f"Preparei uma demonstração personalizada de benefício odontológico "
            f"para a *{empresa}*, aqui em *{bairro}*.\n\n"
            f"🌐 Site personalizado: {link_landing}\n\n"
            f"A partir de R$ 26,90/vida. Se fizer sentido, podemos conversar. "
            f"Sem compromisso! 😊\n\n"
            f"📸 Vou enviar o print da apresentação na sequência."
        )