"""
Dashboard principal de la plataforma de monitoreo de precios.
Arquitectura modular con separación de responsabilidades.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import asyncio
import os
from typing import Optional, List
from datetime import datetime

# Importar módulos propios
from src.scraper import ProductScraper
from src.discover import ProductDiscoverer
from src.sheet_manager import SheetManager
from src.config import config


# ==================== CONFIGURACIÓN ====================

st.set_page_config(
    page_title="Price Monitor Hub",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ==================== ESTILOS CSS ====================

def inject_custom_css():
    """Inyecta estilos CSS personalizados"""
    st.markdown("""
    <style>
        .stMetric { 
            background-color: #f0f2f6; 
            padding: 10px; 
            border-radius: 10px; 
        }
        .stButton>button { 
            width: 100%; 
            border-radius: 5px; 
            height: 3em; 
        }
        div[data-testid="stButton"] > button[kind="secondary"] {
            border-color: #ff4b4b;
            color: #ff4b4b;
        }
        .success-box {
            padding: 1rem;
            border-radius: 0.5rem;
            background-color: #d4edda;
            border: 1px solid #c3e6cb;
        }
        .error-box {
            padding: 1rem;
            border-radius: 0.5rem;
            background-color: #f8d7da;
            border: 1px solid #f5c6cb;
        }
    </style>
    """, unsafe_allow_html=True)


# ==================== GESTIÓN DE DATOS ====================

class DataManager:
    """Maneja operaciones de lectura/escritura de datos"""
    
    @staticmethod
    def load_history() -> pd.DataFrame:
        """Carga el historial de precios"""
        try:
            df = pd.read_csv(config.storage.history_path)
            df['fecha'] = pd.to_datetime(df['fecha'])
            return df
        except FileNotFoundError:
            return pd.DataFrame()
    
    @staticmethod
    def load_targets() -> pd.DataFrame:
        """Carga la lista de URLs objetivo"""
        try:
            return pd.read_csv(config.storage.targets_path)
        except FileNotFoundError:
            return pd.DataFrame(columns=["url"])
    
    @staticmethod
    def save_targets(df: pd.DataFrame) -> bool:
        """Guarda la lista de URLs objetivo"""
        try:
            df.to_csv(config.storage.targets_path, index=False)
            return True
        except Exception as e:
            st.error(f"Error guardando: {e}")
            return False
    
    @staticmethod
    def clear_targets():
        """Limpia la lista de URLs objetivo"""
        with open(config.storage.targets_path, "w") as f:
            f.write("url\n")
    
    @staticmethod
    def clear_history():
        """Borra el historial de precios"""
        if config.storage.history_path.exists():
            config.storage.history_path.unlink()
    
    @staticmethod
    def get_log_lines(n: int = 10) -> List[str]:
        """Obtiene las últimas n líneas del log"""
        try:
            if os.path.exists(config.storage.log_file):
                with open(config.storage.log_file, "r") as f:
                    return f.readlines()[-n:]
            return ["Esperando actividad..."]
        except Exception:
            return ["Log inaccesible."]


# ==================== COMPONENTES UI ====================

class UIComponents:
    """Componentes reutilizables de la interfaz"""
    
    @staticmethod
    def render_kpi_metrics(df: pd.DataFrame):
        """Renderiza las métricas KPI principales"""
        if df.empty:
            return
        
        latest_date = df['fecha'].max()
        latest_data = df[df['fecha'] == latest_date]
        
        c1, c2, c3, c4 = st.columns(4)
        
        with c1:
            st.metric("Productos Rastreados", len(latest_data))
        
        with c2:
            avg = latest_data['precio'].mean() if not latest_data.empty else 0
            st.metric("Promedio Mercado", f"${avg:,.0f}")
        
        with c3:
            min_p = latest_data['precio'].min() if not latest_data.empty else 0
            st.metric("Mejor Precio", f"${min_p:,.0f}")
        
        with c4:
            st.metric("Actualizado", latest_date.strftime('%H:%M %d/%m'))
    
    @staticmethod
    def render_trend_chart(df: pd.DataFrame):
        """Renderiza gráfico de tendencias"""
        fig = px.line(
            df, 
            x="fecha", 
            y="precio", 
            color="producto", 
            markers=True,
            title="Evolución de Precios por Producto"
        )
        st.plotly_chart(fig, use_container_width=True, theme="streamlit")
    
    @staticmethod
    def render_comparison_chart(df: pd.DataFrame):
        """Renderiza gráfico de comparación actual"""
        fig_bar = px.bar(
            df, 
            x="producto", 
            y="precio", 
            color="precio",
            color_continuous_scale="Bluered"
        )
        st.plotly_chart(fig_bar, use_container_width=True, theme="streamlit")
    
    @staticmethod
    def render_welcome_message():
        """Mensaje de bienvenida cuando no hay datos"""
        st.info("👋 **Bienvenido al Monitor de Precios**")
        st.markdown("""
        ### Primeros Pasos:
        1. **Discovery** → Busca productos de tu interés
        2. **Gestión** → Revisa y edita la lista
        3. **Ejecución** → Lanza el scraping
        4. **Dashboard** → Analiza los resultados
        
        💡 **Tip**: Comienza buscando "iPhone 15" en Discovery
        """)


# ==================== LÓGICA DE NEGOCIO ====================

class ScraperController:
    """Controla las operaciones de scraping"""
    
    @staticmethod
    async def run_scraping(urls: List[str]) -> Optional[pd.DataFrame]:
        """
        Ejecuta el proceso de scraping.
        
        Returns:
            DataFrame con resultados o None si falla
        """
        if not urls:
            return None
        
        bot = ProductScraper()
        results = []
        
        progress = st.progress(0)
        status = st.empty()
        total = len(urls)
        
        for i, url in enumerate(urls):
            status.text(f"Scraping ({i+1}/{total}): {url[:50]}...")
            data = await bot.scrape_mercadolibre(url)
            if data:
                results.append(data)
            progress.progress(int((i+1)/total * 90))
        
        await bot.close()
        
        if not results:
            return None
        
        status.text("Procesando datos...")
        df = pd.DataFrame(results)
        df['fecha'] = pd.Timestamp.now()
        
        # Guardar en CSV
        header = not config.storage.history_path.exists()
        df.to_csv(
            config.storage.history_path, 
            mode='a', 
            header=header, 
            index=False
        )
        
        # Intentar subir a Google Sheets
        try:
            if config.google_sheets.is_configured():
                SheetManager().save_data(results)
        except Exception as e:
            st.warning(f"⚠️ No se pudo sincronizar con Google Sheets: {e}")
        
        progress.progress(100)
        status.text("✅ Completado")
        
        return df


# ==================== SIDEBAR ====================

def render_sidebar():
    """Renderiza la barra lateral"""
    with st.sidebar:
        st.title("🎛️ Centro de Control")
        st.markdown("---")
        
        # Estado del sistema
        targets_count = len(DataManager.load_targets())
        history_count = len(DataManager.load_history())
        
        st.info(f"""
        **Estado del Sistema**
        - 📋 URLs objetivo: {targets_count}
        - 📊 Registros históricos: {history_count}
        - ✅ Sistema: ACTIVO
        """)
        
        if st.button("🔄 Refrescar Datos"):
            st.rerun()
        
        st.markdown("---")
        
        # Logs recientes
        st.markdown("### 📝 Logs Recientes")
        log_lines = DataManager.get_log_lines(8)
        for line in log_lines:
            st.caption(line.strip())


# ==================== TABS ====================

def render_dashboard_tab():
    """Tab de Dashboard Principal"""
    df = DataManager.load_history()
    
    if df.empty:
        UIComponents.render_welcome_message()
        return
    
    # KPIs
    UIComponents.render_kpi_metrics(df)
    
    st.divider()
    
    # Gráficos
    col_g1, col_g2 = st.columns([2, 1])
    
    with col_g1:
        st.subheader("📈 Tendencia Histórica")
        UIComponents.render_trend_chart(df)
    
    with col_g2:
        st.subheader("📊 Comparativa Actual")
        latest_date = df['fecha'].max()
        latest_data = df[df['fecha'] == latest_date]
        UIComponents.render_comparison_chart(latest_data)
    
    # Tabla completa
    with st.expander("🔍 Ver tabla de datos completa"):
        st.dataframe(
            df.sort_values(by="fecha", ascending=False),
            use_container_width=True
        )


def render_discovery_tab():
    """Tab de Descubrimiento de Productos"""
    st.header("🔍 Buscador Inteligente")
    st.markdown("Encuentra competidores y agrégalos automáticamente a tu lista de monitoreo.")
    
    col_search, col_limit = st.columns([3, 1])
    keyword = col_search.text_input(
        "Producto a buscar",
        placeholder="Ej: Notebook Lenovo Ideapad"
    )
    limit = col_limit.number_input(
        "Cantidad",
        min_value=1,
        max_value=20,
        value=5
    )
    
    st.divider()
    
    # Configuración
    st.markdown("##### ⚙️ Modo de Carga")
    replace_mode = st.toggle(
        "🗑️ Reemplazar lista existente (borra URLs anteriores)",
        value=False
    )
    
    if replace_mode:
        st.warning("⚠️ Esto eliminará todas las URLs anteriores")
    
    if st.button("🔎 Buscar y Agregar", type="primary"):
        if not keyword:
            st.error("❌ Ingresa una palabra clave")
            return
        
        mode_text = "REEMPLAZAR" if replace_mode else "AGREGAR"
        
        with st.status(f"🕵️ Buscando '{keyword}'...", expanded=True) as status:
            finder = ProductDiscoverer()
            status.write(f"Modo: {mode_text}")
            
            links = asyncio.run(finder.search_products(keyword, limit))
            
            if links:
                status.write(f"✅ Encontrados {len(links)} productos")
                mode_arg = "replace" if replace_mode else "append"
                finder.save_to_csv(links, mode=mode_arg)
                
                status.update(label="✅ Completado", state="complete")
                
                if replace_mode:
                    st.success(f"Base de datos limpiada. {len(links)} productos nuevos.")
                else:
                    st.success(f"Se agregaron {len(links)} productos a la lista.")
                
                # Mostrar URLs encontradas
                with st.expander("Ver URLs agregadas"):
                    for i, link in enumerate(links, 1):
                        st.text(f"{i}. {link}")
            else:
                status.update(label="❌ Sin resultados", state="error")
                st.error("No se encontraron productos válidos")


def render_management_tab():
    """Tab de Gestión de Datos"""
    st.header("📋 Gestión de Base de Datos")
    
    # Sección 1: URLs Objetivo
    st.subheader("1️⃣ Lista de Objetivos")
    st.caption("URLs que se monitoreará en el próximo scraping")
    
    targets_df = DataManager.load_targets()
    st.info(f"📊 Actualmente: **{len(targets_df)}** URLs")
    
    # Editor de datos
    edited_df = st.data_editor(
        targets_df,
        num_rows="dynamic",
        use_container_width=True,
        key="editor_urls"
    )
    
    col_save, col_clear = st.columns(2)
    
    with col_save:
        if st.button("💾 Guardar Cambios", type="primary"):
            if DataManager.save_targets(edited_df):
                st.toast("✅ Lista actualizada", icon="✅")
                st.rerun()
    
    with col_clear:
        if st.button("🗑️ Vaciar Lista", type="secondary"):
            DataManager.clear_targets()
            st.toast("🗑️ Lista vaciada", icon="🗑️")
            st.rerun()
    
    st.divider()
    
    # Sección 2: Historial
    st.subheader("2️⃣ Historial de Precios")
    st.caption("Datos históricos que alimentan el Dashboard")
    
    history_df = DataManager.load_history()
    st.info(f"📊 Registros totales: **{len(history_df)}**")
    
    if not history_df.empty:
        # Preview de los últimos datos
        with st.expander("Vista previa (últimos 10 registros)"):
            st.dataframe(
                history_df.tail(10),
                use_container_width=True
            )
    
    if st.button("🔥 BORRAR HISTORIAL", type="secondary"):
        DataManager.clear_history()
        st.toast("🧹 Historial eliminado", icon="🧹")
        st.rerun()


def render_execution_tab():
    """Tab de Ejecución de Scraping"""
    st.header("⚡ Ejecución Manual")
    
    targets_df = DataManager.load_targets()
    
    if targets_df.empty:
        st.warning("⚠️ No hay URLs en la lista. Ve a **Discovery** primero.")
        return
    
    st.info(f"🎯 Listo para scrapear **{len(targets_df)}** URLs")
    
    if st.button("▶️ EJECUTAR SCRAPING", type="primary", use_container_width=True):
        # Obtener lista de URLs
        col_name = 'url' if 'url' in targets_df.columns else targets_df.columns[0]
        urls = targets_df[col_name].dropna().tolist()
        
        if not urls:
            st.error("❌ Lista vacía o corrupta")
            return
        
        # Ejecutar scraping
        result_df = asyncio.run(ScraperController.run_scraping(urls))
        
        if result_df is not None and not result_df.empty:
            st.success(f"✅ Scraping completado: {len(result_df)}/{len(urls)} productos")
            
            # Mostrar resultados
            st.subheader("📊 Resultados")
            st.dataframe(result_df[["producto", "precio", "moneda"]], use_container_width=True)
            
            st.info("💡 Ve al Dashboard para ver los gráficos actualizados")
        else:
            st.error("❌ No se obtuvieron datos. Revisa los logs.")


# ==================== MAIN ====================

def main():
    """Función principal de la aplicación"""
    inject_custom_css()
    render_sidebar()
    
    # Título
    st.title("🚀 Monitor de Inteligencia de Precios")
    
    # Tabs principales
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Dashboard",
        "🕵️ Discovery",
        "📋 Gestión",
        "⚡ Ejecución"
    ])
    
    with tab1:
        render_dashboard_tab()
    
    with tab2:
        render_discovery_tab()
    
    with tab3:
        render_management_tab()
    
    with tab4:
        render_execution_tab()


if __name__ == "__main__":
    main()