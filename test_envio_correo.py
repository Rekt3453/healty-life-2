"""
Script de prueba para verificar el sistema de envío de correos de confirmación
"""

import sys
sys.path.append('c:\\Users\\user\\Desktop\\healty-life-2')

from usuarios.email_config import enviar_correo_confirmacion_simple

def test_envio_correo():
    """Prueba el envío de correo de confirmación"""
    
    print("=== PRUEBA DE ENVIO DE CORREO DE CONFIRMACION ===\n")
    
    # Datos de prueba
    datos_prueba = {
        'primer_nombre': 'Juan',
        'segundo_nombre': 'Carlos',
        'primer_apellido': 'Perez',
        'segundo_apellido': 'Garcia',
        'email': 'jose1angel2morales@gmail.com',  # Enviar a tu propio correo para probar
        'username': 'test_usuario_001',
        'password': 'Test123456!',
        'cedula': '12345678'
    }
    
    print("Enviando correo de prueba...")
    print(f"Destinatario: {datos_prueba['email']}")
    print(f"Nombre: {datos_prueba['primer_nombre']} {datos_prueba['primer_apellido']}")
    print(f"Usuario: {datos_prueba['username']}")
    print()
    
    resultado = enviar_correo_confirmacion_simple(
        datos_prueba['primer_nombre'],
        datos_prueba['segundo_nombre'],
        datos_prueba['primer_apellido'],
        datos_prueba['segundo_apellido'],
        datos_prueba['email'],
        datos_prueba['username'],
        datos_prueba['password'],
        datos_prueba['cedula']
    )
    
    if resultado:
        print("OK: CORREO ENVIADO EXITOSAMENTE")
        print("Revisa tu bandeja de entrada para verificar el contenido del correo.")
    else:
        print("ERROR: ERROR AL ENVIAR CORREO")
        print("Verifica la configuracion SMTP en email_config.py")
    
    print("\n=== FIN DE PRUEBA ===")

if __name__ == "__main__":
    test_envio_correo()
