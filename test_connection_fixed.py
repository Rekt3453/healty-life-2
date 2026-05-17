import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar ruta del proyecto
BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinica_root.settings')
import django
django.setup()

from django.db import connection

print('=== PRUEBA DE CONEXION A SUPABASE ===')

try:
    # Intentar conectar
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        print(f"[OK] Conexion exitosa: {result}")

    # Probar consulta a tabla de estados
    from usuarios.models import Estado
    estados_count = Estado.objects.count()
    print(f"[OK] Estados disponibles: {estados_count}")

    # Probar consulta a tabla de municipios
    from usuarios.models import Municipio
    municipios_count = Municipio.objects.count()
    print(f"[OK] Municipios disponibles: {municipios_count}")

    print("\n=== CONEXION ESTABLECIDA CORRECTAMENTE ===")

except Exception as e:
    print(f"[ERROR] Error de conexion: {e}")
    print("\n=== INTENTANDO SOLUCION ===")

    # Intentar con configuración alternativa
    try:
        # Probar conexión con timeout extendido
        import psycopg2
        conn = psycopg2.connect(
            dbname=os.environ.get('DB_NAME', 'postgres'),
            user=os.environ.get('DB_USER', 'postgres'),
            password=os.environ.get('DB_PASSWORD', ''),
            host=os.environ.get('DB_HOST', 'localhost'),
            port=os.environ.get('DB_PORT', '5432'),
            connect_timeout=30,
            sslmode='require'
        )
        print("[OK] Conexion directa con psycopg2 exitosa")
        conn.close()

    except Exception as e2:
        print(f"[ERROR] Error en conexion directa: {e2}")
