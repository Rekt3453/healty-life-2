#!/usr/bin/env python
"""
Script para diagnóstico de estructura de tablas en Supabase
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'healty_life.settings')
django.setup()

from django.db import connection

def diagnosticar_supabase():
    print('=== DIAGNÓSTICO INICIAL - ESTRUCTURA DE TABLAS SUPABASE ===')
    
    # Ver columnas de usuarios_userprofile
    try:
        with connection.cursor() as c:
            c.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'usuarios_userprofile'
                ORDER BY ordinal_position
            """)
            print('\n=== usuarios_userprofile ===')
            for row in c.fetchall():
                print(row)
    except Exception as e:
        print(f'Error al consultar usuarios_userprofile: {e}')
    
    # Ver todas las tablas públicas
    try:
        with connection.cursor() as c:
            c.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            print('\n=== Tablas en public ===')
            for row in c.fetchall():
                print(row[0])
    except Exception as e:
        print(f'Error al consultar tablas públicas: {e}')
    
    # Ver estructura de tabla estados
    try:
        with connection.cursor() as c:
            c.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'estados'
            """)
            print('\n=== estados ===')
            for row in c.fetchall():
                print(row)
    except Exception as e:
        print(f'Error al consultar estados: {e}')
    
    # Ver estructura de tabla municipios
    try:
        with connection.cursor() as c:
            c.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'municipios'
            """)
            print('\n=== municipios ===')
            for row in c.fetchall():
                print(row)
    except Exception as e:
        print(f'Error al consultar municipios: {e}')
    
    # Ver estructura de tabla ciudades
    try:
        with connection.cursor() as c:
            c.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'ciudades'
            """)
            print('\n=== ciudades ===')
            for row in c.fetchall():
                print(row)
    except Exception as e:
        print(f'Error al consultar ciudades: {e}')
    
    # Ver estructura de tabla parroquias
    try:
        with connection.cursor() as c:
            c.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'parroquias'
            """)
            print('\n=== parroquias ===')
            for row in c.fetchall():
                print(row)
    except Exception as e:
        print(f'Error al consultar parroquias: {e}')
    
    print('\n=== DIAGNÓSTICO COMPLETADO ===')

if __name__ == '__main__':
    diagnosticar_supabase()
