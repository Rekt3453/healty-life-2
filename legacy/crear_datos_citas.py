#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinica_root.settings')
django.setup()

from citas.models import Sede, Especialidad, Servicio
from usuarios.models import UserProfile

def crear_datos_iniciales():
    print("Creando datos iniciales para el sistema de citas...")
    
    # Crear sedes
    sedes = [
        Sede(nombre="Sede Principal", direccion="Av. Principal 100, Caracas", telefono="0212-5550100"),
        Sede(nombre="Sede Este", direccion="Av. Este 200, Caracas", telefono="0212-5550101"),
        Sede(nombre="Sede Oeste", direccion="Av. Oeste 300, Caracas", telefono="0212-5550102"),
    ]
    
    for sede in sedes:
        sede.save()
        print(f"Sede creada: {sede.nombre}")
    
    # Crear especialidades
    especialidades = [
        Especialidad(nombre="Medicina General", descripcion="Consultas generales y check-ups"),
        Especialidad(nombre="Cardiología", descripcion="Enfermedades del corazón y sistema circulatorio"),
        Especialidad(nombre="Pediatría", descripcion="Atención médica infantil"),
        Especialidad(nombre="Ginecología", descripcion="Salud de la mujer"),
        Especialidad(nombre="Dermatología", descripcion="Enfermedades de la piel"),
    ]
    
    for especialidad in especialidades:
        especialidad.save()
        print(f"Especialidad creada: {especialidad.nombre}")
    
    # Crear servicios
    servicios = [
        # Sede Principal
        Servicio(nombre="Consulta General", especialidad=especialidades[0], sede=sedes[0], precio=150.00),
        Servicio(nombre="Check-up Completo", especialidad=especialidades[0], sede=sedes[0], precio=300.00),
        Servicio(nombre="Evaluación Cardíaca", especialidad=especialidades[1], sede=sedes[0], precio=250.00),
        Servicio(nombre="Electrocardiograma", especialidad=especialidades[1], sede=sedes[0], precio=100.00),
        Servicio(nombre="Consulta Pediátrica", especialidad=especialidades[2], sede=sedes[0], precio=180.00),
        
        # Sede Este
        Servicio(nombre="Consulta General", especialidad=especialidades[0], sede=sedes[1], precio=140.00),
        Servicio(nombre="Control Prenatal", especialidad=especialidades[3], sede=sedes[1], precio=200.00),
        Servicio(nombre="Consulta Dermatológica", especialidad=especialidades[4], sede=sedes[1], precio=160.00),
        
        # Sede Oeste
        Servicio(nombre="Consulta General", especialidad=especialidades[0], sede=sedes[2], precio=130.00),
        Servicio(nombre="Consulta Pediátrica", especialidad=especialidades[2], sede=sedes[2], precio=170.00),
        Servicio(nombre="Consulta Ginecológica", especialidad=especialidades[3], sede=sedes[2], precio=190.00),
    ]
    
    for servicio in servicios:
        servicio.save()
        print(f"Servicio creado: {servicio.nombre} - {servicio.sede.nombre}")
    
    print(f"\nTotal creados:")
    print(f"- Sedes: {Sede.objects.count()}")
    print(f"- Especialidades: {Especialidad.objects.count()}")
    print(f"- Servicios: {Servicio.objects.count()}")
    
    print("\n¡Datos iniciales creados exitosamente!")

if __name__ == "__main__":
    crear_datos_iniciales()
