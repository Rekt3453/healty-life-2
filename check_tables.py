#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinica_root.settings')
django.setup()

from django.db import connection

def check_tables():
    with connection.cursor() as cursor:
        # Obtener todas las tablas
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;")
        tables = cursor.fetchall()
        
        print('Tablas encontradas en Supabase:')
        for table in tables:
            print(f'  - {table[0]}')
        
        # Verificar tablas específicas del sistema
        system_tables = ['auth_user', 'django_content_type', 'django_session', 'usuarios_sede', 'usuarios_userprofile', 'usuarios_pacienteprofile']
        print('\nVerificacion de tablas clave:')
        for table in system_tables:
            cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = %s);", [table])
            exists = cursor.fetchone()[0]
            status = 'OK' if exists else 'FAIL'
            print(f'  [{status}] {table}')

if __name__ == '__main__':
    check_tables()
