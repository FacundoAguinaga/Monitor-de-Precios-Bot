import asyncio
from playwright.async_api import async_playwright
import random

class ProductScraper:
    def __init__(self):
        # CORRECCIÓN: Definimos una LISTA (plural) de agentes, no uno solo.
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0"
        ]

    async def scrape_mercadolibre(self, url: str) -> dict:
        # 1. Limpieza de URL (Quitamos parámetros de tracking para ir más rápido)
        clean_url = url.split("?")[0].split("#")[0]
        print(f"🔍 Analizando: {clean_url} ...")
        
        async with async_playwright() as p:
            # Mantenemos headless=False para que veas el proceso (cámbialo a True cuando termines de probar)
            browser = await p.chromium.launch(
                headless=True, 
                args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
            )
            
            # Ahora sí existe self.user_agents
            context = await browser.new_context(
                user_agent=random.choice(self.user_agents),
                viewport={'width': 1280, 'height': 800}
            )
            page = await context.new_page()

            try:
                # Usamos 'domcontentloaded' para velocidad
                await page.goto(clean_url, wait_until="domcontentloaded", timeout=30000)
                
                # Esperamos explícitamente al PRECIO
                price_selector = ".ui-pdp-price__second-line .andes-money-amount__fraction"
                await page.wait_for_selector(price_selector, timeout=10000)

                # Extraer Título
                title = await page.inner_text("h1.ui-pdp-title")

                # Extraer Precio
                price_text = await page.inner_text(price_selector)
                price = int(price_text.replace('.', ''))

                data = {
                    "producto": title,
                    "precio": price,
                    "url": clean_url,
                    "moneda": "ARS"
                }
                
                print(f"✅ Éxito: ${data['precio']}")
                return data

            except Exception as e:
                # Si falla, toma foto
                await page.screenshot(path="error_screenshot.png")
                print(f"❌ Error en {clean_url}: {e}")
                return None
            
            finally:
                await browser.close()