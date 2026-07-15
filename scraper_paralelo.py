import asyncio
import os
import psycopg2
from dotenv import load_dotenv
from playwright.async_api import async_playwright
from datetime import datetime

load_dotenv()

# Función auxiliar para guardar una publicación y obtener su ID
def guardar_publicacion_db(red_social, autor, contenido, url, likes, vistas):
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT'),
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD')
        )
        cur = conn.cursor()
        
        # Insertar y devolver el ID (si ya existe por URL, actualizamos likes/vistas y devolvemos ID)
        cur.execute("""
            INSERT INTO publicaciones_sismo (red_social, autor, contenido, fecha, url, likes, vistas)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (url) DO UPDATE 
            SET likes = EXCLUDED.likes, vistas = EXCLUDED.vistas
            RETURNING id
        """, (red_social, autor, contenido, datetime.now(), url, likes, vistas))
        
        pub_id = cur.fetchone()[0]
        
        conn.commit()
        cur.close()
        conn.close()
        print(f"[{red_social}] Guardado en DB (Post ID: {pub_id}): {autor} | Likes: {likes} | Vistas: {vistas}")
        return pub_id
    except Exception as e:
        print(f"[{red_social}] Error al guardar publicación en DB: {e}")
        return None

# Función auxiliar para guardar un comentario
def guardar_comentario_db(publicacion_id, autor, contenido):
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT'),
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD')
        )
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO comentarios_sismo (publicacion_id, autor, contenido)
            VALUES (%s, %s, %s)
        """, (publicacion_id, autor, contenido))
        
        conn.commit()
        cur.close()
        conn.close()
        print(f"  -> Comentario guardado: {autor}")
    except Exception as e:
        print(f"  -> Error al guardar comentario: {e}")


async def scrape_facebook(browser):
    print("[Facebook] Iniciando proceso de scraping...")
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    page = await context.new_page()
    try:
        await page.goto("https://www.facebook.com/search/posts/?q=terremoto%20venezuela", timeout=60000)
        await page.wait_for_timeout(5000)
        
        print("[Facebook] Extrayendo publicaciones...")
        
        # EJEMPLO SIMULADO DE EXTRACCIÓN + COMENTARIOS
        pub1_id = guardar_publicacion_db("Facebook", "Noticias FB", "Sismo de magnitud 5.0 reportado en Caracas, Venezuela. #terremoto", "https://facebook.com/post/1", likes=1500, vistas=45000)
        if pub1_id:
            guardar_comentario_db(pub1_id, "Carlos", "Sintieron eso?? Fue fuertísimo!")
            guardar_comentario_db(pub1_id, "Maria", "Dios nos proteja.")
            
        pub2_id = guardar_publicacion_db("Facebook", "Usuario Local", "Se sintió fuerte el temblor en Valencia. Todos bien por aquí.", "https://facebook.com/post/2", likes=45, vistas=800)
        if pub2_id:
            guardar_comentario_db(pub2_id, "Ana", "Sí, los vidrios vibraron.")
            
    except Exception as e:
        print(f"[Facebook] Error: {e}")
    finally:
        await context.close()


async def scrape_instagram(browser):
    print("[Instagram] Iniciando proceso de scraping...")
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
    )
    page = await context.new_page()
    try:
        await page.goto("https://www.instagram.com/explore/tags/terremotovenezuela/", timeout=60000)
        await page.wait_for_timeout(5000)
        
        print("[Instagram] Extrayendo posts del hashtag...")
        
        # EJEMPLO SIMULADO
        pub1_id = guardar_publicacion_db("Instagram", "@noticias_ig", "Alerta sísmica activada en Venezuela hace pocos minutos. Detalles en nuestras historias.", "https://instagram.com/p/123", likes=5600, vistas=120000)
        if pub1_id:
            guardar_comentario_db(pub1_id, "user_99", "Qué miedo, estaba en el piso 10 🏢")
            guardar_comentario_db(pub1_id, "vzla_libre", "Esperemos no haya réplicas fuertes.")
            
        pub2_id = guardar_publicacion_db("Instagram", "@fotografo_vzla", "Imágenes de cómo se vivió el #sismo en la capital.", "https://instagram.com/p/456", likes=890, vistas=15000)
        if pub2_id:
            guardar_comentario_db(pub2_id, "luis_foto", "Tremendas capturas, hermano.")
            
    except Exception as e:
        print(f"[Instagram] Error: {e}")
    finally:
        await context.close()


async def scrape_tiktok(browser):
    print("[TikTok] Iniciando proceso de scraping...")
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    page = await context.new_page()
    try:
        await page.goto("https://www.tiktok.com/search?q=terremoto%20venezuela", timeout=60000)
        await page.wait_for_timeout(5000)
        
        print("[TikTok] Extrayendo videos...")
        
        # EJEMPLO SIMULADO
        pub1_id = guardar_publicacion_db("TikTok", "@tiktoker_vzla", "Grabé justo cuando empezó el terremoto!! #venezuela #sismo", "https://tiktok.com/@tiktoker_vzla/video/1", likes=45000, vistas=800000)
        if pub1_id:
            guardar_comentario_db(pub1_id, "Juan TikTok", "El perrito salió corriendo antes de que temblara 😳")
            guardar_comentario_db(pub1_id, "GamerVzla", "Yo estaba jugando y se me fue el internet jaja")
            guardar_comentario_db(pub1_id, "MariaLuz", "Bendiciones a todos")
            
    except Exception as e:
        print(f"[TikTok] Error: {e}")
    finally:
        await context.close()


async def main():
    print("=== INICIANDO SCRAPING PARALELO (POSTS + COMENTARIOS + MÉTRICAS) ===")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        
        await asyncio.gather(
            scrape_facebook(browser),
            scrape_instagram(browser),
            scrape_tiktok(browser)
        )
        
        await browser.close()
    
    print("=== SCRAPING PARALELO FINALIZADO ===")

if __name__ == "__main__":
    asyncio.run(main())
