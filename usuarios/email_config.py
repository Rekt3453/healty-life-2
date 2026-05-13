"""
Configuración de correo electrónico para Healthy Life
Sistema de envío de correos de confirmación de registro
"""

import ssl, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ── CONFIGURACIÓN SMTP ───────────────────────────────────────────────
# IMPORTANTE: Debes configurar estos valores con tus credenciales reales
# Para Gmail: smtp.gmail.com, puerto 587
# Para Outlook: smtp.office365.com, puerto 587
# Para Yahoo: smtp.mail.yahoo.com, puerto 587

SMTP_HOST_IP   = "smtp.gmail.com"  # Servidor SMTP de Gmail
SMTP_HOST_NAME = "smtp.gmail.com"  # Nombre del certificado (generalmente igual al host)
SMTP_PORT      = 587  # STARTTLS (puerto estándar para TLS)
SMTP_USER      = "jose1angel2morales@gmail.com"  # Tu correo electrónico completo
SMTP_PASS      = "rppr hyic crvx rscp"  # Tu contraseña de aplicación de Gmail

# ── DESTINATARIOS EN COPIA ───────────────────────────────────────────
CC_ADDR  = ""  # Correo en copia visible (opcional)
BCC_ADDR = ""  # Correo en copia oculta (opcional)

# ── CONFIGURACIÓN DEL SITIO ───────────────────────────────────────────
SITE_NAME = "Healthy Life"
SITE_URL = "http://127.0.0.1:8000"  # Cambiar a tu URL de producción

# ── MENSAJE DE CONFIRMACIÓN DE REGISTRO ───────────────────────────────
SUBJECT = f"🏥 ¡Bienvenido a {SITE_NAME}! Tu cuenta ha sido creada exitosamente"

TEMPLATE = """\
Estimado(a) {nombre_completo},

¡Bienvenido(a) a {site_name}! 🏥✨

Nos complace informarte que tu cuenta ha sido creada exitosamente. Estamos emocionados de tenerte en nuestra familia de salud digital.

📋 **Datos de tu cuenta:**

👤 Nombre de Usuario: {username}
📧 Correo Electrónico: {email}
🆔 Cédula: {cedula}
📅 Fecha de Registro: {fecha_registro}

🔐 **Tu contraseña:** {password}

⚠️ **IMPORTANTE:** Por seguridad, te recomendamos cambiar tu contraseña después de tu primer inicio de sesión.

🚀 **¿Qué puedes hacer ahora?**

Ya puedes acceder a tu portal de salud personal a través del siguiente enlace:

{site_url}/login/paciente/

Una vez que inicies sesión, podrás:

✅ Agendar citas médicas con nuestros especialistas
✅ Ver tu historial médico completo
✅ Recibir notificaciones de tus citas
✅ Actualizar tu información personal
✅ Comunicarte con nuestros médicos

💡 **Consejos de seguridad:**

• Nunca compartas tu contraseña con nadie
• Cambia tu contraseña regularmente
• Usa contraseñas fuertes con letras, números y símbolos
• Si sospechas de actividad extraña, contáctanos inmediatamente

📞 **¿Necesitas ayuda?**

Nuestro equipo de soporte está disponible para ayudarte:
📧 Correo: soporte@healthylife.com
📞 Teléfono: +58 123-456-7890

¡Estamos aquí para ti en cada paso de tu viaje hacia una vida más saludable! 💚

🏥 **{site_name} - Tu Salud, Nuestra Prioridad** 🌟

---
Este es un correo automático, por favor no respondas a este mensaje.
Si tienes preguntas, contáctanos a través de nuestros canales de soporte.
"""

def enviar_correo_confirmacion(datos_paciente):
    """
    Envía correo de confirmación a un nuevo paciente después del registro exitoso
    
    Args:
        datos_paciente (dict): Diccionario con los datos del paciente:
            - primer_nombre: Primer nombre
            - segundo_nombre: Segundo nombre (opcional)
            - primer_apellido: Primer apellido
            - segundo_apellido: Segundo apellido (opcional)
            - email: Correo electrónico
            - username: Nombre de usuario
            - password: Contraseña
            - cedula: Cédula de identidad
            - fecha_registro: Fecha de registro (opcional)
    
    Returns:
        bool: True si el correo se envió exitosamente, False en caso contrario
    """
    
    # Verificar que las credenciales estén configuradas
    if not SMTP_USER or not SMTP_PASS:
        print("❌ ERROR: Las credenciales de correo no están configuradas")
        print("Por favor, configura SMTP_USER y SMTP_PASS en email_config.py")
        return False
    
    # Construir nombre completo
    nombre_completo = datos_paciente.get('primer_nombre', '')
    if datos_paciente.get('segundo_nombre'):
        nombre_completo += " " + datos_paciente.get('segundo_nombre')
    nombre_completo += " " + datos_paciente.get('primer_apellido', '')
    if datos_paciente.get('segundo_apellido'):
        nombre_completo += " " + datos_paciente.get('segundo_apellido')
    
    # Preparar datos para la plantilla
    from datetime import datetime
    fecha_registro = datos_paciente.get('fecha_registro', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    template_data = {
        'nombre_completo': nombre_completo.strip(),
        'site_name': SITE_NAME,
        'site_url': SITE_URL,
        'username': datos_paciente.get('username', ''),
        'email': datos_paciente.get('email', ''),
        'password': datos_paciente.get('password', ''),
        'cedula': datos_paciente.get('cedula', ''),
        'fecha_registro': fecha_registro
    }
    
    # Crear mensaje
    msg = MIMEMultipart()
    msg["From"] = SMTP_USER
    msg["To"] = datos_paciente.get('email', '')
    if CC_ADDR:
        msg["Cc"] = CC_ADDR
    if BCC_ADDR:
        msg["Bcc"] = BCC_ADDR
    msg["Subject"] = SUBJECT
    msg.attach(MIMEText(TEMPLATE.format(**template_data), "plain"))
    
    # Enviar correo
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_HOST_IP, SMTP_PORT, timeout=60) as server:
            # Ajusta _host para que la verificación TLS use el nombre del certificado
            if SMTP_HOST_NAME:
                server._host = SMTP_HOST_NAME
            server.starttls(context=context)
            server.login(SMTP_USER, SMTP_PASS)
            
            server.send_message(msg)
            print(f"OK: Correo de confirmacion enviado a {datos_paciente.get('email')}")
            return True
            
    except Exception as e:
        print(f"ERROR: Error al enviar correo a {datos_paciente.get('email')}: {str(e)}")
        return False

def enviar_correo_confirmacion_simple(primer_nombre, segundo_nombre, primer_apellido, segundo_apellido, 
                                     email, username, password, cedula):
    """
    Función simplificada para enviar correo de confirmación con parámetros individuales
    """
    datos_paciente = {
        'primer_nombre': primer_nombre,
        'segundo_nombre': segundo_nombre,
        'primer_apellido': primer_apellido,
        'segundo_apellido': segundo_apellido,
        'email': email,
        'username': username,
        'password': password,
        'cedula': cedula
    }
    
    return enviar_correo_confirmacion(datos_paciente)
