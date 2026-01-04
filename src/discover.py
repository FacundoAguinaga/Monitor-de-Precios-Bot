import asyncio
from playwright.async_api import async_playwright
import csv
import random
import os

class ProductDiscoverer:
    def __init__(self):
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]

    async def search_products(self, keyword: str, limit=5):
        """
        Busca 'keyword' en MercadoLibre y devuelve los primeros 'limit' links.
        Versión robusta para Grid y List view.
        """
        search_query = keyword.replace(" ", "-")
        url = f"https://listado.mercadolibre.com.ar/{search_query}"
        
        print(f"🕵️  Buscando oportunidades para: '{keyword}'...")
        
        found_links = []
        seen_links = set()

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True) 
            context = await browser.new_context(user_agent=random.choice(self.user_agents))
            page = await context.new_page()

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                
                # Selector genérico
                await page.wait_for_selector("li.ui-search-layout__item", timeout=10000)
                items = await page.query_selector_all("li.ui-search-layout__item")
                
                for item in items:
                    if len(found_links) >= limit: break
                    
                    # Buscar links dentro de la tarjeta
                    links_in_card = await item.query_selector_all("a")
                    
                    product_url = None
                    for link in links_in_card:
                        href = await link.get_attribute("href")
                        #evitar publicidad (click1) y asegurar que sea producto
                        if href and ("/p/" in href or "articulo.mercadolibre" in href) and "click1" not in href:
                            product_url = href
                            break 
                    
                    if product_url:
                        clean_link = product_url.split("?")[0].split("#")[0]
                        if clean_link not in seen_links:
                            seen_links.add(clean_link)
                            found_links.append(clean_link)
                            print(f"   -> Encontrado: {clean_link[:40]}...")

            except Exception as e:
                print(f"❌ Error buscando: {e}")
            finally:
                await browser.close()
        
        return found_links

    def save_to_csv(self, links, filename="products.csv", mode="append"):
        """
        Guarda los links en el CSV.
        mode: 'append' (agrega al final) o 'replace' (borra y escribe nuevo).
        """
        existing_urls = set()
        
        # Si el modo es 'append', leemos lo que ya había
        if mode == "append":
            try:
                with open(filename, "r") as f:
                    reader = csv.DictReader(f)
                    fieldnames = reader.fieldnames
                    if fieldnames:
                        url_col = 'url' if 'url' in fieldnames else fieldnames[0]
                        for row in reader:
                            if row.get(url_col):
                                existing_urls.add(row[url_col].strip())
            except FileNotFoundError:
                pass
        else:
            print(f"♻️ Modo Reemplazo: Se sobrescribirá {filename}")

        added_count = 0
        
        write_mode = "a" if mode == "append" and os.path.exists(filename) else "w"
        
        with open(filename, write_mode, newline="") as f:
            writer = csv.writer(f)
            
            # Si escribimos de cero ('w') o el archivo estaba vacío, ponemos header
            if write_mode == "w" or os.stat(filename).st_size == 0:
                 writer.writerow(["url"])

            for link in links:
                if link not in existing_urls:
                    writer.writerow([link])
                    added_count += 1
        
        print(f"💾 Acción completada. Se guardaron {added_count} links nuevos.")