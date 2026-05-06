#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinica_root.settings')
django.setup()

from django.db import connection
from usuarios.models import Sede

def check_existing_sedes():
    print("=== Verificacion de sedes existentes ===")
    
    # Verificar sedes en la tabla
    try:
        sedes = Sede.objects.all()
        print(f"Sedes encontradas: {sedes.count()}")
        for sede in sedes:
            print(f"  ID: {sede.id_sede}, Direccion: {sede.id_direccion}, RIF: {sede.rif_sede}, Telefono: {sede.telefono}, Status: {sede.Status}")
    except Exception as e:
        print(f"Error al consultar sedes: {e}")
    
    # Verificar tabla de direcciones
    with connection.cursor() as cursor:
        cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'sireccion_sede');")
        exists = cursor.fetchone()[0]
        print(f"Tabla sireccion_sede existe: {exists}")
        
        if exists:
            cursor.execute("SELECT * FROM sireccion_sede LIMIT 5;")
            direcciones = cursor.fetchall()
            print(f"Direcciones disponibles: {len(direcciones)}")
            for dir in direcciones:
                print(f"  {dir}")

if __name__ == '__main__':
    check_existing_sedes()
