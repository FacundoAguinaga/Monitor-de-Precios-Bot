import asyncio
import os
import pandas as pd
import csv
import logging # <--- IMPORTANTE
from scraper import ProductScraper
from sheet_manager import SheetManager

# --- CONFIGURACIÓN DE LOGS (Nivel Profesional) ---
logging.basicConfig(
    filename='bot_activity.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    encoding='utf-8'
)

def load_urls_from_csv(file_path="products.csv"):
    urls = []
    try:
        with open(file_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['url'].strip():
                    urls.append(row['url'].strip())
        
        msg = f"📂 Se cargaron {len(urls)} productos desde {file_path}"
        print(msg)
        logging.info(msg) # Guardamos en el log
        return urls
    except FileNotFoundError:
        error_msg = f"⚠️ No se encontró {file_path}. Usando lista vacía."
        print(error_msg)
        logging.warning(error_msg)
        return []

async def run_bot():
    print("--- 🤖 INICIANDO BOT PROFESIONAL v1.2 (Con Logs) ---")
    logging.info("--- INICIO DE SESIÓN DEL BOT ---")
    
    # CARGAR URLS
    target_urls = load_urls_from_csv()

    if not target_urls:
        logging.warning("Abortando: No hay URLs en el CSV.")
        return

    # 1. SCRAPING
    bot = ProductScraper()
    resultados = []

    for url in target_urls:
        data = await bot.scrape_mercadolibre(url)
        if data:
            resultados.append(data)
    
    if not resultados:
        print("❌ No hay datos para procesar.")
        logging.warning("Ciclo finalizado sin datos recolectados.")
        return

    # 2. PROCESAMIENTO LOCAL
    df = pd.DataFrame(resultados)
    df['fecha'] = pd.Timestamp.now()
    history_path = 'data/history.csv'
    write_header = not os.path.exists(history_path)
    df.to_csv(history_path, mode='a', header=write_header, index=False)
    
    logging.info(f"HISTORIAL: Datos guardados en {history_path}")

    print("\n--- 📊 DATOS OBTENIDOS ---")
    print(df[["producto", "precio"]])
    logging.info(f"Procesados {len(df)} productos exitosamente.")
    
    # 3. SUBIDA A LA NUBE
    print("\n--- ☁️ SUBIENDO A LA NUBE ---")
    sheet_bot = SheetManager()
    sheet_bot.save_data(resultados)

    print("\n✅ Proceso finalizado con éxito.")
    logging.info("--- FIN DE SESIÓN DEL BOT ---\n")

def main():
    asyncio.run(run_bot())

if __name__ == "__main__":
    main()