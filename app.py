import asyncio
import datetime
import pandas as pd
from urllib.parse import urljoin
from playwright.async_api import async_playwright

# URL base con zona definida por shape (la que tú pasaste)
BASE_URL = "https://www.idealista.com/areas/venta-viviendas/?shape=%28%28_z_vFbj%7EU%7BmGehNhhKkm%5EhnL%7Cd_%40whPrpM%29%29"
MAX_PAGES = 5  # límite para MVP
OUTPUT_FILE = f"idealista_zona_custom_{datetime.date.today()}.xlsx"

async def scrape_idealista_shape():
    anuncios = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        for pagina in range(1, MAX_PAGES + 1):
            paged_url = BASE_URL + f"&pag={pagina}"
            print(f"Scrapeando página {pagina}: {paged_url}")
            await page.goto(paged_url, timeout=60000)
            await page.wait_for_selector("article.item", timeout=10000)

            items = await page.query_selector_all("article.item")

            if not items:
                print(f"📭 No se encontraron más anuncios en página {pagina}.")
                break

            for item in items:
                try:
                    titulo = await item.query_selector_eval("a.item-link", "el => el.textContent")
                    precio = await item.query_selector_eval(".item-price", "el => el.textContent")
                    detalles = await item.query_selector_all(".item-detail")
                    detalle_textos = [await d.text_content() for d in detalles]

                    relative_url = await item.query_selector_eval("a.item-link", "el => el.getAttribute('href')")
                    full_url = urljoin("https://www.idealista.com", relative_url)

                    anuncios.append({
                        "titulo": titulo.strip(),
                        "precio": precio.strip(),
                        "detalles": " | ".join([d.strip() for d in detalle_textos]),
                        "url": full_url,
                        "fecha_scraping": datetime.date.today().isoformat()
                    })
                except:
                    continue

        await browser.close()

    # Exportar a Excel
    df = pd.DataFrame(anuncios)
    df.to_excel(OUTPUT_FILE, index=False)
    print(f"✅ Scraping finalizado. Archivo guardado como: {OUTPUT_FILE}")

# Ejecutar
if __name__ == "__main__":
    asyncio.run(scrape_idealista_shape())
