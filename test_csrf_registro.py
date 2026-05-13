import requests
import re

# Probar acceso directo al formulario
try:
    response = requests.get('http://127.0.0.1:8000/registro/', timeout=5)
    print(f'Status: {response.status_code}')
    
    # Verificar si hay CSRF token
    if 'csrfmiddlewaretoken' in response.text:
        print('CSRF token presente')
    if 'data-validate' in response.text:
        print('Atributos de validacion presentes')
    if 'password-strength' in response.text:
        print('Indicador de fortaleza presente')
        
    # Intentar obtener el CSRF token
    csrf_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', response.text)
    if csrf_match:
        csrf_token = csrf_match.group(1)
        print(f'CSRF token encontrado: {csrf_token[:20]}...')
        
        # Probar POST con CSRF token
        data = {
            'csrfmiddlewaretoken': csrf_token,
            'username': 'test_csrf_001',
            'email': 'csrf@test.com',
            'password1': 'Test123456!',
            'password2': 'Test123456!',
            'primer_nombre': 'Test',
            'primer_apellido': 'User',
            'tipo_cedula': 'V',
            'cedula': '99999999',
            'sexo': 'M',
            'fecha_nacimiento': '1990-01-01',
            'telefono': '04169999999'
        }
        
        session = requests.Session()
        session.cookies.set('csrftoken', csrf_token)
        
        response = session.post('http://127.0.0.1:8000/registro/', data=data, allow_redirects=False)
        print(f'POST Status: {response.status_code}')
        
        if response.status_code == 302:
            print('POST exitoso (redireccion)')
        elif response.status_code == 200:
            print('POST mostrando errores (normal)')
        else:
            print(f'Error inesperado: {response.status_code}')
    else:
        print('No se encontro CSRF token')
        
except Exception as e:
    print(f'Error: {e}')
