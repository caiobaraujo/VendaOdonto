import os
import re
import time
import random
import subprocess
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class PrintAutomator:
    """
    Gera screenshots personalizados das landing pages.
    Compatível com Chrome 146+.
    """
    
    def __init__(self, pasta_prints='prints_personalizados'):
        self.pasta_prints = os.path.abspath(pasta_prints)
        os.makedirs(self.pasta_prints, exist_ok=True)
        self.driver = None
    
    def _slug_seguro(self, texto: str) -> str:
        texto = re.sub(r"[^\w\s-]", "", str(texto)).strip()
        texto = re.sub(r"\s+", "_", texto)
        texto = texto.replace(" ", "_")
        return texto[:80]
    
    def _encontrar_chromedriver(self):
        resultado = subprocess.run(['which', 'chromedriver'], capture_output=True, text=True)
        if resultado.returncode == 0:
            return resultado.stdout.strip()
        
        caminhos = [
            '/usr/bin/chromedriver',
            '/usr/local/bin/chromedriver',
            '/usr/lib/chromium-browser/chromedriver',
        ]
        for caminho in caminhos:
            if os.path.exists(caminho):
                return caminho
        
        raise FileNotFoundError("chromedriver não encontrado. Execute: sudo apt install chromium-driver")
    
    def _configurar_navegador_mobile(self):
        chromedriver_path = self._encontrar_chromedriver()
        print(f"✅ ChromeDriver: {chromedriver_path}")
        
        chrome_options = Options()
        mobile_emulation = {"deviceName": "iPhone 12 Pro"}
        chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=430,932")
        
        service = Service(chromedriver_path)
        return webdriver.Chrome(service=service, options=chrome_options)
    
    def _esperar_nome_personalizado(self, nome_empresa: str, timeout=8):
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.ID, "empresa-nome"))
            )
            time.sleep(0.5)
            return True
        except Exception as e:
            print(f"⚠️ Timeout: {e}")
            return False
    
    def gerar_print(self, url_preview: str, nome_empresa: str) -> str:
        print(f"🖨️ Iniciando geração de print...")
        
        if not self.driver:
            self.driver = self._configurar_navegador_mobile()
        
        nome_arquivo = f"{self._slug_seguro(nome_empresa)}.png"
        caminho_completo = os.path.join(self.pasta_prints, nome_arquivo)
        
        print(f"🌐 Abrindo: {url_preview}")
        
        self.driver.get(url_preview)
        self.driver.execute_script("window.scrollTo(0, 0);")
        
        ok = self._esperar_nome_personalizado(nome_empresa)
        
        if ok:
            print(f"✅ Página carregada com sucesso!")
        else:
            print(f"⚠️ Página carregada (nome pode não ter sido confirmado)")
        
        self.driver.save_screenshot(caminho_completo)
        
        if os.path.exists(caminho_completo):
            tamanho = os.path.getsize(caminho_completo)
            print(f"✅ Print salvo com {tamanho} bytes!")
        else:
            raise Exception(f"Falha ao salvar arquivo em {caminho_completo}")
        
        return caminho_completo
    
    def fechar(self):
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            finally:
                self.driver = None
    
    def gerar_prints_em_lote(self, leads: list) -> list:
        resultados = []
        total = len(leads)
        
        print(f"\n🖨️ GERANDO {total} PRINTS EM LOTE")
        print("=" * 50)
        
        self.driver = self._configurar_navegador_mobile()
        
        for i, lead in enumerate(leads, 1):
            print(f"\n📸 [{i}/{total}] {lead['empresa_contato']}")
            print(f"⏳ Gerando print...")
            
            try:
                caminho = self.gerar_print(
                    url_preview=lead['link_preview'],
                    nome_empresa=lead['empresa_contato']
                )
                resultados.append({
                    'empresa': lead['empresa_contato'],
                    'caminho_print': caminho,
                    'nome_arquivo': os.path.basename(caminho),
                    'sucesso': True
                })
                print(f"✅ Concluído!")
                time.sleep(random.uniform(0.5, 1.0))
                
            except Exception as e:
                print(f"❌ Falha: {e}")
                resultados.append({
                    'empresa': lead['empresa_contato'],
                    'caminho_print': None,
                    'sucesso': False,
                    'erro': str(e)
                })
        
        self.fechar()
        print(f"\n✅ {len([r for r in resultados if r['sucesso']])}/{total} prints gerados!")
        return resultados