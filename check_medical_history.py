#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinica_root.settings')
django.setup()

from django.db import connection

def check_medical_history():
    print("=== Verificar historial médico existente ===")
    
    with connection.cursor() as cursor:
        # Verificar tabla historial_medico_paciente
        try:
            cursor.execute("SELECT * FROM historial_medico_paciente LIMIT 1;")
            historial = cursor.fetchone()
            if historial:
                print(f"Historial médico encontrado: {historial}")
                return historial[0]  # id_historial_medico
            else:
                print("No hay historiales médicos en la tabla")
        except Exception as e:
            print(f"Error al consultar historial_medico_paciente: {e}")
        
        # Intentar crear un historial médico básico
        try:
            cursor.execute("INSERT INTO historial_medico_paciente (id_alergias, id_tipo_sangre, id_vacunas, id_enfermedades, id_sede, Status) VALUES (NULL, NULL, NULL, NULL, NULL, TRUE) RETURNING id_historial_medico;")
            new_id = cursor.fetchone()[0]
            print(f"Historial médico creado con ID: {new_id}")
            return new_id
        except Exception as e:
            print(f"No se pudo crear historial médico: {e}")
            # Intentar sin el campo Status
            try:
                cursor.execute("INSERT INTO historial_medico_paciente (id_alergias, id_tipo_sangre, id_vacunas, id_enfermedades) VALUES (NULL, NULL, NULL, NULL) RETURNING id_historial_medico;")
                new_id = cursor.fetchone()[0]
                print(f"Historial médico creado sin Status con ID: {new_id}")
                return new_id
            except Exception as e2:
                print(f"Tampoco se pudo crear sin Status: {e2}")
            
            # Verificar qué tablas relacionadas con historial existen
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name ILIKE '%historial%' OR table_name ILIKE '%alergia%' OR table_name ILIKE '%sangre%' OR table_name ILIKE '%vacuna%' ORDER BY table_name;")
            tables = cursor.fetchall()
            print("Tablas relacionadas con historial médico:")
            for table in tables:
                print(f"  - {table[0]}")
        
        return None

if __name__ == '__main__':
    check_medical_history()
