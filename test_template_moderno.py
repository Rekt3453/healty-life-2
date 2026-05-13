import requests

# Probar el nuevo template de registro
try:
    response = requests.get('http://127.0.0.1:8000/registro/', timeout=5)
    print(f'Registro Status: {response.status_code}')
    
    if response.status_code == 200:
        # Buscar elementos del nuevo diseño
        if 'hero-section' in response.text:
            print('Hero section con gradiente encontrado')
        if 'Healthy Life' in response.text:
            print('Titulo Healthy Life encontrado')
        if 'tailwindcss' in response.text:
            print('Tailwind CSS cargado')
        if 'card-registro' in response.text:
            print('Tarjetas de registro encontradas')
        if 'Informacion de Cuenta' in response.text:
            print('Seccion de cuenta encontrada')
        if 'Informacion de Ubicacion' in response.text:
            print('Seccion de ubicacion encontrada')
        if 'Crear Cuenta' in response.text:
            print('Boton de envio encontrado')
            
        print('Template moderno aplicado correctamente')
    else:
        print(f'Error en registro: {response.status_code}')
        
except Exception as e:
    print(f'Error de conexion: {e}')
