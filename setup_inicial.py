#!/usr/bin/env python
"""
Script de configuración inicial del sistema Healthy Life
Crea sedes, especialidades, servicios y usuarios de prueba
"""

import os
import sys

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinica_root.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import django
django.setup()

from django.contrib.auth.models import User
from usuarios.models import Sede, Especialidad, UserProfile, MedicoProfile, PacienteProfile
from citas.models import Servicio, DisponibilidadMedica

def crear_sedes():
    """Crear las sedes principales"""
    print("=" * 60)
    print("CREANDO SEDES")
    print("=" * 60)
    
    sedes_data = [
        {
            'nombre': 'Clínica Caracas',
            'slug': 'caracas',
            'direccion': 'Av. Principal de Caracas, Edificio Salud, Piso 5, Caracas',
            'telefono': '+58 212-555-0101',
            'email': 'caracas@healthylife.com',
            'activa': True
        },
        {
            'nombre': 'Clínica Valencia',
            'slug': 'valencia',
            'direccion': 'Av. Bolívar Norte, Centro Médico Valencia, Torre A, Valencia',
            'telefono': '+58 241-555-0202',
            'email': 'valencia@healthylife.com',
            'activa': True
        }
    ]
    
    for sede_data in sedes_data:
        sede, created = Sede.objects.get_or_create(
            slug=sede_data['slug'],
            defaults=sede_data
        )
        if created:
            print(f"[OK] Sede creada: {sede.nombre}")
        else:
            print(f"[INFO] Sede ya existe: {sede.nombre}")
    
    return Sede.objects.filter(activa=True)

def crear_especialidades():
    """Crear especialidades médicas"""
    print()
    print("=" * 60)
    print("CREANDO ESPECIALIDADES")
    print("=" * 60)
    
    especialidades = [
        'Medicina General',
        'Cardiología',
        'Pediatría',
        'Ginecología',
        'Ortopedia',
        'Dermatología',
        'Neurología',
        'Endocrinología',
        'Psiquiatría',
        'Oftalmología'
    ]
    
    for nombre in especialidades:
        esp, created = Especialidad.objects.get_or_create(nombre=nombre)
        if created:
            print(f"[OK] Especialidad creada: {nombre}")
        else:
            print(f"[INFO] Especialidad ya existe: {nombre}")

def crear_servicios():
    """Crear servicios médicos"""
    print()
    print("=" * 60)
    print("CREANDO SERVICIOS")
    print("=" * 60)
    
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
                print(f"[OK] Servicio creado: {servicio.nombre}")
            else:
                print(f"[INFO] Servicio ya existe: {servicio.nombre}")
        except Exception as e:
            print(f"[ERROR] {servicio_data['nombre']}: {e}")

def crear_usuario_root():
    """Crear superusuario root"""
    print()
    print("=" * 60)
    print("CREANDO USUARIO ROOT")
    print("=" * 60)
    
    try:
        user = User.objects.create_superuser(
            username='admin',
            email='admin@healthylife.com',
            password='admin123',
            first_name='Administrador',
            last_name='Sistema'
        )
        
        # Crear perfil manualmente para evitar problemas con signals
        if not hasattr(user, 'userprofile'):
            sede = Sede.objects.get(slug='caracas')
            UserProfile.objects.create(
                user=user,
                rol='root',
                cedula='V-00000000',
                telefono='+58 000-0000000',
                sede=sede
            )
        
        print("[OK] Usuario root creado: admin / admin123")
        return user
    except Exception as e:
        print(f"[INFO] Usuario root ya existe o error: {e}")
        return User.objects.filter(username='admin').first()

