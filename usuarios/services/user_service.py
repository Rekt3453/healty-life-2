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


def update_contacto_paciente(user, paciente, post_data):
    """
    Actualiza solo los datos de contacto del paciente (email y teléfono).

    Returns:
        (True, mensaje_exito) | (False, mensaje_error)
    """
    _RE_TELEFONO = re.compile(r'^[\d\s\-\+\(\)]+$')

    telefono = post_data.get('telefono', '').strip() or None
    if telefono:
        if len(telefono) < 7:
            return False, 'El teléfono debe tener al menos 7 caracteres.'
        if len(telefono) > 20:
            return False, 'El teléfono no puede exceder 20 caracteres.'
        if not _RE_TELEFONO.match(telefono):
            return False, 'El teléfono solo puede contener números, espacios, guiones, paréntesis y +.'

    nuevo_email = post_data.get('email', '').strip()
    if nuevo_email and nuevo_email != user.email:
        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', nuevo_email):
            return False, 'El correo electrónico no es válido.'
        user.email = nuevo_email
        user.save()

    if not paciente:
        return False, 'No se encontraron datos personales del paciente.'

    try:
        paciente.telefono = telefono
        paciente.save()
        return True, 'Información de contacto actualizada correctamente.'
    except Exception as e:
        return False, f'Error al actualizar contacto: {e}'


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
        citas_pendientes = Cita.objects.filter(
            id_doctor=datos_medico,
            fecha_consulta__date__gte=hoy,
            status=True,
            estado__in=[
                Cita.ESTADO_CONFIRMADA,
                Cita.ESTADO_EN_CONSULTA,
                Cita.ESTADO_APROBADA,
                Cita.ESTADO_PAGADA_ADELANTO,
                Cita.ESTADO_PAGO_PENDIENTE,
            ]
        ).select_related('id_paciente').order_by('fecha_consulta')[:5]
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
    from usuarios.models import UserPaciente, PacienteDatosPersonales, Doctor

    hoy = date.today()

    try:
        citas_pendientes = Cita.objects.filter(
            estado__in=[Cita.ESTADO_SOLICITADA, Cita.ESTADO_PAGO_PENDIENTE]
        ).count()
        citas_hoy        = Cita.objects.filter(fecha_consulta__date=hoy).count()
        citas_en_consulta = Cita.objects.filter(fecha_consulta__date=hoy, estado=Cita.ESTADO_EN_CONSULTA).count()
        citas_recientes  = Cita.objects.select_related('id_paciente', 'id_doctor').order_by('-fecha_emision')[:10]
    except Exception:
        citas_pendientes = citas_hoy = citas_en_consulta = 0
        citas_recientes = []

    try:
        total_pacientes = UserPaciente.objects.filter(status=True).count()
    except Exception:
        total_pacientes = 0

    try:
        citas_hoy_list = Cita.objects.filter(
            fecha_consulta__date=hoy
        ).select_related(
            'id_paciente', 'id_doctor', 'id_especialidades', 'id_consultorio'
        ).order_by('fecha_consulta')
    except Exception:
        citas_hoy_list = []

    try:
        citas_pendientes_list = Cita.objects.filter(
            estado=Cita.ESTADO_SOLICITADA
        ).select_related(
            'id_paciente', 'id_doctor', 'id_especialidades', 'id_consultorio'
        ).order_by('fecha_consulta')[:20]
    except Exception:
        citas_pendientes_list = []

    try:
        pacientes_nuevos_hoy = PacienteDatosPersonales.objects.filter(
            fecha_registro__date=hoy
        ).count()
    except Exception:
        pacientes_nuevos_hoy = 0

    try:
        medicos_activos = Doctor.objects.filter(status=True).count()
    except Exception:
        medicos_activos = 0

    try:
        proximas_citas = Cita.objects.filter(
            fecha_consulta__gte=datetime.now(),
            estado__in=[
                Cita.ESTADO_CONFIRMADA,
                Cita.ESTADO_APROBADA,
                Cita.ESTADO_PAGO_PENDIENTE,
                Cita.ESTADO_PAGADA_ADELANTO,
                Cita.ESTADO_EN_CONSULTA,
            ]
        ).select_related(
            'id_paciente', 'id_doctor', 'id_especialidades'
        ).order_by('fecha_consulta')[:3]
    except Exception:
        proximas_citas = []

    return {
        'citas_pendientes':      citas_pendientes,
        'citas_hoy':             citas_hoy,
        'citas_en_consulta':     citas_en_consulta,
        'citas_recientes':       citas_recientes,
        'total_pacientes':       total_pacientes,
        'citas_hoy_list':        citas_hoy_list,
        'citas_pendientes_list': citas_pendientes_list,
        'pacientes_nuevos_hoy':  pacientes_nuevos_hoy,
        'medicos_activos':       medicos_activos,
        'proximas_citas':      proximas_citas,
    }


