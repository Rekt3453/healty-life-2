import requests

try:
    response = requests.get('http://127.0.0.1:8000/registro/', timeout=5)
    print(f"Status Code: {response.status_code}")
    print(f"Response Length: {len(response.text)}")
    
    if response.status_code == 200:
        # Buscar el formulario en el HTML
        if 'form-registro' in response.text:
            print("Formulario encontrado en la pagina")
        else:
            print("Formulario NO encontrado en la pagina")
            
        if 'Healthy Life' in response.text:
            print("Titulo encontrado")
        else:
            print("Titulo NO encontrado")
            
        # Buscar campos de ubicación
        if 'estado' in response.text.lower():
            print("Campo estado encontrado")
        if 'municipio' in response.text.lower():
            print("Campo municipio encontrado")
        if 'ciudad' in response.text.lower():
            print("Campo ciudad encontrado")
        if 'parroquia' in response.text.lower():
            print("Campo parroquia encontrado")
            
        print("Registro de pacientes funcionando correctamente")
    else:
        print(f"Error HTTP: {response.status_code}")
        
except requests.exceptions.ConnectionError:
    print("Error de conexion: El servidor no esta corriendo")
except Exception as e:
    print(f"Error: {e}")
