#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinica_root.settings')
django.setup()

from django.db import connection

def find_any_sede():
    print("=== Buscar cualquier sede existente ===")
    
    with connection.cursor() as cursor:
        # Intentar encontrar sedes directamente en la tabla
        try:
            cursor.execute("SELECT * FROM \"Sede\" LIMIT 1;")
            sede = cursor.fetchone()
            if sede:
                print(f"Sede encontrada: {sede}")
                return sede
            else:
                print("No hay sedes en la tabla Sede")
        except Exception as e:
            print(f"Error al consultar Sede: {e}")
        
        # Buscar en tablas relacionadas
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name ILIKE '%sede%' ORDER BY table_name;")
        tables = cursor.fetchall()
        print("Tablas con 'sede':")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Intentar insertar una sede sin restricciones (temporal) - omitiendo campos con FK
        try:
            cursor.execute("INSERT INTO \"Sede\" (rif_sede, telefono, status) VALUES (NULL, NULL, TRUE) RETURNING id_sede;")
            new_id = cursor.fetchone()[0]
            print(f"Sede creada con ID: {new_id}")
            return new_id
        except Exception as e:
            print(f"No se pudo crear sede: {e}")
            # Intentar sin el campo status
            try:
                cursor.execute("INSERT INTO \"Sede\" (rif_sede, telefono) VALUES (NULL, NULL) RETURNING id_sede;")
                new_id = cursor.fetchone()[0]
                print(f"Sede creada sin status con ID: {new_id}")
                return new_id
            except Exception as e2:
                print(f"Tampoco se pudo crear sin status: {e2}")
            
    return None

if __name__ == '__main__':
    find_any_sede()