def get_gerente_dashboard_context():
    """
    Devuelve el contexto de estadísticas reales para el dashboard del gerente.
    """
    from datetime import date, timedelta
    from django.db.models import Sum, Count, Q
    from citas.models import Cita, PagoCita
    from usuarios.models import UserPaciente, UserDoctor, UserRecepcionista

    hoy = date.today()
    inicio_mes = hoy.replace(day=1)
    # mes anterior
    if hoy.month == 1:
        inicio_mes_ant = hoy.replace(year=hoy.year - 1, month=12, day=1)
        fin_mes_ant = hoy.replace(year=hoy.year - 1, month=12, day=31)
    else:
        inicio_mes_ant = hoy.replace(month=hoy.month - 1, day=1)
        fin_mes_ant = (inicio_mes - timedelta(days=1))

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

    # --- KPIs mensuales ---
    try:
        citas_mes = Cita.objects.filter(
            fecha_consulta__date__gte=inicio_mes
        ).count()
    except Exception:
        citas_mes = 0

    try:
        citas_mes_anterior = Cita.objects.filter(
            fecha_consulta__date__gte=inicio_mes_ant,
            fecha_consulta__date__lte=fin_mes_ant
        ).count()
    except Exception:
        citas_mes_anterior = 0

    try:
        pacientes_mes = UserPaciente.objects.filter(
            date_joined__date__gte=inicio_mes
        ).count()
    except Exception:
        pacientes_mes = 0

    try:
        pacientes_mes_anterior = UserPaciente.objects.filter(
            date_joined__date__gte=inicio_mes_ant,
            date_joined__date__lte=fin_mes_ant
        ).count()
    except Exception:
        pacientes_mes_anterior = 0

    try:
        # Ingresos de pagos de citas
        ingresos_pagos_citas = PagoCita.objects.filter(
            fecha_pago__date__gte=inicio_mes,
            estado_pago=Cita.ESTADO_PAGADA_ADELANTO
        ).aggregate(total=Sum('monto_pagar'))['total'] or 0

        # Ingresos de servicios realizados en consultas médicas
        from citas.models import ConsultaMedica, ConsultaServicio
        ingresos_servicios = ConsultaServicio.objects.filter(
            id_consulta__fecha_inicio__date__gte=inicio_mes
        ).aggregate(total=Sum('precio_cobrado'))['total'] or 0

        # $5 por cada cita aceptada (APROBADA, CONFIRMADA, EN_CONSULTA, ATENDIDA, PAGADA_ADELANTO)
        estados_aceptados = [
            Cita.ESTADO_APROBADA,
            Cita.ESTADO_CONFIRMADA,
            Cita.ESTADO_EN_CONSULTA,
            Cita.ESTADO_ATENDIDA,
            Cita.ESTADO_PAGADA_ADELANTO
        ]
        citas_aceptadas_count = Cita.objects.filter(
            fecha_consulta__date__gte=inicio_mes,
            estado__in=estados_aceptados
        ).count()
        ingresos_tarifa_citas = citas_aceptadas_count * 5

        # Total de ingresos
        ingresos_mes = float(ingresos_pagos_citas or 0) + float(ingresos_servicios or 0) + float(ingresos_tarifa_citas)
    except Exception:
        ingresos_mes = 0

    try:
        # Ingresos de pagos de citas mes anterior
        ingresos_pagos_citas_ant = PagoCita.objects.filter(
            fecha_pago__date__gte=inicio_mes_ant,
            fecha_pago__date__lte=fin_mes_ant,
            estado_pago=Cita.ESTADO_PAGADA_ADELANTO
        ).aggregate(total=Sum('monto_pagar'))['total'] or 0

        # Ingresos de servicios mes anterior
        ingresos_servicios_ant = ConsultaServicio.objects.filter(
            id_consulta__fecha_inicio__date__gte=inicio_mes_ant,
            id_consulta__fecha_inicio__date__lte=fin_mes_ant
        ).aggregate(total=Sum('precio_cobrado'))['total'] or 0

        # $5 por cada cita aceptada mes anterior
        citas_aceptadas_count_ant = Cita.objects.filter(
            fecha_consulta__date__gte=inicio_mes_ant,
            fecha_consulta__date__lte=fin_mes_ant,
            estado__in=estados_aceptados
        ).count()
        ingresos_tarifa_citas_ant = citas_aceptadas_count_ant * 5

        # Total de ingresos mes anterior
        ingresos_mes_anterior = float(ingresos_pagos_citas_ant or 0) + float(ingresos_servicios_ant or 0) + float(ingresos_tarifa_citas_ant)
    except Exception:
        ingresos_mes_anterior = 0

    # --- Citas por estado ---
    estados_interes = {
        'pendientes': [Cita.ESTADO_SOLICITADA, Cita.ESTADO_PAGO_PENDIENTE],
        'aprobadas': [Cita.ESTADO_APROBADA, Cita.ESTADO_CONFIRMADA, Cita.ESTADO_PAGADA_ADELANTO, Cita.ESTADO_EN_CONSULTA],
        'canceladas': [Cita.ESTADO_CANCELADA, Cita.ESTADO_RECHAZADA, Cita.ESTADO_NO_ASISTIO],
        'completadas': [Cita.ESTADO_ATENDIDA],
    }
    citas_por_estado = {}
    for nombre, lista_estados in estados_interes.items():
        try:
            citas_por_estado[nombre] = Cita.objects.filter(estado__in=lista_estados).count()
        except Exception:
            citas_por_estado[nombre] = 0

    total_estados = sum(citas_por_estado.values())
    porcentajes = {}
    for k in citas_por_estado:
        porcentajes[k] = round((citas_por_estado[k] / total_estados * 100), 1) if total_estados > 0 else 0

    # --- Citas por especialidad (para gráfico) ---
    citas_especialidad_labels = []
    citas_especialidad_data = []
    try:
        from citas.models import Especialidad
        qs = Cita.objects.exclude(id_especialidades__isnull=True).values(
            'id_especialidades__tipo_especialidad'
        ).annotate(cnt=Count('id_citas')).order_by('-cnt')[:6]
        for item in qs:
            citas_especialidad_labels.append(item['id_especialidades__tipo_especialidad'] or 'Sin nombre')
            citas_especialidad_data.append(item['cnt'])
    except Exception:
        pass

    # --- Ingresos últimos 6 meses (para gráfico) ---
    ingresos_labels = []
    ingresos_data = []
    try:
        # Estados aceptados para la tarifa de $5 por cita
        estados_aceptados = [
            Cita.ESTADO_APROBADA,
            Cita.ESTADO_CONFIRMADA,
            Cita.ESTADO_EN_CONSULTA,
            Cita.ESTADO_ATENDIDA,
            Cita.ESTADO_PAGADA_ADELANTO
        ]
        for i in range(5, -1, -1):
            mes_ref = (hoy.replace(day=1) - timedelta(days=1))
            if i > 0:
                for _ in range(i):
                    mes_ref = mes_ref.replace(day=1) - timedelta(days=1)
            mes_ref = mes_ref.replace(day=1)
            fin_mes = (mes_ref + timedelta(days=32)).replace(day=1) - timedelta(days=1)

            # Ingresos de pagos de citas
            ingresos_pagos_citas = PagoCita.objects.filter(
                fecha_pago__date__gte=mes_ref,
                fecha_pago__date__lte=fin_mes,
                estado_pago=Cita.ESTADO_PAGADA_ADELANTO
            ).aggregate(total=Sum('monto_pagar'))['total'] or 0

            # Ingresos de servicios realizados en consultas médicas
            ingresos_servicios = ConsultaServicio.objects.filter(
                id_consulta__fecha_inicio__date__gte=mes_ref,
                id_consulta__fecha_inicio__date__lte=fin_mes
            ).aggregate(total=Sum('precio_cobrado'))['total'] or 0

            # $5 por cada cita aceptada
            citas_aceptadas_count = Cita.objects.filter(
                fecha_consulta__date__gte=mes_ref,
                fecha_consulta__date__lte=fin_mes,
                estado__in=estados_aceptados
            ).count()
            ingresos_tarifa_citas = citas_aceptadas_count * 5

            # Total de ingresos del mes
            total = float(ingresos_pagos_citas or 0) + float(ingresos_servicios or 0) + float(ingresos_tarifa_citas)

            meses_nombres = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']
            ingresos_labels.append(meses_nombres[mes_ref.month - 1])
            ingresos_data.append(total)
    except Exception:
        pass

    # --- Actividades recientes (últimas 10 citas) ---
    actividades = []
    try:
        recientes = Cita.objects.select_related(
            'id_paciente', 'id_doctor', 'id_especialidades'
        ).order_by('-fecha_emision')[:10]
        for c in recientes:
            pac = getattr(c.id_paciente, 'nombre_completo', str(c.id_paciente)) if c.id_paciente else 'Desconocido'
            doc = getattr(c.id_doctor, 'nombre_completo', str(c.id_doctor)) if c.id_doctor else 'Sin médico'
            esp = getattr(c.id_especialidades, 'nombre', '') if c.id_especialidades else ''
            fecha_str = c.fecha_emision.strftime('%d/%m/%Y %H:%M') if c.fecha_emision else ''
            actividades.append({
                'fecha': fecha_str,
                'usuario': pac,
                'accion': c.get_estado_display() or 'Cita',
                'detalle': f'{esp} - {doc}' if esp else doc,
                'estado': c.estado or '',
            })
    except Exception:
        pass

    def var_pct(actual, anterior):
        if anterior and anterior > 0:
            return round(((actual - anterior) / anterior) * 100, 1)
        return 0

    # --- Comisiones pendientes a doctores ---
    honorarios_pendientes = []
    total_honorarios_pendientes = 0
    try:
        from citas.models import HonorarioMedico
        honorarios_pendientes = HonorarioMedico.objects.filter(
            estado_pago=HonorarioMedico.ESTADO_PENDIENTE,
            status=True,
        ).select_related('id_doctor', 'id_cita').order_by('-fecha_atencion')[:50]
        total_honorarios_pendientes = HonorarioMedico.objects.filter(
            estado_pago=HonorarioMedico.ESTADO_PENDIENTE,
            status=True,
        ).aggregate(total=Sum('monto_honorario'))['total'] or 0
    except Exception:
        pass

    # --- Pagos a recepcionistas (mes actual) ---
    pagos_recepcionistas_mes = 0
    cantidad_pagos_recepcionistas = 0
    try:
        from citas.models import MovimientoCaja
        from django.db.models import Q
        recepcionista_qs = MovimientoCaja.objects.filter(
            fecha_movimiento__date__gte=inicio_mes,
            fecha_movimiento__date__lte=hoy,
            tipo_movimiento=MovimientoCaja.TIPO_EGRESO,
            status=True,
        ).filter(
            Q(concepto__icontains='recepcionista') |
            Q(concepto__icontains='recepcion') |
            Q(concepto__icontains='nomina') |
            Q(concepto__icontains='salario')
        )
        pagos_recepcionistas_mes = recepcionista_qs.aggregate(total=Sum('monto'))['total'] or 0
        cantidad_pagos_recepcionistas = recepcionista_qs.count()
    except Exception:
        pass

    promedio_pago_recepcionista = round(
        pagos_recepcionistas_mes / cantidad_pagos_recepcionistas, 2
    ) if cantidad_pagos_recepcionistas > 0 else 0

    return {
        'total_citas':          total_citas,
        'total_pacientes':      total_pacientes,
        'total_medicos':        total_medicos,
        'total_recepcionistas': total_recepcionistas,
        'citas_mes':            citas_mes,
        'citas_mes_anterior':   citas_mes_anterior,
        'citas_mes_var':        var_pct(citas_mes, citas_mes_anterior),
        'pacientes_mes':        pacientes_mes,
        'pacientes_mes_anterior': pacientes_mes_anterior,
        'pacientes_mes_var':    var_pct(pacientes_mes, pacientes_mes_anterior),
        'ingresos_mes':         float(ingresos_mes),
        'ingresos_mes_anterior': float(ingresos_mes_anterior),
        'ingresos_mes_var':     var_pct(float(ingresos_mes), float(ingresos_mes_anterior)),
        'citas_por_estado':     citas_por_estado,
        'porcentajes':          porcentajes,
        'citas_especialidad_labels': citas_especialidad_labels,
        'citas_especialidad_data': citas_especialidad_data,
        'ingresos_labels':      ingresos_labels,
        'ingresos_data':        ingresos_data,
        'actividades':          actividades,
        'honorarios_pendientes': honorarios_pendientes,
        'total_honorarios_pendientes': float(total_honorarios_pendientes),
        'pagos_recepcionistas_mes': float(pagos_recepcionistas_mes),
        'cantidad_pagos_recepcionistas': cantidad_pagos_recepcionistas,
        'promedio_pago_recepcionista': float(promedio_pago_recepcionista),
    }


# ── Utilidades ─────────────────────────────────────────────────────────────────

def calcular_edad(fecha_nacimiento):
    """Calcula la edad en años a partir de una fecha de nacimiento (date o datetime)."""
    if not fecha_nacimiento:
        return None
    hoy = date.today()
    fn = fecha_nacimiento.date() if hasattr(fecha_nacimiento, 'date') else fecha_nacimiento
    return hoy.year - fn.year - ((hoy.month, hoy.day) < (fn.month, fn.day))
