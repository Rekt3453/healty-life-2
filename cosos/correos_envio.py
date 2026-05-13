#!/usr/bin/env python3
"""
Envía correos de bienvenida personalizados para HealthCore - Sistema de Citas Médicas
CC visible  : soporte@healthcore.com
BCC (oculta): admin@healthcore.com
"""

import ssl, smtplib, time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ── CONFIGURACIÓN SMTP ───────────────────────────────────────────────
SMTP_HOST_IP   = "204.13.23"            # fuerza IPv4
SMTP_HOST_NAME = ""     # nombre del certificado
SMTP_PORT      = 587                         # STARTTLS
SMTP_USER      = ""
SMTP_PASS      = ""

# ── DESTINATARIOS EN COPIA ───────────────────────────────────────────
CC_ADDR  = "soporte@healthcore.com"
BCC_ADDR = "admin@healthcore.com"

# ── MENSAJE ──────────────────────────────────────────────────────────
SUBJECT  = "🏥 ¡Bienvenido al Portal Médico! Gestiona tu salud con facilidad"

TEMPLATE = """\
Estimado(a) {firstname} {lastname},

¡Bienvenido(a) a HealthCore! 🏥✨ Estamos emocionados de tenerte en nuestra familia médica digital.

¡Felicidades! Has dado el primer paso hacia una experiencia médica revolucionaria. En HealthCore, hemos transformado la atención médica tradicional para ponerte a ti en el centro de todo, con tecnología de vanguardia que hará tu vida más fácil y tu salud más accesible.

¿Qué hace HealthCore tan especial? 🌟

📅 **CITAS 24/7**: Agenda tus consultas médicas en cualquier momento, desde cualquier lugar. ¡No más esperas ni llamadas frustrantes!

📋 **HISTORIAL MÉDICO DIGITAL**: Accede a toda tu información médica, resultados de exámenes y evolución de tratamientos con solo un clic.

💊 **RECETAS INTELIGENTES**: Recibe tus recetas médicas digitalmente con recordatorios automáticos para que nunca olvides tus medicamentos.

💬 **CHAT MÉDICO**: Comunícate directamente con tus médicos para consultas rápidas, seguimiento de tratamientos y dudas urgentes.

🏥 **ESPECIALISTAS DE ÉLITE**: Accede a nuestra red de médicos especialistas en todas las áreas de la salud, todos ellos certificados y con amplia experiencia.

🔒 **SEGURIDAD MÁXIMA**: Tus datos médicos están protegidos con encriptación de nivel bancario y cumplimiento total de las normativas de privacidad médica.

Ya puedes acceder a tu portal médico personal a través del siguiente enlace:

https://healthcore.com/login

Tus credenciales de acceso son:

👤 Usuario: {username}
🔒 Contraseña: {password}
📧 Correo electrónico: {email}

🚀 **¡Comienza tu viaje de salud ahora mismo!**

Te recomendamos seguir estos pasos para aprovechar al máximo tu experiencia:

✅ Completa tu perfil médico con tu información básica
✅ Agenda tu primera cita médica de bienvenida
✅ Explora tu historial médico digital
✅ Configura tus recordatorios de medicamentos
✅ Conoce a tus médicos asignados

En HealthCore, no solo gestionamos citas médicas: construimos relaciones de confianza, empoderamos a nuestros pacientes con información y tecnología, y creamos una experiencia médica que realmente pone tu bienestar primero.

¿Sabías que? 🤔
- Nuestro sistema reduce los tiempos de espera en un 85%
- El 97% de nuestros pacientes reportan mayor satisfacción con su atención médica
- Tienes acceso a telemedicina desde cualquier dispositivo
- Nuestros médicos están disponibles para consultas virtuales 24/7

Este no es solo un sistema de citas médicas: es tu puerta de entrada a una nueva era de atención médica donde tú eres el protagonista, tu tiempo es valioso, y tu salud es nuestra misión más importante.

¡Estamos aquí para ti en cada paso de tu viaje hacia una vida más saludable! 💚

¿Necesitas ayuda? Nuestro equipo de soporte está disponible 24/7:
📞 Teléfono: +58 123-456-7890
📧 Correo: soporte@healthcore.com
💬 Chat: Disponible en tu portal

¡Mucho éxito en esta nueva etapa de cuidado médico! Estamos seguros de que HealthCore transformará tu experiencia con la salud para siempre.

🏥 **HealthCore - Tu Salud, Nuestra Misión** 🌟"""

