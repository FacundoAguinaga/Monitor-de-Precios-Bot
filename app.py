import streamlit as st
import pandas as pd
import plotly.express as px
import asyncio
import os
import csv

# Importamos módulos
from src.scraper import ProductScraper
from src.discover import ProductDiscoverer
from src.sheet_manager import SheetManager

# --- CONFIGURACIÓN ---
st.set_page_config(
    page_title="Price Monitor Hub",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS ---
st.markdown("""
<style>
    .stMetric { background-color: #f0f2f6; padding: 10px; border-radius: 10px; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; }
    /* Destacar botones de borrado */
    div[data-testid="stButton"] > button[kind="secondary"] {
        border-color: #ff4b4b;
        color: #ff4b4b;
    }
</style>
""", unsafe_allow_html=True)

# --- FUNCIONES ---
def load_data():
    try:
        df = pd.read_csv("data/history.csv")
        df['fecha'] = pd.to_datetime(df['fecha'])
        return df
    except FileNotFoundError:
        return pd.DataFrame()

def load_targets():
    try:
        return pd.read_csv("products.csv")
    except FileNotFoundError:
        return pd.DataFrame(columns=["url"])

def save_targets(df):
    df.to_csv("products.csv", index=False)

def clear_targets():
    """Borra la lista de búsqueda (products.csv)"""
    with open("products.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["url"])

def clear_history():
    """Borra los datos históricos del dashboard (history.csv)"""
    if os.path.exists("data/history.csv"):
        os.remove("data/history.csv")
        # Opcional: Recrear vacío con headers si prefieres no borrar el archivo
        # with open("data/history.csv", "w") as f: f.write("fecha,producto,precio,url,moneda\n")

# --- SIDEBAR ---
with st.sidebar:
    st.title("🎛️ Centro de Control")
    st.markdown("---")
    st.info("Estado del Sistema: **ACTIVO**")
    if st.button("🔄 Refrescar Datos"):
        st.rerun()
    st.markdown("---")
    st.markdown("### 📝 Logs Recientes")
    try:
        if os.path.exists("bot_activity.log"):
            with open("bot_activity.log", "r") as f:
                lines = f.readlines()[-10:] 
                for line in lines:
                    st.caption(line.strip())
        else:
            st.caption("Esperando actividad...")
    except:
        st.caption("Log inaccesible.")

st.title("🚀 Monitor de Inteligencia de Precios")

# --- PESTAÑAS ---
tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "🕵️ Discovery (Buscador)", "📋 Gestión de Datos", "⚡ Ejecución"])

# === TAB 1: DASHBOARD ===
with tab1:
    df = load_data()
    if not df.empty:
        latest_date = df['fecha'].max()
        latest_data = df[df['fecha'] == latest_date]
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Productos Rastreados", len(latest_data))
        
        avg = latest_data['precio'].mean() if not latest_data.empty else 0
        c2.metric("Promedio Mercado", f"${avg:,.0f}")
        
        min_p = latest_data['precio'].min() if not latest_data.empty else 0
        c3.metric("Mejor Precio", f"${min_p:,.0f}")
        
        c4.metric("Actualizado", latest_date.strftime('%H:%M %d/%m'))
        
        st.divider()
        col_g1, col_g2 = st.columns([2, 1])
        with col_g1:
            st.subheader("Tendencia Histórica")
            fig = px.line(df, x="fecha", y="precio", color="producto", markers=True)
            st.plotly_chart(fig, theme="streamlit")
        with col_g2:
            st.subheader("Comparativa Actual")
            fig_bar = px.bar(latest_data, x="producto", y="precio", color="precio")
            st.plotly_chart(fig_bar, theme="streamlit")
            
        # Tabla de datos crudos al final
        with st.expander("Ver tabla de datos completa"):
            st.dataframe(df.sort_values(by="fecha", ascending=False), width="stretch")
            
    else:
        st.info("👋 **Bienvenido.** No hay datos históricos para mostrar.")
        st.markdown("""
        **Pasos para iniciar:**
        1. Ve a la pestaña **Discovery** para buscar productos.
        2. Ve a la pestaña **Ejecución** para obtener los precios actuales.
        """)

