import os
os.chdir('c:\\Users\\user\\Desktop\\healty-life-2')
os.environ['DJANGO_SETTINGS_MODULE'] = 'clinica_root.settings'
import django
django.setup()

# Verificar tablas existentes
from django.db import connection

with connection.cursor() as c:
    c.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)
    print('\n=== Tablas en Supabase ===')
    for row in c.fetchall():
        print(f'  {row[0]}')

# Buscar tabla de usuarios
with connection.cursor() as c:
    c.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_name LIKE '%user%' 
        ORDER BY table_name
    """)
    print('\n=== Tablas con "user" ===')
    for row in c.fetchall():
        print(f'  {row[0]}')
