"""
SCRAPER GOOGLE MAPS - Modo Transparente (Antidetecção)
Mostra o navegador para o usuário ver a mágica acontecer.
Isso reduz bloqueios e impressiona recrutadores.
"""

import asyncio
import re
import random
from datetime import datetime
from urllib.parse import quote_plus
from playwright.async_api import async_playwright


class GoogleMapsScraper:
    
    def __init__(self, max_leads=30):
        self.max_leads = max_leads
        self.progresso = []
        self.status = "parado"
    
    def _normalizar_telefone(self, valor: str) -> str:
        if not valor:
            return ""
        apenas_digitos = re.sub(r"\D", "", str(valor))
        if not apenas_digitos:
            return ""
        if apenas_digitos.startswith("55") and len(apenas_digitos) > 11:
            apenas_digitos = apenas_digitos[2:]
        if apenas_digitos.startswith("0") and len(apenas_digitos) >= 11:
            apenas_digitos = apenas_digitos[1:]
        return apenas_digitos
    
    async def _esperar(self, min_s=1.0, max_s=2.5):
        await asyncio.sleep(random.uniform(min_s, max_s))
    
    async def _extrair_telefone(self, page) -> str:
        try:
            phone_el = await page.query_selector('button[data-item-id^="phone:tel:"]')
            if phone_el:
                phone_raw = await phone_el.get_attribute("data-item-id")
                if phone_raw:
                    phone = phone_raw.replace("phone:tel:", "")
                    phone = self._normalizar_telefone(phone)
                    if phone:
                        return phone
        except Exception:
            pass
        
        try:
            main_panel = await page.query_selector('div[role="main"]')
            if main_panel:
                texto = await main_panel.inner_text()
                match = re.search(r'(\(?\d{2}\)?\s?9?\d{4}[-\s]?\d{4})', texto)
                if match:
                    phone = self._normalizar_telefone(match.group(1))
                    if phone:
                        return phone
        except Exception:
            pass
        
        return ""
    
    async def _extrair_site(self, page) -> str:
        try:
            site_el = await page.query_selector('a[data-item-id="authority"]')
            if site_el:
                href = await site_el.get_attribute("href")
                return href or ""
        except Exception:
            pass
        return ""
    
    async def _scrape_async(self, consulta: str) -> list:
        data_captura = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.progresso = []
        self.status = "executando"
        
        self.progresso.append(f"🔍 Buscando: {consulta}")
        self.progresso.append("🌐 Abrindo Google Maps...")
        
        async with async_playwright() as p:
            # MODO VISÍVEL - headless=False mostra o navegador
            browser = await p.chromium.launch(
                headless=False,  # Mostra a janela!
                slow_mo=300  # Mais lento para parecer humano
            )
            context = await browser.new_context(
                viewport={"width": 1366, "height": 900},
                locale="pt-BR",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            search_url = f"https://www.google.com/maps/search/{quote_plus(consulta)}"
            
            await page.goto(search_url, wait_until="domcontentloaded")
            self.progresso.append("⏳ Aguardando carregamento do Maps...")
            await page.wait_for_timeout(6000)
            
            self.progresso.append("📜 Scroll para carregar resultados...")
            for i in range(4):
                await page.mouse.move(250, 420)
                await page.mouse.wheel(0, 2500)
                await self._esperar(2.0, 3.0)
                self.progresso.append(f"   Scroll {i+1}/4")
            
            items = await page.query_selector_all('div[role="article"]')
            total_encontrados = len(items)
            self.progresso.append(f"📊 {total_encontrados} locais encontrados!")
            
            max_extrair = min(self.max_leads, total_encontrados)
            self.progresso.append(f"🎯 Extraindo {max_extrair} leads (limite configurado)")
            
            leads = []
            
            for i in range(max_extrair):
                try:
                    item = items[i]
                    title_el = await item.query_selector(".fontHeadlineSmall")
                    nome = await title_el.inner_text() if title_el else ""
                    
                    nome = (nome or "").strip()
                    if not nome:
                        continue
                    
                    await item.click()
                    await page.wait_for_timeout(2500)
                    
                    telefone = await self._extrair_telefone(page)
                    site = await self._extrair_site(page)
                    
                    lead = {
                        "nome": nome,
                        "telefone": telefone if telefone else "Não encontrado",
                        "site": site if site else "N/A",
                        "data_captura": data_captura,
                    }
                    
                    status_msg = f"✅ {i+1:02d}/{max_extrair}. {nome[:60]}"
                    if telefone:
                        status_msg += f" | 📱 {telefone}"
                    else:
                        status_msg += " | ❌ Sem telefone"
                    
                    self.progresso.append(status_msg)
                    leads.append(lead)
                    
                    await self._esperar(1.5, 2.5)
                    
                except Exception as e:
                    self.progresso.append(f"⚠️ Erro no item {i+1}: {str(e)[:50]}")
                    continue
            
            await browser.close()
        
        self.status = "finalizado"
        
        # Filtra só quem tem telefone
        leads_validos = [lead for lead in leads if lead['telefone'] != 'Não encontrado']
        self.progresso.append(f"\n📌 {len(leads_validos)} leads com telefone encontrados!")
        
        # Remove duplicados
        seen = set()
        unique_leads = []
        for lead in leads_validos:
            if lead['telefone'] not in seen:
                seen.add(lead['telefone'])
                unique_leads.append(lead)
        
        if len(unique_leads) < len(leads_validos):
            self.progresso.append(f"🗑️ {len(leads_validos) - len(unique_leads)} duplicados removidos")
        
        self.progresso.append(f"✨ Total final: {len(unique_leads)} leads únicos!")
        return unique_leads
    
    def buscar_leads(self, bairro: str = "Santo Agostinho Belo Horizonte", nicho: str = "Clínica de Estética") -> dict:
        """
        Retorna dict com:
        - leads: lista de leads
        - progresso: lista de mensagens de progresso
        """
        consulta = f"{nicho} em {bairro}"
        
        leads = asyncio.run(self._scrape_async(consulta))
        
        return {
            "leads": leads,
            "progresso": self.progresso,
            "total": len(leads)
        }