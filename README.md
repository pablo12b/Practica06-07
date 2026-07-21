# Proyecto Final: Pipeline Concurrente de Extracción y Análisis de Redes Sociales

Este proyecto presenta una **Solución Web Integral** que aplica técnicas de Computación Paralela e Inteligencia Artificial para la extracción masiva de datos (Web Scraping) desde cuatro redes sociales simultáneamente, seguida de una clasificación avanzada de sentimientos utilizando Modelos de Lenguaje Grande (LLMs) y la generación de *Storytelling*.

## 🚀 Arquitectura y Tecnologías
- **Extracción Concurrente (I/O-Bound):** `asyncio` con Playwright para extraer datos de Facebook, Instagram, TikTok y **Reddit** en paralelo.
- **Análisis de Sentimientos Paralelo (I/O-Bound):** `ThreadPoolExecutor` para lanzar peticiones concurrentes a la API de OpenRouter (Llama 3.3 70B Instruct).
- **Aplicación Web:** `Streamlit` para la interfaz de usuario y `Plotly` para la visualización de datos interactiva.
- **Base de Datos:** `PostgreSQL` para garantizar la trazabilidad de la información (Esquema relacional).

---

## ⚙️ Requisitos Previos

1.  **PostgreSQL:** Debes tener un servidor PostgreSQL local o en la nube ejecutándose.
2.  **API Key de OpenRouter:** Regístrate en [OpenRouter.ai](https://openrouter.ai/) y genera una API Key para utilizar el modelo Llama 3.3.
3.  **Variables de Entorno:** Configura tu archivo `.env` en la raíz del proyecto:
    ```env
    DB_HOST=localhost
    DB_PORT=5432
    DB_NAME=tu_base_datos
    DB_USER=tu_usuario
    DB_PASSWORD=tu_contraseña
    OPENROUTER_API_KEY=tu_api_key_aqui
    ```
4.  **Dependencias de Python:** Instala los requerimientos ejecutando:
    ```bash
    pip install -r requirements.txt
    playwright install chromium
    ```

---

## 🛠️ Instrucciones de Ejecución

El flujo del proyecto se ha simplificado y unificado gracias a la aplicación web. Sigue estos tres pasos para inicializar el sistema:

### Paso 1: Inicialización de la Base de Datos
Antes de ejecutar la aplicación, debemos crear las tablas relacionales. Este paso borrará tablas anteriores y creará el esquema limpio.
```bash
python db_init.py
```

### Paso 2: Autenticación Manual (Anti-CAPTCHA)
Las redes sociales (especialmente Facebook e Instagram) bloquean la extracción agresiva. Para evadir esto, ejecutaremos una única vez el script de login:
```bash
python login_redes.py
```
> **Instrucción:** Se abrirá un navegador. Inicia sesión manualmente con tus cuentas en las pestañas que se abran. Al terminar, presiona ENTER en la consola. Esto guardará tu sesión en la carpeta `playwright_profile`, volviendo al scraper indetectable.

### Paso 3: Ejecución de la Aplicación Web (Streamlit)
Levanta la interfaz gráfica que orquesta todos los procesos paralelos:
```bash
streamlit run app.py
```
> **Flujo en la Web:**
> 1. Abre el navegador en la URL indicada por Streamlit (usualmente `http://localhost:8501`).
> 2. En el panel izquierdo, ingresa tu término de búsqueda (Ej. *"Sismo Venezuela"*).
> 3. Haz click en **"Ejecutar Pipeline Completo"**.
> 4. Observa cómo el Backend extrae los datos de las 4 redes en paralelo y luego lanza los 10 hilos concurrentes para consultar a Llama 3.3.
> 5. Al finalizar, la web dibujará el Tablero de Control y Llama 3.3 generará un párrafo de *Storytelling* explicando los hallazgos.

---

## 📊 Clasificación y Visualización (Resultados)
A diferencia de prácticas anteriores que usaban diccionarios locales limitados, este proyecto utiliza Inteligencia Artificial de última generación para clasificar semánticamente cada comentario en una de 5 categorías exigidas:
- **Muy positivo**
- **Positivo/Neutral/Mixto** (según el contexto)
- **Muy negativo**
- **Irónico**
- **No clasificable**

La aplicación web te permitirá explorar estos resultados de manera agrupada a través de gráficos de Plotly y filtros de tabla en tiempo real, evidenciando el poder de la Computación Paralela combinada con la Inteligencia Artificial.
