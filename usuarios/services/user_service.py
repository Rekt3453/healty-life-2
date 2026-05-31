"""
Servicio de usuarios.
Encapsula lógica de negocio para perfiles, contraseñas, y datos de dashboards,
manteniendo las vistas limpias de lógica ORM y de dominio.
"""
from datetime import date, datetime
from django.db.models import Sum


# ── Perfil paciente ───────────────────────────────────────────────────────────

import re

def update_perfil_paciente(user, paciente, post_data):
    """
    Actualiza los datos personales del paciente.

    Returns:
        (True, mensaje_exito) | (False, mensaje_error)
    """
    from usuarios.models import PacienteDatosPersonales

    _RE_NOMBRE = re.compile(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ\\s]+$')
    _RE_TELEFONO = re.compile(r'^[\\d\\s\\-\\+\\(\\)]+$')
    _SEXOS = {'Masculino', 'Femenino', 'Otro'}

    # ── Validaciones de campos obligatorios ──
    nombre_1 = post_data.get('nombre_1', '').strip()
    if not nombre_1:
        return False, 'El primer nombre es obligatorio.'
    if len(nombre_1) < 2:
        return False, 'El primer nombre debe tener al menos 2 caracteres.'
    if len(nombre_1) > 30:
        return False, 'El primer nombre no puede exceder 30 caracteres.'
    if not _RE_NOMBRE.match(nombre_1):
        return False, 'El primer nombre solo puede contener letras, espacios y tildes.'

    apellido_1 = post_data.get('apellido_1', '').strip()
    if not apellido_1:
        return False, 'El primer apellido es obligatorio.'
    if len(apellido_1) < 2:
        return False, 'El primer apellido debe tener al menos 2 caracteres.'
    if len(apellido_1) > 30:
        return False, 'El primer apellido no puede exceder 30 caracteres.'
    if not _RE_NOMBRE.match(apellido_1):
        return False, 'El primer apellido solo puede contener letras, espacios y tildes.'

    # cedula y tipo_cedula no son editables desde el perfil; se conservan los valores actuales
    cedula = paciente.cedula if paciente else None

    # ── Validaciones de campos opcionales ──
    nombre_2 = post_data.get('nombre_2', '').strip() or None
    if nombre_2:
        if len(nombre_2) < 2:
            return False, 'El segundo nombre debe tener al menos 2 caracteres.'
        if len(nombre_2) > 30:
            return False, 'El segundo nombre no puede exceder 30 caracteres.'
        if not _RE_NOMBRE.match(nombre_2):
            return False, 'El segundo nombre solo puede contener letras, espacios y tildes.'

    apellido_2 = post_data.get('apellido_2', '').strip() or None
    if apellido_2:
        if len(apellido_2) < 2:
            return False, 'El segundo apellido debe tener al menos 2 caracteres.'
        if len(apellido_2) > 30:
            return False, 'El segundo apellido no puede exceder 30 caracteres.'
        if not _RE_NOMBRE.match(apellido_2):
            return False, 'El segundo apellido solo puede contener letras, espacios y tildes.'

    telefono = post_data.get('telefono', '').strip() or None
    if telefono:
        if len(telefono) < 7:
            return False, 'El teléfono debe tener al menos 7 caracteres.'
        if len(telefono) > 20:
            return False, 'El teléfono no puede exceder 20 caracteres.'
        if not _RE_TELEFONO.match(telefono):
            return False, 'El teléfono solo puede contener números, espacios, guiones, paréntesis y +.'

    # tipo_cedula y cedula no son editables desde el perfil
    tipo_cedula = paciente.tipo_cedula if paciente else None

    sexo = post_data.get('sexo', '').strip() or None
    if sexo and sexo not in _SEXOS:
        return False, 'Sexo no válido.'

    # ── Fecha de nacimiento ──
    fn_raw = post_data.get('fecha_nacimiento', '').strip()
    fecha_nac = None
    if fn_raw:
        try:
            fecha_nac = datetime.strptime(fn_raw, '%Y-%m-%d')
        except ValueError:
            return False, 'La fecha de nacimiento no es válida.'
        from datetime import date as _date
        if fecha_nac.date() > _date.today():
            return False, 'La fecha de nacimiento no puede ser futura.'
        # Verificar que sea mayor de edad (>= 18)
        hoy = _date.today()
        edad = hoy.year - fecha_nac.year - ((hoy.month, hoy.day) < (fecha_nac.month, fecha_nac.day))
        if edad < 18:
            return False, 'Debes ser mayor de edad (18+ años) para registrar tu perfil.'

    # ── Email ──
    nuevo_email = post_data.get('email', '').strip()
    if nuevo_email and nuevo_email != user.email:
        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', nuevo_email):
            return False, 'El correo electrónico no es válido.'
        user.email = nuevo_email
        user.save()

    datos = {
        'nombre_1':          nombre_1.upper(),
        'nombre_2':          nombre_2.upper() if nombre_2 else None,
        'apellido_1':        apellido_1.upper(),
        'apellido_2':        apellido_2.upper() if apellido_2 else None,
        'telefono':          telefono,
        'sexo':              sexo,
        'cedula':            cedula,
        'tipo_cedula':       tipo_cedula,
        'fecha_nacimiento':  fecha_nac,
        'id_sede':           user.id_sede,
        'id_user_paciente':  user,
        'status':            True,
    }

    try:
        if paciente:
            for k, v in datos.items():
                setattr(paciente, k, v)
            paciente.save()
            return True, 'Perfil actualizado correctamente.'
        else:
            PacienteDatosPersonales.objects.create(**datos)
            return True, 'Perfil creado correctamente.'
    except Exception as e:
        return False, f'Error al actualizar perfil: {e}'


