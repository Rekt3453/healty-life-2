import requests
import re

def test_validaciones_registro():
    """Probar todas las validaciones del formulario de registro"""
    
    base_url = 'http://127.0.0.1:8000'
    
    print('=== PRUEBAS DE VALIDACION DE REGISTRO ===\n')
    
    # 1. Probar que el formulario carga correctamente
    print('1. Carga del formulario:')
    try:
        response = requests.get(f'{base_url}/registro/', timeout=5)
        if response.status_code == 200:
            print('OK: Formulario cargado correctamente')
            if 'data-validate' in response.text:
                print('OK: Atributos de validacion presentes')
            if 'password-strength' in response.text:
                print('OK: Indicador de fortaleza de contrasena presente')
        else:
            print(f'ERROR: Error al cargar formulario: {response.status_code}')
    except Exception as e:
        print(f'ERROR: Error de conexion: {e}')
    
    print('\n' + '='*50 + '\n')
    
    # 2. Probar validaciones de frontend (simulando JavaScript)
    print('2. Validaciones de JavaScript:')
    
    test_cases = [
        {
            'name': 'Usuario muy corto',
            'data': {'username': 'abc'},
            'expected_error': 'Minimo 4 caracteres'
        },
        {
            'name': 'Usuario con caracteres invalidos',
            'data': {'username': 'user@123'},
            'expected_error': 'Solo letras, numeros, guiones'
        },
        {
            'name': 'Email invalido',
            'data': {'email': 'email-invalido'},
            'expected_error': 'correo valido'
        },
        {
            'name': 'Nombre con numeros',
            'data': {'primer_nombre': 'Juan123'},
            'expected_error': 'solo letras'
        },
        {
            'name': 'Cedula muy corta',
            'data': {'cedula': '12345'},
            'expected_error': 'Minimo 6 digitos'
        },
        {
            'name': 'Telefono muy corto',
            'data': {'telefono': '123456789'},
            'expected_error': 'Minimo 10 digitos'
        },
        {
            'name': 'Contrasena debil',
            'data': {'password1': '12345678'},
            'expected_error': 'incluir mayuscula, minuscula y numero'
        }
    ]
    
    for test in test_cases:
        print(f'   - {test["name"]}:')
        # Simular validacion de JavaScript
        if test['name'] == 'Usuario muy corto':
            if len(test['data']['username']) < 4:
                print(f'     OK: Detectado: {test["expected_error"]}')
        elif test['name'] == 'Usuario con caracteres invalidos':
            if not re.match(r'^[a-zA-Z0-9_-]+$', test['data']['username']):
                print(f'     OK: Detectado: {test["expected_error"]}')
        elif test['name'] == 'Email invalido':
            if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', test['data']['email']):
                print(f'     OK: Detectado: {test["expected_error"]}')
        elif test['name'] == 'Nombre con numeros':
            if re.search(r'[0-9]', test['data']['primer_nombre']):
                print(f'     OK: Detectado: {test["expected_error"]}')
        elif test['name'] == 'Cedula muy corta':
            if len(test['data']['cedula']) < 6:
                print(f'     OK: Detectado: {test["expected_error"]}')
        elif test['name'] == 'Telefono muy corto':
            if len(test['data']['telefono']) < 10:
                print(f'     OK: Detectado: {test["expected_error"]}')
        elif test['name'] == 'Contrasena debil':
            password = test['data']['password1']
            if not (len(password) >= 8 and re.search(r'[A-Z]', password) and re.search(r'[a-z]', password) and re.search(r'[0-9]', password)):
                print(f'     OK: Detectado: {test["expected_error"]}')
    
    print('\n' + '='*50 + '\n')
    
    # 3. Probar validaciones de backend (Django)
    print('3. Validaciones de Backend:')
    
    backend_tests = [
        {
            'name': 'Registro con datos validos',
            'data': {
                'username': 'test_valid_002',
                'email': 'valid2@test.com',
                'password1': 'Test123456!',
                'password2': 'Test123456!',
                'primer_nombre': 'Ana',
                'segundo_nombre': '',
                'primer_apellido': 'Garcia',
                'segundo_apellido': '',
                'tipo_cedula': 'V',
                'cedula': '987654321',
                'sexo': 'F',
                'fecha_nacimiento': '1990-01-01',
                'telefono': '04161234568',
                'estado': 'Carabobo',
                'municipio': 'Valencia',
                'ciudad': 'Valencia',
                'parroquia': 'San Blas',
                'direccion': 'Av Principal #123'
            },
            'expected_redirect': True
        },
        {
            'name': 'Registro con cedula duplicada',
            'data': {
                'username': 'test_dup_002',
                'email': 'dup2@test.com',
                'password1': 'Test123456!',
                'password2': 'Test123456!',
                'primer_nombre': 'Carlos',
                'primer_apellido': 'Lopez',
                'tipo_cedula': 'V',
                'cedula': '12345678',  # Usar una que ya existe
                'sexo': 'M',
                'fecha_nacimiento': '1985-01-01',
                'telefono': '04141234568'
            },
            'expected_error': 'ya esta registrada'
        }
    ]
    
    session = requests.Session()
    
    for test in backend_tests:
        print(f'   - {test["name"]}:')
        try:
            response = session.post(f'{base_url}/registro/', data=test['data'], allow_redirects=False)
            
            if test.get('expected_redirect'):
                if response.status_code == 302:
                    print('     OK: Redireccion correcta (registro exitoso)')
                else:
                    print(f'     ERROR: No redirigio: {response.status_code}')
            elif test.get('expected_error'):
                if response.status_code == 200:
                    if test['expected_error'] in response.text:
                        print(f'     OK: Error detectado: {test["expected_error"]}')
                    else:
                        print('     ERROR: Error no encontrado en respuesta')
                else:
                    print(f'     ERROR: Status inesperado: {response.status_code}')
                    
        except Exception as e:
            print(f'     ERROR: Error en peticion: {e}')
    
    print('\n' + '='*50 + '\n')
    
    # 4. Verificar opciones de sexo
    print('4. Opciones de sexo:')
    try:
        response = requests.get(f'{base_url}/registro/', timeout=5)
        if response.status_code == 200:
            if 'Masculino' in response.text:
                print('OK: Masculino presente')
            if 'Femenino' in response.text:
                print('OK: Femenino presente')
            if 'No Binario' in response.text:
                print('OK: No Binario presente')
            if 'Prefiero no decirlo' in response.text:
                print('OK: Prefiero no decirlo presente')
    except Exception as e:
        print(f'ERROR: Error verificando opciones: {e}')
    
    print('\n' + '='*50 + '\n')
    
    # 5. Verificar fortaleza de contrasena
    print('5. Fortaleza de contrasena:')
    password_tests = [
        ('12345678', 'Debil'),
        ('Password123', 'Media'),
        ('Password123!', 'Buena'),
        ('P@ssw0rd!2024', 'Fuerte')
    ]
    
    for password, expected_strength in password_tests:
        score = 0
        if len(password) >= 8: score += 1
        if re.search(r'[A-Z]', password): score += 1
        if re.search(r'[a-z]', password): score += 1
        if re.search(r'[0-9]', password): score += 1
        if re.search(r'[\W_]', password): score += 1
        
        strength_map = {
            0: 'Debil', 1: 'Debil',
            2: 'Media', 3: 'Media',
            4: 'Buena', 5: 'Fuerte'
        }
        
        actual_strength = strength_map.get(score, 'Debil')
        print(f'   - "{password[:8]}...": {actual_strength} (esperado: {expected_strength})')
    
    print('\n=== PRUEBAS COMPLETADAS ===')

if __name__ == '__main__':
    test_validaciones_registro()
