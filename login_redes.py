import asyncio
from playwright.async_api import async_playwright

async def login_manual():
    print("=== INICIANDO CONFIGURACIÓN DE AUTENTICACIÓN ===")
    print("Abriendo navegador para inicio de sesión manual...")
    
    async with async_playwright() as p:
        # Usamos launch_persistent_context para escribir directamente en la carpeta
        print("Lanzando contexto persistente en 'playwright_profile'...")
        try:
            context = await p.chromium.launch_persistent_context(
                user_data_dir="playwright_profile",
                headless=False,
                channel="msedge",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        except Exception:
            context = await p.chromium.launch_persistent_context(
                user_data_dir="playwright_profile",
                headless=False,
                channel="chrome",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        
        # Inyectar script anti-detección de bots para evitar pantallas en blanco en el login (Especialmente Meta)
        await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # Abrir Facebook
        page_fb = await context.new_page()
        try:
            await page_fb.goto("https://www.facebook.com/", timeout=60000, wait_until="domcontentloaded")
        except Exception:
            pass
        print("\n[Acción Requerida] Se ha abierto una pestaña de Facebook.")
        
        # Abrir Instagram
        page_ig = await context.new_page()
        try:
            await page_ig.goto("https://www.instagram.com/", timeout=60000, wait_until="domcontentloaded")
        except Exception:
            pass
        print("[Acción Requerida] Se ha abierto una pestaña de Instagram.")
        
        # Abrir TikTok
        page_tt = await context.new_page()
        try:
            await page_tt.goto("https://www.tiktok.com/login", timeout=60000, wait_until="domcontentloaded")
        except Exception:
            pass
        print("[Acción Requerida] Se ha abierto una pestaña de TikTok.")
        
        print("\n" + "="*50)
        print("IMPORTANTE: INICIA SESIÓN EN LAS TRES PESTAÑAS MANUALMENTE.")
        print("Resuelve los captchas si aparecen o ingresa los códigos SMS.")
        print("="*50 + "\n")
        
        # Pausamos el script asíncrono esperando input del usuario en la consola
        input(">>> PRESIONA ENTER AQUÍ EN LA CONSOLA CUANDO HAYAS INICIADO SESIÓN EN LAS TRES REDES <<<")
        
        print("\n[ÉXITO] ¡Tu perfil persistente se ha actualizado con éxito!")
        print("Cierra esta ventana si sigue abierta y ya puedes usar tu scraper_paralelo.")
        
        await context.close()

if __name__ == "__main__":
    asyncio.run(login_manual())
