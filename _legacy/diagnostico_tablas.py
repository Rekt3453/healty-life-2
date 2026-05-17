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
    print("\n=== public.user_paciente ===")
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
    print("\n=== public.paciente_datos_personales ===")
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
    print("\n=== public.paciente_especial ===")
    for row in c.fetchall():
        print(f"  {row[0]:35s} | {row[1]:20s} | nullable={row[2]}")

# Ver columnas de sede
with connection.cursor() as c:
    c.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns 
        WHERE table_name = 'sede'
        ORDER BY ordinal_position
    """)
    print("\n=== public.sede ===")
    for row in c.fetchall():
        print(f"  {row[0]:35s} | {row[1]:20s} | nullable={row[2]}")

# Ver todos los esquemas
with connection.cursor() as c:
    c.execute("""
        SELECT schema_name 
        FROM information_schema.schemata 
        WHERE schema_name NOT IN ('pg_catalog', 'information_schema')
        ORDER BY schema_name
    """)
    print("\n=== Esquemas disponibles ===")
    for row in c.fetchall():
        print(f"  {row[0]}")

# Ver todas las tablas que contienen 'userprofile' o 'sede'
with connection.cursor() as c:
    c.execute("""
        SELECT table_schema, table_name 
        FROM information_schema.tables 
        WHERE table_name LIKE '%userprofile%' 
           OR table_name LIKE '%sede%'
           OR table_name LIKE '%paciente%'
        ORDER BY table_schema, table_name
    """)
    print("\n=== Tablas relevantes ===")
    for row in c.fetchall():
        print(f"  {row[0]}.{row[1]}")

# Ver sedes disponibles
with connection.cursor() as c:
    c.execute("SELECT id_sede, nombre_sede, telefono FROM public.sede WHERE status = true")
    print("\n=== Sedes disponibles ===")
    for row in c.fetchall():
        print(f"  ID: {row[0]} | {row[1]} | {row[2]}")

# Ver tablas de ubicación
with connection.cursor() as c:
    c.execute("""
        SELECT table_schema, table_name 
        FROM information_schema.tables 
        WHERE table_name LIKE '%estado%' 
           OR table_name LIKE '%ciudad%'
           OR table_name LIKE '%ubicacion%'
        ORDER BY table_schema, table_name
    """)
    print("\n=== Tablas de ubicación ===")
    for row in c.fetchall():
        print(f"  {row[0]}.{row[1]}")
