#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinica_root.settings')
django.setup()

from django.db import connection

def find_patient_table():
    with connection.cursor() as cursor:
        # Buscar tablas que contengan 'paciente' en el nombre
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name ILIKE '%paciente%' ORDER BY table_name;")
        patient_tables = cursor.fetchall()
        
        print('Tablas que contienen "paciente":')
        for table in patient_tables:
            print(f'  - {table[0]}')
            # Verificar estructura
            cursor.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = %s ORDER BY ordinal_position LIMIT 10;", [table[0]])
            columns = cursor.fetchall()
            print(f'    Columnas: {[col[0] for col in columns]}')
        
        # También buscar tablas que puedan ser de pacientes
        possible_tables = ['paciente_datos_personales', 'paciente_especial']
        print('\nOtras tablas posibles de pacientes:')
        for table in possible_tables:
            cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = %s);", [table])
            exists = cursor.fetchone()[0]
            if exists:
                cursor.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = %s ORDER BY ordinal_position LIMIT 10;", [table])
                columns = cursor.fetchall()
                print(f'  [OK] {table}')
                print(f'    Columnas: {[col[0] for col in columns]}')

if __name__ == '__main__':
    find_patient_table()
