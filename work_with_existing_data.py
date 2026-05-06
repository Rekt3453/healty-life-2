#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinica_root.settings')
django.setup()

from django.db import connection

def work_with_existing_data():
    print("=== Trabajar con datos existentes ===")
    
    with connection.cursor() as cursor:
        # Buscar direcciones existentes
        try:
            cursor.execute("SELECT * FROM direccion_sede LIMIT 1;")
            direccion = cursor.fetchone()
            if direccion:
                print(f"Direccion encontrada: {direccion}")
                direccion_id = direccion[0]
                
                # Ahora intentar crear sede con esta direccion
                try:
                    cursor.execute("INSERT INTO \"Sede\" (id_direccion, rif_sede, telefono) VALUES (%s, NULL, NULL) RETURNING id_sede;", [direccion_id])
                    new_id = cursor.fetchone()[0]
                    print(f"Sede creada con ID: {new_id}")
                    return new_id
                except Exception as e:
                    print(f"No se pudo crear sede: {e}")
            else:
                print("No hay direcciones en direccion_sede")
        except Exception as e:
            print(f"Error al consultar direccion_sede: {e}")
        
        # Buscar cualquier sede existente (ignorando mayúsculas/minúsculas)
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND lower(table_name) = 'sede';")
        tables = cursor.fetchall()
        if tables:
            table_name = tables[0][0]
            print(f"Tabla encontrada: {table_name}")
            try:
                cursor.execute(f"SELECT * FROM \"{table_name}\" LIMIT 1;")
                sede = cursor.fetchone()
                if sede:
                    print(f"Sede existente: {sede}")
                    return sede[0]  # id_sede
                else:
                    print(f"Tabla {table_name} está vacía")
            except Exception as e:
                print(f"Error al consultar {table_name}: {e}")
        
        # Como último recurso, buscar en otras tablas que puedan tener información de sedes
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name ILIKE '%admin%' OR table_name ILIKE '%doctor%' OR table_name ILIKE '%recepcion%' ORDER BY table_name;")
        tables = cursor.fetchall()
        print("Tablas relacionadas con personal:")
        for table in tables:
            print(f"  - {table[0]}")
        
        return None

if __name__ == '__main__':
    work_with_existing_data()
