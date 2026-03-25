import asyncio
import pandas as pd
import re
import random
from playwright.async_api import async_playwright
import playwright_stealth

async def human_delay(min_time=1, max_time=2):
    await asyncio.sleep(random.uniform(min_time, max_time))

async def scrape_beauty_leads(city, niche="Salão de Beleza"):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 900}
        )
        page = await context.new_page()
        
        # Sua correção Stealth
        try:
            if hasattr(playwright_stealth, 'stealth_async'): await playwright_stealth.stealth_async(page)
            elif hasattr(playwright_stealth, 'stealth'): await playwright_stealth.stealth(page)
        except: pass

        search_query = f"{niche} em {city}"
        url = f"https://www.google.com/maps/search/{search_query.replace(' ', '+')}"
        await page.goto(url)
        await page.wait_for_timeout(6000)

        # Scroll da lista lateral
        sidebar = 'div[role="feed"]'
        await page.mouse.move(200, 400) 
        for _ in range(5):
            await page.mouse.wheel(0, 3000)
            await asyncio.sleep(2)

        items = await page.query_selector_all('div[role="article"]')
        print(f"📊 {len(items)} itens encontrados. Extraindo...")

        leads = []
        for item in items:
            try:
                # Extrai nome
                title_el = await item.query_selector('.fontHeadlineSmall')
                name = await title_el.inner_text() if title_el else "N/A"
                
                # Clique para abrir detalhes
                await item.click()
                # ESPERA CRUCIAL: Aguarda o painel de detalhes carregar o conteúdo
                await page.wait_for_timeout(3000) 

                phone = "Não encontrado"
                
                # TENTATIVA 1: Pelo atributo de sistema do Google
                phone_el = await page.query_selector('button[data-item-id^="phone:tel:"]')
                if phone_el:
                    phone_raw = await phone_el.get_attribute('data-item-id')
                    phone = phone_raw.replace('phone:tel:', '')
                
                # TENTATIVA 2: Se falhar, busca por Regex no texto do painel lateral
                if phone == "Não encontrado":
                    # Pega o texto de todo o painel lateral de detalhes
                    panel = await page.query_selector('div[role="main"]')
                    if panel:
                        panel_text = await panel.inner_text()
                        # Regex para telefones brasileiros (fixo ou celular)
                        match = re.search(r'(\(?\d{2}\)?\s?9?\d{4}[-\s]?\d{4})', panel_text)
                        if match:
                            phone = match.group(0)

                # Busca Site
                site_el = await page.query_selector('a[data-item-id="authority"]')
                site = await site_el.get_attribute('href') if site_el else "N/A"

                leads.append({"Empresa": name, "Telefone": phone, "Site": site})
                print(f"✅ {name} | {phone}")

                # Move o mouse para "limpar" o foco antes do próximo
                await page.mouse.move(random.randint(700, 900), random.randint(200, 500))

            except Exception:
                continue

        if leads:
            df = pd.DataFrame(leads)
            df = df[df['Telefone'] != "Não encontrado"].drop_duplicates(subset=['Telefone'])
            filename = f"leads_{city.lower().replace(' ', '_')}.csv"
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            print(f"\n🚀 Sucesso! {len(df)} leads salvos.")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_beauty_leads("Santo Agostinho Belo Horizonte", "Clínica de Estética"))