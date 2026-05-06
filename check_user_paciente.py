#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinica_root.settings')
django.setup()

from django.db import connection

def check_user_paciente():
    print("=== Verificar tabla User_paciente ===")
    
    with connection.cursor() as cursor:
        # Verificar estructura de User_paciente
        cursor.execute("SELECT column_name, data_type, character_maximum_length, is_nullable FROM information_schema.columns WHERE table_name = 'User_paciente' ORDER BY ordinal_position;")
        columns = cursor.fetchall()
        
        print("Estructura de la tabla User_paciente:")
        for col in columns:
            null_status = 'NULL' if col[3] == 'YES' else 'NOT NULL'
            max_length = col[2] if col[2] else 'N/A'
            print(f"  {col[0]}: {col[1]} ({max_length}) - {null_status}")
        
        # Verificar si hay datos existentes
        try:
            cursor.execute("SELECT * FROM \"User_paciente\" LIMIT 1;")
            user_paciente = cursor.fetchone()
            if user_paciente:
                print(f"User_paciente existente: {user_paciente}")
            else:
                print("No hay datos en User_paciente")
        except Exception as e:
            print(f"Error al consultar User_paciente: {e}")
        
        # Intentar crear un User_paciente básico
        try:
            # Probar con el nombre exacto como aparece en la estructura
            cursor.execute("INSERT INTO \"User_paciente\" (\"Usename\", contrasena, \"Correo\", id_sede, \"Status\") VALUES ('testuser', 'password123', 'test@test.com', NULL, TRUE) RETURNING id_user_paceinte;")
            new_id = cursor.fetchone()[0]
            print(f"User_paciente creado con ID: {new_id}")
            return new_id
        except Exception as e:
            print(f"No se pudo crear User_paciente con nombres exactos: {e}")
            # Intentar solo con los campos obligatorios
            try:
                cursor.execute("INSERT INTO \"User_paciente\" (contrasena) VALUES ('password123') RETURNING id_user_paceinte;")
                new_id = cursor.fetchone()[0]
                print(f"User_paciente creado solo con contraseña ID: {new_id}")
                return new_id
            except Exception as e2:
                print(f"Tampoco con solo contraseña: {e2}")
                
                # Como último recurso, intentar insertar sin especificar campos (dejando NULL)
                try:
                    cursor.execute("INSERT INTO \"User_paciente\" DEFAULT VALUES RETURNING id_user_paceinte;")
                    new_id = cursor.fetchone()[0]
                    print(f"User_paciente creado con DEFAULT VALUES ID: {new_id}")
                    return new_id
                except Exception as e3:
                    print(f"Tampoco con DEFAULT VALUES: {e3}")
            
    return None

if __name__ == '__main__':
    check_user_paciente()