# === TAB 2: DISCOVERY ===
with tab2:
    st.header("🔍 Buscador Inteligente")
    st.markdown("Busca competidores y agrégalos a tu base de datos.")
    
    col_search, col_limit = st.columns([3, 1])
    keyword = col_search.text_input("Producto a buscar", placeholder="Ej: Playstation 5")
    limit = col_limit.number_input("Cantidad", 1, 10, 3)
    
    st.divider()
    
    # MODO DE CARGA
    st.markdown("##### ⚙️ Configuración de carga")
    replace_mode = st.toggle("🗑️ Borrar lista anterior antes de agregar nuevos (Modo Reemplazo)", value=False)
    
    if st.button("🔎 Buscar y Procesar"):
        if keyword:
            mode_text = "REEMPLAZAR" if replace_mode else "AGREGAR"
            with st.status(f"🕵️ Iniciando Crawler (Modo: {mode_text})...", expanded=True) as status:
                finder = ProductDiscoverer()
                status.write(f"Buscando '{keyword}'...")
                
                links = asyncio.run(finder.search_products(keyword, limit))
                
                if links:
                    status.write(f"✅ Encontrados {len(links)} productos.")
                    mode_arg = "replace" if replace_mode else "append"
                    finder.save_to_csv(links, mode=mode_arg)
                    status.update(label="¡Proceso completado!", state="complete", expanded=False)
                    
                    if replace_mode:
                        st.success(f"Base de datos limpiada. Se agregaron {len(links)} productos nuevos.")
                    else:
                        st.success(f"Se sumaron {len(links)} productos a la lista existente.")
                else:
                    status.update(label="Sin resultados", state="error")
                    st.error("No se encontraron productos válidos.")
        else:
            st.warning("Ingresa una palabra clave.")

# === TAB 3: GESTIÓN (NUEVO: BOTÓN BORRAR HISTORIAL) ===
with tab3:
    st.header("📋 Gestión de Base de Datos")
    
    # SECCIÓN 1: URLs (Futuro)
    st.subheader("1. Lista de Objetivos (Lo que se va a buscar)")
    targets_df = load_targets()
    st.caption(f"Actualmente monitoreando **{len(targets_df)}** URLs.")
    
    edited_df = st.data_editor(targets_df, num_rows="dynamic", width="stretch", key="editor_urls")
    
    col_save, col_clear_list = st.columns(2)
    with col_save:
        if st.button("💾 Guardar Cambios en Lista"):
            save_targets(edited_df)
            st.toast("Lista actualizada", icon="✅")
            st.rerun()
    with col_clear_list:
        if st.button("🗑️ Borrar toda la Lista de URLs", type="secondary"):
            clear_targets()
            st.toast("Lista vaciada", icon="🗑️")
            st.rerun()

    st.divider()

    # SECCIÓN 2: Historial (Pasado)
    st.subheader("2. Historial de Precios (Datos del Dashboard)")
    st.caption("Aquí se guardan los precios recolectados en el pasado para generar los gráficos.")
    
    if st.button("🔥 BORRAR HISTORIAL DE DATOS (Reset Dashboard)", type="secondary"):
        clear_history()
        st.toast("Historial eliminado. El Dashboard está limpio.", icon="🧹")
        st.rerun()

# === TAB 4: EJECUCIÓN ===
with tab4:
    st.header("⚡ Ejecución Manual")
    if st.button("▶️ EJECUTAR SCRAPING", type="primary"):
        progress = st.progress(0)
        status = st.empty()
        
        try:
            raw_targets = load_targets()
            if raw_targets.empty:
                st.error("Lista de URLs vacía. Ve a Discovery.")
            else:
                col_name = 'url' if 'url' in raw_targets.columns else raw_targets.columns[0]
                targets = raw_targets[col_name].dropna().tolist()
                
                bot = ProductScraper()
                res = []
                total = len(targets)
                
                for i, url in enumerate(targets):
                    status.text(f"Scraping ({i+1}/{total}): {url[:30]}...")
                    data = asyncio.run(bot.scrape_mercadolibre(url))
                    if data: res.append(data)
                    progress.progress(int((i+1)/total * 90))
                
                if res:
                    status.text("Guardando datos...")
                    df_r = pd.DataFrame(res)
                    df_r['fecha'] = pd.Timestamp.now()
                    
                    os.makedirs("data", exist_ok=True)
                    header = not os.path.exists('data/history.csv')
                    df_r.to_csv('data/history.csv', mode='a', header=header, index=False)
                    
                    try:
                        SheetManager().save_data(res)
                    except: pass
                    
                    progress.progress(100)
                    st.success("✅ Completado")
                    st.dataframe(df_r, width="stretch")
                else:
                    st.error("❌ Fallo general.")
        except Exception as e:
            st.error(f"Error: {e}")