def crear_usuarios_prueba(sedes):
    """Crear usuarios de prueba para cada rol"""
    print()
    print("=" * 60)
    print("CREANDO USUARIOS DE PRUEBA")
    print("=" * 60)
    
    caracas = sedes.get(slug='caracas')
    valencia = sedes.get(slug='valencia')
    
    usuarios_data = [
        # Gerentes
        {
            'username': 'gerente_general',
            'email': 'gerente.general@healthylife.com',
            'password': 'gerente123',
            'first_name': 'Gerente',
            'last_name': 'General',
            'rol': 'gerente_general',
            'sede': caracas,
            'cedula': 'V-10000001',
            'telefono': '+58 412-1111111'
        },
        {
            'username': 'gerente_caracas',
            'email': 'gerente.caracas@healthylife.com',
            'password': 'gerente123',
            'first_name': 'Gerente',
            'last_name': 'Caracas',
            'rol': 'gerente',
            'sede': caracas,
            'cedula': 'V-10000002',
            'telefono': '+58 412-2222222'
        },
        # Médicos
        {
            'username': 'dr_perez',
            'email': 'dr.perez@healthylife.com',
            'password': 'medico123',
            'first_name': 'Juan',
            'last_name': 'Pérez',
            'rol': 'medico',
            'sede': caracas,
            'cedula': 'V-20000001',
            'telefono': '+58 414-1111111',
            'especialidad': 'Medicina General',
            'numero_matricula': 'MED-2024-001'
        },
        {
            'username': 'dra_martinez',
            'email': 'dra.martinez@healthylife.com',
            'password': 'medico123',
            'first_name': 'Ana',
            'last_name': 'Martínez',
            'rol': 'medico',
            'sede': caracas,
            'cedula': 'V-20000002',
            'telefono': '+58 414-2222222',
            'especialidad': 'Cardiología',
            'numero_matricula': 'MED-2024-002'
        },
        {
            'username': 'dr_gomez_valencia',
            'email': 'dr.gomez@healthylife.com',
            'password': 'medico123',
            'first_name': 'Carlos',
            'last_name': 'Gómez',
            'rol': 'medico',
            'sede': valencia,
            'cedula': 'V-20000003',
            'telefono': '+58 414-3333333',
            'especialidad': 'Pediatría',
            'numero_matricula': 'MED-2024-003'
        },
        # Recepcionistas
        {
            'username': 'recepcionista_caracas',
            'email': 'recepcion.caracas@healthylife.com',
            'password': 'recepcion123',
            'first_name': 'María',
            'last_name': 'Recepción',
            'rol': 'recepcionista',
            'sede': caracas,
            'cedula': 'V-30000001',
            'telefono': '+58 416-1111111'
        },
        {
            'username': 'recepcionista_valencia',
            'email': 'recepcion.valencia@healthylife.com',
            'password': 'recepcion123',
            'first_name': 'Pedro',
            'last_name': 'Recepción',
            'rol': 'recepcionista',
            'sede': valencia,
            'cedula': 'V-30000002',
            'telefono': '+58 416-2222222'
        },
        # Pacientes
        {
            'username': 'paciente_caracas',
            'email': 'paciente.caracas@gmail.com',
            'password': 'paciente123',
            'first_name': 'Paciente',
            'last_name': 'Caracas',
            'rol': 'paciente',
            'sede': caracas,
            'cedula': 'V-40000001',
            'telefono': '+58 424-1111111',
            'fecha_nacimiento': '1990-05-15'
        },
        {
            'username': 'paciente_valencia',
            'email': 'paciente.valencia@gmail.com',
            'password': 'paciente123',
            'first_name': 'Paciente',
            'last_name': 'Valencia',
            'rol': 'paciente',
            'sede': valencia,
            'cedula': 'V-40000002',
            'telefono': '+58 424-2222222',
            'fecha_nacimiento': '1985-08-20'
        }
    ]
    
    for user_data in usuarios_data:
        try:
            # Verificar si el usuario ya existe
            if User.objects.filter(username=user_data['username']).exists():
                print(f"[INFO] Usuario ya existe: {user_data['username']}")
                continue
            
            # Crear usuario (el signal crea UserProfile automáticamente)
            user = User.objects.create_user(
                username=user_data['username'],
                email=user_data['email'],
                password=user_data['password'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name']
            )
            
            # Actualizar UserProfile creado por el signal
            userprofile = user.userprofile
            userprofile.rol = user_data['rol']
            userprofile.cedula = user_data['cedula']
            userprofile.telefono = user_data['telefono']
            userprofile.sede = user_data['sede']
            userprofile.save()
            
            # Crear perfil específico según el rol
            if user_data['rol'] == 'medico':
                especialidad = Especialidad.objects.get(nombre=user_data['especialidad'])
                MedicoProfile.objects.get_or_create(
                    user_profile=userprofile,
                    defaults={
                        'especialidad': especialidad,
                        'numero_matricula': user_data['numero_matricula']
                    }
                )
                
                # Crear disponibilidad para el médico
                dias_laborables = [0, 1, 2, 3, 4]  # Lunes a Viernes
                for dia in dias_laborables:
                    DisponibilidadMedica.objects.get_or_create(
                        medico=userprofile.medico_profile,
                        dia_semana=dia,
                        defaults={
                            'hora_inicio': '08:00',
                            'hora_fin': '16:00',
                            'activo': True
                        }
                    )
                    
            elif user_data['rol'] == 'paciente':
                # Actualizar fecha de nacimiento en UserProfile
                if user_data.get('fecha_nacimiento'):
                    userprofile.fecha_nacimiento = user_data['fecha_nacimiento']
                    userprofile.save()
                PacienteProfile.objects.get_or_create(
                    user_profile=userprofile
                )
            
            print(f"[OK] Usuario creado: {user_data['username']} ({user_data['rol']}) - Sede: {user_data['sede'].slug}")
            
        except Exception as e:
            print(f"[ERROR] {user_data['username']}: {e}")

def resumen():
    """Mostrar resumen de datos creados"""
    print()
    print("=" * 60)
    print("RESUMEN FINAL")
    print("=" * 60)
    
    print(f"Sedes: {Sede.objects.count()}")
    print(f"Especialidades: {Especialidad.objects.count()}")
    print(f"Servicios: {Servicio.objects.count()}")
    print(f"Usuarios: {User.objects.count()}")
    print(f"Perfiles: {UserProfile.objects.count()}")
    print(f"Medicos: {MedicoProfile.objects.count()}")
    print(f"Pacientes: {PacienteProfile.objects.count()}")
    print(f"Disponibilidades: {DisponibilidadMedica.objects.count()}")
    
    print()
    print("=" * 60)
    print("CONFIGURACIÓN COMPLETADA")
    print("=" * 60)
    print()
    print("USUARIOS DE PRUEBA:")
    print("  - admin / admin123 (Root)")
    print("  - gerente_general / gerente123 (Gerente General)")
    print("  - gerente_caracas / gerente123 (Gerente Caracas)")
    print("  - dr_perez / medico123 (Médico Caracas - Medicina General)")
    print("  - dra_martinez / medico123 (Médico Caracas - Cardiología)")
    print("  - dr_gomez_valencia / medico123 (Médico Valencia - Pediatría)")
    print("  - recepcionista_caracas / recepcion123 (Recepción Caracas)")
    print("  - recepcionista_valencia / recepcion123 (Recepción Valencia)")
    print("  - paciente_caracas / paciente123 (Paciente Caracas)")
    print("  - paciente_valencia / paciente123 (Paciente Valencia)")
    print()
    print("SEDES:")
    print("  - Caracas: http://127.0.0.1:8000/caracas/")
    print("  - Valencia: http://127.0.0.1:8000/valencia/")

if __name__ == '__main__':
    print("INICIANDO CONFIGURACIÓN DEL SISTEMA HEALTHY LIFE")
    print("=" * 60)
    
    sedes = crear_sedes()
    crear_especialidades()
    crear_servicios()
    crear_usuario_root()
    crear_usuarios_prueba(sedes)
    resumen()
