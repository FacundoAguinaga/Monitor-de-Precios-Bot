# 🛒 E-commerce Competitor Price Monitor

Un bot de monitoreo de precios de alto rendimiento construido en Python. Rastrea precios de competidores en tiempo real utilizando estrategias de evasión de detección y sincroniza los datos automáticamente con Google Sheets para análisis de inteligencia de mercado.

## 🚀 Características Clave
- **Motor Asíncrono:** Utiliza `Playwright` + `Asyncio` para scraping paralelo de alta velocidad.
- **Modo Stealth:** Rotación de User-Agents y evasión de huellas digitales de automatización (evita bloqueos de MercadoLibre/Amazon).
- **Cloud Sync:** Integración nativa con Google Sheets API para reportes en vivo.
- **Resiliencia:** Manejo robusto de errores, reintentos y limpieza de URLs "sucias".
- **Arquitectura Modular:** Separación clara de responsabilidades (Scraper, Storage, Orchestrator).

## 🛠️ Tech Stack
- **Lenguaje:** Python 3.13
- **Scraping:** Playwright (Webkit/Chromium Engine)
- **Data Processing:** Pandas
- **Cloud/API:** Google Sheets API (gspread), OAuth2

## ⚙️ Instalación

1. **Clonar el repositorio:**
   ```bash
   git clone [https://github.com/TU_USUARIO/price-monitor-bot.git](https://github.com/TU_USUARIO/price-monitor-bot.git)
   cd price-monitor-bot