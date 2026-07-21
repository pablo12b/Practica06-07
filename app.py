import streamlit as st
import pandas as pd
import plotly.express as px
import psycopg2
import os
import requests
import asyncio
from dotenv import load_dotenv

# Importar funciones de nuestros módulos paralelos
from scraper_paralelo import ejecutar_scraping_completo
from analisis_sentimientos import ejecutar_analisis_completo

load_dotenv()

st.set_page_config(page_title="Proyecto Final - NLP & Paralelismo", layout="wide", page_icon="📊")

def load_data():
    """Carga los datos de la base de datos PostgreSQL a un DataFrame de Pandas."""
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'), port=os.getenv('DB_PORT'),
            dbname=os.getenv('DB_NAME'), user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD')
        )
        query = """
        SELECT red_social, contenido, sentimiento, 'Publicación' as tipo FROM publicaciones_sismo WHERE sentimiento IS NOT NULL
        UNION ALL
        SELECT p.red_social, c.contenido, c.sentimiento, 'Comentario' as tipo 
        FROM comentarios_sismo c
        JOIN publicaciones_sismo p ON c.publicacion_id = p.id
        WHERE c.sentimiento IS NOT NULL
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error al conectar con la Base de Datos: {e}")
        return pd.DataFrame()

def generar_storytelling(df, query):
    """Genera un análisis cualitativo usando Llama 3.3 vía OpenRouter."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key or "tu_api_key" in api_key:
        return "⚠️ Por favor, configura tu OPENROUTER_API_KEY en el archivo .env para generar el Storytelling."
        
    # Preparar el resumen estadístico para la IA
    conteo = df.groupby(['red_social', 'sentimiento']).size().unstack(fill_value=0)
    resumen_txt = conteo.to_string()
    
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    data = {
        "model": "meta-llama/llama-3.3-70b-instruct",
        "messages": [
            {
                "role": "system", 
                "content": "Eres un analista de datos experto. A partir de una tabla de distribución de sentimientos en redes sociales, redacta un párrafo de 'storytelling' (máximo 150 palabras) explicando las conclusiones cualitativas de la búsqueda. Explica qué red fue más hostil o positiva y por qué podría ser. No uses lenguaje de programación, habla fluidamente."
            },
            {
                "role": "user", 
                "content": f"Búsqueda realizada: '{query}'.\nDistribución de sentimientos:\n{resumen_txt}"
            }
        ],
        "temperature": 0.5,
    }
    
    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data, timeout=30)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error al generar storytelling: {e}"

# ================= INTERFAZ WEB =================

st.title("🌐 Pipeline Concurrente: Extracción y NLP")
st.markdown("Proyecto Final de Computación Paralela. Arquitectura basada en extracción concurrente (AsyncIO) e inferencia paralela (ThreadPoolExecutor) con LLMs.")

# SIDEBAR: PANEL DE CONTROL
with st.sidebar:
    st.header("⚙️ Panel de Control")
    search_query = st.text_input("Tema a analizar:", value="sismo venezuela")
    
    if st.button("🚀 Ejecutar Pipeline Completo", use_container_width=True):
        with st.status("Ejecutando Pipeline...", expanded=True) as status:
            st.write("1. Extrayendo datos de Facebook, Instagram, TikTok y Reddit concurrentemente...")
            try:
                # Ejecutar asyncio en un hilo normal
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(ejecutar_scraping_completo(search_query))
                st.write("✅ Extracción finalizada.")
            except Exception as e:
                st.error(f"Error en Scraper: {e}")
                
            st.write("2. Clasificando sentimientos con IA (Multi-Threading)...")
            try:
                procesados = ejecutar_analisis_completo()
                st.write(f"✅ Análisis completado ({procesados} textos evaluados).")
            except Exception as e:
                st.error(f"Error en Análisis: {e}")
                
            status.update(label="¡Pipeline completado con éxito!", state="complete", expanded=False)
            st.success("Refresca la página o mira el tablero actualizado.")

# MAIN: DASHBOARD Y VISUALIZACIÓN
df = load_data()

if not df.empty:
    st.header("📊 Tablero de Control y Storytelling")
    
    # Storytelling Card
    with st.expander("🤖 Análisis Interpretativo (Storytelling por Llama 3.3)", expanded=True):
        st.write("Generando análisis en vivo desde la base de datos...")
        with st.spinner("Llama 3.3 está analizando los datos..."):
            storytelling = generar_storytelling(df, search_query)
            st.info(storytelling)
            
    st.divider()
    
    # KPI Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Textos Procesados", len(df))
    col2.metric("Redes Analizadas", df['red_social'].nunique())
    try:
        col3.metric("Más Positiva", df[df['sentimiento'] == 'Muy positivo']['red_social'].mode()[0])
    except: col3.metric("Más Positiva", "N/A")
    try:
        col4.metric("Más Negativa", df[df['sentimiento'] == 'Muy negativo']['red_social'].mode()[0])
    except: col4.metric("Más Negativa", "N/A")
    
    # Gráficos
    st.subheader("Distribución de Sentimientos por Red Social")
    colA, colB = st.columns(2)
    
    with colA:
        # Gráfico de Barras Apiladas
        conteo = df.groupby(['red_social', 'sentimiento']).size().reset_index(name='cantidad')
        fig_bar = px.bar(conteo, x='red_social', y='cantidad', color='sentimiento', 
                         title="Comparativa de Sentimientos", barmode='group',
                         color_discrete_map={
                             "Muy positivo": "#28a745", "Positivo": "#94d3a2",
                             "Neutral": "#6c757d", "Mixto": "#ffc107",
                             "Irónico": "#fd7e14",
                             "Muy negativo": "#dc3545", "Negativo": "#e4606d",
                             "No clasificable": "#343a40"
                         })
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with colB:
        # Gráfico de Pastel Global
        conteo_global = df['sentimiento'].value_counts().reset_index()
        fig_pie = px.pie(conteo_global, values='count', names='sentimiento', 
                         title="Distribución Global del Tema", hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)
        
    st.divider()
    
    # Explorador de Datos
    st.subheader("🔍 Explorador de Comentarios (Raw Data)")
    red_filtro = st.selectbox("Filtrar por Red Social:", ["Todas"] + list(df['red_social'].unique()))
    sentimiento_filtro = st.selectbox("Filtrar por Sentimiento:", ["Todos"] + list(df['sentimiento'].unique()))
    
    df_filtrado = df
    if red_filtro != "Todas":
        df_filtrado = df_filtrado[df_filtrado['red_social'] == red_filtro]
    if sentimiento_filtro != "Todos":
        df_filtrado = df_filtrado[df_filtrado['sentimiento'] == sentimiento_filtro]
        
    st.dataframe(df_filtrado, use_container_width=True, height=300)
    
else:
    st.warning("No hay datos analizados en la Base de Datos. Ve al Panel de Control y ejecuta el Pipeline para extraer información.")
