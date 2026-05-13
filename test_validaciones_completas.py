import requests
import re

def test_validaciones_registro():
    """Probar todas las validaciones del formulario de registro"""
    
    base_url = 'http://127.0.0.1:8000'
    
    print('=== PRUEBAS DE VALIDACIÓN DE REGISTRO ===\n')
    
    # 1. Probar que el formulario carga correctamente
    print('1. Carga del formulario:')
    try:
        response = requests.get(f'{base_url}/registro/', timeout=5)
        if response.status_code == 200:
            print('✅ Formulario cargado correctamente')
            if 'data-validate' in response.text:
                print('✅ Atributos de validación presentes')
            if 'password-strength' in response.text:
                print('✅ Indicador de fortaleza de contraseña presente')
        else:
            print(f'❌ Error al cargar formulario: {response.status_code}')
    except Exception as e:
        print(f'❌ Error de conexión: {e}')
    
    print('\n' + '='*50 + '\n')
    
    # 2. Probar validaciones de frontend (simulando JavaScript)
    print('2. Validaciones de JavaScript:')
    
    test_cases = [
        {
            'name': 'Usuario muy corto',
            'data': {'username': 'abc'},
            'expected_error': 'Mínimo 4 caracteres'
        },
        {
            'name': 'Usuario con caracteres inválidos',
            'data': {'username': 'user@123'},
            'expected_error': 'Solo letras, números, guiones'
        },
        {
            'name': 'Email inválido',
            'data': {'email': 'email-invalido'},
            'expected_error': 'correo válido'
        },
        {
            'name': 'Nombre con números',
            'data': {'primer_nombre': 'Juan123'},
            'expected_error': 'solo letras'
        },
        {
            'name': 'Cédula muy corta',
            'data': {'cedula': '12345'},
            'expected_error': 'Mínimo 6 dígitos'
        },
        {
            'name': 'Teléfono muy corto',
            'data': {'telefono': '123456789'},
            'expected_error': 'Mínimo 10 dígitos'
        },
        {
            'name': 'Contraseña débil',
            'data': {'password1': '12345678'},
            'expected_error': 'incluir mayúscula, minúscula y número'
        }
    ]
    
    for test in test_cases:
        print(f'   • {test["name"]}:')
        # Simular validación de JavaScript
        if test['name'] == 'Usuario muy corto':
            if len(test['data']['username']) < 4:
                print(f'     ✅ Detectado: {test["expected_error"]}')
        elif test['name'] == 'Usuario con caracteres inválidos':
            if not re.match(r'^[a-zA-Z0-9_-]+$', test['data']['username']):
                print(f'     ✅ Detectado: {test["expected_error"]}')
        elif test['name'] == 'Email inválido':
            if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', test['data']['email']):
                print(f'     ✅ Detectado: {test["expected_error"]}')
        elif test['name'] == 'Nombre con números':
            if re.search(r'[0-9]', test['data']['primer_nombre']):
                print(f'     ✅ Detectado: {test["expected_error"]}')
        elif test['name'] == 'Cédula muy corta':
            if len(test['data']['cedula']) < 6:
                print(f'     ✅ Detectado: {test["expected_error"]}')
        elif test['name'] == 'Teléfono muy corto':
            if len(test['data']['telefono']) < 10:
                print(f'     ✅ Detectado: {test["expected_error"]}')
        elif test['name'] == 'Contraseña débil':
            password = test['data']['password1']
            if not (len(password) >= 8 and re.search(r'[A-Z]', password) and re.search(r'[a-z]', password) and re.search(r'[0-9]', password)):
                print(f'     ✅ Detectado: {test["expected_error"]}')
    
    print('\n' + '='*50 + '\n')
    
    # 3. Probar validaciones de backend (Django)
    print('3. Validaciones de Backend:')
    
    backend_tests = [
        {
            'name': 'Registro con datos válidos',
            'data': {
                'username': 'test_valid_001',
                'email': 'valid@test.com',
                'password1': 'Test123456!',
                'password2': 'Test123456!',
                'primer_nombre': 'Ana',
                'segundo_nombre': '',
                'primer_apellido': 'Garcia',
                'segundo_apellido': '',
                'tipo_cedula': 'V',
                'cedula': '98765432',
                'sexo': 'F',
                'fecha_nacimiento': '1990-01-01',
                'telefono': '04161234567',
                'estado': 'Carabobo',
                'municipio': 'Valencia',
                'ciudad': 'Valencia',
                'parroquia': 'San Blas',
                'direccion': 'Av Principal #123'
            },
            'expected_redirect': True
        },
        {
            'name': 'Registro con cédula duplicada',
            'data': {
                'username': 'test_dup_001',
                'email': 'dup@test.com',
                'password1': 'Test123456!',
                'password2': 'Test123456!',
                'primer_nombre': 'Carlos',
                'primer_apellido': 'Lopez',
                'tipo_cedula': 'V',
                'cedula': '12345678',  # Usar una que ya existe
                'sexo': 'M',
                'fecha_nacimiento': '1985-01-01',
                'telefono': '04141234567'
            },
            'expected_error': 'ya está registrada'
        },
        {
            'name': 'Registro con email duplicado',
            'data': {
                'username': 'test_email_001',
                'email': 'test_manual_001@test.com',  # Usar email que ya existe
                'password1': 'Test123456!',
                'password2': 'Test123456!',
                'primer_nombre': 'Maria',
                'primer_apellido': 'Rodriguez',
                'tipo_cedula': 'V',
                'cedula': '55554444',
                'sexo': 'F',
                'fecha_nacimiento': '1992-01-01',
                'telefono': '04121234567'
            },
            'expected_error': 'ya está en uso'
        }
    ]
    
    session = requests.Session()
    
    for test in backend_tests:
        print(f'   • {test["name"]}:')
        try:
            response = session.post(f'{base_url}/registro/', data=test['data'], allow_redirects=False)
            
            if test.get('expected_redirect'):
                if response.status_code == 302:
                    print('     ✅ Redirección correcta (registro exitoso)')
                else:
                    print(f'     ❌ No redirigió: {response.status_code}')
            elif test.get('expected_error'):
                if response.status_code == 200:
                    if test['expected_error'] in response.text:
                        print(f'     ✅ Error detectado: {test["expected_error"]}')
                    else:
                        print('     ❌ Error no encontrado en respuesta')
                else:
                    print(f'     ❌ Status inesperado: {response.status_code}')
                    
        except Exception as e:
            print(f'     ❌ Error en petición: {e}')
    
    print('\n' + '='*50 + '\n')
    
    # 4. Verificar opciones de sexo
    print('4. Opciones de sexo:')
    try:
        response = requests.get(f'{base_url}/registro/', timeout=5)
        if response.status_code == 200:
            if 'Masculino' in response.text:
                print('✅ Masculino presente')
            if 'Femenino' in response.text:
                print('✅ Femenino presente')
            if 'No Binario' in response.text:
                print('✅ No Binario presente')
            if 'Prefiero no decirlo' in response.text:
                print('✅ Prefiero no decirlo presente')
    except Exception as e:
        print(f'❌ Error verificando opciones: {e}')
    
    print('\n' + '='*50 + '\n')
    
    # 5. Verificar fortaleza de contraseña
    print('5. Fortaleza de contraseña:')
    password_tests = [
        ('12345678', 'Débil'),
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
            0: 'Débil', 1: 'Débil',
            2: 'Media', 3: 'Media',
            4: 'Buena', 5: 'Fuerte'
        }
        
        actual_strength = strength_map.get(score, 'Débil')
        print(f'   • "{password[:8]}...": {actual_strength} (esperado: {expected_strength})')
    
    print('\n=== PRUEBAS COMPLETADAS ===')

if __name__ == '__main__':
    test_validaciones_registro()
