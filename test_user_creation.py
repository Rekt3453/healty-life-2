#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinica_root.settings')
django.setup()

from django.contrib.auth.models import User
from usuarios.models import UserProfile, PacienteProfile, Sede

def test_user_creation():
    print("=== Prueba de creacion de usuario ===")
    
    try:
        # Verificar que exista al menos una sede
        sedes = Sede.objects.all()
        print(f"Sedes disponibles: {sedes.count()}")
        if sedes.count() == 0:
            print("No hay sedes disponibles. Creando una sede de prueba...")
            sede = Sede.objects.create(
                id_direccion=1,
                rif_sede='J-123456789',
                telefono='04141234567',
                id_CM=1,
                Status=True
            )
            print(f"[OK] Sede creada: {sede}")
        else:
            sede = sedes.first()
            print(f"[OK] Usando sede existente: {sede}")
        
        # Crear usuario de prueba
        print("\nCreando usuario de prueba...")
        user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123',
            first_name='Juan',
            last_name='Perez'
        )
        print(f"[OK] User creado: {user}")
        
        # Crear PacienteProfile
        print("\nCreando PacienteProfile...")
        paciente_profile = PacienteProfile.objects.create(
            nombre_1='Juan',
            nombre_2='',
            apellido_1='Perez',
            apellido_2='',
            id_historial_medico_paciente=1,
            id_user_paciente=user,
            cedula='V12345678',
            tipo_cedula='V',
            sexo='M'
        )
        print(f"[OK] PacienteProfile creado: {paciente_profile}")
        
        # Probar autenticacion
        print("\nProbando autenticacion...")
        from django.contrib.auth import authenticate
        authenticated_user = authenticate(username='testuser', password='testpass123')
        
        if authenticated_user:
            print(f"[OK] Autenticacion exitosa: {authenticated_user}")
            print(f"   Perfil de paciente: {authenticated_user.pacienteprofile}")
        else:
            print("[FAIL] Autenticacion fallida")
            
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_user_creation()
