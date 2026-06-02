"""
Configuración de correo electrónico para Healthy Life
Sistema de envío de correos de confirmación de registro
"""

import os, ssl, smtplib, time
import logging
from pathlib import Path

logger = logging.getLogger('usuarios')
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / '.env')
except ImportError:
    pass

# ── CONFIGURACIÓN SMTP ───────────────────────────────────────────────
# Las credenciales se leen desde el archivo .env en la raíz del proyecto
# Para Gmail: agrega PASSWORD_APP (contraseña de aplicación, no la cuenta)

SMTP_HOST_IP   = os.environ.get('EMAIL_HOST',     'smtp.gmail.com')
SMTP_HOST_NAME = os.environ.get('EMAIL_HOST',     'smtp.gmail.com')
SMTP_PORT      = int(os.environ.get('EMAIL_PORT', '587'))
SMTP_SSL_PORT  = int(os.environ.get('EMAIL_SSL_PORT', '465'))
SMTP_USER      = os.environ.get('EMAIL_HOST_USER',     '')
SMTP_PASS      = os.environ.get('EMAIL_HOST_PASSWORD', '')
SMTP_TIMEOUT   = int(os.environ.get('EMAIL_TIMEOUT', '120'))

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
🏥 Centro Médico asignado: {centro_medico}
📅 Fecha de Registro: {fecha_registro}




🚀 **¿Qué puedes hacer ahora?**

Ya puedes acceder a tu portal de salud personal a través del siguiente enlace:

{site_url}/login/paciente/

Una vez que inicies sesión, podrás:

✅ Agendar citas médicas con nuestros especialistas
✅ Ver tu historial médico completo
✅ Recibir notificaciones de tus citas
✅ Actualizar tu información personal

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

def _conectar_y_enviar(msg, destinatario):
    """
    Helper robusto para enviar correos vía SMTP.
    Intenta SSL directo (puerto 465) primero; si falla usa STARTTLS (puerto 587).
    Incluye reintentos y manejo detallado de errores.
    """
    if not SMTP_USER or not SMTP_PASS:
        logger.error("Credenciales de correo no configuradas")
        return False

    # Estrategias: (host, puerto, usar_ssl_directo)
    estrategias = [
        (SMTP_HOST_IP, SMTP_SSL_PORT, True),   # SSL directo (Gmail = 465)
        (SMTP_HOST_IP, SMTP_PORT, False),      # STARTTLS (Gmail = 587)
    ]

    errores = []
    for host, puerto, usar_ssl in estrategias:
        for intento in range(1, 3):
            try:
                logger.debug(f"Intentando {host}:{puerto} (SSL={usar_ssl}) intento {intento}/2")
                if usar_ssl:
                    context = ssl.create_default_context()
                    server = smtplib.SMTP_SSL(host, puerto, timeout=SMTP_TIMEOUT, context=context)
                    if SMTP_HOST_NAME:
                        server._host = SMTP_HOST_NAME
                    server.login(SMTP_USER, SMTP_PASS)
                    server.send_message(msg)
                    server.quit()
                else:
                    context = ssl.create_default_context()
                    server = smtplib.SMTP(host, puerto, timeout=SMTP_TIMEOUT)
                    if SMTP_HOST_NAME:
                        server._host = SMTP_HOST_NAME
                    server.starttls(context=context)
                    server.login(SMTP_USER, SMTP_PASS)
                    server.send_message(msg)
                    server.quit()

                logger.info(f"Correo enviado a {destinatario}")
                return True

            except Exception as exc:
                err_msg = f"{host}:{puerto} SSL={usar_ssl} intento {intento}: {exc}"
                logger.warning(f"SMTP: {err_msg}")
                errores.append(err_msg)
                time.sleep(1)

    logger.error(f"No se pudo enviar correo a {destinatario}: {errores}")
    return False


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
            - password: Contraseña (ignorado, no se envía)
            - cedula: Cédula de identidad
            - fecha_registro: Fecha de registro (opcional)
    
    Returns:
        bool: True si el correo se envió exitosamente, False en caso contrario
    """
    if not SMTP_USER or not SMTP_PASS:
        logger.error("Credenciales de correo no configuradas. Configura EMAIL_HOST_USER y EMAIL_HOST_PASSWORD en el archivo .env")
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
        'cedula': datos_paciente.get('cedula', ''),
        'centro_medico': datos_paciente.get('centro_medico', 'Nuestro Centro Médico'),
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
    
    return _conectar_y_enviar(msg, datos_paciente.get('email', ''))

TEMPLATE_DOCTOR = """\
Estimado(a) Dr./Dra. {nombre_completo},

