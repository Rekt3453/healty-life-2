#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinica_root.settings')
django.setup()

from django.contrib.auth.models import User
from usuarios.models import PacienteProfile

def create_test_data_simple():
    print("=== Crear datos de prueba simples ===")
    
    try:
        # Crear usuario de prueba sin dependencias
        print("Creando usuario de prueba...")
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        user = User.objects.create_user(
            username=f'testuser_{unique_id}',
            email=f'test{unique_id}@test.com',
            password='testpass123',
            first_name='Juan',
            last_name='Perez'
        )
        print(f"[OK] User creado: {user}")
        
        # Crear User_paciente primero
        print("\nCreando User_paciente...")
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("INSERT INTO \"User_paciente\" (\"Usename\", contrasena, \"Correo\", \"Status\") VALUES (%s, 'password123', %s, TRUE) RETURNING id_user_paceinte;", [user.username, user.email])
            user_paciente_id = cursor.fetchone()[0]
            print(f"[OK] User_paciente creado con ID: {user_paciente_id}")
        
        # Crear PacienteProfile con valores mínimos
        print("\nCreando PacienteProfile...")
        paciente_profile = PacienteProfile.objects.create(
            nombre_1='Juan',
            nombre_2='',
            apellido_1='Perez',
            apellido_2='',
            id_historial_medico_paciente=1,  # ID del historial médico creado
            id_user_paciente=user_paciente_id,  # ID del User_paciente
            cedula='V12345678',
            tipo_cedula='V',
            sexo='M'
        )
        print(f"[OK] PacienteProfile creado: {paciente_profile}")
        
        # Probar autenticacion
        print("\nProbando autenticacion...")
        from django.contrib.auth import authenticate
        authenticated_user = authenticate(username=user.username, password='testpass123')
        
        if authenticated_user:
            print(f"[OK] Autenticacion exitosa: {authenticated_user}")
            # Buscar el perfil de paciente manualmente
            try:
                # Buscar por nombre de usuario en User_paciente
                from django.db import connection
                with connection.cursor() as cursor:
                    cursor.execute("SELECT id_user_paceinte FROM \"User_paciente\" WHERE \"Usename\" = %s;", [authenticated_user.username])
                    result = cursor.fetchone()
                    if result:
                        user_paciente_id = result[0]
                        paciente = PacienteProfile.objects.filter(id_user_paciente=user_paciente_id).first()
                        if paciente:
                            print(f"   Perfil de paciente: {paciente}")
                        else:
                            print("   No se encontró perfil de paciente")
                    else:
                        print("   No se encontró User_paciente")
            except Exception as e:
                print(f"   Error al buscar perfil: {e}")
        else:
            print("[FAIL] Autenticacion fallida")
            
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    create_test_data_simple()
