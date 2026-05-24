"""
Servicio de correo electrónico.
Wrapper sobre email_config que añade logging, manejo de errores silencioso
y una interfaz orientada a objetos de negocio (en lugar de dicts crudos).
"""
import logging

logger = logging.getLogger('usuarios.email')


def send_welcome_email(user, datos_paciente, password_plana):
    """
    Envía el correo de bienvenida a un paciente recién registrado.
    El fallo es silencioso (no interrumpe el flujo de registro).

    Args:
        user:            Instancia de UserPaciente.
        datos_paciente:  Instancia de PacienteDatosPersonales (puede ser None).
        password_plana:  Contraseña en texto plano para incluir en el correo.
    """
    from usuarios.email_config import enviar_correo_confirmacion
    try:
        enviar_correo_confirmacion({
            'primer_nombre':    datos_paciente.nombre_1   if datos_paciente else '',
            'segundo_nombre':   datos_paciente.nombre_2   if datos_paciente else '',
            'primer_apellido':  datos_paciente.apellido_1 if datos_paciente else '',
            'segundo_apellido': datos_paciente.apellido_2 if datos_paciente else '',
            'email':    user.email,
            'username': user.username,
            'password': password_plana,
            'cedula':   datos_paciente.cedula if datos_paciente else '',
        })
        logger.info('Correo de bienvenida enviado a %s', user.email)
    except Exception as exc:
        logger.warning('No se pudo enviar correo de bienvenida a %s: %s', user.email, exc)


def send_welcome_doctor(user_doctor, datos_doctor, password_plana):
    """
    Envía el correo de bienvenida a un médico recién registrado.

    Args:
        user_doctor:   Instancia de UserDoctor.
        datos_doctor:  Instancia de Doctor (puede ser None).
        password_plana: Contraseña en texto plano.
    """
    from usuarios.email_config import enviar_correo_doctor
    try:
        enviar_correo_doctor({
            'primer_nombre':    datos_doctor.nombre_1   if datos_doctor else '',
            'segundo_nombre':   datos_doctor.nombre_2   if datos_doctor else '',
            'primer_apellido':  datos_doctor.apellido_1 if datos_doctor else '',
            'segundo_apellido': datos_doctor.apellido_2 if datos_doctor else '',
            'email':    user_doctor.email,
            'username': user_doctor.username,
            'password': password_plana,
        })
        logger.info('Correo de bienvenida médico enviado a %s', user_doctor.email)
    except Exception as exc:
        logger.warning('No se pudo enviar correo al médico %s: %s', user_doctor.email, exc)


def send_welcome_recepcionista(user_recep, datos_recep, password_plana):
    """
    Envía el correo de bienvenida a una recepcionista recién registrada.

    Args:
        user_recep:   Instancia de UserRecepcionista.
        datos_recep:  Instancia de Recepcionista (puede ser None).
        password_plana: Contraseña en texto plano.
    """
    from usuarios.email_config import enviar_correo_recepcionista
    try:
        enviar_correo_recepcionista({
            'primer_nombre':    datos_recep.nombre_1   if datos_recep else '',
            'segundo_nombre':   datos_recep.nombre_2   if datos_recep else '',
            'primer_apellido':  datos_recep.apellido_1 if datos_recep else '',
            'segundo_apellido': datos_recep.apellido_2 if datos_recep else '',
            'email':    user_recep.email,
            'username': user_recep.username,
            'password': password_plana,
        })
        logger.info('Correo de bienvenida recepcionista enviado a %s', user_recep.email)
    except Exception as exc:
        logger.warning('No se pudo enviar correo a recepcionista %s: %s', user_recep.email, exc)
