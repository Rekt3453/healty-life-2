#!/usr/bin/env python
"""
Script para crear datos de prueba para ubicación en la base de datos local
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'healty_life.settings')
django.setup()

from usuarios.models import Estado, Municipio, Ciudad, Parroquia

def crear_datos_ubicacion():
    """Crear datos de prueba para estados, municipios, ciudades y parroquias"""
    
    print("=== CREANDO DATOS DE UBICACIÓN ===")
    
    # Limpiar datos existentes
    print("Limpiando datos existentes...")
    Parroquia.objects.all().delete()
    Ciudad.objects.all().delete()
    Municipio.objects.all().delete()
    Estado.objects.all().delete()
    
    # Crear estados
    print("Creando estados...")
    estados_data = [
        (1, 'Distrito Capital'),
        (2, 'Carabobo'),
        (3, 'Zulia'),
        (4, 'Miranda'),
        (5, 'Anzoátegui'),
    ]
    
    for id_estado, nombre in estados_data:
        estado = Estado.objects.create(id_estado=id_estado, estado=nombre)
        print(f"  Creado estado: {estado.estado}")
    
    # Crear municipios
    print("Creando municipios...")
    municipios_data = [
        (1, 1, 'Libertador'),
        (2, 1, 'Baruta'),
        (3, 2, 'Valencia'),
        (4, 2, 'Guacara'),
        (5, 3, 'Maracaibo'),
        (6, 3, 'San Francisco'),
        (7, 4, 'Sucre'),
        (8, 4, 'Baruta'),
        (9, 5, 'Anaco'),
        (10, 5, 'Barcelona'),
    ]
    
    for id_municipio, id_estado, nombre in municipios_data:
        estado = Estado.objects.get(id_estado=id_estado)
        municipio = Municipio.objects.create(
            id_municipio=id_municipio,
            municipio=nombre,
            id_estado=estado
        )
        print(f"  Creado municipio: {municipio.municipio} (Estado: {estado.estado})")
    
    # Crear ciudades
    print("Creando ciudades...")
    ciudades_data = [
        (1, 1, 'Caracas'),
        (2, 1, 'Los Teques'),
        (3, 2, 'Valencia'),
        (4, 2, 'Naguanagua'),
        (5, 3, 'Maracaibo'),
        (6, 3, 'San Francisco'),
        (7, 4, 'Los Teques'),
        (8, 4, 'Baruta'),
        (9, 5, 'Barcelona'),
        (10, 5, 'Puerto La Cruz'),
    ]
    
    for id_ciudad, id_estado, nombre in ciudades_data:
        estado = Estado.objects.get(id_estado=id_estado)
        ciudad = Ciudad.objects.create(
            id_ciudad=id_ciudad,
            ciudad=nombre,
            id_estado=estado
        )
        print(f"  Creada ciudad: {ciudad.ciudad} (Estado: {estado.estado})")
    
    # Crear parroquias
    print("Creando parroquias...")
    parroquias_data = [
        (1, 1, 'Altagracia'),
        (2, 1, 'Catedral'),
        (3, 1, 'San Juan'),
        (4, 1, 'Santa Rosalía'),
        (5, 2, 'Baruta'),
        (6, 2, 'El Cafetal'),
        (7, 3, 'San José'),
        (8, 3, 'Catedral'),
        (9, 4, 'San Francisco'),
        (10, 4, 'Maracaibo'),
        (11, 5, 'Petare'),
        (12, 5, 'La Dolorita'),
        (13, 6, 'Anaco'),
        (14, 6, 'Santa Rosa'),
        (15, 7, 'Barcelona'),
        (16, 7, 'Guanta'),
    ]
    
    for id_parroquia, id_municipio, nombre in parroquias_data:
        municipio = Municipio.objects.get(id_municipio=id_municipio)
        parroquia = Parroquia.objects.create(
            id_parroquia=id_parroquia,
            parroquia=nombre,
            id_municipio=municipio
        )
        print(f"  Creada parroquia: {parroquia.parroquia} (Municipio: {municipio.municipio})")
    
    print("\n=== RESUMEN DE DATOS CREADOS ===")
    print(f"Estados: {Estado.objects.count()}")
    print(f"Municipios: {Municipio.objects.count()}")
    print(f"Ciudades: {Ciudad.objects.count()}")
    print(f"Parroquias: {Parroquia.objects.count()}")
    
    print("\n=== VERIFICACIÓN DE RELACIONES ===")
    
    # Verificar municipios del Distrito Capital
    print("\nMunicipios del Distrito Capital:")
    for municipio in Municipio.objects.filter(id_estado=1):
        print(f"  - {municipio.municipio}")
    
    # Verificar ciudades del Distrito Capital
    print("\nCiudades del Distrito Capital:")
    for ciudad in Ciudad.objects.filter(id_estado=1):
        print(f"  - {ciudad.ciudad}")
    
    # Verificar parroquias de Libertador
    print("\nParroquias de Libertador:")
    for parroquia in Parroquia.objects.filter(id_municipio=1):
        print(f"  - {parroquia.parroquia}")
    
    print("\n=== DATOS CREADOS EXITOSAMENTE ===")
    print("Ahora puedes probar los selectores dependientes en el formulario de registro.")

if __name__ == '__main__':
    crear_datos_ubicacion()