def enviar_correo_bienvenida(datos_paciente):
    """
    Envía correo de bienvenida a un nuevo paciente usando datos del formulario register.html
    
    Args:
        datos_paciente (dict): Diccionario con los datos del paciente:
            - nombre_1: Primer nombre
            - nombre_2: Segundo nombre (opcional)
            - apellido_1: Primer apellido
            - apellido_2: Segundo apellido (opcional)
            - email: Correo electrónico
            - password: Contraseña
            - cedula: Cédula (usada como username)
    """
    
    # Construir nombre completo
    firstname = datos_paciente.get('nombre_1', '')
    lastname = datos_paciente.get('apellido_1', '')
    
    # Agregar segundo nombre y apellido si existen
    if datos_paciente.get('nombre_2'):
        firstname += " " + datos_paciente.get('nombre_2')
    if datos_paciente.get('apellido_2'):
        lastname += " " + datos_paciente.get('apellido_2')
    
    # Preparar datos para la plantilla
    template_data = {
        'firstname': firstname,
        'lastname': lastname,
        'email': datos_paciente.get('email', ''),
        'username': datos_paciente.get('cedula', ''),
        'password': datos_paciente.get('password', '')
    }
    
    # Crear mensaje
    msg = MIMEMultipart()
    msg["From"]    = SMTP_USER
    msg["To"]      = datos_paciente.get('email', '')
    msg["Cc"]      = CC_ADDR
    msg["Bcc"]     = BCC_ADDR
    msg["Subject"] = SUBJECT
    msg.attach(MIMEText(TEMPLATE.format(**template_data), "plain"))
    
    # Enviar correo
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_HOST_IP, SMTP_PORT, timeout=60) as server:
            # Ajusta _host para que la verificación TLS use el nombre del certificado
            server._host = SMTP_HOST_NAME
            server.starttls(context=context)
            server.login(SMTP_USER, SMTP_PASS)
            
            server.send_message(msg)
            print(f"✔ Correo de bienvenida enviado a {datos_paciente.get('email')}")
            
    except Exception as e:
        print(f"❌ Error al enviar correo a {datos_paciente.get('email')}: {str(e)}")
        return False
    
    return True

def enviar_correo_bienvenida_individual(nombre_1, nombre_2, apellido_1, apellido_2, email, password, cedula):
    """
    Función simplificada para enviar correo de bienvenida con parámetros individuales
    """
    datos_paciente = {
        'nombre_1': nombre_1,
        'nombre_2': nombre_2,
        'apellido_1': apellido_1,
        'apellido_2': apellido_2,
        'email': email,
        'password': password,
        'cedula': cedula
    }
    
    return enviar_correo_bienvenida(datos_paciente)

# ── EJEMPLO DE USO ────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Ejemplo de cómo usar la función con datos del formulario register.html
    datos_ejemplo = {
        'nombre_1': 'Juan',
        'nombre_2': 'Carlos',
        'apellido_1': 'Pérez',
        'apellido_2': 'García',
        'email': 'juan.perez@email.com',
        'password': 'Password123!',
        'cedula': '12345678'
    }
    
    print("� Enviando correo de bienvenida de ejemplo...")
    if enviar_correo_bienvenida(datos_ejemplo):
        print("🎉 ¡Correo enviado exitosamente!")
    else:
        print("❌ Error al enviar el correo")
    
    print("\n📋 Para usar con datos del formulario register.html:")
    print("1. Captura los datos del formulario")
    print("2. Llama a enviar_correo_bienvenida(datos_paciente)")
    print("3. O usa la función individual: enviar_correo_bienvenida_individual(...)")
