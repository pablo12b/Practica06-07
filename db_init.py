import os
import psycopg2
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

load_dotenv()

def init_db():
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT'),
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD')
        )
        cur = conn.cursor()
        
        # Eliminar tablas anteriores si existen (para aplicar el nuevo esquema)
        cur.execute('DROP TABLE IF EXISTS comentarios_sismo;')
        cur.execute('DROP TABLE IF EXISTS publicaciones_sismo;')

        # Crear tabla para almacenar las publicaciones del terremoto
        cur.execute('''
            CREATE TABLE publicaciones_sismo (
                id SERIAL PRIMARY KEY,
                red_social VARCHAR(50),
                autor VARCHAR(255),
                contenido TEXT,
                fecha TIMESTAMP,
                url TEXT UNIQUE,
                likes INTEGER DEFAULT 0,
                vistas INTEGER DEFAULT 0,
                creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Crear tabla relacional para comentarios
        cur.execute('''
            CREATE TABLE comentarios_sismo (
                id SERIAL PRIMARY KEY,
                publicacion_id INTEGER REFERENCES publicaciones_sismo(id) ON DELETE CASCADE,
                autor VARCHAR(255),
                contenido TEXT,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        print('[EXITO] Base de datos y tablas (publicaciones_sismo, comentarios_sismo) inicializadas correctamente.')
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f'[ERROR] No se pudo inicializar la base de datos: {e}')

if __name__ == '__main__':
    init_db()