¡Bienvenido(a) al equipo médico de {site_name}! 🏥✨

Tu cuenta de médico ha sido creada exitosamente por el área administrativa.

📋 **Datos de tu cuenta:**

👤 Usuario: {username}
📧 Correo Electrónico: {email}

⚠️ **IMPORTANTE:** Por seguridad, te recomendamos cambiar tu contraseña después de tu primer inicio de sesión.

🚀 **Accede a tu portal médico aquí:**

{login_url}

Una vez que inicies sesión, podrás:

✅ Ver y gestionar tus citas asignadas
✅ Confirmar citas pendientes
✅ Consultar tu calendario de atención
✅ Gestionar tus horarios disponibles

📞 **¿Necesitas ayuda?**

Contáctanos a través de los canales de soporte internos de {site_name}.

¡Bienvenido al equipo! 💚

🏥 **{site_name} - Tu Salud, Nuestra Prioridad** 🌟

---
Este es un correo automático, por favor no respondas a este mensaje.
"""

def enviar_correo_doctor(datos_doctor):
    """
    Envía correo de bienvenida a un nuevo médico registrado.

    Args:
        datos_doctor (dict):
            - primer_nombre, segundo_nombre, primer_apellido, segundo_apellido
            - email, username
    Returns:
        bool
    """
    if not SMTP_USER or not SMTP_PASS:
        logger.error("Credenciales de correo no configuradas")
        return False

    nombre_completo = datos_doctor.get('primer_nombre', '')
    if datos_doctor.get('segundo_nombre'):
        nombre_completo += ' ' + datos_doctor['segundo_nombre']
    nombre_completo += ' ' + datos_doctor.get('primer_apellido', '')
    if datos_doctor.get('segundo_apellido'):
        nombre_completo += ' ' + datos_doctor['segundo_apellido']

    from datetime import datetime
    template_data = {
        'nombre_completo': nombre_completo.strip(),
        'site_name':  SITE_NAME,
        'site_url':   SITE_URL,
        'login_url':  f"{SITE_URL}/login/medico/",
        'username':   datos_doctor.get('username', ''),
        'email':      datos_doctor.get('email', ''),
    }

    msg = MIMEMultipart()
    msg["From"]    = SMTP_USER
    msg["To"]      = datos_doctor.get('email', '')
    msg["Subject"] = f"🏥 Bienvenido al equipo médico de {SITE_NAME}"
    if CC_ADDR:
        msg["Cc"] = CC_ADDR
    msg.attach(MIMEText(TEMPLATE_DOCTOR.format(**template_data), "plain"))

    return _conectar_y_enviar(msg, datos_doctor.get('email', ''))


TEMPLATE_RECEPCIONISTA = """\
Estimado(a) {nombre_completo},

¡Bienvenido(a) al equipo de {site_name}! 🏥✨

Tu cuenta de recepcionista ha sido creada exitosamente por el área administrativa.

📋 **Datos de tu cuenta:**

👤 Usuario: {username}
📧 Correo Electrónico: {email}

⚠️ **IMPORTANTE:** Por seguridad, te recomendamos cambiar tu contraseña después de tu primer inicio de sesión.

🚀 **Accede a tu portal de recepcionista aquí:**