def change_password(user, pwd_actual, pwd_nuevo, pwd_confirm):
    """
    Cambia la contraseña del usuario tras validar la actual.

    Returns:
        (True, mensaje_exito) | (False, mensaje_error)
    """
    if not user.check_password(pwd_actual):
        return False, 'La contraseña actual es incorrecta.'
    if pwd_nuevo != pwd_confirm:
        return False, 'Las contraseñas nuevas no coinciden.'
    if len(pwd_nuevo) < 6:
        return False, 'Mínimo 6 caracteres.'
    try:
        user.set_password(pwd_nuevo)
        user.save()
        return True, 'Contraseña actualizada.'
    except Exception as e:
        return False, f'Error: {e}'


def update_direccion_paciente(paciente, post_data):
    """
    Crea o actualiza la dirección del paciente.

    Returns:
        (True, mensaje_exito) | (False, mensaje_error)
    """
    from usuarios.models import DireccionPaciente

    id_estado = post_data.get('id_estado') or None
    id_municipio = post_data.get('id_municipio') or None
    id_parroquia = post_data.get('id_parroquia') or None
    direccion = post_data.get('direccion', '').strip()
    referencia = post_data.get('referencia', '').strip() or None

    if not id_estado:
        return False, 'Debe seleccionar un estado.'
    if not id_municipio:
        return False, 'Debe seleccionar un municipio.'
    if not id_parroquia:
        return False, 'Debe seleccionar una parroquia.'
    if not direccion:
        return False, 'La dirección es obligatoria.'
    if len(direccion) < 5:
        return False, 'La dirección debe tener al menos 5 caracteres.'
    if len(direccion) > 255:
        return False, 'La dirección no puede exceder 255 caracteres.'
    if referencia and len(referencia) > 255:
        return False, 'La referencia no puede exceder 255 caracteres.'

    dir_data = {
        'id_estado_id':    id_estado,
        'id_municipio_id': id_municipio,
        'id_parroquia_id': id_parroquia,
        'id_ciudad_id':    post_data.get('id_ciudad') or None,
        'direccion':       direccion,
        'referencia':      referencia,
    }
    try:
        if paciente and paciente.id_direccion_paciente_id:
            DireccionPaciente.objects.filter(pk=paciente.id_direccion_paciente_id).update(**dir_data)
        elif paciente:
            nueva_dir = DireccionPaciente(**dir_data)
            nueva_dir.save()
            paciente.id_direccion_paciente = nueva_dir
            paciente.save()
        return True, 'Dirección actualizada.'
    except Exception as e:
        return False, f'Error al actualizar dirección: {e}'


# ── Contexto de dashboards ────────────────────────────────────────────────────

