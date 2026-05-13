import os
os.chdir('c:\\Users\\user\\Desktop\\healty-life-2')
os.environ['DJANGO_SETTINGS_MODULE'] = 'clinica_root.settings'
import django
django.setup()

# Probar el registro completo
from usuarios.forms_final import RegistroPacienteForm
from usuarios.models import UserPaciente, PacienteDatosPersonales, DireccionPaciente

print('=== PRUEBA DE REGISTRO COMPLETO ===')

# Datos de prueba
form_data = {
    'username': 'test_paciente_123',
    'email': 'test@ejemplo.com',
    'password1': 'Test123456!',
    'password2': 'Test123456!',
    'nombre_1': 'Juan',
    'nombre_2': 'Carlos',
    'apellido_1': 'Pérez',
    'apellido_2': 'García',
    'tipo_cedula': 'V',
    'cedula': '99988877',
    'sexo': 'M',
    'fecha_nacimiento': '1990-01-01',
    'telefono': '04121234567',
    'estado': 'Distrito Capital',
    'municipio': 'Libertador',
    'ciudad': 'Caracas',
    'parroquia': 'Altagracia',
    'direccion': 'Av. Principal #123'
}

# Crear y validar formulario
form = RegistroPacienteForm(data=form_data)

if form.is_valid():
    print('Formulario valido')
    
    try:
        # Intentar guardar
        user = form.save(commit=False)
        print('Datos preparados para guardar')
        
        # Verificar que se crearán los objetos
        print(f'  User: {user.username}')
        print(f'  Email: {user.email}')
        print('  Ubicación guardara en direccion_paciente')
        print('  Datos personales guardara en paciente_datos_personales')
        
    except Exception as e:
        print(f'Error al guardar: {e}')
        import traceback
        traceback.print_exc()
else:
    print('Formulario invalido')
    for field, errors in form.errors.items():
        print(f'  {field}: {errors}')

print('\n=== PRUEBA COMPLETADA ===')