{login_url}

Una vez que inicies sesión, podrás:

✅ Gestionar y aprobar citas de pacientes
✅ Consultar el listado de citas activas
✅ Registrar y actualizar información de pacientes
✅ Coordinar con el equipo médico

📞 **¿Necesitas ayuda?**

Contáctanos a través de los canales de soporte internos de {site_name}.

¡Bienvenido(a) al equipo! 💚

🏥 **{site_name} - Tu Salud, Nuestra Prioridad** 🌟

---
Este es un correo automático, por favor no respondas a este mensaje.
"""

def enviar_correo_recepcionista(datos_recepcionista):
    """
    Envía correo de bienvenida a una nueva recepcionista registrada.

    Args:
        datos_recepcionista (dict):
            - primer_nombre, segundo_nombre, primer_apellido, segundo_apellido
            - email, username
    Returns:
        bool
    """
    if not SMTP_USER or not SMTP_PASS:
        logger.error("Credenciales de correo no configuradas")
        return False

    nombre_completo = datos_recepcionista.get('primer_nombre', '')
    if datos_recepcionista.get('segundo_nombre'):
        nombre_completo += ' ' + datos_recepcionista['segundo_nombre']
    nombre_completo += ' ' + datos_recepcionista.get('primer_apellido', '')
    if datos_recepcionista.get('segundo_apellido'):
        nombre_completo += ' ' + datos_recepcionista['segundo_apellido']

    template_data = {
        'nombre_completo': nombre_completo.strip(),
        'site_name':  SITE_NAME,
        'site_url':   SITE_URL,
        'login_url':  f"{SITE_URL}/login/recepcionista/",
        'username':   datos_recepcionista.get('username', ''),
        'email':      datos_recepcionista.get('email', ''),
    }

    msg = MIMEMultipart()
    msg["From"]    = SMTP_USER
    msg["To"]      = datos_recepcionista.get('email', '')
    msg["Subject"] = f"🏥 Bienvenido(a) al equipo de {SITE_NAME}"
    if CC_ADDR:
        msg["Cc"] = CC_ADDR
    msg.attach(MIMEText(TEMPLATE_RECEPCIONISTA.format(**template_data), "plain"))

    return _conectar_y_enviar(msg, datos_recepcionista.get('email', ''))


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


TEMPLATE_SUPERADMIN = """\
Estimado(a) {nombre_completo},

¡Bienvenido(a) a {site_name}! 🏥✨

Tu cuenta de Super Administrador ha sido creada exitosamente. Ahora puedes gestionar tu centro médico y sus sedes.

📋 **Datos de tu cuenta:**

👤 Usuario: {username}
📧 Correo Electrónico: {email}
🏥 Centro Médico: {centro_medico}

🚀 **Accede a tu panel de Super Admin aquí:**

{login_url}

Una vez que inicies sesión, podrás:

✅ Gestionar tu centro médico y sedes
✅ Administrar médicos, recepcionistas y pacientes
✅ Ver reportes y estadísticas
✅ Configurar horarios y servicios

📞 **¿Necesitas ayuda?**

Contáctanos a través de los canales de soporte de {site_name}.

¡Bienvenido(a) al equipo directivo! 💚

🏥 **{site_name} - Tu Salud, Nuestra Prioridad** 🌟