def get_paciente_dashboard_context(datos_paciente):
    """
    Devuelve el contexto de estadísticas de citas para el dashboard del paciente.
    """
    from citas.models import Cita, PagoCita

    citas = Cita.objects.none()
    pagos = PagoCita.objects.none()
    if datos_paciente:
        citas = Cita.objects.filter(id_paciente=datos_paciente).order_by('-fecha_emision')
        pagos = PagoCita.objects.filter(id_paciente=datos_paciente).order_by('-fecha_consulta')

    try:
        citas_activas    = citas.filter(status=True).count()
        citas_canceladas = citas.filter(status=False).count()
        total_citas      = citas.count()
    except Exception:
        citas_activas = citas_canceladas = total_citas = 0

    proxima_cita = None
    try:
        proxima_cita = citas.filter(
            status=True, fecha_consulta__gte=datetime.now()
        ).order_by('fecha_consulta').first()
    except Exception:
        pass

    pagos_lista = []
    total_pagado = pendiente_pago = 0
    try:
        pagos_lista    = list(pagos[:20])
        total_pagado   = sum((p.monto_pagar or 0) for p in pagos_lista if p.status)
        pendiente_pago = sum((p.monto_pagar or 0) for p in pagos_lista if not p.status)
    except Exception:
        pass

    return {
        'citas':             citas,
        'proxima_cita':      proxima_cita,
        'pagos_lista':       pagos_lista,
        'citas_activas':     citas_activas,
        'citas_canceladas':  citas_canceladas,
        'total_citas':       total_citas,
        'total_pagado':      total_pagado,
        'pendiente_pago':    pendiente_pago,
    }


def get_medico_dashboard_context(datos_medico):
    """
    Devuelve el contexto de citas para el dashboard del médico.
    """
    from citas.models import Cita

    if not datos_medico:
        return {'citas_hoy': Cita.objects.none(), 'citas_pendientes': Cita.objects.none(), 'total_citas': 0}

    try:
        hoy              = date.today()
        citas_hoy        = Cita.objects.filter(id_doctor=datos_medico, fecha_consulta__date=hoy, status=True)
        citas_pendientes = Cita.objects.filter(id_doctor=datos_medico, status=True).select_related('id_paciente').order_by('fecha_consulta')[:5]
        total_citas      = Cita.objects.filter(id_doctor=datos_medico).count()
    except Exception:
        citas_hoy = citas_pendientes = Cita.objects.none()
        total_citas = 0

    return {
        'citas_hoy':        citas_hoy,
        'citas_pendientes': citas_pendientes,
        'total_citas':      total_citas,
    }


def get_recepcionista_dashboard_context():
    """
    Devuelve el contexto de estadísticas para el dashboard de recepcionista.
    """
    from citas.models import Cita
    from usuarios.models import UserPaciente

    try:
        hoy              = date.today()
        citas_pendientes = Cita.objects.filter(status=True).count()
        citas_hoy        = Cita.objects.filter(fecha_consulta__date=hoy).count()
        citas_recientes  = Cita.objects.select_related('id_paciente', 'id_doctor').order_by('-fecha_emision')[:10]
    except Exception:
        citas_pendientes = citas_hoy = 0
        citas_recientes = []

    try:
        total_pacientes = UserPaciente.objects.filter(status=True).count()
    except Exception:
        total_pacientes = 0

    return {
        'citas_pendientes': citas_pendientes,
        'citas_hoy':        citas_hoy,
        'citas_recientes':  citas_recientes,
        'total_pacientes':  total_pacientes,
    }


def get_gerente_dashboard_context():
    """
    Devuelve el contexto de estadísticas para el dashboard del gerente.
    """
    from citas.models import Cita
    from usuarios.models import UserPaciente, UserDoctor, UserRecepcionista

    try:
        total_citas = Cita.objects.count()
    except Exception:
        total_citas = 0

    try:
        total_pacientes      = UserPaciente.objects.count()
        total_medicos        = UserDoctor.objects.count()
        total_recepcionistas = UserRecepcionista.objects.count()
    except Exception:
        total_pacientes = total_medicos = total_recepcionistas = 0

    return {
        'total_citas':         total_citas,
        'total_pacientes':     total_pacientes,
        'total_medicos':       total_medicos,
        'total_recepcionistas': total_recepcionistas,
    }


# ── Utilidades ─────────────────────────────────────────────────────────────────

def calcular_edad(fecha_nacimiento):
    """Calcula la edad en años a partir de una fecha de nacimiento (date o datetime)."""
    if not fecha_nacimiento:
        return None
    hoy = date.today()
    fn = fecha_nacimiento.date() if hasattr(fecha_nacimiento, 'date') else fecha_nacimiento
    return hoy.year - fn.year - ((hoy.month, hoy.day) < (fn.month, fn.day))
