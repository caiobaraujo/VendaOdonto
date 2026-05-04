"""
Envio automático de mensagem + print via WhatsApp Web
"""
import os
import time
import re
import pyperclip
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime

class WhatsAppAutomator:
    """
    Envia mensagem + imagem automaticamente via WhatsApp Web
    """
    
    def __init__(self, headless=False):
        """
        Args:
            headless: Se True, roda em background (sem mostrar navegador)
        """
        self.driver = None
        self.headless = headless
        self.mensagem_gen = None
        
        # Importa o gerador de mensagens
        from backend.senders.mensagem_persuasiva import MensagemPersuasiva
        self.mensagem_gen = MensagemPersuasiva()

    
    def _encontrar_chromedriver(self):
        """Localiza o executável do chromedriver (mesmo método do print_automator.py)"""
        import subprocess
        resultado = subprocess.run(['which', 'chromedriver'], capture_output=True, text=True)
        if resultado.returncode == 0:
            return resultado.stdout.strip()
        
        # Fallback para caminhos comuns
        caminhos = [
            os.path.expanduser('~/.wdm/drivers/chromedriver/linux64/146.0.7680.165/chromedriver-linux64/chromedriver'),
            '/usr/bin/chromedriver',
            '/usr/local/bin/chromedriver',
            '/usr/lib/chromium-browser/chromedriver',
        ]
        for caminho in caminhos:
            if os.path.isfile(caminho) and os.access(caminho, os.X_OK):
                return caminho
        
        # Tenta encontrar pelo webdriver_manager e ajusta
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            path = ChromeDriverManager().install()
            # Se retornar um diretório, procura o binário dentro dele
            if os.path.isdir(path):
                for root, dirs, files in os.walk(path):
                    for file in files:
                        if file == 'chromedriver' and os.access(os.path.join(root, file), os.X_OK):
                            return os.path.join(root, file)
            # Se for arquivo, verifica
            if os.path.isfile(path):
                # Garante permissão de execução
                os.chmod(path, 0o755)
                return path
        except Exception:
            pass
    
        raise FileNotFoundError("chromedriver não encontrado. Execute: sudo apt install chromium-driver")


    def _configurar_driver(self):
        """Configura o Chrome para WhatsApp Web"""
        options = Options()
        
        if self.headless:
            options.add_argument("--headless=new")
        
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1")
        
        # Localiza o chromedriver corretamente
        chromedriver_path = self._encontrar_chromedriver()
        print(f"✅ ChromeDriver: {chromedriver_path}")
        
        service = Service(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_window_size(430, 932)
        
        return driver
    
    def _esperar_qr_code(self, driver, timeout=60):
        """Aguarda o usuário escanear o QR Code"""
        print("\n📱 ==================================")
        print("📱 ESCANEIE O QR CODE DO WHATSAPP")
        print("📱 Você tem 60 segundos...")
        print("📱 ==================================\n")
        
        try:
            WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, "//canvas[@aria-label='Scan me!']"))
            )
            print("⏳ Aguardando scan do QR Code...")
            
            # Aguarda o QR code desaparecer (login feito)
            WebDriverWait(driver, 120).until_not(
                EC.presence_of_element_located((By.XPATH, "//canvas[@aria-label='Scan me!']"))
            )
            print("✅ Login realizado com sucesso!")
            return True
            
        except Exception as e:
            print(f"❌ Tempo esgotado para escanear QR Code")
            return False
    
    def _esperar_carregamento(self, driver, timeout=30):
        """Aguarda o WhatsApp carregar completamente"""
        try:
            WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, "//div[@contenteditable='true'][@data-tab='10']"))
            )
            time.sleep(2)
            return True
        except:
            return False
    
    def _abrir_conversa(self, driver, telefone):
        """Abre a conversa com o número especificado"""
        # Limpa o telefone
        telefone = re.sub(r'\D', '', str(telefone))
        if telefone.startswith('55'):
            telefone = telefone[2:]
        
        # Abre diretamente via URL
        url = f"https://web.whatsapp.com/send?phone=55{telefone}"
        driver.get(url)
        
        # Aguarda carregar a conversa
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//div[@contenteditable='true'][@data-tab='10']"))
            )
            time.sleep(2)
            print(f"✅ Conversa aberta com {telefone}")
            return True
        except Exception as e:
            print(f"❌ Erro ao abrir conversa: {e}")
            return False
    
    def _enviar_mensagem(self, driver, mensagem):
        """Envia a mensagem de texto"""
        try:
            # Encontra o campo de mensagem
            campo_mensagem = driver.find_element(By.XPATH, "//div[@contenteditable='true'][@data-tab='10']")
            campo_mensagem.click()
            
            # Cola a mensagem
            pyperclip.copy(mensagem)
            campo_mensagem.send_keys(Keys.CONTROL + 'v') if os.name == 'nt' else campo_mensagem.send_keys(Keys.COMMAND + 'v')
            
            time.sleep(1)
            
            # Envia
            campo_mensagem.send_keys(Keys.ENTER)
            time.sleep(2)
            
            print("✅ Mensagem enviada!")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao enviar mensagem: {e}")
            return False
    
    def _enviar_imagem(self, driver, caminho_imagem):
        """Envia uma imagem"""
        try:
            if not os.path.exists(caminho_imagem):
                print(f"❌ Arquivo não encontrado: {caminho_imagem}")
                return False
            
            # Clica no botão de anexar
            btn_anexar = driver.find_element(By.XPATH, "//span[@data-icon='attach-menu-plus']")
            btn_anexar.click()
            time.sleep(2)
            
            # Clica em "Fotos e vídeos"
            btn_fotos = driver.find_element(By.XPATH, "//input[@accept='image/*,video/mp4,video/3gpp,video/quicktime']")
            
            # Envia o caminho absoluto da imagem
            caminho_absoluto = os.path.abspath(caminho_imagem)
            btn_fotos.send_keys(caminho_absoluto)
            
            time.sleep(3)
            
            # Clica no botão de enviar
            btn_enviar = driver.find_element(By.XPATH, "//span[@data-icon='send']")
            btn_enviar.click()
            
            time.sleep(2)
            print("✅ Imagem enviada!")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao enviar imagem: {e}")
            return False
    
    def enviar_lead_completo(self, dados_lead: dict) -> dict:
        """
        Envia mensagem + print para um lead
        
        Args:
            dados_lead: Dicionário com:
                - empresa_contato
                - telefone
                - bairro
                - link_landing
                - caminho_print
                - prioridade
        
        Returns:
            dict com status do envio
        """
        resultado = {
            'sucesso': False,
            'empresa': dados_lead.get('empresa_contato', ''),
            'telefone': dados_lead.get('telefone', ''),
            'etapas': []
        }
        
        try:
            # 1. Configura o driver (uma vez)
            if not self.driver:
                self.driver = self._configurar_driver()
                self.driver.get("https://web.whatsapp.com")
                
                if not self._esperar_qr_code(self.driver):
                    resultado['erro'] = "QR Code não escaneado"
                    return resultado
                
                self._esperar_carregamento(self.driver)
                resultado['etapas'].append("✅ WhatsApp conectado")
            
            # 2. Gera a mensagem
            if dados_lead.get('prioridade', 0) >= 7:
                mensagem = self.mensagem_gen.gerar_mensagem_completa(dados_lead)
            else:
                mensagem = self.mensagem_gen.gerar_mensagem_curta(dados_lead)
            
            # 3. Abre conversa
            if not self._abrir_conversa(self.driver, dados_lead['telefone']):
                resultado['erro'] = "Não abriu conversa"
                return resultado
            
            resultado['etapas'].append("✅ Conversa aberta")
            
            # 4. Envia a mensagem
            if not self._enviar_mensagem(self.driver, mensagem):
                resultado['erro'] = "Não enviou mensagem"
                return resultado
            
            resultado['etapas'].append("✅ Mensagem enviada")
            
            # 5. Envia o print (imagem)
            if dados_lead.get('caminho_print'):
                time.sleep(2)  # Pequena pausa entre mensagens
                if self._enviar_imagem(self.driver, dados_lead['caminho_print']):
                    resultado['etapas'].append("✅ Print enviado")
                else:
                    resultado['etapas'].append("⚠️ Print não enviado")
            
            resultado['sucesso'] = True
            resultado['data_envio'] = datetime.now().isoformat()
            
            return resultado
            
        except Exception as e:
            resultado['erro'] = str(e)
            return resultado
    
    def enviar_lote(self, lista_leads: list) -> list:
        """
        Envia para múltiplos leads em sequência
        
        Args:
            lista_leads: Lista de dicionários com dados dos leads
        
        Returns:
            Lista de resultados
        """
        resultados = []
        total = len(lista_leads)
        
        print(f"\n🚀 INICIANDO ENVIO EM LOTE PARA {total} LEADS")
        print("=" * 50)
        
        for i, lead in enumerate(lista_leads, 1):
            print(f"\n📱 [{i}/{total}] {lead.get('empresa_contato', 'N/A')}")
            
            resultado = self.enviar_lead_completo(lead)
            resultados.append(resultado)
            
            status = "✅" if resultado['sucesso'] else "❌"
            print(f"{status} {resultado.get('etapas', [])}")
            
            # Pausa entre envios (anti-bloqueio)
            if i < total:
                pausa = 5  # 5 segundos entre cada envio
                print(f"⏳ Aguardando {pausa}s antes do próximo...")
                time.sleep(pausa)
        
        # Resumo final
        sucessos = len([r for r in resultados if r['sucesso']])
        print(f"\n📊 RESUMO: {sucessos}/{total} enviados com sucesso!")
        
        return resultados
    
    def fechar(self):
        """Fecha o navegador"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None


# Instância global (singleton)
whatsapp_bot = None

def get_whatsapp_bot():
    """Retorna a instância única do bot"""
    global whatsapp_bot
    if whatsapp_bot is None:
        whatsapp_bot = WhatsAppAutomator(headless=False)  # False = mostra navegador
    return whatsapp_bot