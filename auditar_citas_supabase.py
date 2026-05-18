import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinica_root.settings')
django.setup()

def auditar_citas_supabase():
    """Auditar estructura de tablas de citas en Supabase"""
    print("=== AUDITANDO TABLAS DE CITAS EN SUPABASE ===")
    
    try:
        from django.db import connection
        
        # 1. Tabla citas
        print("\n1. TABLA CITAS:")
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'citas' 
                ORDER BY ordinal_position
            """)
            columnas = cursor.fetchall()
            for col in columnas:
                print(f"   - {col[0]} ({col[1]}, nullable: {col[2]}, default: {col[3]})")
        
        # 2. Tabla servicios_especialidad
        print("\n2. TABLA SERVICIOS_ESPECIALIDAD:")
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'servicios_especialidad' 
                ORDER BY ordinal_position
            """)
            columnas = cursor.fetchall()
            for col in columnas:
                print(f"   - {col[0]} ({col[1]}, nullable: {col[2]}, default: {col[3]})")
        
        # 3. Tabla consultorio
        print("\n3. TABLA CONSULTORIO:")
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'consultorio' 
                ORDER BY ordinal_position
            """)
            columnas = cursor.fetchall()
            for col in columnas:
                print(f"   - {col[0]} ({col[1]}, nullable: {col[2]}, default: {col[3]})")
        
        # 4. Tabla pagos_cita
        print("\n4. TABLA PAGOS_CITA:")
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'pagos_cita' 
                ORDER BY ordinal_position
            """)
            columnas = cursor.fetchall()
            for col in columnas:
                print(f"   - {col[0]} ({col[1]}, nullable: {col[2]}, default: {col[3]})")
        
        # 5. Tabla especialidades
        print("\n5. TABLA ESPECIALIDADES:")
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'especialidades' 
                ORDER BY ordinal_position
            """)
            columnas = cursor.fetchall()
            for col in columnas:
                print(f"   - {col[0]} ({col[1]}, nullable: {col[2]}, default: {col[3]})")
        
        # 6. Tabla paciente_datos_personales
        print("\n6. TABLA PACIENTE_DATOS_PERSONALES:")
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'paciente_datos_personales' 
                ORDER BY ordinal_position
            """)
            columnas = cursor.fetchall()
            for col in columnas:
                print(f"   - {col[0]} ({col[1]}, nullable: {col[2]}, default: {col[3]})")
        
        # 7. Tabla doctor
        print("\n7. TABLA DOCTOR:")
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'doctor' 
                ORDER BY ordinal_position
            """)
            columnas = cursor.fetchall()
            for col in columnas:
                print(f"   - {col[0]} ({col[1]}, nullable: {col[2]}, default: {col[3]})")
        
        # 8. Tabla sede
        print("\n8. TABLA SEDE:")
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'sede' 
                ORDER BY ordinal_position
            """)
            columnas = cursor.fetchall()
            for col in columnas:
                print(f"   - {col[0]} ({col[1]}, nullable: {col[2]}, default: {col[3]})")
        
        # 9. Datos de ejemplo
        print("\n9. DATOS DE EJEMPLO:")
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM especialidades LIMIT 5")
            print("   Especialidades:", cursor.fetchall())
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM servicios_especialidad LIMIT 5")
            print("   Servicios especialidad:", cursor.fetchall())
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM consultorio LIMIT 5")
            print("   Consultorios:", cursor.fetchall())
        
        print("\n=== AUDITORIA COMPLETADA ===")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    auditar_citas_supabase()
