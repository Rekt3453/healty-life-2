import os
os.chdir('c:\\Users\\user\\Desktop\\healty-life-2')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinica_root.settings')
import django
django.setup()

# Probar el nuevo formulario de registro
from usuarios.forms_registro import RegistroPacienteForm

print('=== PRUEBA DEL FORMULARIO DE REGISTRO ===')

# Crear instancia del formulario
form = RegistroPacienteForm()

print('Campos del formulario:')
for field_name, field in form.fields.items():
    print(f'  {field_name}: {field.label} - {type(field).__name__}')

print('\nSelectores de ubicación:')
print(f'  Estados: {form.fields["id_estado"].queryset.count()}')
print(f'  Municipios: {form.fields["id_municipio"].queryset.count()}')
print(f'  Ciudades: {form.fields["id_ciudad"].queryset.count()}')
print(f'  Parroquias: {form.fields["id_parroquia"].queryset.count()}')

print('\n=== FORMULARIO CREADO EXITOSAMENTE ===')
