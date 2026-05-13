import os
os.chdir('c:\\Users\\user\\Desktop\\healty-life-2')
os.environ['DJANGO_SETTINGS_MODULE'] = 'clinica_root.settings'
import django
django.setup()

# Probar el formulario de registro manualmente
from usuarios.forms_final import RegistroPacienteForm

print('=== PRUEBA MANUAL DE FORMULARIO ===')

# Datos de prueba
form_data = {
    'username': 'test_manual_001',
    'email': 'manual@test.com',
    'password1': 'Test123456!',
    'password2': 'Test123456!',
    'nombre_1': 'Carlos',
    'nombre_2': '',
    'apellido_1': 'Rodriguez',
    'apellido_2': '',
    'tipo_cedula': 'V',
    'cedula': '55544433',
    'sexo': 'M',
    'fecha_nacimiento': '1985-03-15',
    'telefono': '04169876543',
    'estado': 'Miranda',
    'municipio': 'Sucre',
    'ciudad': 'Petare',
    'parroquia': 'La Dolorita',
    'direccion': 'Calle Principal #789'
}

# Crear formulario
form = RegistroPacienteForm(data=form_data)

print(f'Formulario válido: {form.is_valid()}')

if form.is_valid():
    print('Campos válidos:')
    for field, value in form.cleaned_data.items():
        print(f'  {field}: {value}')
    
    try:
        # Intentar guardar
        user = form.save()
        print(f'Usuario guardado: {user.username}')
        print('Registro EXITOSO')
    except Exception as e:
        print(f'Error al guardar: {e}')
        import traceback
        traceback.print_exc()
else:
    print('Errores del formulario:')
    for field, errors in form.errors.items():
        print(f'  {field}: {errors}')

print('=== FIN DE PRUEBA ===')
