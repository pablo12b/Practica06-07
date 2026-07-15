import os
import time
import multiprocessing
import psycopg2
import re
from dotenv import load_dotenv

load_dotenv()

# Diccionario básico de polaridad en español para el análisis local
# Se usa este enfoque local para evitar llamadas I/O a APIs externas y asegurar que la tarea sea CPU-Bound.
PALABRAS_POSITIVAS = {'bien', 'excelente', 'gracias', 'afortunadamente', 'seguro', 'proteja', 'libre', 'bendiciones', 'estable', 'recuperando', 'ayuda', 'rescate', 'calma'}
PALABRAS_NEGATIVAS = {'temblor', 'terremoto', 'miedo', 'fuerte', 'pánico', 'sismo', 'heridos', 'daños', 'peligro', 'triste', 'desastre', 'replica', 'susto', 'terrible', 'gravedad', 'lamentable'}

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
        
        cur.execute("ALTER TABLE publicaciones_sismo ADD COLUMN IF NOT EXISTS sentimiento VARCHAR(20);")
        cur.execute("ALTER TABLE comentarios_sismo ADD COLUMN IF NOT EXISTS sentimiento VARCHAR(20);")
        
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
        
        # Obtener publicaciones (id, contenido, 'publicacion')
        cur.execute("SELECT id, contenido FROM publicaciones_sismo WHERE sentimiento IS NULL;")
        for row in cur.fetchall():
            datos.append((row[0], row[1], 'publicacion'))
            
        # Obtener comentarios (id, contenido, 'comentario')
        cur.execute("SELECT id, contenido FROM comentarios_sismo WHERE sentimiento IS NULL;")
        for row in cur.fetchall():
            datos.append((row[0], row[1], 'comentario'))
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"[ERROR DB] No se pudieron obtener los textos: {e}")
        
    return datos

def analizar_sentimiento_cpu_bound(item):
    """
    Función pura de análisis de sentimientos.
    Intencionalmente CPU-Bound (agrega carga matemática para simular procesamiento complejo de NLP).
    item es una tupla: (id, texto, tipo)
    Retorna: (id, sentimiento, tipo)
    """
    item_id, texto, tipo = item
    
    if not texto:
        return (item_id, "Neutral", tipo)
        
    texto_limpio = re.sub(r'[^\w\s]', '', texto.lower())
    palabras = texto_limpio.split()
    
    score = 0
    for palabra in palabras:
        if palabra in PALABRAS_POSITIVAS:
            score += 1
        elif palabra in PALABRAS_NEGATIVAS:
            score -= 1
            
        # Simulador de carga de red neuronal/NLP profundo (CPU-Bound estricto)
        # Esto justifica matemáticamente el uso de Multiprocessing sobre Threading
        _carga = sum([i * i for i in range(10000)])
            
    if score > 0:
        sentimiento = "Positivo"
    elif score < 0:
        sentimiento = "Negativo"
    else:
        sentimiento = "Neutral"
        
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
    print("=== INICIANDO ANÁLISIS DE SENTIMIENTOS PARALELO ===")
    
    # 1. Preparar Base de Datos
    inicializar_columnas_db()
    
    # 2. Leer corpus de textos
    datos_a_procesar = obtener_textos_db()
    print(f"Textos pendientes de análisis: {len(datos_a_procesar)}")
    
    if datos_a_procesar:
        inicio = time.perf_counter()
        
        # 3. PARALELISMO BASADO EN PROCESOS (Multiprocessing)
        # Usamos Pool para distribuir los textos entre todos los núcleos disponibles.
        # Justificación: El NLP (tokenización y cálculos) es puramente CPU-Bound.
        num_nucleos = multiprocessing.cpu_count()
        print(f"Distribuyendo carga NLP en {num_nucleos} núcleos lógicos...")
        
        with multiprocessing.Pool(processes=num_nucleos) as pool:
            # map bloquea hasta que todos los procesos hijos terminen de analizar
            resultados_clasificacion = pool.map(analizar_sentimiento_cpu_bound, datos_a_procesar)
            
        fin = time.perf_counter()
        print(f"Análisis concurrente completado en {fin - inicio:.2f} segundos.")
        
        # 4. Guardar resultados en el almacenamiento relacional
        actualizar_sentimientos_db(resultados_clasificacion)
    else:
        print("No hay datos nuevos para procesar. Ejecuta el scraper primero.")
        
    print("=== PROCESO FINALIZADO ===")
