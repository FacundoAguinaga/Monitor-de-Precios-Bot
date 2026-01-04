import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de la página
st.set_page_config(page_title="Monitor de Mercado", layout="wide")

# Título y Descripción Profesional
st.title("📊 Dashboard de Inteligencia de Precios")
st.markdown("""
Esta herramienta monitorea los precios de la competencia en tiempo real para facilitar la toma de decisiones estratégicas de **Dynamic Pricing**.
""")

# Cargar datos
try:
    df = pd.read_csv("data/history.csv")
    # Convertir fecha a objeto datetime
    df['fecha'] = pd.to_datetime(df['fecha'])
except FileNotFoundError:
    st.error("❌ No hay datos históricos aún. Ejecuta el bot primero.")
    st.stop()

# --- KPI METRICS (Lo que le importa al jefe) ---
st.markdown("### ⚡ Resumen de Última Hora")
latest_date = df['fecha'].max()
latest_data = df[df['fecha'] == latest_date]

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Productos Monitoreados", len(latest_data))
with col2:
    avg_price = latest_data['precio'].mean()
    st.metric("Precio Promedio Mercado", f"${avg_price:,.0f} ARS")
with col3:
    min_price = latest_data['precio'].min()
    st.metric("Precio Más Bajo Detectado", f"${min_price:,.0f} ARS")

st.divider()

# --- ANÁLISIS VISUAL ---
col_izq, col_der = st.columns([2, 1])

with col_izq:
    st.subheader("📈 Tendencia de Precios (Línea de Tiempo)")
    # Gráfico interactivo con Plotly
    fig = px.line(df, x="fecha", y="precio", color="producto", markers=True,
                  title="Evolución de Precios por Producto")
    st.plotly_chart(fig, use_container_width=True)

with col_der:
    st.subheader("🛒 Comparativa Actual")
    fig_bar = px.bar(latest_data, x="producto", y="precio", color="precio",
                     color_continuous_scale="Bluered")
    st.plotly_chart(fig_bar, use_container_width=True)

# --- TABLA DE DATOS ---
with st.expander("Ver Datos Crudos"):
    st.dataframe(df.sort_values(by="fecha", ascending=False))

# --- BOTÓN DE ACCIÓN MANUAL ---
if st.button("🔄 Ejecutar Scraper Manualmente"):
    st.warning("Esta función requiere conectar el script al dashboard (Feature en desarrollo).")