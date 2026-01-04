# 🚀 Market Intelligence & Price Monitor Hub

![Python](https://img.shields.io/badge/Python-3.13-blue?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Playwright](https://img.shields.io/badge/Playwright-Automation-green?style=for-the-badge&logo=google-chrome&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-Data_Viz-3F4F75?style=for-the-badge&logo=plotly&logoColor=white)

Una plataforma completa de **Business Intelligence (BI)** para el monitoreo de precios en e-commerce. Integra descubrimiento automático de competidores, scraping asíncrono de alto rendimiento y un dashboard interactivo para la toma de decisiones basada en datos.

## 🌟 Características Principales

### 1. 🕵️ Módulo de Auto-Descubrimiento (Crawler)
- Busca oportunidades de mercado automáticamente basado en palabras clave (Keywords).
- Capacidad de **"Modo Reemplazo"** o **"Modo Acumulativo"** para gestionar nichos de mercado.
- Detecta y filtra enlaces válidos de productos ignorando publicidad.

### 2. 🤖 Motor de Scraping (ETL)
- **Tecnología:** Playwright + Asyncio.
- **Stealth Mode:** Rotación de User-Agents y evasión de detección de bots.
- **Resiliencia:** Manejo automático de errores de red y cambios en el DOM.

### 3. 📊 Dashboard Interactivo (UI)
- Visualización de tendencias de precios históricos.
- Métricas clave (KPIs): Precio Promedio, Mínimo y Volatilidad.
- Gestión completa de base de datos (CRUD) desde la interfaz web.
- Botones de pánico para purgado de datos y limpieza de historial.

## 🛠️ Arquitectura del Proyecto

```text
Monitor-de-Precios-Bot/
├── data/                  # Almacenamiento local (Historial CSV)
├── src/
│   ├── discover.py        # Crawler de búsqueda de productos
│   ├── scraper.py         # Extractor de precios (Scraper Core)
│   ├── sheet_manager.py   # Conector API Google Sheets
│   └── main.py            # Lógica de backend
├── app.py                 # Frontend (Streamlit Dashboard)
├── products.csv           # Base de datos de objetivos (Targets)
├── bot_activity.log       # Logs de auditoría del sistema
└── requirements.txt       # Dependencias

```

## ⚙️ Instalación y Uso

### 1. Clonar y Configurar

```bash
git clone [https://github.com/FacundoAguinaga/Monitor-de-Precios-Bot.git](https://github.com/FacundoAguinaga/Monitor-de-Precios-Bot.git)
cd Monitor-de-Precios-Bot
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
playwright install

```

### 2. Ejecutar la Plataforma

Para iniciar la interfaz gráfica de control:

```bash
streamlit run app.py

```

El sistema abrirá automáticamente el dashboard en tu navegador (`http://localhost:8501`).

### 3. Flujo de Trabajo Recomendado

1. Ve a la pestaña **Discovery** y busca un producto (ej: "iPhone 15").
2. Revisa la lista en la pestaña **Gestión**.
3. Ve a **Ejecución** y lanza el bot manual para obtener los precios actuales.
4. Analiza los resultados en el **Dashboard**.

## 🚧 Roadmap

* [x] Interfaz Gráfica con Streamlit.
* [x] Crawler de búsqueda automática.
* [x] Gestión de historial y limpieza de datos.
* [ ] Implementación de Alertas vía Telegram.
* [ ] Dockerización para despliegue en la nube.

---

**Disclaimer:** Proyecto desarrollado con fines educativos y de análisis de datos públicos.

