import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinica_root.settings')
django.setup()

from django.db import connection

# Ver columnas de user_paciente
with connection.cursor() as c:
    c.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns 
        WHERE table_name = 'user_paciente'
        ORDER BY ordinal_position
    """)
    print("\n=== user_paciente ===")
    for row in c.fetchall():
        print(f"  {row[0]:35s} | {row[1]:20s} | nullable={row[2]}")

# Ver columnas de paciente_datos_personales
with connection.cursor() as c:
    c.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns 
        WHERE table_name = 'paciente_datos_personales'
        ORDER BY ordinal_position
    """)
    print("\n=== paciente_datos_personales ===")
    for row in c.fetchall():
        print(f"  {row[0]:35s} | {row[1]:20s} | nullable={row[2]}")

# Ver columnas de paciente_especial
with connection.cursor() as c:
    c.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns 
        WHERE table_name = 'paciente_especial'
        ORDER BY ordinal_position
    """)
    print("\n=== paciente_especial ===")
    for row in c.fetchall():
        print(f"  {row[0]:35s} | {row[1]:20s} | nullable={row[2]}")

# Ver columnas de la tabla 'sede'
with connection.cursor() as c:
    c.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns 
        WHERE table_name = 'sede'
        ORDER BY ordinal_position
    """)
    print("\n=== sede ===")
    for row in c.fetchall():
        print(f"  {row[0]:35s} | {row[1]:20s} | nullable={row[2]}")
