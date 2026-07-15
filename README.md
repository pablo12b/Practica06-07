# Práctica de Laboratorio 06: Extracción y Análisis Paralelo de Redes Sociales

Este proyecto simula un sistema integral de **Extracción Concurrente de Datos** (Web Scraping) desde múltiples redes sociales y su posterior **Análisis de Sentimientos en Paralelo**, utilizando PostgreSQL como sistema gestor de base de datos relacional para garantizar la trazabilidad de la información.

## 🚀 Requisitos Previos

1.  **PostgreSQL:** Debes tener un servidor PostgreSQL ejecutándose.
2.  **Variables de Entorno:** Debes configurar tu archivo `.env` en la raíz del proyecto con tus credenciales de base de datos:
    ```env
    DB_HOST=localhost
    DB_PORT=5432
    DB_NAME=tu_base_datos
    DB_USER=tu_usuario
    DB_PASSWORD=tu_contraseña
    ```
3.  **Dependencias de Python:**
    Instalar los requerimientos ejecutando:
    ```bash
    pip install -r requirements.txt
    playwright install chromium
    ```

---

## 🛠️ Instrucciones de Ejecución (Paso a Paso)

El flujo del proyecto consta de cuatro pasos lógicos que deben ejecutarse en orden:

### Paso 1: Inicialización de la Base de Datos
Antes de ejecutar cualquier script, debemos crear las tablas relacionales (`publicaciones_sismo` y `comentarios_sismo`).

```bash
python db_init.py
```
> **Nota:** Este script borrará las tablas anteriores (si existen) y creará el esquema limpio para la práctica.

---

### Paso 2: Autenticación Manual (Anti-CAPTCHA)
Las redes sociales bloquean la extracción si no tienes una sesión iniciada. Para solucionar esto sin ser detectados como bots, ejecutamos este script:

```bash
python login_redes.py
```
> **Nota:** Se abrirá un navegador visible. Inicia sesión con tus cuentas de prueba manualmente en las 3 pestañas y luego presiona ENTER en la consola. Esto guardará toda tu sesión en la carpeta persistente `playwright_profile` como si fuera un navegador de uso diario, haciendo el scraper indetectable.

---

### Paso 3: Extracción de Datos (I/O-Bound)
El script de extracción utiliza **Asincronía (`asyncio`)** para ejecutar la recolección de datos en Facebook, Instagram y TikTok de forma concurrente, ya que el web scraping es una tarea limitada por los tiempos de respuesta de internet (I/O-Bound).

```bash
python scraper_paralelo.py
```
**Mecanismo Anti-Baneos:** 
Para evitar ser bloqueados por los servidores (Rate-Limiting), el script simula la extracción por lotes. Entre cada lote extraído, se introdujo intencionalmente un retraso asíncrono de **60 segundos** (`await asyncio.sleep(60)`). Al usar concurrencia, las 3 redes sociales hacen sus pausas en paralelo sin bloquearse entre sí, optimizando el tiempo total.

---

### Paso 4: Análisis de Sentimientos Paralelo (CPU-Bound)
Una vez que la base de datos esté llena con las publicaciones, procedemos a clasificar los textos en *Positivo, Negativo o Neutral*.
Dado que el Procesamiento de Lenguaje Natural (NLP) requiere mucho cálculo matemático, es una tarea **limitada por Procesador (CPU-Bound)**. Por ende, este script evoca la librería `multiprocessing` (Paralelismo basado en Procesos) para evadir el GIL de Python y utilizar el 100% de los núcleos físicos del CPU.

```bash
python analisis_sentimientos.py
```
**Lo que hace este script:**
1. Altera la base de datos mágicamente para agregar la columna `sentimiento`.
2. Lee todos los textos pendientes.
3. Divide los textos en *lotes (chunks)* y los procesa en paralelo.
4. Actualiza la base de datos con los resultados conservando toda la trazabilidad.

---

## 📊 Trazabilidad de Resultados
Al finalizar, puedes abrir tu gestor de PostgreSQL (como pgAdmin) y consultar la tabla `publicaciones_sismo` y `comentarios_sismo`. 
Verás que cada texto analizado mantiene su trazabilidad completa: sabrás de qué `red_social` proviene, su `url` original, la métrica de `likes` y `vistas`, y finalmente, su `sentimiento` etiquetado para su posterior graficación o reporte académico.
