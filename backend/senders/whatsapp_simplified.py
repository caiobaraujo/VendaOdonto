"""
Abre WhatsApp Web com mensagem pronta
"""
import webbrowser
import urllib.parse
from datetime import datetime

class WhatsAppSimplified:
    
    def __init__(self):
        self.mensagem_gen = None
        from backend.senders.mensagem_persuasiva import MensagemPersuasiva
        self.mensagem_gen = MensagemPersuasiva()
    
    def enviar_mensagem_individual(self, dados_lead: dict) -> dict:
        """Abre WhatsApp Web com a mensagem (sem link do print)"""
        telefone = self._limpar_telefone(dados_lead.get('telefone', ''))
        empresa = dados_lead.get('empresa_contato', '')
        
        # Gera mensagem sem link do print
        if dados_lead.get('prioridade', 0) >= 7:
            mensagem = self.mensagem_gen.gerar_mensagem_completa(dados_lead)
        else:
            mensagem = self.mensagem_gen.gerar_mensagem_curta(dados_lead)
        
        # Codifica para URL
        mensagem_encoded = urllib.parse.quote(mensagem)
        
        # Abre WhatsApp Web
        url = f"https://web.whatsapp.com/send?phone=55{telefone}&text={mensagem_encoded}"
        
        print(f"📱 Abrindo WhatsApp para {empresa}")
        webbrowser.open(url, new=2)
        
        return {
            'sucesso': True,
            'telefone': telefone,
            'empresa': empresa,
            'mensagem': mensagem
        }
    
    def _limpar_telefone(self, telefone: str) -> str:
        import re
        telefone = re.sub(r'\D', '', str(telefone))
        if telefone.startswith('55') and len(telefone) > 11:
            telefone = telefone[2:]
        return telefone