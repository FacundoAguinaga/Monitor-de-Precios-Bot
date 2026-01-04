import asyncio
import pandas as pd
import os
from scraper import ProductScraper
from sheet_manager import SheetManager # <--- Importamos la nueva clase

TARGET_URLS = [
    "https://www.mercadolibre.com.ar/apple-iphone-13-128-gb-blanco-estelar-distribuidor-autorizado/p/MLA1018500855?pdp_filters=item_id:MLA1556924909#is_advertising=true&searchVariation=MLA1018500855&backend_model=search-backend&position=1&search_layout=grid&type=pad&tracking_id=9e399b85-21a9-4cc3-be0c-5217da79eb5b&ad_domain=VQCATCORE_LST&ad_position=1&ad_click_id=NGVlMDFkYmItY2NhMC00ODk4LTg4N2QtNjc1ZTJmYTE5MzJi"
    # Puedes agregar más URLs aquí
]

async def run_bot():
    print("--- 🤖 INICIANDO BOT PROESIONAL v1.0 ---")
    
    # 1. SCRAPING
    bot = ProductScraper()
    resultados = []

    for url in TARGET_URLS:
        data = await bot.scrape_mercadolibre(url)
        if data:
            resultados.append(data)
    
    if not resultados:
        print("❌ No hay datos para procesar.")
        return

    # 2. PROCESAMIENTO LOCAL (PANDAS)
    df = pd.DataFrame(resultados)
    print("\n--- 📊 DATOS OBTENIDOS ---")
    print(df[["producto", "precio"]])
    
    # 3. SUBIDA A LA NUBE (GOOGLE SHEETS)
    print("\n--- ☁️ SUBIENDO A LA NUBE ---")
    sheet_bot = SheetManager() # Busca service_account.json por defecto
    sheet_bot.save_data(resultados)

    print("\n✅ Proceso finalizado con éxito.")

def main():
    asyncio.run(run_bot())

if __name__ == "__main__":
    main()