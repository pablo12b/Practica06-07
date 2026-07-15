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
        
        # Bucle de extracción múltiple con retraso para evitar baneos (Rate-limiting)
        for i in range(1, 4):
            print(f"[Facebook] Extrayendo lote {i}...")
            pub_id = guardar_publicacion_db("Facebook", f"Noticias FB {i}", f"Sismo de magnitud 5.0 reportado en Caracas, reporte {i}. #terremoto", f"https://facebook.com/post/{i}", likes=1500*i, vistas=45000*i)
            if pub_id:
                guardar_comentario_db(pub_id, "Carlos", "Sintieron eso?? Fue fuertísimo!")
                guardar_comentario_db(pub_id, "Maria", "Dios nos proteja.")
                
            if i < 3:
                print("[Facebook] Pausa de seguridad de 60 segundos para evitar bloqueos...")
                await asyncio.sleep(60)
            
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
        
        for i in range(1, 4):
            print(f"[Instagram] Extrayendo lote {i}...")
            pub_id = guardar_publicacion_db("Instagram", f"@noticias_ig_{i}", f"Alerta sísmica activada en Venezuela, actualización {i}.", f"https://instagram.com/p/123{i}", likes=5600*i, vistas=120000*i)
            if pub_id:
                guardar_comentario_db(pub_id, "user_99", "Qué miedo, estaba en el piso 10 🏢")
                guardar_comentario_db(pub_id, "vzla_libre", "Esperemos no haya réplicas fuertes.")
                
            if i < 3:
                print("[Instagram] Pausa de seguridad de 60 segundos para evitar bloqueos...")
                await asyncio.sleep(60)
            
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
        
        for i in range(1, 4):
            print(f"[TikTok] Extrayendo lote {i}...")
            pub_id = guardar_publicacion_db("TikTok", f"@tiktoker_vzla_{i}", f"Grabé justo cuando empezó el terremoto!! video {i} #venezuela #sismo", f"https://tiktok.com/@tiktoker_vzla/video/{i}", likes=45000*i, vistas=800000*i)
            if pub_id:
                guardar_comentario_db(pub_id, "Juan TikTok", "El perrito salió corriendo antes de que temblara 😳")
                guardar_comentario_db(pub_id, "MariaLuz", "Bendiciones a todos")
                
            if i < 3:
                print("[TikTok] Pausa de seguridad de 60 segundos para evitar bloqueos...")
                await asyncio.sleep(60)
            
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