---
Este es un correo automático, por favor no respondas a este mensaje.
"""

def enviar_correo_superadmin(datos_superadmin):
    """
    Envía correo de bienvenida a un nuevo Super Admin registrado.
    Incluye la contraseña para que pueda iniciar sesión.

    Args:
        datos_superadmin (dict):
            - primer_nombre, segundo_nombre, primer_apellido, segundo_apellido
            - email, username, password, centro_medico
    Returns:
        bool
    """
    if not SMTP_USER or not SMTP_PASS:
        logger.error("Credenciales de correo no configuradas")
        return False

    nombre_completo = datos_superadmin.get('primer_nombre', '')
    if datos_superadmin.get('segundo_nombre'):
        nombre_completo += ' ' + datos_superadmin['segundo_nombre']
    nombre_completo += ' ' + datos_superadmin.get('primer_apellido', '')
    if datos_superadmin.get('segundo_apellido'):
        nombre_completo += ' ' + datos_superadmin['segundo_apellido']

    template_data = {
        'nombre_completo': nombre_completo.strip(),
        'site_name':  SITE_NAME,
        'site_url':   SITE_URL,
        'login_url':  f"{SITE_URL}/login/superadmin/",
        'username':   datos_superadmin.get('username', ''),
        'email':      datos_superadmin.get('email', ''),
        'centro_medico': datos_superadmin.get('centro_medico', 'Nuestro Centro Médico'),
    }

    msg = MIMEMultipart()
    msg["From"]    = SMTP_USER
    msg["To"]      = datos_superadmin.get('email', '')
    msg["Subject"] = f"🏥 Bienvenido(a) a {SITE_NAME} - Credenciales de Super Admin"
    if CC_ADDR:
        msg["Cc"] = CC_ADDR
    msg.attach(MIMEText(TEMPLATE_SUPERADMIN.format(**template_data), "plain"))

    return _conectar_y_enviar(msg, datos_superadmin.get('email', ''))


# ── Activación de cuenta ─────────────────────────────────────────────────────

def generar_token_activacion(user_id, correo=None):
    """Genera un token seguro para activación de cuenta."""
    from usuarios.tokens import generar_token_seguro
    return generar_token_seguro(user_id, 'activacion')

TEMPLATE_ACTIVACION = """\
Estimado(a) {nombre_completo},

¡Bienvenido(a) a {site_name}! 🏥✨

Has sido registrado en nuestro sistema como {rol}.

📋 **Datos de tu cuenta:**

👤 Nombre: {nombre_completo}
👤 Nombre de Usuario: {username}

Para establecer tu contraseña y activar tu cuenta, haz clic en el siguiente enlace:

{enlace}

⚠️ Este enlace expira en 24 horas y es de un solo uso.

💡 **Consejos de seguridad:**

• Nunca compartas tu contraseña con nadie
• Cambia tu contraseña regularmente
• Usa contraseñas fuertes con letras, números y símbolos

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

def enviar_correo_activacion(user, rol, enlace):
    """
    Envía correo de activación de cuenta con enlace (SIN contraseña).

    Args:
        user: Instancia del modelo de usuario (debe tener atributos: nombre_1, nombre_2, etc.)
        rol: str, nombre del rol para mostrar en el correo.
        enlace: str, URL de activación.
    Returns:
        bool
    """
    if not SMTP_USER or not SMTP_PASS:
        logger.error("Credenciales de correo no configuradas")
        return False

    nombre_completo = getattr(user, 'nombre_1', '') or ''
    if getattr(user, 'nombre_2', ''):
        nombre_completo += ' ' + user.nombre_2
    nombre_completo += ' ' + (getattr(user, 'apellido_1', '') or '')
    if getattr(user, 'apellido_2', ''):
        nombre_completo += ' ' + user.apellido_2

    template_data = {
        'nombre_completo': nombre_completo.strip(),
        'site_name': SITE_NAME,
        'site_url': SITE_URL,
        'rol': rol,
        'enlace': enlace,
        'username': getattr(user, 'username', ''),
    }

    msg = MIMEMultipart()
    msg["From"] = SMTP_USER
    msg["To"] = getattr(user, 'email', '') or getattr(user, 'correo', '')
    msg["Subject"] = f"🏥 Activa tu cuenta en {SITE_NAME}"
    if CC_ADDR:
        msg["Cc"] = CC_ADDR
    msg.attach(MIMEText(TEMPLATE_ACTIVACION.format(**template_data), "plain"))

    return _conectar_y_enviar(msg, getattr(user, 'email', '') or getattr(user, 'correo', ''))
