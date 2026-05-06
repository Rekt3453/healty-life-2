#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinica_root.settings')
django.setup()

from django.db import connection

def check_real_tables():
    with connection.cursor() as cursor:
        # Verificar estructura de tablas que podrían corresponder a nuestros modelos
        possible_mappings = {
            'Sede': 'usuarios_sede',
            'user_paciente': 'usuarios_pacienteprofile', 
            'administrador': 'usuarios_userprofile',
            'doctor': 'usuarios_medicoprofile',
            'recepcionista': 'usuarios_userprofile'
        }
        
        print('Verificacion de tablas reales vs esperadas:')
        for real_table, expected_table in possible_mappings.items():
            cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = %s);", [real_table])
            exists = cursor.fetchone()[0]
            if exists:
                # Verificar estructura
                cursor.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = %s ORDER BY ordinal_position;", [real_table])
                columns = cursor.fetchall()
                print(f'  [OK] {real_table} -> {expected_table}')
                print(f'      Columnas: {[col[0] for col in columns]}')
            else:
                print(f'  [FAIL] {real_table} no existe')

if __name__ == '__main__':
    check_real_tables()
