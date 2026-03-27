import asyncio
import pandas as pd
import re
import random
from datetime import datetime
from urllib.parse import quote_plus

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError


CITY = "Santo Agostinho Belo Horizonte"
NICHE = "Clínica de Estética"


def normalizar_telefone(valor: str) -> str:
    if not valor:
        return ""

    apenas_digitos = re.sub(r"\D", "", str(valor))

    if not apenas_digitos:
        return ""

    # remove prefixo 55 se vier
    if apenas_digitos.startswith("55") and len(apenas_digitos) > 11:
        apenas_digitos = apenas_digitos[2:]

    # remove zero inicial de DDD
    if apenas_digitos.startswith("0") and len(apenas_digitos) >= 11:
        apenas_digitos = apenas_digitos[1:]

    return apenas_digitos


async def esperar(min_s=1.0, max_s=2.0):
    await asyncio.sleep(random.uniform(min_s, max_s))


async def extrair_telefone(page) -> str:
    # tentativa 1
    try:
        phone_el = await page.query_selector('button[data-item-id^="phone:tel:"]')
        if phone_el:
            phone_raw = await phone_el.get_attribute("data-item-id")
            if phone_raw:
                phone = phone_raw.replace("phone:tel:", "")
                phone = normalizar_telefone(phone)
                if phone:
                    return phone
    except Exception:
        pass

    # tentativa 2
    try:
        main_panel = await page.query_selector('div[role="main"]')
        if main_panel:
            texto = await main_panel.inner_text()
            match = re.search(r'(\(?\d{2}\)?\s?9?\d{4}[-\s]?\d{4})', texto)
            if match:
                phone = normalizar_telefone(match.group(1))
                if phone:
                    return phone
    except Exception:
        pass

    return ""


async def extrair_site(page) -> str:
    try:
        site_el = await page.query_selector('a[data-item-id="authority"]')
        if site_el:
            href = await site_el.get_attribute("href")
            return href or ""
    except Exception:
        pass
    return ""


async def scrape_beauty_leads(city=CITY, niche=NICHE):
    data_captura = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data_arquivo = datetime.now().strftime("%Y%m%d_%H%M")
    consulta = f"{niche} em {city}"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=250)
        context = await browser.new_context(
            viewport={"width": 1366, "height": 900},
            locale="pt-BR",
        )
        page = await context.new_page()

        search_url = f"https://www.google.com/maps/search/{quote_plus(consulta)}"

        print(f"🌐 Abrindo busca: {consulta}")
        await page.goto(search_url, wait_until="domcontentloaded")
        await page.wait_for_timeout(5000)

        # scroll conservador na lista
        print("🧭 Carregando resultados...")
        for _ in range(6):
            await page.mouse.move(250, 420)
            await page.mouse.wheel(0, 2200)
            await esperar(1.5, 2.5)

        items = await page.query_selector_all('div[role="article"]')
        print(f"📊 {len(items)} itens encontrados. Extraindo...")

        leads = []

        for i, item in enumerate(items, start=1):
            try:
                title_el = await item.query_selector(".fontHeadlineSmall")
                nome = await title_el.inner_text() if title_el else ""

                nome = (nome or "").strip()
                if not nome:
                    continue

                await item.click()
                await page.wait_for_timeout(2500)

                telefone = await extrair_telefone(page)
                site = await extrair_site(page)

                lead = {
                    "Empresa": nome,
                    "Telefone": telefone if telefone else "Não encontrado",
                    "Site": site if site else "N/A",
                    "Consulta": consulta,
                    "Data_Captura": data_captura,
                }

                leads.append(lead)
                print(f"✅ {i:02d}. {nome} | {telefone if telefone else 'Sem telefone'}")

                await esperar(1.2, 2.2)

            except PlaywrightTimeoutError:
                print(f"⚠️ Timeout no item {i}")
                continue
            except Exception as e:
                print(f"⚠️ Erro no item {i}: {e}")
                continue

        await browser.close()

    if not leads:
        print("❌ Nenhum lead encontrado.")
        return

    df = pd.DataFrame(leads)

    # mantém só quem tem telefone
    df = df[df["Telefone"] != "Não encontrado"].copy()

    # remove duplicados por telefone, mantendo o primeiro
    df = df.drop_duplicates(subset=["Telefone"]).reset_index(drop=True)

    nome_base = f"leads_{city.lower().replace(' ', '_')}"
    arquivo_datado = f"{nome_base}_{data_arquivo}.csv"
    arquivo_estavel = f"{nome_base}.csv"

    df.to_csv(arquivo_datado, index=False, encoding="utf-8-sig")
    df.to_csv(arquivo_estavel, index=False, encoding="utf-8-sig")

    print(f"\n✅ Leads salvos:")
    print(f"- {arquivo_datado}")
    print(f"- {arquivo_estavel}")
    print(f"📌 Total final: {len(df)}")


if __name__ == "__main__":
    asyncio.run(scrape_beauty_leads())