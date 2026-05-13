import os
os.chdir('c:\\Users\\user\\Desktop\\healty-life-2')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinica_root.settings')
import django
django.setup()

from django.db import connection

print('=== PRUEBA DE CONEXIÓN A SUPABASE ===')

try:
    # Intentar conectar
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        print(f"✅ Conexión exitosa: {result}")
        
    # Probar consulta a tabla de estados
    from usuarios.models import Estado
    estados_count = Estado.objects.count()
    print(f"✅ Estados disponibles: {estados_count}")
    
    # Probar consulta a tabla de municipios
    from usuarios.models import Municipio
    municipios_count = Municipio.objects.count()
    print(f"✅ Municipios disponibles: {municipios_count}")
    
    print("\n=== CONEXIÓN ESTABLECIDA CORRECTAMENTE ===")
    
except Exception as e:
    print(f"❌ Error de conexión: {e}")
    print("\n=== INTENTANDO SOLUCIÓN ===")
    
    # Intentar con configuración alternativa
    try:
        # Probar conexión con timeout extendido
        import psycopg2
        conn = psycopg2.connect(
            dbname='postgres',
            user='postgres.xpzrljaykpanthomlegn',
            password='TVqFID3AdDXi85aF',
            host='aws-1-us-west-2.pooler.supabase.com',
            port='6543',
            connect_timeout=30,
            sslmode='require'
        )
        print("✅ Conexión directa con psycopg2 exitosa")
        conn.close()
        
    except Exception as e2:
        print(f"❌ Error en conexión directa: {e2}")
        
        # Intentar con IP directa
        try:
            conn = psycopg2.connect(
                dbname='postgres',
                user='postgres.xpzrljaykpanthomlegn',
                password='TVqFID3AdDXi85aF',
                host='44.252.246.120',  # IP directa
                port='6543',
                connect_timeout=30,
                sslmode='require'
            )
            print("✅ Conexión con IP directa exitosa")
            conn.close()
            
        except Exception as e3:
            print(f"❌ Error con IP directa: {e3}")
