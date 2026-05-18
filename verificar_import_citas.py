import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinica_root.settings')
django.setup()

def verificar_import_citas():
    """Verificar que los modelos de citas se importen correctamente"""
    print("=== VERIFICANDO IMPORTACIÓN DE MODELOS DE CITAS ===")
    
    try:
        # 1. Importar modelos de citas
        print("\n1. IMPORTANDO MODELOS DE CITAS:")
        
        from citas.models import (
            Especialidad, Consultorio, ServicioEspecialidad, 
            PagoCita, Cita
        )
        
        print("   OK: Modelos de citas importados correctamente")
        
        # 2. Verificar que los modelos tengan los campos correctos
        print("\n2. VERIFICANDO CAMPOS DE MODELOS:")
        
        # Verificar Cita
        campos_cita = [field.name for field in Cita._meta.fields]
        print(f"   Campos de Cita: {campos_cita}")
        
        campos_esperados_cita = [
            'id_citas', 'id_consultorio', 'id_doctor', 'id_especialidades',
            'motivo', 'id_paciente', 'id_sede', 'id_pago_cita',
            'fecha_consulta', 'fecha_emision', 'status', 'id_servicio_especialidad'
        ]
        
        for campo in campos_esperados_cita:
            if campo in campos_cita:
                print(f"   OK: {campo} existe en Cita")
            else:
                print(f"   ERROR: {campo} NO existe en Cita")
        
        # Verificar ServicioEspecialidad
        campos_servicio = [field.name for field in ServicioEspecialidad._meta.fields]
        print(f"   Campos de ServicioEspecialidad: {campos_servicio}")
        
        # 3. Verificar que los modelos se puedan consultar
        print("\n3. VERIFICANDO CONSULTAS A MODELOS:")
        
        try:
            especialidades = Especialidad.objects.all()
            print(f"   OK: Especialidades consultadas: {especialidades.count()} registros")
        except Exception as e:
            print(f"   ERROR al consultar Especialidades: {e}")
        
        try:
            servicios = ServicioEspecialidad.objects.all()
            print(f"   OK: ServicioEspecialidad consultados: {servicios.count()} registros")
        except Exception as e:
            print(f"   ERROR al consultar ServicioEspecialidad: {e}")
        
        try:
            consultorios = Consultorio.objects.all()
            print(f"   OK: Consultorios consultados: {consultorios.count()} registros")
        except Exception as e:
            print(f"   ERROR al consultar Consultorios: {e}")
        
        try:
            citas = Cita.objects.all()
            print(f"   OK: Citas consultadas: {citas.count()} registros")
        except Exception as e:
            print(f"   ERROR al consultar Citas: {e}")
        
        # 4. Verificar que los formularios se puedan importar
        print("\n4. VERIFICANDO IMPORTACIÓN DE FORMULARIOS:")
        
        from citas.forms import (
            SolicitudCitaForm, AsignarMedicoForm, 
            CrearPagoForm, CancelarCitaForm
        )
        
        print("   OK: Formularios importados correctamente")
        
        # 5. Verificar que las vistas se puedan importar
        print("\n5. VERIFICANDO IMPORTACIÓN DE VISTAS:")
        
        from citas.views import (
            solicitar_cita, mis_citas, detalle_cita, cancelar_cita,
            gestionar_citas, asignar_medico_cita, citas_doctor
        )
        
        print("   OK: Vistas importadas correctamente")
        
        print("\n=== VERIFICACIÓN COMPLETADA ===")
        print("Todos los modelos, formularios y vistas se importan correctamente")
        print("El módulo de citas está listo para funcionar")
        
    except Exception as e:
        print(f"ERROR EN VERIFICACIÓN: {e}")
        import traceback
        traceback.print_exc()

def main():
    verificar_import_citas()

if __name__ == '__main__':
    main()
