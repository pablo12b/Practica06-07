import os
import time
import concurrent.futures
import psycopg2
import requests
from dotenv import load_dotenv

load_dotenv()

def inicializar_columnas_db():
    """Agrega las columnas 'sentimiento' a las tablas si no existen."""
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT'),
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD')
        )
        cur = conn.cursor()
        
        cur.execute("ALTER TABLE publicaciones_sismo ADD COLUMN IF NOT EXISTS sentimiento VARCHAR(30);")
        cur.execute("ALTER TABLE comentarios_sismo ADD COLUMN IF NOT EXISTS sentimiento VARCHAR(30);")
        
        conn.commit()
        cur.close()
        conn.close()
        print("[DB] Columnas de sentimiento inicializadas correctamente.")
    except Exception as e:
        print(f"[ERROR DB] No se pudo alterar las tablas: {e}")

def obtener_textos_db():
    """Obtiene todas las publicaciones y comentarios que aún no tienen sentimiento."""
    datos = []
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT'),
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD')
        )
        cur = conn.cursor()
        
        # Obtener publicaciones
        cur.execute("SELECT id, contenido FROM publicaciones_sismo WHERE sentimiento IS NULL;")
        for row in cur.fetchall():
            datos.append((row[0], row[1], 'publicacion'))
            
        # Obtener comentarios
        cur.execute("SELECT id, contenido FROM comentarios_sismo WHERE sentimiento IS NULL;")
        for row in cur.fetchall():
            datos.append((row[0], row[1], 'comentario'))
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"[ERROR DB] No se pudieron obtener los textos: {e}")
        
    return datos

def analizar_sentimiento_api_io_bound(item):
    """
    Función de análisis de sentimientos usando IA en la nube (OpenRouter).
    Intencionalmente I/O-Bound (espera respuesta de red).
    item es una tupla: (id, texto, tipo)
    Retorna: (id, sentimiento, tipo)
    """
    item_id, texto, tipo = item
    
    if not texto:
        return (item_id, "No clasificable", tipo)
        
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key or "tu_api_key" in api_key:
        return (item_id, "Error_API_Key", tipo)
        
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "meta-llama/llama-3.3-70b-instruct",
        "messages": [
            {
                "role": "system", 
                "content": "Eres un experto analista de sentimientos de redes sociales. Evalúa el sentimiento del texto provisto. Responde ÚNICAMENTE con una de las siguientes cinco categorías exactas: 'Muy positivo', 'Muy negativo', 'Mixto', 'Irónico' o 'No clasificable'. No incluyas puntuación final, explicaciones ni ningún texto adicional."
            },
            {
                "role": "user", 
                "content": f"Texto a analizar: {texto}"
            }
        ],
        "temperature": 0.0,
        "max_tokens": 10
    }
    
    for intento in range(3): # Hasta 3 intentos
        try:
            response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data, timeout=60)
            response.raise_for_status()
            resultado = response.json()
            
            respuesta_ia = resultado["choices"][0]["message"]["content"].strip().replace('.', '')
            respuesta_lower = respuesta_ia.lower()
            
            # Normalización de la respuesta de la IA a las nuevas categorías
            if "muy positivo" in respuesta_lower: sentimiento = "Muy positivo"
            elif "muy negativo" in respuesta_lower: sentimiento = "Muy negativo"
            elif "mixto" in respuesta_lower: sentimiento = "Mixto"
            elif "irónico" in respuesta_lower or "ironico" in respuesta_lower: sentimiento = "Irónico"
            else: sentimiento = "No clasificable"
            
            break # Si fue exitoso, salir del bucle de reintentos
            
        except Exception as e:
            if intento == 2: # Si es el último intento y falla
                print(f"[API Error] Falló el análisis para ID {item_id} tras 3 intentos: {e}")
                sentimiento = "No clasificable" # Fallback en caso de timeout total
            else:
                time.sleep(2) # Pequeña pausa antes de reintentar
                
    return (item_id, sentimiento, tipo)

def actualizar_sentimientos_db(resultados):
    """Actualiza la base de datos con los sentimientos calculados."""
    if not resultados:
        return
        
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT'),
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD')
        )
        cur = conn.cursor()
        
        pubs_actualizadas = 0
        coms_actualizados = 0
        
        for item_id, sentimiento, tipo in resultados:
            if sentimiento == "Error_API_Key": continue
            
            if tipo == 'publicacion':
                cur.execute("UPDATE publicaciones_sismo SET sentimiento = %s WHERE id = %s", (sentimiento, item_id))
                pubs_actualizadas += 1
            elif tipo == 'comentario':
                cur.execute("UPDATE comentarios_sismo SET sentimiento = %s WHERE id = %s", (sentimiento, item_id))
                coms_actualizados += 1
                
        conn.commit()
        cur.close()
        conn.close()
        print(f"[EXITO] Actualizadas {pubs_actualizadas} publicaciones y {coms_actualizados} comentarios.")
    except Exception as e:
        print(f"[ERROR DB] No se pudieron guardar los resultados: {e}")

if __name__ == '__main__':
    print("=== INICIANDO ANÁLISIS DE SENTIMIENTOS PARALELO (I/O BOUND) ===")
    
    # 1. Preparar Base de Datos
    inicializar_columnas_db()
    
    # 2. Leer corpus de textos
    datos_a_procesar = obtener_textos_db()
    print(f"Textos pendientes de análisis: {len(datos_a_procesar)}")
    
    if datos_a_procesar:
        inicio = time.perf_counter()
        
        # 3. PARALELISMO BASADO EN HILOS (Threading)
        # Usamos ThreadPoolExecutor porque enviar datos a una API web y esperar la respuesta es una tarea I/O-Bound.
        max_hilos = 10 # 10 hilos para no saturar OpenRouter
        print(f"Lanzando {max_hilos} hilos concurrentes para peticiones a la API de OpenRouter (Llama 3.3)...")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_hilos) as executor:
            # map asigna los textos a los hilos de trabajo y espera los resultados
            resultados_clasificacion = list(executor.map(analizar_sentimiento_api_io_bound, datos_a_procesar))
            
        fin = time.perf_counter()
        print(f"Análisis IA concurrente completado en {fin - inicio:.2f} segundos.")
        
        # Revisión si faltó la API Key
        if any(res[1] == "Error_API_Key" for res in resultados_clasificacion):
            print("[ADVERTENCIA] No has configurado tu OPENROUTER_API_KEY en el archivo .env.")
            print("Por favor agrégala y vuelve a correr el script.")
        
        # 4. Guardar resultados en el almacenamiento relacional
        actualizar_sentimientos_db(resultados_clasificacion)
    else:
        print("No hay datos nuevos para procesar. Ejecuta el scraper primero.")
        
    print("=== PROCESO FINALIZADO ===")
