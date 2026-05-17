#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinica_root.settings')
django.setup()

from django.contrib.auth.models import User
from usuarios.models import Sede, UserProfile, Especialidad, MedicoProfile, PacienteProfile

def crear_datos_iniciales():
    print("Creando datos iniciales para Healthy Life...")
    
    # Crear superusuario ROOT
    try:
        root_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@healthylife.com',
                'is_superuser': True,
                'is_staff': True
            }
        )
        if created:
            root_user.set_password('admin123')
            root_user.save()
            UserProfile.objects.get_or_create(
                user=root_user,
                defaults={
                    'rol': 'gerente_general',
                    'cedula': 'V-00000000',
                    'telefono': '04140000000',
                    'activo': True
                }
            )
            print("OK Superusuario ROOT creado: admin / admin123")
        else:
            print("- Superusuario ROOT ya existe")
    except Exception as e:
        print(f"ERROR creando superusuario: {e}")
    
    # Crear sedes
    sedes_data = [
        {
            'nombre': 'Caracas',
            'slug': 'caracas',
            'direccion': 'Av. Principal, Centro Médico Caracas',
            'telefono': '0212-1234567',
            'email': 'caracas@healthylife.com'
        },
        {
            'nombre': 'Valencia', 
            'slug': 'valencia',
            'direccion': 'Av. Bolívar, Centro Médico Valencia',
            'telefono': '0241-1234567',
            'email': 'valencia@healthylife.com'
        }
    ]
    
    for sede_data in sedes_data:
        try:
            sede, created = Sede.objects.get_or_create(
                slug=sede_data['slug'],
                defaults=sede_data
            )
            if created:
                print(f"OK Sede creada: {sede.nombre}")
            else:
                print(f"- Sede existente: {sede.nombre}")
        except Exception as e:
            print(f"ERROR creando sede {sede_data['nombre']}: {e}")
    
    # Crear especialidades
    especialidades_data = [
        {'nombre': 'Medicina General', 'descripcion': 'Consultas médicas generales'},
        {'nombre': 'Cardiología', 'descripcion': 'Especialista en corazón y sistema cardiovascular'},
        {'nombre': 'Pediatría', 'descripcion': 'Atención médica para niños y adolescentes'},
        {'nombre': 'Ginecología', 'descripcion': 'Salud reproductiva femenina'},
        {'nombre': 'Ortopedia', 'descripcion': 'Especialista en huesos y articulaciones'},
    ]
    
    for esp_data in especialidades_data:
        try:
            especialidad, created = Especialidad.objects.get_or_create(
                nombre=esp_data['nombre'],
                defaults=esp_data
            )
            if created:
                print(f"OK Especialidad creada: {especialidad.nombre}")
            else:
                print(f"- Especialidad existente: {especialidad.nombre}")
        except Exception as e:
            print(f"ERROR creando especialidad {esp_data['nombre']}: {e}")
    
    # Crear Gerente General
    try:
        gerente_general_user = User.objects.create_user(
            username='gerente_general',
            email='gerente_general@healthylife.com',
            password='gerente123',
            first_name='Carlos',
            last_name='Rodríguez'
        )
        UserProfile.objects.create(
            user=gerente_general_user,
            rol='gerente_general',
            cedula='V-12345678',
            telefono='04141234567',
            activo=True
        )
        print("OK Gerente General creado: gerente_general / gerente123")
    except Exception as e:
        print(f"ERROR creando gerente general: {e}")
    
    # Crear Gerente de Caracas
    try:
        sede_caracas = Sede.objects.get(slug='caracas')
        gerente_caracas_user = User.objects.create_user(
            username='gerente_caracas',
            email='gerente_caracas@healthylife.com',
            password='gerente123',
            first_name='María',
            last_name='González'
        )
        UserProfile.objects.create(
            user=gerente_caracas_user,
            rol='gerente',
            sede=sede_caracas,
            cedula='V-87654321',
            telefono='04147654321',
            activo=True
        )
        print("OK Gerente Caracas creado: gerente_caracas / gerente123")
    except Exception as e:
        print(f"ERROR creando gerente caracas: {e}")
    
    # Crear Médicos
    medicos_data = [
        {
            'username': 'dr_perez',
            'email': 'dr_perez@healthylife.com',
            'password': 'medico123',
            'first_name': 'Juan',
            'last_name': 'Pérez',
            'cedula': 'V-11111111',
            'telefono': '04141111111',
            'especialidad': 'Medicina General',
            'matricula': 'MP-12345',
            'experiencia': 10,
            'precio': 150.00,
            'sede': 'caracas'
        },
        {
            'username': 'dra_martinez',
            'email': 'dra_martinez@healthylife.com',
            'password': 'medico123',
            'first_name': 'Ana',
            'last_name': 'Martínez',
            'cedula': 'V-22222222',
            'telefono': '04142222222',
            'especialidad': 'Cardiología',
            'matricula': 'MC-67890',
            'experiencia': 8,
            'precio': 250.00,
            'sede': 'caracas'
        }
    ]
    
    for medico_data in medicos_data:
        try:
            # Crear usuario
            medico_user = User.objects.create_user(
                username=medico_data['username'],
                email=medico_data['email'],
                password=medico_data['password'],
                first_name=medico_data['first_name'],
                last_name=medico_data['last_name']
            )
            
            # Crear UserProfile
            user_profile = UserProfile.objects.create(
                user=medico_user,
                rol='medico',
                cedula=medico_data['cedula'],
                telefono=medico_data['telefono'],
                sede=Sede.objects.get(slug=medico_data['sede']),
                activo=True
            )
            
            # Crear MedicoProfile
            especialidad = Especialidad.objects.get(nombre=medico_data['especialidad'])
            MedicoProfile.objects.create(
                user_profile=user_profile,
                especialidad=especialidad,
                numero_matricula=medico_data['matricula'],
                experiencia_anios=medico_data['experiencia'],
                consulta_precio_base=medico_data['precio']
            )
            
            print(f"OK Medico creado: {medico_data['username']} / medico123")
        except Exception as e:
            print(f"ERROR creando medico {medico_data['username']}: {e}")
    
    # Crear Recepcionista
    try:
        recepcionista_user = User.objects.create_user(
            username='recepcionista_caracas',
            email='recepcionista_caracas@healthylife.com',
            password='recepcion123',
            first_name='Laura',
            last_name='Sánchez'
        )
        UserProfile.objects.create(
            user=recepcionista_user,
            rol='recepcionista',
            sede=Sede.objects.get(slug='caracas'),
            cedula='V-33333333',
            telefono='04143333333',
            activo=True
        )
        print("OK Recepcionista creada: recepcionista_caracas / recepcion123")
    except Exception as e:
        print(f"ERROR creando recepcionista: {e}")
    
    # Crear Paciente de prueba
    try:
        paciente_user = User.objects.create_user(
            username='paciente_prueba',
            email='paciente_prueba@email.com',
            password='paciente123',
            first_name='Roberto',
            last_name='López'
        )
        
        user_profile = UserProfile.objects.create(
            user=paciente_user,
            rol='paciente',
            cedula='V-44444444',
            telefono='04144444444',
            fecha_nacimiento='1990-01-01',
            direccion='Av. Libertador, Caracas',
            sede=Sede.objects.get(slug='caracas'),
            activo=True
        )
        
        PacienteProfile.objects.create(user_profile=user_profile)
        print("OK Paciente creado: paciente_prueba / paciente123")
    except Exception as e:
        print(f"ERROR creando paciente: {e}")
    
    print("\n¡Datos iniciales creados exitosamente!")
    print("\nCuentas de prueba:")
    print("- ROOT: admin / admin123")
    print("- Gerente General: gerente_general / gerente123")
    print("- Gerente Caracas: gerente_caracas / gerente123")
    print("- Médico 1: dr_perez / medico123")
    print("- Médico 2: dra_martinez / medico123")
    print("- Recepcionista: recepcionista_caracas / recepcion123")
    print("- Paciente: paciente_prueba / paciente123")

if __name__ == '__main__':
    crear_datos_iniciales()
