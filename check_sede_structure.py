#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinica_root.settings')
django.setup()

from django.db import connection

def check_sede_structure():
    with connection.cursor() as cursor:
        cursor.execute("SELECT column_name, data_type, character_maximum_length, is_nullable FROM information_schema.columns WHERE table_name = 'Sede' ORDER BY ordinal_position;")
        columns = cursor.fetchall()
        
        print("Estructura de la tabla Sede:")
        for col in columns:
            null_status = 'NULL' if col[3] == 'YES' else 'NOT NULL'
            max_length = col[2] if col[2] else 'N/A'
            print(f"  {col[0]}: {col[1]} ({max_length}) - {null_status}")

if __name__ == '__main__':
    check_sede_structure()
