#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinica_root.settings')
django.setup()

from django.utils import timezone
from datetime import datetime, timedelta
from usuarios.models import MedicoProfile, Sede, Especialidad
from citas.models import Servicio, DisponibilidadMedica

def crear_datos_citas():
    print("Creando datos para el sistema de citas...")
    
    # Crear servicios médicos
    servicios_data = [
        {
            'nombre': 'Consulta General',
            'descripcion': 'Consulta médica general de 30 minutos',
            'especialidad': 'Medicina General',
            'precio_base': 150.00,
            'duracion_minutos': 30
        },
        {
            'nombre': 'Consulta Cardiología',
            'descripcion': 'Evaluación cardiológica completa',
            'especialidad': 'Cardiología',
            'precio_base': 250.00,
            'duracion_minutos': 45
        },
        {
            'nombre': 'Consulta Pediatría',
            'descripcion': 'Consulta pediátrica general',
            'especialidad': 'Pediatría',
            'precio_base': 180.00,
            'duracion_minutos': 30
        },
        {
            'nombre': 'Consulta Ginecología',
            'descripcion': 'Examen ginecológico completo',
            'especialidad': 'Ginecología',
            'precio_base': 200.00,
            'duracion_minutos': 40
        },
        {
            'nombre': 'Consulta Ortopedia',
            'descripcion': 'Evaluación ortopédica',
            'especialidad': 'Ortopedia',
            'precio_base': 180.00,
            'duracion_minutos': 30
        },
        {
            'nombre': 'Chequeo Preventivo',
            'descripcion': 'Examen médico preventivo completo',
            'especialidad': 'Medicina General',
            'precio_base': 300.00,
            'duracion_minutos': 60
        },
        {
            'nombre': 'Electrocardiograma',
            'descripcion': 'Estudio electrocardiográfico',
            'especialidad': 'Cardiología',
            'precio_base': 120.00,
            'duracion_minutos': 20
        },
        {
            'nombre': 'Control Embarazo',
            'descripcion': 'Control prenatal rutinario',
            'especialidad': 'Ginecología',
            'precio_base': 150.00,
            'duracion_minutos': 25
        }
    ]
    
    for servicio_data in servicios_data:
        try:
            especialidad = Especialidad.objects.get(nombre=servicio_data['especialidad'])
            servicio, created = Servicio.objects.get_or_create(
                nombre=servicio_data['nombre'],
                defaults={
                    'descripcion': servicio_data['descripcion'],
                    'especialidad': especialidad,
                    'precio_base': servicio_data['precio_base'],
                    'duracion_minutos': servicio_data['duracion_minutos'],
                    'activo': True
                }
            )
            if created:
                print(f"OK Servicio creado: {servicio.nombre}")
            else:
                print(f"- Servicio existente: {servicio.nombre}")
        except Especialidad.DoesNotExist:
            print(f"ERROR: Especialidad {servicio_data['especialidad']} no encontrada")
        except Exception as e:
            print(f"ERROR creando servicio {servicio_data['nombre']}: {e}")
    
    # Crear disponibilidades médicas
    disponibilidades_data = [
        # Dr. Juan Pérez (Medicina General)
        {'medico': 'dr_perez', 'dias': [1, 2, 3, 4, 5], 'inicio': '08:00', 'fin': '16:00'},
        
        # Dra. Ana Martínez (Cardiología)
        {'medico': 'dra_martinez', 'dias': [2, 3, 4, 5], 'inicio': '09:00', 'fin': '17:00'},
        
        # Agregar más médicos si existen
    ]
    
    for disp_data in disponibilidades_data:
        try:
            medico_user = MedicoProfile.objects.select_related('user_profile__user').get(
                user_profile__user__username=disp_data['medico']
            )
            
            for dia in disp_data['dias']:
                disponibilidad, created = DisponibilidadMedica.objects.get_or_create(
                    medico=medico_user,
                    dia_semana=dia,
                    hora_inicio=disp_data['inicio'],
                    hora_fin=disp_data['fin'],
                    defaults={'activo': True}
                )
                if created:
                    print(f"OK Disponibilidad creada: {medico_user} - {disp_data['inicio']} a {disp_data['fin']} (día {dia})")
                else:
                    print(f"- Disponibilidad existente: {medico_user} - día {dia}")
                    
        except MedicoProfile.DoesNotExist:
            print(f"ERROR: Médico {disp_data['medico']} no encontrado")
        except Exception as e:
            print(f"ERROR creando disponibilidad para {disp_data['medico']}: {e}")
    
    print("\n¡Datos de citas creados exitosamente!")

if __name__ == '__main__':
    crear_datos_citas()
