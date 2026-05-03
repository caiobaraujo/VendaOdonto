"""
Gerador de mensagens persuasivas para WhatsApp
"""
from datetime import datetime

class MensagemPersuasiva:
    
    def gerar_mensagem_completa(self, dados_lead: dict) -> str:
        """
        Gera a mensagem completa com print + link de forma persuasiva
        """
        empresa = dados_lead.get('empresa_contato', 'sua clínica')
        bairro = dados_lead.get('bairro', 'Belo Horizonte')
        telefone = dados_lead.get('telefone', '')
        
        # Saudação por horário
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
            f"📸 *Na imagem abaixo*, você vai ver como ficaria a comunicação "
            f"de um benefício odontológico pensado para clínicas aqui em *{bairro}*.\n\n"
            f"É uma proposta simples, a partir de R$ 26,90 por pessoa, "
            f"que pode ajudar na retenção e cuidado com sua equipe.\n\n"
            f"🔗 *Link da apresentação completa:*\n"
            f"{dados_lead.get('link_landing', '')}\n\n"
            f"Não é propaganda genérica — montei essa visualização "
            f"especificamente para vocês, porque acredito que faça sentido "
            f"para o setor de estética.\n\n"
            f"Se acharem interessante, podemos conversar rapidinho. "
            f"Sem compromisso! 😊"
        )
        
        return mensagem.strip()
    
    def gerar_mensagem_curta(self, dados_lead: dict) -> str:
        """Versão mais direta para leads com score menor"""
        empresa = dados_lead.get('empresa_contato', 'sua clínica')
        bairro = dados_lead.get('bairro', 'Belo Horizonte')
        
        hora = datetime.now().hour
        saudacao = "Bom dia" if hora < 12 else "Boa tarde" if hora < 18 else "Boa noite"
        
        return (
            f"{saudacao}! Tudo bem?\n\n"
            f"Preparei uma demonstração personalizada de benefício odontológico "
            f"para a *{empresa}*, aqui em *{bairro}*.\n\n"
            f"📸 Segue o print da apresentação\n"
            f"🔗 Link completo: {dados_lead.get('link_landing', '')}\n\n"
            f"Se fizer sentido, podemos conversar. Sem compromisso! 😊"
        )