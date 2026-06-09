import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_GET
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from usuarios.decorators import rol_requerido
from usuarios.models import PacienteDatosPersonales, Doctor, PacienteEspecial
from usuarios.audit_services import registrar_evento
from usuarios.authentication import CustomAuthBackend
from .models import (
    Cita, PagoCita, Sede, Especialidad, Horario,
    ServicioEspecialidad, EspecialidadDoctor, Consultorio, ConsultaMedica, Factura,
    MovimientoCaja, HonorarioMedico, ServicioMedico, ConsultaServicio, CitaServicioSolicitado,
    Recipe, HistorialMedicoPaciente,
)
from .services import CitaService, FacturacionService
from .reportes import ReportesService
from .forms import ConsultaMedicaForm, RegistrarAdelantoForm

logger = logging.getLogger('citas')

@login_required(login_url='/login/paciente/')
@rol_requerido('paciente')
def solicitar_cita(request):
    """Flujo: Paciente Objetivo → Sede → Especialidad → Doctor → Fecha/Hora → Servicio → Motivo.

    Si el tutor selecciona un paciente especial (menor), se valida en el servidor
    que la especialidad elegida tenga clasificación 'Pediatría' o 'General'.
    El motivo lleva un prefijo automático con el nombre del menor.
    """
    user = request.user
    paciente = PacienteDatosPersonales.objects.filter(id_user_paciente=user).first()

    menores = []
    if paciente:
        menores = list(
            PacienteEspecial.objects.filter(
                id_paciente_tutor=paciente, status=True
            ).order_by('nombre_1', 'apellido_1')
        )

    if request.method == 'POST':
        sede_id = request.POST.get('sede')
        especialidad_id = request.POST.get('especialidad')
        doctor_id = request.POST.get('doctor') or request.POST.get('medico')
        servicio_id = request.POST.get('servicio') or None
        fecha = request.POST.get('fecha')
        hora = request.POST.get('hora') or request.POST.get('hora_solicitada')
        motivo_raw = request.POST.get('motivo', '').strip()
        paciente_objetivo = request.POST.get('paciente_objetivo', 'self')
        servicios_seleccionados = request.POST.getlist('servicios_medico')

        if not all([sede_id, especialidad_id, doctor_id, fecha, hora, motivo_raw]):
            messages.error(request, "Todos los campos obligatorios deben completarse.")
        else:
            # Guardar datos en sesión para el checkout de reserva
            request.session['reserva_cita'] = {
                'sede_id': sede_id,
                'especialidad_id': especialidad_id,
                'doctor_id': doctor_id,
                'servicio_id': servicio_id,
                'fecha': fecha,
                'hora': hora,
                'motivo_raw': motivo_raw,
                'paciente_objetivo': paciente_objetivo,
                'servicios_seleccionados': servicios_seleccionados,
            }
            return redirect('checkout_reserva')

    from datetime import timedelta
    sedes = Sede.objects.filter(status__in=[True, None]).order_by('nombre_sede')
    return render(request, 'citas/solicitar_cita.html', {
        'sedes': sedes,
        'hoy': date.today().isoformat(),
        'manana': (date.today() + timedelta(days=1)).isoformat(),
        'paciente': paciente,
        'menores': menores,
        'especialidad_preseleccionada': request.GET.get('especialidad', ''),
    })


@login_required(login_url='/login/paciente/')
@rol_requerido('paciente')
def checkout_reserva(request):
    """Checkout de pago por reserva: muestra datos bancarios y captura
    cédula, teléfono, banco emisor y referencia de transferencia."""
    user = request.user
    reserva = request.session.get('reserva_cita')
    if not reserva:
        messages.warning(request, "No hay datos de reserva pendientes.")
        return redirect('solicitar_cita')

    paciente = PacienteDatosPersonales.objects.filter(id_user_paciente=user).first()

    DATOS_BANCARIOS = {
        'banco': 'Banco Nacional de Crédito',
        'cuenta': '0191-XXXX-XXXX-XXXX',
        'titular': 'Healthy Life C.A.',
        'rif': 'J-12345678-9',
        'tipo': 'Cuenta Corriente',
    }

    MONTO_RESERVA = Decimal('5.00')

    if request.method == 'POST':
        monto_pago = request.POST.get('monto_pago', '').strip()
        cedula = request.POST.get('cedula', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        banco_emisor = request.POST.get('banco_emisor', '').strip()
        referencia = request.POST.get('referencia', '').strip()

        import re
        errores = []
        if not all([monto_pago, cedula, telefono, banco_emisor, referencia]):
            errores.append("Todos los campos de datos bancarios son obligatorios.")
        if not re.fullmatch(r'^\d{1,3},\d{2}$', monto_pago):
            errores.append("El monto del pago debe tener formato 0,00 (ej: 5,00).")
        if not re.fullmatch(r'^\d{6,9}$', cedula):
            errores.append("La cédula debe contener solo entre 6 y 9 dígitos numéricos.")
        if not re.fullmatch(r'^\d{10,11}$', telefono):
            errores.append("El teléfono debe contener solo entre 10 y 11 dígitos numéricos.")
        if len(banco_emisor) < 2 or len(banco_emisor) > 30:
            errores.append("El banco emisor debe tener entre 2 y 30 caracteres.")
        if not re.fullmatch(r'^\d{6}$', referencia):
            errores.append("La referencia debe tener exactamente 6 dígitos numéricos.")

        if errores:
            for e in errores:
                messages.error(request, e)
        else:
            try:
                cita, mensaje = CitaService.crear_cita_con_reserva(
                    user,
                    sede_id=reserva['sede_id'],
                    especialidad_id=reserva['especialidad_id'],
                    doctor_id=reserva['doctor_id'],
                    servicio_id=reserva.get('servicio_id'),
                    fecha=reserva['fecha'],
                    hora=reserva['hora'],
                    motivo_raw=reserva['motivo_raw'],
                    paciente_objetivo=reserva.get('paciente_objetivo', 'self'),
                    cedula=cedula,
                    telefono=telefono,
                    banco_emisor=banco_emisor,
                    referencia=referencia,
                    monto_pago=monto_pago,
                    servicios_seleccionados=reserva.get('servicios_seleccionados', []),
                )
                del request.session['reserva_cita']
                request.session.modified = True
                registrar_evento(
                    user=request.user,
                    role='paciente',
                    action='CREATE',
                    model_affected='Cita',
                    object_id=cita.pk,
                    details={'cita_id': cita.pk, 'estado': cita.estado},
                    request=request,
                )
                messages.success(request, mensaje)
                return redirect('dashboard_paciente')
            except PermissionError as e:
                messages.error(request, str(e))
            except ValueError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f"Error al registrar la cita: {e}")

    # Recuperar nombres para mostrar en el resumen
    from usuarios.models import Sede, Doctor
    from citas.models import Especialidad, ServicioEspecialidad
    sede = Sede.objects.filter(id_sede=reserva['sede_id']).first()
    doctor = Doctor.objects.filter(id_doctor=reserva['doctor_id']).first()
    especialidad = Especialidad.objects.filter(id_especialidad=reserva['especialidad_id']).first()
    servicio = ServicioEspecialidad.objects.filter(
        id_servicios_especialidad=reserva.get('servicio_id')
    ).first() if reserva.get('servicio_id') else None

    return render(request, 'citas/checkout_reserva.html', {
        'datos_bancarios': DATOS_BANCARIOS,
        'reserva': reserva,
        'sede': sede,
        'doctor': doctor,
        'especialidad': especialidad,
        'servicio': servicio,
        'paciente': paciente,
        'monto_reserva': MONTO_RESERVA,
    })


@login_required(login_url='/login/medico/')
@rol_requerido('medico')
def citas_pendientes_medico(request):
    """Todas las citas del medico autenticado con paginacion, ordenamiento, busqueda y filtros."""
    try:
        citas_pendientes, citas_asignadas, datos_medico = CitaService.listar_citas_medico(request.user)
    except PermissionError as e:
        messages.error(request, str(e))
        return redirect('home')

    todas_citas = []
    citas_completadas = []
    busqueda = request.GET.get('q', '').strip()
    filtro = request.GET.get('filtro', 'todas')
    orden = request.GET.get('orden', 'fecha_desc')

    if datos_medico:
        qs = Cita.objects.filter(
            id_doctor=datos_medico
        ).select_related('id_paciente', 'id_especialidades')

        if busqueda:
            try:
                qs = qs.filter(id_citas=int(busqueda))
            except ValueError:
                qs = qs.none()

        # Filtro por estado
        por_atender = [
            Cita.ESTADO_SOLICITADA, Cita.ESTADO_APROBADA,
            Cita.ESTADO_PAGO_PENDIENTE, Cita.ESTADO_PAGADA_ADELANTO,
            Cita.ESTADO_CONFIRMADA, Cita.ESTADO_EN_CONSULTA,
        ]
        sin_atender = [Cita.ESTADO_CANCELADA, Cita.ESTADO_RECHAZADA, Cita.ESTADO_NO_ASISTIO]

        if filtro == 'por_atender':
            qs = qs.filter(estado__in=por_atender)
        elif filtro == 'sin_atender':
            qs = qs.filter(estado__in=sin_atender)

        # Ordenamiento
        if orden == 'fecha_asc':
            qs = qs.order_by('fecha_consulta')
        elif orden == 'fecha_desc':
            qs = qs.order_by('-fecha_consulta')
        elif orden == 'estado_asc':
            qs = qs.order_by('estado')
        elif orden == 'estado_desc':
            qs = qs.order_by('-estado')
        else:
            qs = qs.order_by('-fecha_consulta')

        todas_citas = qs
        citas_completadas = [c for c in todas_citas if c.estado == Cita.ESTADO_ATENDIDA]

    total_citas_count = len(todas_citas)

    paginator = Paginator(todas_citas, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Conteos por estado para los marcadores del médico
    conteo_pendientes   = 0
    conteo_confirmadas  = 0
    conteo_completadas  = 0
    conteo_canceladas   = 0

    if datos_medico:
        base_conteo = Cita.objects.filter(id_doctor=datos_medico, status=True)
        conteo_pendientes = base_conteo.filter(
            estado__in=[Cita.ESTADO_SOLICITADA, Cita.ESTADO_APROBADA, Cita.ESTADO_PAGO_PENDIENTE]
        ).count()
        conteo_confirmadas = base_conteo.filter(
            estado__in=[Cita.ESTADO_CONFIRMADA, Cita.ESTADO_PAGADA_ADELANTO, Cita.ESTADO_EN_CONSULTA]
        ).count()
        conteo_completadas = base_conteo.filter(
            estado=Cita.ESTADO_ATENDIDA
        ).count()
        conteo_canceladas = Cita.objects.filter(
            id_doctor=datos_medico,
            estado__in=[Cita.ESTADO_CANCELADA, Cita.ESTADO_RECHAZADA, Cita.ESTADO_NO_ASISTIO]
        ).count()

    return render(request, 'citas/citas_pendientes_medico.html', {
        'citas_pendientes':   citas_pendientes,
        'citas_asignadas':    citas_asignadas,
        'citas_completadas':  citas_completadas,
        'page_obj':           page_obj,
        'total_citas_count':  total_citas_count,
        'orden':              orden,
        'busqueda':           busqueda,
        'filtro':             filtro,
        'datos_medico':       datos_medico,
        'conteo_pendientes':  conteo_pendientes,
        'conteo_confirmadas': conteo_confirmadas,
        'conteo_completadas': conteo_completadas,
        'conteo_canceladas':  conteo_canceladas,
    })


@login_required(login_url='/login/medico/')
@rol_requerido('medico')
def confirmar_cita(request, cita_id):
    """Médico confirma/acepta una cita pendiente → estado='confirmada'."""
    from usuarios.authentication import CustomAuthBackend
    datos_medico = CustomAuthBackend().get_datos_personales(request.user)
    cita = get_object_or_404(Cita, id_citas=cita_id, id_doctor=datos_medico)
    if request.method == 'POST':
        try:
            CitaService.transicionar(cita, Cita.ESTADO_CONFIRMADA)
            cita.status = True
            cita.save(update_fields=['status'])
            registrar_evento(
                user=request.user,
                role='medico',
                action='UPDATE',
                model_affected='Cita',
                object_id=cita.pk,
                details={'cita_id': cita_id, 'nuevo_estado': 'confirmada'},
                request=request,
            )
            messages.success(request, f"Cita #{cita_id} confirmada.")
        except ValueError as e:
            messages.error(request, str(e))
    return redirect('citas_pendientes_medico')


@login_required(login_url='/login/medico/')
@rol_requerido('medico')
def gestionar_horarios(request):
    """Dashboard del médico para configurar disponibilidad por fecha específica."""
    from usuarios.authentication import CustomAuthBackend
    from usuarios.models import Doctor
    from citas.models import DisponibilidadDoctor
    from calendar import Calendar
    from datetime import date, datetime

    doctor = CustomAuthBackend().get_datos_personales(request.user)
    if not doctor:
        messages.error(request, "No se encontró tu perfil de médico.")
        return redirect('dashboard_medico')

    hoy = date.today()

    if request.method == 'POST':
        fecha_str = request.POST.get('fecha', '').strip()
        action = request.POST.get('action', 'save')
        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, "Fecha no válida.")
            return redirect('gestionar_horarios')

        if fecha <= hoy:
            messages.error(request, "Solo puedes configurar disponibilidad a partir de mañana.")
            return redirect(f'{request.path}?año={fecha.year}&mes={fecha.month}')

        if action == 'delete':
            DisponibilidadDoctor.objects.filter(doctor=doctor, fecha=fecha).delete()
            messages.success(request, f"Disponibilidad eliminada para {fecha.strftime('%d/%m/%Y')}.")
        else:
            mañana = bool(request.POST.get('turno_mañana'))
            tarde = bool(request.POST.get('turno_tarde'))
            if mañana or tarde:
                DisponibilidadDoctor.objects.update_or_create(
                    doctor=doctor,
                    fecha=fecha,
                    defaults={'turno_mañana': mañana, 'turno_tarde': tarde}
                )
                messages.success(request, f"Disponibilidad guardada para {fecha.strftime('%d/%m/%Y')}.")
            else:
                DisponibilidadDoctor.objects.filter(doctor=doctor, fecha=fecha).delete()
                messages.info(request, f"Sin turnos seleccionados — disponibilidad eliminada para {fecha.strftime('%d/%m/%Y')}.")

        # Preserve current month view
        return redirect(f'{request.path}?año={fecha.year}&mes={fecha.month}')

    # Calendario mensual
    try:
        año = int(request.GET.get('año', hoy.year))
        mes = int(request.GET.get('mes', hoy.month))
    except ValueError:
        año, mes = hoy.year, hoy.month

    if mes < 1:
        mes, año = 12, año - 1
    elif mes > 12:
        mes, año = 1, año + 1

    cal = Calendar(firstweekday=0)
    semanas = cal.monthdayscalendar(año, mes)

    mes_nombres = [
        'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
        'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
    ]
    dia_nombres = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']

    # Cargar disponibilidad del mes mostrado
    fecha_inicio = date(año, mes, 1)
    if mes == 12:
        fecha_fin = date(año + 1, 1, 1)
    else:
        fecha_fin = date(año, mes + 1, 1)

    disponibilidad = {
        d.fecha.isoformat(): d
        for d in DisponibilidadDoctor.objects.filter(
            doctor=doctor, fecha__gte=fecha_inicio, fecha__lt=fecha_fin
        )
    }

    calendario_semanas = []
    for semana in semanas:
        fila = []
        for dia_num in semana:
            if dia_num == 0:
                fila.append(None)
            else:
                dia_fecha = date(año, mes, dia_num)
                key = dia_fecha.isoformat()
                disp = disponibilidad.get(key)
                fila.append({
                    'dia': dia_num,
                    'fecha': dia_fecha,
                    'fecha_iso': key,
                    'mañana': disp.turno_mañana if disp else False,
                    'tarde': disp.turno_tarde if disp else False,
                    'trabaja': (disp.turno_mañana or disp.turno_tarde) if disp else False,
                    'es_hoy': dia_fecha == hoy,
                    'es_pasado_o_hoy': dia_fecha < hoy,
                })
        calendario_semanas.append(fila)

    mes_anterior = mes - 1 if mes > 1 else 12
    año_anterior = año if mes > 1 else año - 1
    mes_siguiente = mes + 1 if mes < 12 else 1
    año_siguiente = año if mes < 12 else año + 1

    return render(request, 'citas/gestionar_horarios.html', {
        'datos_medico': doctor,
        'calendario':   calendario_semanas,
        'dia_nombres':  dia_nombres,
        'mes_nombre':   mes_nombres[mes - 1],
        'año':          año,
        'mes':          mes,
        'hoy':          hoy,
        'mes_anterior': mes_anterior,
        'año_anterior': año_anterior,
        'mes_siguiente': mes_siguiente,
        'año_siguiente': año_siguiente,
    })


@login_required(login_url='/login/recepcionista/')
@rol_requerido('recepcionista', 'gerente')
def gestionar_citas(request):
    """Recepcionista/gerente: solicitudes nuevas, pagos por confirmar y citas aceptadas."""
    _base = Cita.objects.select_related(
        'id_paciente', 'id_doctor', 'id_sede',
        'id_especialidades', 'id_servicio_especialidad', 'id_pago_cita',
        'reserva_pago',
    ).order_by('-fecha_consulta')

    # Si se pasa ?hoy=1, filtrar solo citas del día actual
    if request.GET.get('hoy') == '1':
        hoy = date.today()
        _base = _base.filter(fecha_consulta__date=hoy)

    try:
        citas_solicitud = _base.filter(estado=Cita.ESTADO_SOLICITADA)
    except Exception:
        citas_solicitud = Cita.objects.none()

    try:
        citas_pago = _base.filter(estado=Cita.ESTADO_PAGO_PENDIENTE)
    except Exception:
        citas_pago = Cita.objects.none()

    try:
        citas_aceptadas = _base.filter(
            estado__in=[Cita.ESTADO_PAGADA_ADELANTO, Cita.ESTADO_CONFIRMADA]
        )
    except Exception:
        citas_aceptadas = Cita.objects.none()

    return render(request, 'citas/gestionar_citas.html', {
        'citas_solicitud': citas_solicitud,
        'citas_pago':      citas_pago,
        'citas_aceptadas': citas_aceptadas,
        'total': citas_solicitud.count() + citas_pago.count() + citas_aceptadas.count(),
        'filtro_hoy': request.GET.get('hoy') == '1',
    })


@login_required(login_url='/login/recepcionista/')
@rol_requerido('recepcionista', 'gerente')
def confirmar_pago(request, cita_id):
    """Recepcionista confirma que el pago del paciente fue verificado → estado='confirmada'."""
    if request.method == 'POST':
        cita = get_object_or_404(
            Cita.objects.select_related('id_pago_cita'), id_citas=cita_id
        )
        try:
            CitaService.confirmar_pago(request.user, cita)
            registrar_evento(
                user=request.user,
                role=CustomAuthBackend().get_rol(request.user),
                action='UPDATE',
                model_affected='Cita',
                object_id=cita.pk,
                details={'cita_id': cita_id, 'accion': 'confirmar_pago'},
                request=request,
            )
            messages.success(request, f"✅ Pago de cita #{cita_id} confirmado. Cita lista para consulta.")
        except PermissionError as e:
            messages.error(request, str(e))
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f"Error al confirmar pago: {e}")
    return redirect('gestionar_citas')


@login_required(login_url='/login/medico/')
@rol_requerido('medico')
def calendario_citas(request):
    """Calendario semanal de citas del medico autenticado."""
    from usuarios.authentication import CustomAuthBackend
    from django.utils.timezone import localtime
    datos_medico = CustomAuthBackend().get_datos_personales(request.user)

    hoy = date.today()
    try:
        semana_offset = int(request.GET.get('semana', 0))
    except ValueError:
        semana_offset = 0

    # Lunes de la semana solicitada
    dias_desde_lunes = hoy.weekday()  # 0=lun, 6=dom
    lunes = hoy - timedelta(days=dias_desde_lunes) + timedelta(weeks=semana_offset)
    domingo = lunes + timedelta(days=6)

    dia_nombres = ['Lun','Mar','Mie','Jue','Vie','Sab','Dom']
    dias_semana = []
    for i in range(7):
        d = lunes + timedelta(days=i)
        dias_semana.append({
            'fecha': d,
            'dia_num': d.day,
            'dia_nombre': dia_nombres[i],
            'es_hoy': d == hoy,
        })

    # Citas del medico en esta semana
    citas_por_dia = {d['fecha'].isoformat(): [] for d in dias_semana}
    total_citas = 0
    if datos_medico:
        citas = Cita.objects.filter(
            id_doctor=datos_medico,
            fecha_consulta__date__gte=lunes,
            fecha_consulta__date__lte=domingo,
            status=True,
        ).exclude(estado__in=[
            Cita.ESTADO_CANCELADA, Cita.ESTADO_RECHAZADA, Cita.ESTADO_NO_ASISTIO
        ]).select_related('id_paciente', 'id_especialidades').order_by('fecha_consulta')

        for c in citas:
            dia_key = localtime(c.fecha_consulta).date().isoformat()
            if dia_key in citas_por_dia:
                citas_por_dia[dia_key].append(c)
                total_citas += 1

    dias_con_citas = sum(1 for v in citas_por_dia.values() if v)
    promedio_citas = round(total_citas / dias_con_citas, 1) if dias_con_citas > 0 else 0

    # Rango texto para titulo
    rango_texto = f"{lunes.day} de {mes_nombre(lunes.month)} - {domingo.day} de {mes_nombre(domingo.month)} {lunes.year}"

    return render(request, 'citas/calendario_citas.html', {
        'dias_semana':    dias_semana,
        'citas_por_dia':  citas_por_dia,
        'total_citas':    total_citas,
        'promedio_citas': promedio_citas,
        'rango_texto':    rango_texto,
        'semana_offset':  semana_offset,
        'prev_offset':    semana_offset - 1,
        'next_offset':    semana_offset + 1,
        'hoy':            hoy.isoformat(),
        'datos_medico':   datos_medico,
    })


def mes_nombre(mes):
    nombres = [
        'Enero','Febrero','Marzo','Abril','Mayo','Junio',
        'Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre'
    ]
    return nombres[mes - 1]


@login_required(login_url='/login/recepcionista/')
@rol_requerido('recepcionista', 'gerente')
def aprobar_cita(request, cita_id):
    """Recepcionista aprueba la solicitud de cita → estado='aprobada'."""
    if request.method == 'POST':
        cita = get_object_or_404(Cita, id_citas=cita_id)
        try:
            CitaService.aprobar_cita(request.user, cita)
            registrar_evento(
                user=request.user,
                role=CustomAuthBackend().get_rol(request.user),
                action='UPDATE',
                model_affected='Cita',
                object_id=cita.pk,
                details={'cita_id': cita_id, 'nuevo_estado': 'aprobada'},
                request=request,
            )
            messages.success(request, f"✅ Cita #{cita_id} aprobada correctamente.")
        except PermissionError as e:
            messages.error(request, str(e))
        except ValueError as e:
            messages.error(request, str(e))
    return redirect('gestionar_citas')


@login_required(login_url='/login/recepcionista/')
@rol_requerido('recepcionista', 'gerente')
def rechazar_cita(request, cita_id):
    """Rechazar cita → estado='rechazada'."""
    cita = get_object_or_404(Cita, id_citas=cita_id)
    if request.method == 'POST':
        try:
            CitaService.transicionar(cita, Cita.ESTADO_RECHAZADA)
            cita.status = False
            cita.save(update_fields=['status'])
            registrar_evento(
                user=request.user,
                role=CustomAuthBackend().get_rol(request.user),
                action='UPDATE',
                model_affected='Cita',
                object_id=cita.pk,
                details={'cita_id': cita_id, 'nuevo_estado': 'rechazada'},
                request=request,
            )
            messages.info(request, f"Cita #{cita_id} rechazada.")
        except ValueError as e:
            messages.error(request, str(e))
    return redirect('gestionar_citas')


@rol_requerido('recepcionista', 'gerente')
def cancelar_cita_secretaria(request, cita_id):
    """Cancela una cita aceptada desde el dashboard de recepcionista/gerente."""
    if request.method == 'POST':
        cita = get_object_or_404(Cita, id_citas=cita_id)
        motivo = request.POST.get('motivo_cancelacion', 'Cancelada por recepcionista/gerente').strip()
        try:
            CitaService.cancelar_cita(cita, cancelada_por=request.user, motivo=motivo)
            registrar_evento(
                user=request.user,
                role=CustomAuthBackend().get_rol(request.user),
                action='UPDATE',
                model_affected='Cita',
                object_id=cita.pk,
                details={'cita_id': cita_id, 'nuevo_estado': 'cancelada', 'motivo': motivo},
                request=request,
            )
            messages.info(request, f"Cita #{cita_id} cancelada correctamente.")
        except ValueError as e:
            messages.error(request, str(e))
    return redirect('gestionar_citas')


@login_required(login_url='/login/recepcionista/')
@rol_requerido('recepcionista', 'gerente')
def marcar_llegada(request, cita_id):
    """Recepcionista marca que el paciente llegó → estado='en_consulta'."""
    if request.method == 'POST':
        cita = get_object_or_404(Cita, id_citas=cita_id)
        try:
            CitaService.transicionar(cita, Cita.ESTADO_EN_CONSULTA)
            cita.status = True
            cita.save(update_fields=['status'])
            registrar_evento(
                user=request.user,
                role=CustomAuthBackend().get_rol(request.user),
                action='UPDATE',
                model_affected='Cita',
                object_id=cita.pk,
                details={'cita_id': cita_id, 'nuevo_estado': 'en_consulta'},
                request=request,
            )
            messages.success(request, f"Paciente de cita #{cita_id} marcado como llegado.")
        except ValueError as e:
            messages.error(request, str(e))
    return redirect('dashboard_recepcionista')


@rol_requerido('recepcionista', 'gerente')
def registrar_adelanto(request, cita_id):
    """Recepcionista registra un adelanto de pago sin generar factura inmediata."""
    cita = get_object_or_404(Cita.objects.select_related('id_paciente', 'id_sede'), id_citas=cita_id)
    if request.method == 'POST':
        form = RegistrarAdelantoForm(request.POST)
        if form.is_valid():
            try:
                CitaService.registrar_adelanto(
                    request.user,
                    cita,
                    monto=form.cleaned_data['monto'],
                    metodo_pago=form.cleaned_data['metodo_pago'],
                    referencia=form.cleaned_data.get('referencia'),
                )
                registrar_evento(
                    user=request.user,
                    role=CustomAuthBackend().get_rol(request.user),
                    action='UPDATE',
                    model_affected='Cita',
                    object_id=cita.pk,
                    details={'cita_id': cita_id, 'accion': 'registrar_adelanto', 'monto': str(form.cleaned_data['monto'])},
                    request=request,
                )
                messages.success(request, f"✅ Adelanto registrado. Cita #{cita_id} marcada como pagada con adelanto.")
                return redirect('gestionar_citas')
            except PermissionError as e:
                messages.error(request, str(e))
            except ValueError as e:
                messages.error(request, str(e))
    else:
        form = RegistrarAdelantoForm()
    return render(request, 'citas/registrar_adelanto.html', {
        'form': form,
        'cita': cita,
    })


# ─── Endpoints AJAX ─────────────────────────────────────────────

# Mapa de clasificaciones permitidas por tipo de paciente
_CLASIFICACIONES_POR_TIPO = {
    'adulto': ['Adultos', 'General'],
    'menor':  ['Pediatría', 'General'],
}

@login_required
@require_GET
def ajax_especialidades(request):
    """Especialidades activas en una sede, filtradas por tipo de paciente.

    Parámetro tipo_paciente:
      'adulto' → clasificaciones ['Adultos', 'General']
      'menor'  → clasificaciones ['Pediatría', 'General']
      omitido  → igual que 'adulto' (comportamiento por defecto seguro)
    """
    sede_id      = request.GET.get('sede_id')
    tipo_paciente = request.GET.get('tipo_paciente', 'adulto').strip().lower()
    if not sede_id:
        return JsonResponse([], safe=False)
    try:
        qs = Especialidad.objects.filter(id_sede_id=sede_id, status__in=[True, None])
        # Aplicar filtro de clasificación según el tipo de paciente
        clasificaciones = _CLASIFICACIONES_POR_TIPO.get(tipo_paciente)
        if clasificaciones:
            qs = qs.filter(clasificacion_especialidad__in=clasificaciones)
        data = [
            {'id': e['id_especialidad'], 'nombre': e['tipo_especialidad']}
            for e in qs.values('id_especialidad', 'tipo_especialidad')
        ]
    except Exception as exc:
        return JsonResponse({'error': str(exc)}, safe=False, status=500)
    return JsonResponse(data, safe=False)


@login_required
@require_GET
def ajax_doctores(request):
    """Doctores por especialidad y sede (AJAX)."""
    especialidad_id = request.GET.get('especialidad_id')
    sede_id = request.GET.get('sede_id')
    if not especialidad_id or not sede_id:
        return JsonResponse([], safe=False)

    try:
        doctores = CitaService.obtener_doctores_disponibles(especialidad_id, sede_id)
        return JsonResponse(doctores, safe=False)
    except Exception as exc:
        return JsonResponse({'error': str(exc)}, safe=False, status=500)


@require_GET
def ajax_fechas_disponibles(request):
    """Fechas con disponibilidad para un doctor en un mes."""
    from datetime import date
    from citas.models import DisponibilidadDoctor

    doctor_id = request.GET.get('doctor_id')
    if not doctor_id:
        return JsonResponse({'fechas': [], 'debug': 'doctor_id vacio'})
    try:
        año = int(request.GET.get('anio', request.GET.get('año', date.today().year)))
        mes = int(request.GET.get('mes', date.today().month))

        inicio = date(año, mes, 1)
        if mes == 12:
            fin = date(año + 1, 1, 1)
        else:
            fin = date(año, mes + 1, 1)

        fechas = list(
            DisponibilidadDoctor.objects.filter(
                doctor_id=doctor_id,
                fecha__gte=inicio,
                fecha__lt=fin,
            ).exclude(
                turno_mañana=False, turno_tarde=False
            ).values_list('fecha', flat=True)
        )
        return JsonResponse({'fechas': [f.isoformat() for f in fechas]})
    except Exception as exc:
        return JsonResponse({'fechas': [], 'error': str(exc)})


@login_required
@require_GET
def ajax_horas_disponibles(request):
    """Slots de 1 hora disponibles para un doctor en una fecha."""
    doctor_id = request.GET.get('medico_id') or request.GET.get('doctor_id')
    fecha = request.GET.get('fecha')
    if not doctor_id or not fecha:
        return JsonResponse({'horas': []})
    try:
        horas, mensaje = CitaService.obtener_horas_disponibles(doctor_id, fecha)
        if mensaje:
            return JsonResponse({'horas': horas, 'mensaje': mensaje})
        return JsonResponse({'horas': horas})
    except Exception as exc:
        return JsonResponse({'horas': [], 'error': str(exc)})


@login_required
@require_GET
def ajax_servicios(request):
    """Servicios por doctor (y opcionalmente sede/especialidad)."""
    doctor_id = request.GET.get('doctor_id')
    if not doctor_id:
        return JsonResponse([], safe=False)
    try:
        servicios = ServicioEspecialidad.objects.filter(
            id_doctor_id=doctor_id, status__in=[True, None]
        ).values('id_servicios_especialidad', 'servicios')
        data = [{'id': s['id_servicios_especialidad'], 'nombre': s['servicios']} for s in servicios]
    except Exception as exc:
        return JsonResponse({'error': str(exc)}, safe=False, status=500)
    return JsonResponse(data, safe=False)

@login_required
@require_GET
def ajax_servicios_medico(request):
    """Servicios médicos activos de un doctor (nombre + precio). Usado por paciente al solicitar cita."""
    doctor_id = request.GET.get('doctor_id')
    if not doctor_id:
        return JsonResponse([], safe=False)
    try:
        servicios = ServicioMedico.objects.filter(
            id_doctor_id=doctor_id, activo=True
        ).order_by('nombre').values(
            'id_servicio_medico', 'nombre', 'descripcion', 'precio'
        )
        data = [
            {
                'id': s['id_servicio_medico'],
                'nombre': s['nombre'],
                'descripcion': s['descripcion'] or '',
                'precio': str(s['precio']),
            }
            for s in servicios
        ]
    except Exception as exc:
        return JsonResponse({'error': str(exc)}, safe=False, status=500)
    return JsonResponse(data, safe=False)


# ─── Vistas del paciente ───────────────────────────────────────────────────────

@login_required(login_url='/login/paciente/')
@rol_requerido('paciente')
def mis_citas(request):
    """Lista paginada de citas del paciente autenticado con filtros por estado."""
    user = request.user
    paciente = PacienteDatosPersonales.objects.filter(id_user_paciente=user).first()

    citas_qs = Cita.objects.none()
    if paciente:
        citas_qs = Cita.objects.filter(id_paciente=paciente).select_related(
            'id_doctor', 'id_especialidades', 'id_sede', 'id_servicio_especialidad'
        ).order_by('-fecha_emision')

    # Filtros por estado del modelo Cita
    estado_filtro = request.GET.get('estado', 'todos')
    if estado_filtro == 'pendiente':
        citas_qs = citas_qs.filter(estado__in=[
            Cita.ESTADO_SOLICITADA,
            Cita.ESTADO_APROBADA,
            Cita.ESTADO_PAGO_PENDIENTE,
            Cita.ESTADO_PAGADA_ADELANTO,
        ])
    elif estado_filtro == 'confirmada':
        citas_qs = citas_qs.filter(estado__in=[
            Cita.ESTADO_CONFIRMADA,
            Cita.ESTADO_EN_CONSULTA,
        ])
    elif estado_filtro == 'completada':
        citas_qs = citas_qs.filter(estado=Cita.ESTADO_ATENDIDA)
    elif estado_filtro == 'cancelada':
        citas_qs = citas_qs.filter(estado__in=[
            Cita.ESTADO_CANCELADA,
            Cita.ESTADO_RECHAZADA,
            Cita.ESTADO_NO_ASISTIO,
        ])

    paginator = Paginator(citas_qs, 10)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    estados_choices = [
        ('todos', _('Todos')),
        ('pendiente', _('Pendientes')),
        ('confirmada', _('Confirmadas')),
        ('completada', _('Completadas')),
        ('cancelada', _('Canceladas / Rechazadas')),
    ]

    return render(request, 'citas/mis_citas.html', {
        'page_obj': page_obj,
        'estados_choices': estados_choices,
        'estado_actual': estado_filtro,
    })


@login_required(login_url='/login/paciente/')
@rol_requerido('paciente')
def mis_facturas(request):
    """Lista de citas del paciente con estado de pago y factura."""
    user = request.user
    paciente = PacienteDatosPersonales.objects.filter(id_user_paciente=user).first()

    citas_qs = Cita.objects.none()
    if paciente:
        citas_qs = Cita.objects.filter(id_paciente=paciente).select_related(
            'id_pago_cita', 'id_sede', 'id_especialidades', 'id_doctor'
        ).prefetch_related(
            'consulta_medica__servicios_realizados',
            'factura',
        ).order_by('-fecha_consulta')

    estado_filtro = request.GET.get('estado', '')
    if estado_filtro == 'pagado':
        citas_qs = citas_qs.filter(
            estado__in=[Cita.ESTADO_CONFIRMADA, Cita.ESTADO_EN_CONSULTA, Cita.ESTADO_ATENDIDA]
        )
    elif estado_filtro == 'pendiente':
        citas_qs = citas_qs.filter(estado=Cita.ESTADO_APROBADA)
    elif estado_filtro == 'solicitada':
        citas_qs = citas_qs.filter(
            estado__in=[Cita.ESTADO_SOLICITADA, Cita.ESTADO_PAGO_PENDIENTE]
        )

    paginator = Paginator(citas_qs, 10)
    page_obj  = paginator.get_page(request.GET.get('page', 1))

    # Totales reales de facturas del paciente
    total_facturas = 0
    total_pagado = Decimal('0.00')
    total_adeudado = Decimal('0.00')
    facturas_pendientes = 0
    if paciente:
        citas_ids = list(citas_qs.values_list('id_citas', flat=True))
        facturas_qs = Factura.objects.filter(id_cita__in=citas_ids)
        total_facturas = facturas_qs.count()
        total_pagado = (
            facturas_qs.filter(estado=Factura.ESTADO_PAGADA)
            .aggregate(total=Sum('total'))['total'] or Decimal('0.00')
        )
        facturas_pendientes_qs = facturas_qs.exclude(
            estado__in=[Factura.ESTADO_PAGADA, Factura.ESTADO_ANULADA]
        )
        total_adeudado = (
            facturas_pendientes_qs.aggregate(total=Sum('total'))['total'] or Decimal('0.00')
        )
        facturas_pendientes = facturas_pendientes_qs.count()
        facturas_pagadas = facturas_qs.filter(estado=Factura.ESTADO_PAGADA).count()

    estados_choices = [
        ('pagado', _('Pagadas')),
        ('pendiente', _('Por pagar')),
        ('solicitada', _('En proceso')),
    ]
    return render(request, 'citas/mis_facturas.html', {
        'page_obj':            page_obj,
        'estados_choices':     estados_choices,
        'estado_actual':       estado_filtro,
        'total_facturas':      total_facturas,
        'total_pagado':        total_pagado,
        'total_adeudado':      total_adeudado,
        'facturas_pendientes': facturas_pendientes,
        'facturas_pagadas':    facturas_pagadas,
    })


@login_required(login_url='/login/paciente/')
@rol_requerido('paciente', 'recepcionista', 'gerente')
def detalle_cita(request, cita_id):
    """Detalle de una cita específica."""
    user = request.user
    auth_backend = CustomAuthBackend()
    user_rol = auth_backend.get_rol(user)

    cita_qs = Cita.objects.select_related(
        'id_doctor', 'id_especialidades', 'id_sede',
        'id_servicio_especialidad', 'id_consultorio', 'id_pago_cita'
    )

    if user_rol == 'paciente':
        paciente = PacienteDatosPersonales.objects.filter(id_user_paciente=user).first()
        cita = get_object_or_404(cita_qs, id_citas=cita_id, id_paciente=paciente)
    else:
        cita = get_object_or_404(cita_qs, id_citas=cita_id)

    consulta = None
    try:
        consulta = cita.consulta_medica
    except ConsultaMedica.DoesNotExist:
        pass
    receta = Recipe.objects.filter(id_cita=cita).select_related(
        'id_Recipe_diagnostico', 'id_Recipe_tratamiento',
        'id_Recipe_reposo', 'id_Recipe_medicamentos_especiales',
        'id_Recipe_estudios', 'id_Recipes_ordenes_medicas',
    ).first()
    return render(request, 'citas/detalle_cita.html', {'cita': cita, 'consulta': consulta, 'receta': receta})


@login_required(login_url='/login/paciente/')
@rol_requerido('paciente')
def historial_consultas(request):
    """Muestra todas las citas atendidas del paciente con los resultados de la consulta médica."""
    user = request.user
    paciente = PacienteDatosPersonales.objects.filter(id_user_paciente=user).first()

    citas_atendidas = Cita.objects.filter(
        id_paciente=paciente,
        estado=Cita.ESTADO_ATENDIDA,
    ).select_related(
        'id_doctor', 'id_especialidades', 'id_sede'
    ).prefetch_related(
        'consulta_medica'
    ).order_by('-fecha_consulta')

    # Enriquecer cada cita con su consulta médica (si existe)
    citas_con_consulta = []
    for cita in citas_atendidas:
        consulta = None
        try:
            consulta = cita.consulta_medica
        except ConsultaMedica.DoesNotExist:
            pass
        citas_con_consulta.append({'cita': cita, 'consulta': consulta})

    return render(request, 'citas/historial_consultas.html', {
        'citas_con_consulta': citas_con_consulta,
        'paciente': paciente,
    })


@login_required(login_url='/login/paciente/')
@rol_requerido('paciente')
def cancelar_cita_paciente(request, cita_id):
    """Cancela (status=False) una cita activa del paciente."""
    user = request.user
    paciente = PacienteDatosPersonales.objects.filter(id_user_paciente=user).first()
    cita = get_object_or_404(Cita, id_citas=cita_id, id_paciente=paciente)
    if request.method == 'POST':
        try:
            CitaService.cancelar_cita(cita, cancelada_por=user, motivo='Cancelada por el paciente')
            registrar_evento(
                user=user,
                role='paciente',
                action='UPDATE',
                model_affected='Cita',
                object_id=cita.pk,
                details={'cita_id': cita_id, 'nuevo_estado': 'cancelada', 'motivo': 'Cancelada por el paciente'},
                request=request,
            )
            messages.info(request, f"Cita #{cita_id} cancelada correctamente.")
        except ValueError as e:
            messages.warning(request, str(e))
        return redirect('mis_citas')
    return render(request, 'citas/cancelar_cita.html', {'cita': cita})


@login_required(login_url='/login/paciente/')
@rol_requerido('paciente')
def pagar_cita(request, cita_id):
    """Paciente registra el pago de una cita (post-consulta o aprobada)."""
    import re
    user = request.user
    paciente = PacienteDatosPersonales.objects.filter(id_user_paciente=user).first()
    cita = get_object_or_404(
        Cita.objects.select_related('id_pago_cita')
                    .prefetch_related('servicios_solicitados'),
        id_citas=cita_id,
        id_paciente=paciente,
    )

    estados_pagables = [Cita.ESTADO_APROBADA, Cita.ESTADO_SOLICITADA, Cita.ESTADO_ATENDIDA]
    if cita.estado not in estados_pagables:
        messages.warning(request, "Esta cita no está disponible para pago.")
        return redirect('mis_citas')

    # Desglose de cargos (en Bs)
    costo_consulta_bs = Decimal('0')

    # Costo de consulta = precio del servicio por el que se pidió la cita
    servicios_solicitados = cita.servicios_solicitados.all()
    for svc in servicios_solicitados:
        precio_unit = Decimal(str(svc.precio_estimado or 0))
        cantidad = svc.cantidad or 1
        costo_consulta_bs += precio_unit * cantidad

    total_bs = costo_consulta_bs

    METODOS_PAGO = [
        ('transferencia', _('Transferencia bancaria')),
        ('efectivo',      _('Efectivo')),
        ('otro',          _('Otro')),
    ]

    if request.method == 'POST':
        metodo     = request.POST.get('metodo_pago', '').strip()
        # Hay múltiples inputs con name="referencia_pago" (transferencia y otro);
        # tomamos el primero que no esté vacío.
        referencia_vals = [v.strip() for v in request.POST.getlist('referencia_pago') if v.strip()]
        referencia = referencia_vals[0] if referencia_vals else ''
        cedula     = request.POST.get('cedula', '').strip()
        telefono   = request.POST.get('telefono', '').strip()
        monto_pago = request.POST.get('monto_pago', '').strip()

        errores = []
        if not metodo:
            errores.append("Debes seleccionar un método de pago.")

        if metodo == 'transferencia':
            if not cedula or not re.fullmatch(r'^\d{7,8}$', cedula):
                errores.append("La cédula debe tener entre 7 y 8 dígitos numéricos.")
            if not telefono or not re.fullmatch(r'^\d{1,11}$', telefono):
                errores.append("El teléfono debe tener máximo 11 dígitos numéricos.")
            if not referencia or not re.fullmatch(r'^\d{6}$', referencia):
                errores.append("La referencia debe tener exactamente 6 dígitos numéricos (últimos 6 dígitos).")
            if not monto_pago or not re.fullmatch(r'^\d{1,27},\d{2}$', monto_pago):
                errores.append("El monto debe tener formato 0,00 (ej: 50,00).")

        if errores:
            for e in errores:
                messages.error(request, e)
        else:
            try:
                from django.db import transaction as _tx
                with _tx.atomic():
                    pago = cita.id_pago_cita
                    if pago:
                        pago.metodo_pago     = metodo
                        pago.referencia_pago = referencia
                        pago.estado_pago     = PagoCita.ESTADO_PENDIENTE
                        if monto_pago:
                            try:
                                pago.monto_pagar = Decimal(str(monto_pago).replace(',', '.'))
                            except Exception:
                                pass
                        pago.save(update_fields=['metodo_pago', 'referencia_pago', 'estado_pago', 'monto_pagar'])

                    # Guardar datos de transferencia
                    from citas.models import ReservaTransferencia
                    rt, created = ReservaTransferencia.objects.get_or_create(cita=cita)
                    rt.cedula   = cedula
                    rt.telefono = telefono
                    rt.referencia = referencia
                    rt.save(update_fields=['cedula', 'telefono', 'referencia'])

                    # Solo cambiar estado si no es atendida
                    if cita.estado != Cita.ESTADO_ATENDIDA:
                        cita.estado = Cita.ESTADO_PAGO_PENDIENTE
                        cita.save(update_fields=['estado'])

                registrar_evento(
                    user=user,
                    role='paciente',
                    action='UPDATE',
                    model_affected='Cita',
                    object_id=cita.pk,
                    details={'cita_id': cita_id, 'accion': 'pago_registrado', 'metodo': metodo},
                    request=request,
                )
                messages.success(
                    request,
                    "✅ Pago registrado. La recepcionista verificará y confirmará tu pago."
                )
                return redirect('mis_citas')
            except Exception as e:
                messages.error(request, f"Error al registrar el pago: {e}")

    return render(request, 'citas/pagar_cita.html', {
        'cita':               cita,
        'metodos_pago':       METODOS_PAGO,
        'costo_consulta':     costo_consulta_bs,
        'total':              total_bs,
    })


# ─── Vista de receta médica ────────────────────────────────────────────────────

@login_required(login_url='/login/medico/')
@rol_requerido('medico')
def realizar_receta(request, cita_id):
    """
    GET:  Muestra el formulario de receta médica para la cita indicada.
          Verifica que el doctor autenticado sea el asignado a la cita.
    POST: Valida el formulario. Dentro de una transacción atómica:
          - Crea un registro en cada tabla hija solo si el campo tiene texto.
          - Crea el registro principal en recipes con todas las FK.
          La relación inversa paciente→recetas se obtiene vía Recipe.objects.filter(id_paciente=...).
    """
    from django.db import transaction
    from usuarios.authentication import CustomAuthBackend
    from .models import (
        RecipesOrdenesMedicas, RecipeTratamiento, RecipeReposo,
        RecipeMedicamentosEspeciales, RecipeEstudios, RecipeDiagnostico, Recipe,
    )
    from .forms import RecetaForm

    # Obtener el perfil del médico autenticado
    datos_medico = CustomAuthBackend().get_datos_personales(request.user)
    if not datos_medico:
        messages.error(request, "No se encontraron datos del médico.")
        return redirect('citas_pendientes_medico')

    # La cita debe pertenecer al médico logueado; si no, devuelve 404
    cita = get_object_or_404(
        Cita.objects.select_related('id_paciente', 'id_sede', 'id_especialidades'),
        id_citas=cita_id,
        id_doctor=datos_medico,
    )
    paciente = cita.id_paciente
    sede     = cita.id_sede

    if request.method == 'POST':
        form = RecetaForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            try:
                with transaction.atomic():
                    # Crear registros hijos solo si el campo tiene contenido
                    ordenes_obj = (
                        RecipesOrdenesMedicas.objects.create(ordenes_medicas=cd['ordenes_medicas'])
                        if cd.get('ordenes_medicas') else None
                    )
                    tratamiento_obj = (
                        RecipeTratamiento.objects.create(tratamiento_necesario=cd['tratamiento'])
                        if cd.get('tratamiento') else None
                    )
                    reposo_obj = (
                        RecipeReposo.objects.create(reposo=cd['reposo'])
                        if cd.get('reposo') else None
                    )
                    meds_obj = (
                        RecipeMedicamentosEspeciales.objects.create(
                            medicamentos_especiales=cd['medicamentos_especiales']
                        )
                        if cd.get('medicamentos_especiales') else None
                    )
                    estudios_obj = (
                        RecipeEstudios.objects.create(estudios_realizar=cd['estudios'])
                        if cd.get('estudios') else None
                    )
                    diagnostico_obj = (
                        RecipeDiagnostico.objects.create(diagnostico=cd['diagnostico'])
                        if cd.get('diagnostico') else None
                    )

                    # Crear el registro principal que relaciona todo
                    recipe = Recipe.objects.create(
                        id_doctor=datos_medico,
                        id_cita=cita,
                        id_paciente=paciente,
                        id_sede=sede,
                        id_Recipes_ordenes_medicas=ordenes_obj,
                        id_Recipe_tratamiento=tratamiento_obj,
                        id_Recipe_reposo=reposo_obj,
                        id_Recipe_medicamentos_especiales=meds_obj,
                        id_Recipe_estudios=estudios_obj,
                        id_Recipe_diagnostico=diagnostico_obj,
                        status=True,
                        fecha_emision=timezone.now(),
                    )

                registrar_evento(
                    user=request.user,
                    role='medico',
                    action='CREATE',
                    model_affected='Recipe',
                    object_id=recipe.pk,
                    details={'cita_id': cita_id, 'receta_id': recipe.pk},
                    request=request,
                )
                messages.success(
                    request,
                    f"✅ Receta #{recipe.pk} generada exitosamente para "
                    f"{paciente.nombre_completo if paciente else 'el paciente'}."
                )
                return redirect('citas_pendientes_medico')

            except Exception as exc:
                messages.error(request, f"Error al guardar la receta: {exc}")
                logger.error(f"Error realizar_receta cita_id={cita_id}: {exc}")
    else:
        form = RecetaForm()

    return render(request, 'citas/realizar_receta.html', {
        'form':         form,
        'cita':         cita,
        'paciente':     paciente,
        'datos_medico': datos_medico,
    })


def _generar_o_actualizar_factura_consulta(cita, consulta, total_servicios):
    """Genera o actualiza la factura usando el total calculado de servicios."""
    from django.utils import timezone

    total = Decimal(str(total_servicios))
    impuesto = Decimal('0.00')

    # Buscar factura existente
    try:
        factura = cita.factura
    except Factura.DoesNotExist:
        factura = None

    pago = getattr(cita, 'id_pago_cita', None)

    if factura:
        # Actualizar factura existente
        factura.subtotal = total
        factura.impuesto = impuesto
        factura.total = total
        factura.descripcion = _descripcion_servicios(consulta)
        # Estado: pagada si el adelanto cubre o excede el total
        if pago and pago.monto_pagar and Decimal(str(pago.monto_pagar)) >= total:
            factura.estado = Factura.ESTADO_PAGADA
        else:
            factura.estado = Factura.ESTADO_EMITIDA
        factura.save(update_fields=['subtotal', 'impuesto', 'total', 'descripcion', 'estado'])
    else:
        # Crear nueva factura
        numero = f"FAC-{timezone.now().strftime('%Y%m%d')}-{cita.pk}"
        estado = Factura.ESTADO_EMITIDA
        if pago and pago.monto_pagar and Decimal(str(pago.monto_pagar)) >= total:
            estado = Factura.ESTADO_PAGADA
        Factura.objects.create(
            id_cita=cita,
            id_pago_cita=pago,
            numero=numero,
            descripcion=_descripcion_servicios(consulta),
            subtotal=total,
            impuesto=impuesto,
            total=total,
            estado=estado,
        )


def _descripcion_servicios(consulta):
    """Genera descripción de la factura basada en los servicios realizados."""
    servicios = ConsultaServicio.objects.filter(id_consulta=consulta)
    if servicios.exists():
        nombres = [s.nombre_servicio or str(s.id_servicio_medico) for s in servicios]
        return ", ".join(nombres)
    return "Consulta médica"


# ─── Consulta médica ──────────────────────────────────────────────────────────

@login_required(login_url='/login/medico/')
@rol_requerido('medico')
def iniciar_consulta(request, cita_id):
    """Médico inicia o continúa una consulta médica."""
    from usuarios.authentication import CustomAuthBackend
    datos_medico = CustomAuthBackend().get_datos_personales(request.user)
    cita = get_object_or_404(
        Cita.objects.select_related('id_paciente', 'id_paciente__id_user_paciente', 'id_especialidades', 'id_doctor'),
        pk=cita_id
    )

    # Verificar que la cita pertenezca al médico autenticado
    if cita.id_doctor_id != datos_medico.pk:
        messages.error(request, "No puedes iniciar consulta de una cita que no te pertenece.")
        return redirect('citas_pendientes_medico')

    # Historial médico del paciente
    paciente = cita.id_paciente
    edad = paciente.edad if paciente else None
    # Soporte para managed=False: la columna puede existir en BD aunque no esté declarada
    paciente_especial = getattr(cita, 'id_paciente_especial', None)

    historial = None
    alergias = []
    enfermedades = []
    tipo_sangre = None

    if paciente:
        historial = HistorialMedicoPaciente.objects.filter(
            id_paciente=paciente
        ).select_related('id_tipo_sangre').first()

    if not historial and paciente_especial:
        historial = HistorialMedicoPaciente.objects.filter(
            id_paciente_especial=paciente_especial
        ).select_related('id_tipo_sangre').first()

    if historial:
        alergias = list(historial.alergias.all())
        enfermedades = list(historial.enfermedades.all())
        tipo_sangre = historial.id_tipo_sangre

    try:
        consulta, _ = CitaService.iniciar_consulta(request.user, cita)
    except PermissionError as e:
        messages.error(request, str(e))
        return redirect('citas_pendientes_medico')
    except ValueError as e:
        messages.error(request, str(e))
        return redirect('citas_pendientes_medico')

    # Servicios del médico para selección en consulta
    servicios_doctor = ServicioMedico.objects.filter(
        id_doctor=datos_medico, activo=True
    ).order_by('nombre')

    # Servicios ya seleccionados en esta consulta (si existen)
    servicios_seleccionados = set()
    if consulta.pk:
        servicios_seleccionados = set(
            ConsultaServicio.objects.filter(id_consulta=consulta)
            .values_list('id_servicio_medico_id', flat=True)
        )

    # Si es primera vez que abre la consulta, pre-seleccionar servicios solicitados por el paciente
    preseleccion_paciente = []
    if consulta.estado == ConsultaMedica.ESTADO_ABIERTA and not servicios_seleccionados:
        preseleccion = CitaServicioSolicitado.objects.filter(
            id_cita=cita,
            id_servicio_medico__isnull=False,
        )
        if preseleccion.exists():
            servicios_seleccionados = set(
                preseleccion.values_list('id_servicio_medico_id', flat=True)
            )
            preseleccion_paciente = list(preseleccion)

    if request.method == 'POST':
        form = ConsultaMedicaForm(request.POST, instance=consulta)
        if form.is_valid():
            form.save()

            # Procesar servicios seleccionados
            servicios_ids = request.POST.getlist('servicios')
            if servicios_ids:
                # Limpiar servicios previos de esta consulta
                ConsultaServicio.objects.filter(id_consulta=consulta).delete()
                total_servicios = Decimal('0.00')

                for sid in servicios_ids:
                    try:
                        servicio = ServicioMedico.objects.get(pk=int(sid), id_doctor=datos_medico, activo=True)
                        ConsultaServicio.objects.create(
                            id_consulta=consulta,
                            id_servicio_medico=servicio,
                            nombre_servicio=servicio.nombre,
                            precio_cobrado=servicio.precio,
                            cantidad=1,
                        )
                        total_servicios += Decimal(str(servicio.precio or 0))
                    except (ServicioMedico.DoesNotExist, ValueError):
                        continue

                # Generar/actualizar factura con total de servicios
                if total_servicios > 0:
                    _generar_o_actualizar_factura_consulta(cita, consulta, total_servicios)

            # Guardar borrador: solo persistir, sin cerrar consulta
            if request.POST.get('guardar_borrador') == '1':
                messages.success(request, 'Borrador guardado correctamente.')
                return redirect('iniciar_consulta', cita_id=cita_id)

            try:
                CitaService.cerrar_consulta(request.user, cita)
                registrar_evento(
                    user=request.user,
                    role='medico',
                    action='UPDATE',
                    model_affected='Cita',
                    object_id=cita.pk,
                    details={'cita_id': cita_id, 'nuevo_estado': 'atendida', 'accion': 'cerrar_consulta'},
                    request=request,
                )
                messages.success(
                    request,
                    '✅ Consulta guardada y cerrada correctamente. La cita ha sido marcada como atendida.'
                )
            except (PermissionError, ValueError) as e:
                messages.error(request, str(e))
                return redirect('iniciar_consulta', cita_id=cita_id)
            return redirect('citas_pendientes_medico')
    else:
        form = ConsultaMedicaForm(instance=consulta)

    return render(request, 'citas/consulta_medica.html', {
        'form': form,
        'cita': cita,
        'consulta': consulta,
        'servicios_doctor': servicios_doctor,
        'servicios_seleccionados': servicios_seleccionados,
        'preseleccion_paciente': preseleccion_paciente,
        'alergias': alergias,
        'enfermedades': enfermedades,
        'tipo_sangre': tipo_sangre,
        'edad': edad,
    })


@login_required(login_url='/login/medico/')
@rol_requerido('medico')
def cerrar_consulta(request, cita_id):
    """Médico cierra la consulta y marca la cita como atendida."""
    cita = get_object_or_404(
        Cita.objects.select_related('id_paciente', 'id_paciente__id_user_paciente', 'id_especialidades', 'id_doctor'),
        pk=cita_id
    )
    consulta = get_object_or_404(ConsultaMedica, id_cita=cita)
    edad = cita.id_paciente.edad if cita.id_paciente else None

    if consulta.estado == ConsultaMedica.ESTADO_CERRADA:
        messages.warning(request, 'Esta consulta ya está cerrada.')
        return redirect('iniciar_consulta', cita_id=cita_id)

    if request.method == 'POST':
        try:
            CitaService.cerrar_consulta(request.user, cita)
            registrar_evento(
                user=request.user,
                role='medico',
                action='UPDATE',
                model_affected='Cita',
                object_id=cita.pk,
                details={'cita_id': cita_id, 'nuevo_estado': 'atendida', 'accion': 'cerrar_consulta'},
                request=request,
            )
            messages.success(request, '✅ Consulta cerrada. Cita marcada como atendida.')
            return redirect('citas_pendientes_medico')
        except PermissionError as e:
            messages.error(request, str(e))
        except ValueError as e:
            messages.error(request, str(e))

    return render(request, 'citas/consulta_medica.html', {
        'form':     ConsultaMedicaForm(instance=consulta),
        'cita':     cita,
        'consulta': consulta,
        'edad':     edad,
    })


# ─── Facturación ──────────────────────────────────────────────────────────

@login_required(login_url='/login/')
def detalle_factura(request, cita_id):
    """Devuelve o genera la factura de una cita con pago aprobado."""
    cita = get_object_or_404(
        Cita.objects.select_related('id_pago_cita').prefetch_related('consulta_medica__servicios_realizados'),
        pk=cita_id
    )
    try:
        factura = cita.factura
    except Factura.DoesNotExist:
        try:
            factura = FacturacionService.generar_factura_cita(cita)
        except ValueError as e:
            messages.error(request, str(e))
            return redirect('mis_citas')

    # Servicios realizados para el desglose
    servicios = []
    try:
        consulta = cita.consulta_medica
        servicios = list(consulta.servicios_realizados.all())
    except (AttributeError, ConsultaMedica.DoesNotExist):
        pass

    # Pago asociado y saldo
    pago = getattr(cita, 'id_pago_cita', None)
    monto_pagado = Decimal(str(pago.monto_pagar or 0)) if pago else Decimal('0.00')
    saldo_pendiente = max(Decimal('0.00'), Decimal(str(factura.total or 0)) - monto_pagado)

    return render(request, 'citas/factura_detalle.html', {
        'factura': factura,
        'servicios': servicios,
        'pago': pago,
        'monto_pagado': monto_pagado,
        'saldo_pendiente': saldo_pendiente,
    })


@login_required(login_url='/login/')
def factura_pdf(request, factura_id):
    """Genera y descarga la factura en PDF con formato profesional y datos reales."""
    from io import BytesIO
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
    from usuarios.models import PacienteDatosPersonales

    factura = get_object_or_404(Factura, pk=factura_id)

    # Verificar propiedad si el usuario es paciente
    if hasattr(request.user, 'id_user_paciente'):
        paciente = PacienteDatosPersonales.objects.filter(id_user_paciente=request.user).first()
        if paciente and factura.id_cita.id_paciente != paciente:
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden('No tienes permiso para descargar esta factura.')

    # Datos reales
    cita = factura.id_cita
    pago = factura.id_pago_cita
    sede = cita.id_sede
    cm_obj = sede.id_cm if sede else None
    paciente = cita.id_paciente
    doctor = cita.id_doctor

    # Servicios solicitados en la cita
    from citas.models import CitaServicioSolicitado
    servicios_qs = CitaServicioSolicitado.objects.filter(id_cita=cita)
    if not servicios_qs.exists():
        # Si no hay servicios, crear uno por defecto con la descripcion de la factura
        servicios_qs = [{
            'id': '-',
            'descripcion': factura.descripcion or 'Consulta medica',
            'doctor': str(doctor) if doctor else 'N/A',
            'iva': 'General (16%)',
            'precio': factura.total
        }]
    else:
        servicios = []
        for s in servicios_qs:
            servicios.append({
                'id': str(s.id_cita_servicio),
                'descripcion': s.nombre_servicio or (str(s.id_servicio_medico) if s.id_servicio_medico else 'Servicio'),
                'doctor': str(doctor) if doctor else 'N/A',
                'iva': 'General (16%)',
                'precio': s.precio_estimado
            })
        servicios_qs = servicios

    # Direccion formateada
    direccion_sede = ''
    if sede and sede.id_direccion:
        d = sede.id_direccion
        partes = []
        if d.direccion: partes.append(d.direccion)
        if d.id_ciudad: partes.append(str(d.id_ciudad))
        if d.id_municipio: partes.append(str(d.id_municipio))
        if d.id_estado: partes.append(str(d.id_estado))
        direccion_sede = ', '.join(partes)

    # Totales
    monto_abonado = pago.monto_pagar if pago else Decimal('0.00')
    saldo_restante = factura.total - monto_abonado if monto_abonado else factura.total
    base_imponible = factura.total - factura.impuesto if factura.impuesto else factura.subtotal
    monto_exento = Decimal('0.00')  # No hay campo separado; todo es base imponible por defecto

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=1.5*cm, leftMargin=1.5*cm,
                            topMargin=1.5*cm, bottomMargin=1.5*cm)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Heading1'],
                                 fontSize=20, textColor=colors.HexColor('#0070F3'),
                                 spaceAfter=4, alignment=1, fontName='Helvetica-Bold')
    subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'],
                                    fontSize=9, textColor=colors.HexColor('#64748B'),
                                    spaceAfter=12, alignment=1)
    section_style = ParagraphStyle('Section', parent=styles['Heading2'],
                                   fontSize=11, textColor=colors.HexColor('#1E293B'),
                                   spaceAfter=6, spaceBefore=12, fontName='Helvetica-Bold')
    label_style = ParagraphStyle('Label', parent=styles['Normal'],
                                 fontSize=9, textColor=colors.HexColor('#64748B'),
                                 spaceAfter=2)
    value_style = ParagraphStyle('Value', parent=styles['Normal'],
                                 fontSize=9, textColor=colors.HexColor('#1E293B'),
                                 spaceAfter=4)
    normal_style = styles['Normal']
    normal_style.fontSize = 9

    elements = []

    # ========== ENCABEZADO CLINICA ==========
    elements.append(Paragraph(str(cm_obj.nombre_cm).upper() if cm_obj else 'CENTRO MEDICO HEALTHY LIFE, C.A.', title_style))
    rif_text = f"RIF: {cm_obj.rif_cm}" if cm_obj and cm_obj.rif_cm else 'RIF: J-123456789'
    elements.append(Paragraph(rif_text, subtitle_style))

    # Info sede en tabla
    sede_data = [
        [Paragraph(f"<b>Sede:</b> {sede.nombre_sede if sede else 'Principal'}", normal_style),
         Paragraph(f"<b>Telefono:</b> {sede.telefono if sede else '—'}", normal_style)],
        [Paragraph(f"<b>Direccion:</b> {direccion_sede or '—'}", normal_style), '']
    ]
    sede_table = Table(sede_data, colWidths=[8*cm, 8*cm])
    sede_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
    ]))
    elements.append(sede_table)
    elements.append(Spacer(1, 0.3*cm))
    elements.append(HRFlowable(width='100%', thickness=1, color=colors.HexColor('#E2E8F0')))
    elements.append(Spacer(1, 0.3*cm))

    # ========== DATOS PACIENTE + DOCUMENTO (2 columnas) ==========
    col1_data = [
        [Paragraph('<b>DATOS DEL PACIENTE</b>', section_style)],
        [Paragraph(f"<b>Cedula/RIF:</b> {paciente.cedula if paciente and hasattr(paciente, 'cedula') else '—'}", normal_style)],
        [Paragraph(f"<b>Nombre:</b> {str(paciente) if paciente else '—'}", normal_style)],
        [Paragraph('<b>Tipo paciente:</b> Regular', normal_style)],
    ]

    col2_data = [
        [Paragraph('<b>DOCUMENTO DE PAGO</b>', section_style)],
        [Paragraph(f"<b>Tipo:</b> COMPROBANTE DE PAGO", normal_style)],
        [Paragraph(f"<b>Nº Factura:</b> {factura.numero}", normal_style)],
        [Paragraph(f"<b>ID Cita:</b> {cita.id_citas}", normal_style)],
        [Paragraph(f"<b>Fecha:</b> {factura.fecha_emision.strftime('%d/%m/%Y')}", normal_style)],
        [Paragraph(f"<b>Hora:</b> {factura.fecha_emision.strftime('%H:%M')}", normal_style)],
    ]

    doc_table = Table([[Table(col1_data, colWidths=[8*cm]), Table(col2_data, colWidths=[8*cm])]],
                      colWidths=[8*cm, 8*cm])
    doc_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(doc_table)
    elements.append(Spacer(1, 0.3*cm))

    # ========== SERVICIOS PRESTADOS ==========
    elements.append(Paragraph('<b>SERVICIOS PRESTADOS</b>', section_style))
    serv_data = [['ID', 'Descripcion', 'Doctor', 'Tipo IVA', 'Precio unitario']]
    for s in servicios_qs:
        serv_data.append([
            s['id'], s['descripcion'], s['doctor'], s['iva'], f"${s['precio']}"
        ])
    serv_table = Table(serv_data, colWidths=[1.5*cm, 7*cm, 3*cm, 2.5*cm, 2.5*cm])
    serv_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0070F3')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F7F9FC')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(serv_table)
    elements.append(Spacer(1, 0.3*cm))

    # ========== TOTALES (2 columnas: totales + detalles pago) ==========
    totales_data = [
        [Paragraph('<b>TOTALES DE LA TRANSACCION</b>', section_style)],
        [Paragraph(f"<b>Monto exento:</b> ${monto_exento}", normal_style)],
        [Paragraph(f"<b>Base imponible IVA:</b> ${base_imponible}", normal_style)],
        [Paragraph(f"<b>Monto IVA (16%):</b> ${factura.impuesto}", normal_style)],
        [Paragraph(f"<b>Total a pagar:</b> ${factura.total}", ParagraphStyle('Total', parent=normal_style, fontSize=11, textColor=colors.HexColor('#1E293B'), fontName='Helvetica-Bold'))],
        [Paragraph(f"<b>Abonado (adelanto):</b> ${monto_abonado}", normal_style)],
        [Paragraph(f"<b>Saldo restante:</b> ${saldo_restante}", normal_style)],
        [Paragraph(f"<b>Cantidad de servicios:</b> {len(servicios_qs)}", normal_style)],
    ]

    metodo = pago.metodo_pago if pago else '—'
    ref = pago.referencia_pago if pago else '—'
    pago_data = [
        [Paragraph('<b>DETALLES DEL PAGO</b>', section_style)],
        [Paragraph(f"<b>Metodo de pago:</b> {metodo}", normal_style)],
        [Paragraph(f"<b>Banco origen:</b> Banco de Venezuela", normal_style)],
        [Paragraph(f"<b>Referencia:</b> {ref}", normal_style)],
    ]

    totales_table = Table([[Table(totales_data, colWidths=[8*cm]), Table(pago_data, colWidths=[8*cm])]],
                          colWidths=[8*cm, 8*cm])
    totales_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(totales_table)
    elements.append(Spacer(1, 0.5*cm))

    # ========== ESTADO Y FOOTER ==========
    estado_color = {
        'pagada': colors.HexColor('#059669'),
        'emitida': colors.HexColor('#0070F3'),
        'anulada': colors.HexColor('#DC2626'),
    }.get(factura.estado, colors.HexColor('#64748B'))
    elements.append(Paragraph(f"<b>ESTADO:</b> {factura.get_estado_display().upper()}",
                              ParagraphStyle('Estado', parent=normal_style, fontSize=12, textColor=estado_color, fontName='Helvetica-Bold')))

    if factura.estado == 'anulada':
        elements.append(Spacer(1, 0.5*cm))
        elements.append(Paragraph('*** DOCUMENTO ANULADO ***',
                                  ParagraphStyle('Anulada', parent=normal_style, fontSize=24, textColor=colors.HexColor('#DC2626'),
                                                 alignment=1, fontName='Helvetica-Bold')))

    elements.append(Spacer(1, 1*cm))
    elements.append(HRFlowable(width='100%', thickness=0.5, color=colors.HexColor('#E2E8F0')))
    elements.append(Paragraph('Healthy Life - Clinica medica | Gracias por confiar en nosotros',
                              ParagraphStyle('Footer', parent=normal_style, fontSize=8, textColor=colors.HexColor('#94A3B8'), alignment=1)))

    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(content_type='application/pdf')
    filename = f"factura-{factura.numero}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.write(pdf)
    return response


@login_required
def receta_pdf(request, cita_id):
    """Genera y descarga la receta medica en PDF con datos reales."""
    from io import BytesIO
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
    from citas.models import Recipe

    cita = get_object_or_404(
        Cita.objects.select_related('id_doctor', 'id_paciente', 'id_sede', 'id_especialidades'),
        id_citas=cita_id,
    )
    receta = (
        Recipe.objects.select_related(
            'id_doctor', 'id_paciente', 'id_sede',
            'id_Recipe_diagnostico', 'id_Recipe_tratamiento',
            'id_Recipe_reposo', 'id_Recipe_medicamentos_especiales',
            'id_Recipe_estudios', 'id_Recipes_ordenes_medicas',
        )
        .filter(id_cita__id_citas=cita_id)
        .first()
    )
    consulta = None
    try:
        consulta = cita.consulta_medica
    except ConsultaMedica.DoesNotExist:
        pass
    if not receta and not consulta:
        messages.error(request, 'No hay receta disponible para descargar.')
        return redirect('detalle_cita', cita_id=cita_id)

    # Verificar propiedad si es paciente
    if hasattr(request.user, 'id_user_paciente'):
        paciente = PacienteDatosPersonales.objects.filter(id_user_paciente=request.user).first()
        if paciente and cita.id_paciente != paciente:
            return HttpResponseForbidden('No tienes permiso para descargar esta receta.')

    paciente = (receta.id_paciente if receta else None) or cita.id_paciente
    doctor = (receta.id_doctor if receta else None) or cita.id_doctor
    sede = (receta.id_sede if receta else None) or cita.id_sede
    especialidad = cita.id_especialidades
    if not especialidad and doctor and doctor.id_especialidad_doctor:
        especialidad = Especialidad.objects.filter(id_especialidad=doctor.id_especialidad_doctor).first()

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Heading1'],
                                   fontSize=20, textColor=colors.HexColor('#0070F3'),
                                   spaceAfter=4, alignment=1, fontName='Helvetica-Bold')
    subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'],
                                    fontSize=9, textColor=colors.HexColor('#64748B'),
                                    spaceAfter=12, alignment=1)
    section_style = ParagraphStyle('Section', parent=styles['Heading2'],
                                   fontSize=11, textColor=colors.HexColor('#1E293B'),
                                   spaceAfter=6, spaceBefore=12, fontName='Helvetica-Bold')
    normal_style = styles['Normal']
    normal_style.fontSize = 9

    elements = []

    # Header
    elements.append(Paragraph('HEALTHY LIFE - RECETA MEDICA', title_style))
    elements.append(Paragraph(f"Sede: {sede.nombre_sede if sede else 'Principal'}", subtitle_style))
    elements.append(Spacer(1, 0.2*cm))
    elements.append(HRFlowable(width='100%', thickness=1, color=colors.HexColor('#E2E8F0')))
    elements.append(Spacer(1, 0.3*cm))

    # Paciente + Doctor (2 columnas)
    col1 = [
        [Paragraph('<b>PACIENTE</b>', section_style)],
        [Paragraph(f"<b>Nombre:</b> {str(paciente) if paciente else '—'}", normal_style)],
        [Paragraph(f"<b>Cedula:</b> {paciente.cedula if paciente else '—'}", normal_style)],
        [Paragraph(f"<b>Telefono:</b> {paciente.telefono if paciente else '—'}", normal_style)],
    ]
    fecha_emision = None
    if receta and receta.fecha_emision:
        fecha_emision = receta.fecha_emision
    elif consulta and consulta.fecha_inicio:
        fecha_emision = consulta.fecha_inicio

    col2 = [
        [Paragraph('<b>MEDICO</b>', section_style)],
        [Paragraph(f"<b>Nombre:</b> {str(doctor) if doctor else '—'}", normal_style)],
        [Paragraph(f"<b>Especialidad:</b> {especialidad.tipo_especialidad if especialidad else 'Medicina General'}", normal_style)],
        [Paragraph(f"<b>Fecha:</b> {fecha_emision.strftime('%d/%m/%Y %H:%M') if fecha_emision else '—'}", normal_style)],
    ]
    elements.append(Table([[Table(col1, colWidths=[8*cm]), Table(col2, colWidths=[8*cm])]],
                          colWidths=[8*cm, 8*cm],
                          style=TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')])))
    elements.append(Spacer(1, 0.3*cm))

    def add_section(title, content, bg=colors.HexColor('#F7F9FC')):
        if not content:
            return
        elements.append(Paragraph(f'<b>{title.upper()}</b>', section_style))
        data = [[Paragraph(content.replace('\n', '<br/>'), normal_style)]]
        t = Table(data, colWidths=[16*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), bg),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 0.2*cm))

    # Secciones: usar Recipe preferentemente, ConsultaMedica como fallback
    diag = None
    if receta and receta.id_Recipe_diagnostico and receta.id_Recipe_diagnostico.diagnostico:
        diag = receta.id_Recipe_diagnostico.diagnostico
    elif consulta and consulta.diagnostico:
        diag = consulta.diagnostico
    if diag:
        add_section('Diagnostico', diag)

    trat = None
    if receta and receta.id_Recipe_tratamiento and receta.id_Recipe_tratamiento.tratamiento_necesario:
        trat = receta.id_Recipe_tratamiento.tratamiento_necesario
    elif consulta and consulta.plan_tratamiento:
        trat = consulta.plan_tratamiento
    if trat:
        add_section('Tratamiento / Medicamentos', trat)

    meds = None
    if receta and receta.id_Recipe_medicamentos_especiales and receta.id_Recipe_medicamentos_especiales.medicamentos_especiales:
        meds = receta.id_Recipe_medicamentos_especiales.medicamentos_especiales
    elif consulta and consulta.medicamentos:
        meds = consulta.medicamentos
    if meds:
        add_section('Medicamentos especiales / Controlados', meds, bg=colors.HexColor('#FFFBEB'))

    est = None
    if receta and receta.id_Recipe_estudios and receta.id_Recipe_estudios.estudios_realizar:
        est = receta.id_Recipe_estudios.estudios_realizar
    elif consulta and consulta.estudios:
        est = consulta.estudios
    if est:
        add_section('Estudios y examenes', est)

    obs = None
    if receta and receta.id_Recipes_ordenes_medicas and receta.id_Recipes_ordenes_medicas.ordenes_medicas:
        obs = receta.id_Recipes_ordenes_medicas.ordenes_medicas
    elif consulta and consulta.observaciones:
        obs = consulta.observaciones
    if obs:
        add_section('Ordenes medicas y observaciones', obs)

    rep = None
    if receta and receta.id_Recipe_reposo and receta.id_Recipe_reposo.reposo:
        rep = receta.id_Recipe_reposo.reposo
    elif consulta and consulta.reposo:
        rep = consulta.reposo
    if rep:
        add_section('Indicacion de reposo', rep, bg=colors.HexColor('#F0FDF4'))

    # Footer
    elements.append(Spacer(1, 0.5*cm))
    elements.append(HRFlowable(width='100%', thickness=0.5, color=colors.HexColor('#E2E8F0')))
    elements.append(Paragraph('Healthy Life - Clinica medica | Esta receta tiene validez de 30 dias a partir de su emision.',
                              ParagraphStyle('Footer', parent=normal_style, fontSize=8, textColor=colors.HexColor('#94A3B8'), alignment=1)))
    id_firma = f'HL-{receta.id_recipes}-{fecha_emision.strftime("%Y%m%d%H%M%S")}' if receta and fecha_emision else f'HL-CITA-{cita_id}-{fecha_emision.strftime("%Y%m%d%H%M%S") if fecha_emision else ""}'
    elements.append(Paragraph(f'ID de firma: {id_firma}',
                              ParagraphStyle('Firma', parent=normal_style, fontSize=8, textColor=colors.HexColor('#64748B'), alignment=1)))

    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(content_type='application/pdf')
    filename = f"receta-{receta.id_recipes if receta else cita_id}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.write(pdf)
    return response


# ─── Facturación global (recepcionista / gerente) ─────────────────────────────

@login_required(login_url='/login/recepcionista/')
@rol_requerido('recepcionista', 'gerente')
def gestionar_facturas(request):
    """Lista global de facturas con filtros por estado, fecha y búsqueda de paciente."""
    qs = Factura.objects.select_related(
        'id_cita__id_paciente', 'id_cita__id_doctor', 'id_cita__id_sede'
    ).order_by('-fecha_emision')

    # Filtros
    estado  = request.GET.get('estado', '').strip()
    fecha_desde = request.GET.get('fecha_desde', '').strip()
    fecha_hasta = request.GET.get('fecha_hasta', '').strip()
    busqueda    = request.GET.get('q', '').strip()

    if estado:
        qs = qs.filter(estado=estado)
    if fecha_desde:
        qs = qs.filter(fecha_emision__date__gte=fecha_desde)
    if fecha_hasta:
        qs = qs.filter(fecha_emision__date__lte=fecha_hasta)
    if busqueda:
        qs = qs.filter(
            Q(numero__icontains=busqueda) |
            Q(id_cita__id_paciente__nombre_1__icontains=busqueda) |
            Q(id_cita__id_paciente__apellido_1__icontains=busqueda)
        )

    paginator = Paginator(qs, 20)
    page_obj  = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'citas/gestionar_facturas.html', {
        'page_obj':       page_obj,
        'estados_choices': Factura.ESTADOS,
        'estado_actual':  estado,
        'fecha_desde':    fecha_desde,
        'fecha_hasta':    fecha_hasta,
        'busqueda':       busqueda,
    })


@login_required(login_url='/login/recepcionista/')
@rol_requerido('recepcionista', 'gerente')
def facturas_recepcionista(request):
    """Lista de citas pagadas con datos de facturación para recepcionista."""
    # Estados que indican que la cita fue pagada
    estados_pagados = [
        Cita.ESTADO_PAGADA_ADELANTO,
        Cita.ESTADO_ATENDIDA,
    ]

    qs = Cita.objects.filter(
        estado__in=estados_pagados,
        id_pago_cita__isnull=False,
    ).select_related(
        'id_paciente',
        'id_doctor',
        'id_pago_cita',
        'id_pago_cita__id_factura',
        'id_sede',
    ).prefetch_related(
        'factura',
    ).order_by('-fecha_consulta')

    # Filtros
    fecha_desde = request.GET.get('fecha_desde', '').strip()
    fecha_hasta = request.GET.get('fecha_hasta', '').strip()
    busqueda    = request.GET.get('q', '').strip()

    if fecha_desde:
        qs = qs.filter(fecha_consulta__date__gte=fecha_desde)
    if fecha_hasta:
        qs = qs.filter(fecha_consulta__date__lte=fecha_hasta)
    if busqueda:
        qs = qs.filter(
            Q(id_paciente__nombre_1__icontains=busqueda) |
            Q(id_paciente__apellido_1__icontains=busqueda) |
            Q(id_doctor__nombre_1__icontains=busqueda) |
            Q(id_doctor__apellido_1__icontains=busqueda)
        )

    paginator = Paginator(qs, 20)
    page_obj  = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'citas/facturas_recepcionista.html', {
        'page_obj':    page_obj,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'busqueda':    busqueda,
    })


# ─── Reportes (gerente / admin) ───────────────────────────────────────────────

@login_required(login_url='/login/gerente/')
@rol_requerido('gerente', 'admin')
def reporte_atencion_diaria(request):
    """Reporte diario de personas atendidas."""
    from datetime import datetime
    
    # Obtener parámetros de filtro
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    id_sede = request.GET.get('id_sede')
    
    # Valores por defecto: hoy
    hoy = timezone.now().date()
    if not fecha_inicio:
        fecha_inicio = hoy
    else:
        fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
    
    if not fecha_fin:
        fecha_fin = hoy
    else:
        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
    
    # Convertir id_sede a int si está presente
    if id_sede:
        id_sede = int(id_sede)
    
    # Generar reporte
    datos = ReportesService.reporte_diario_atencion(fecha_inicio, fecha_fin, id_sede)
    
    # Obtener sedes para el filtro
    sedes = ReportesService.obtener_sedes()
    
    return render(request, 'citas/reporte_atencion_diaria.html', {
        'datos': datos,
        'sedes': sedes,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'id_sede': id_sede,
    })


@login_required(login_url='/login/gerente/')
@rol_requerido('gerente', 'admin')
def reporte_caja(request):
    """Reporte de caja (ingresos por pagos del día o período)."""
    from datetime import datetime
    
    # Obtener parámetros de filtro
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    id_sede = request.GET.get('id_sede')
    
    # Valores por defecto: hoy
    hoy = timezone.now().date()
    if not fecha_inicio:
        fecha_inicio = hoy
    else:
        fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
    
    if not fecha_fin:
        fecha_fin = hoy
    else:
        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
    
    # Convertir id_sede a int si está presente
    if id_sede:
        id_sede = int(id_sede)
    
    # Generar reporte
    datos = ReportesService.reporte_caja(fecha_inicio, fecha_fin, id_sede)
    
    # Obtener sedes para el filtro
    sedes = ReportesService.obtener_sedes()
    
    return render(request, 'citas/reporte_caja.html', {
        'datos': datos,
        'sedes': sedes,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'id_sede': id_sede,
    })


@login_required(login_url='/login/gerente/')
@rol_requerido('gerente', 'admin')
def reporte_balance(request):
    """Reporte de balance (sumatoria de costos generados)."""
    from datetime import datetime
    
    # Obtener parámetros de filtro
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    id_sede = request.GET.get('id_sede')
    
    # Valores por defecto: mes actual
    hoy = timezone.now().date()
    if not fecha_inicio:
        fecha_inicio = hoy.replace(day=1)
    else:
        fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
    
    if not fecha_fin:
        fecha_fin = hoy
    else:
        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
    
    # Convertir id_sede a int si está presente
    if id_sede:
        id_sede = int(id_sede)
    
    # Generar reporte
    datos = ReportesService.reporte_balance(fecha_inicio, fecha_fin, id_sede)
    
    # Obtener sedes para el filtro
    sedes = ReportesService.obtener_sedes()
    
    return render(request, 'citas/reporte_balance.html', {
        'datos': datos,
        'sedes': sedes,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'id_sede': id_sede,
    })


@login_required(login_url='/login/gerente/')
@rol_requerido('gerente', 'admin')
def reporte_pagos_medicos(request):
    """Reporte de pagos a médicos por consultas atendidas."""
    from datetime import datetime
    
    # Obtener parámetros de filtro
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    id_sede = request.GET.get('id_sede')
    id_doctor = request.GET.get('id_doctor')
    
    # Valores por defecto: mes actual
    hoy = timezone.now().date()
    if not fecha_inicio:
        fecha_inicio = hoy.replace(day=1)
    else:
        fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
    
    if not fecha_fin:
        fecha_fin = hoy
    else:
        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
    
    # Convertir ids a int si están presentes
    if id_sede:
        id_sede = int(id_sede)
    if id_doctor:
        id_doctor = int(id_doctor)
    
    # Generar reporte
    datos = ReportesService.reporte_pagos_medicos(fecha_inicio, fecha_fin, id_sede, id_doctor)
    
    # Obtener sedes y médicos para los filtros
    sedes = ReportesService.obtener_sedes()
    medicos = ReportesService.obtener_medicos(id_sede)
    
    return render(request, 'citas/reporte_pagos_medicos.html', {
        'datos': datos,
        'sedes': sedes,
        'medicos': medicos,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'id_sede': id_sede,
        'id_doctor': id_doctor,
    })


@login_required(login_url='/login/paciente/')
@rol_requerido('paciente')
def pagar_saldo(request, cita_id):
    """Paciente paga el saldo pendiente de una cita atendida."""
    cita = get_object_or_404(Cita, pk=cita_id)

    # Verificar que el paciente sea dueño de la cita
    paciente = PacienteDatosPersonales.objects.filter(id_user_paciente=request.user).first()
    if not paciente or cita.id_paciente_id != paciente.id_datos_paciente:
        messages.error(request, "No tienes permiso para realizar esta acción.")
        return redirect('dashboard_paciente')

    # Verificar que la cita esté atendida
    if cita.estado != Cita.ESTADO_ATENDIDA:
        messages.error(request, "Solo se puede pagar el saldo de citas ya atendidas.")
        return redirect('dashboard_paciente')

    # Verificar que exista factura con saldo pendiente
    try:
        factura = cita.factura
    except Factura.DoesNotExist:
        messages.error(request, "No existe factura asociada a esta cita.")
        return redirect('dashboard_paciente')

    if factura.estado == Factura.ESTADO_PAGADA:
        messages.info(request, "Esta factura ya está completamente pagada.")
        return redirect('dashboard_paciente')

    pago = getattr(cita, 'id_pago_cita', None)
    if not pago:
        messages.error(request, "No existe pago asociado a esta cita.")
        return redirect('dashboard_paciente')

    # Calcular saldo pendiente
    monto_pagado = Decimal(str(pago.monto_pagar or 0))
    monto_total = Decimal(str(factura.total or 0))
    saldo = monto_total - monto_pagado

    if saldo <= 0:
        messages.info(request, "No hay saldo pendiente por pagar.")
        return redirect('dashboard_paciente')

    if request.method == 'POST':
        # Confirmar pago del saldo
        try:
            with transaction.atomic():
                # Actualizar monto pagado
                pago.monto_pagar = monto_total
                pago.estado_pago = PagoCita.ESTADO_APROBADO
                pago.save(update_fields=['monto_pagar', 'estado_pago'])

                # Actualizar factura a pagada
                factura.estado = Factura.ESTADO_PAGADA
                factura.save(update_fields=['estado'])

            messages.success(
                request,
                f"✅ Saldo de ${saldo:.2f} pagado exitosamente. Tu factura #{factura.numero} está saldada."
            )
            return redirect('dashboard_paciente')
        except Exception as e:
            messages.error(request, f"Error al procesar el pago: {e}")
            return redirect('dashboard_paciente')

    # Servicios realizados para desglose
    servicios = []
    try:
        consulta = cita.consulta_medica
        servicios = list(consulta.servicios_realizados.all())
    except (AttributeError, ConsultaMedica.DoesNotExist):
        pass

    return render(request, 'citas/pagar_saldo.html', {
        'cita': cita,
        'factura': factura,
        'pago': pago,
        'monto_pagado': monto_pagado,
        'monto_total': monto_total,
        'saldo': saldo,
        'servicios': servicios,
    })


# ─── Catálogo de Servicios Médicos (Fase 6) ──────────────────────────────────

@login_required(login_url='/login/medico/')
@rol_requerido('medico')
def servicios_doctor(request):
    """Listado de servicios médicos del doctor autenticado."""
    from usuarios.authentication import CustomAuthBackend
    datos_medico = CustomAuthBackend().get_datos_personales(request.user)
    if not datos_medico:
        messages.error(request, "No se encontró tu perfil de médico.")
        return redirect('dashboard_medico')

    servicios = ServicioMedico.objects.filter(
        id_doctor=datos_medico,
        activo=True,
    ).order_by('nombre')

    return render(request, 'citas/servicios_doctor.html', {
        'servicios': servicios,
    })


@login_required(login_url='/login/medico/')
@rol_requerido('medico')
def servicio_crear(request):
    """Crear un nuevo servicio médico para el doctor."""
    from usuarios.authentication import CustomAuthBackend
    datos_medico = CustomAuthBackend().get_datos_personales(request.user)
    if not datos_medico:
        messages.error(request, "No se encontró tu perfil de médico.")
        return redirect('dashboard_medico')

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()
        precio_str = request.POST.get('precio', '').strip()

        if not nombre:
            messages.error(request, "El nombre del servicio es obligatorio.")
        else:
            try:
                precio = Decimal(precio_str) if precio_str else Decimal('0.00')
                ServicioMedico.objects.create(
                    nombre=nombre,
                    descripcion=descripcion or None,
                    precio=precio,
                    id_doctor=datos_medico,
                    activo=True,
                )
                messages.success(request, f"Servicio '{nombre}' creado exitosamente.")
                return redirect('servicios_doctor')
            except Exception as e:
                messages.error(request, f"Error al crear el servicio: {e}")

    return render(request, 'citas/servicio_form.html', {
        'titulo': 'Nuevo Servicio',
        'accion': 'Crear',
    })


@login_required(login_url='/login/medico/')
@rol_requerido('medico')
def servicio_editar(request, servicio_id):
    """Editar un servicio médico existente (solo si pertenece al doctor)."""
    from usuarios.authentication import CustomAuthBackend
    datos_medico = CustomAuthBackend().get_datos_personales(request.user)
    if not datos_medico:
        messages.error(request, "No se encontró tu perfil de médico.")
        return redirect('dashboard_medico')

    servicio = get_object_or_404(
        ServicioMedico,
        pk=servicio_id,
        id_doctor=datos_medico,
    )

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()
        precio_str = request.POST.get('precio', '').strip()

        if not nombre:
            messages.error(request, "El nombre del servicio es obligatorio.")
        else:
            try:
                servicio.nombre = nombre
                servicio.descripcion = descripcion or None
                servicio.precio = Decimal(precio_str) if precio_str else Decimal('0.00')
                servicio.save(update_fields=['nombre', 'descripcion', 'precio'])
                messages.success(request, f"Servicio '{nombre}' actualizado.")
                return redirect('servicios_doctor')
            except Exception as e:
                messages.error(request, f"Error al actualizar: {e}")

    return render(request, 'citas/servicio_form.html', {
        'titulo': 'Editar Servicio',
        'accion': 'Guardar',
        'servicio': servicio,
    })


@login_required(login_url='/login/medico/')
@rol_requerido('medico')
def servicio_toggle(request, servicio_id):
    """Activar o desactivar un servicio médico."""
    from usuarios.authentication import CustomAuthBackend
    datos_medico = CustomAuthBackend().get_datos_personales(request.user)
    if not datos_medico:
        messages.error(request, "No se encontró tu perfil de médico.")
        return redirect('dashboard_medico')

    servicio = get_object_or_404(
        ServicioMedico,
        pk=servicio_id,
        id_doctor=datos_medico,
    )
    servicio.activo = not servicio.activo
    servicio.save(update_fields=['activo'])
    estado = "activado" if servicio.activo else "desactivado"
    messages.success(request, f"Servicio '{servicio.nombre}' {estado}.")
    return redirect('servicios_doctor')


@login_required(login_url='/login/gerente/')
@rol_requerido('gerente')
def pagar_honorario_doctor(request):
    """Procesa el pago de un honorario médico pendiente y genera un comprobante PDF."""
    from io import BytesIO
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from django.utils import timezone
    from usuarios.models import UserAdmin

    user_id = request.session.get('_auth_user_id')
    if not user_id:
        messages.error(request, 'Acceso denegado.')
        return redirect('login_gerente')
    user = UserAdmin.objects.filter(id_user_admin=user_id).first()
    if not user or CustomAuthBackend().get_rol(user) != 'gerente':
        messages.error(request, 'Acceso denegado.')
        return redirect('login_gerente')
    sede = user.id_sede

    if request.method != 'POST':
        messages.error(request, 'Método no permitido.')
        return redirect('dashboard_gerente')

    id_honorario = request.POST.get('id_honorario')
    if not id_honorario:
        messages.error(request, 'ID de honorario no proporcionado.')
        return redirect('dashboard_gerente')

    try:
        honorario = HonorarioMedico.objects.select_related('id_doctor', 'id_cita', 'id_sede').get(
            id_honorario=id_honorario,
            estado_pago=HonorarioMedico.ESTADO_PENDIENTE,
            status=True,
        )
    except HonorarioMedico.DoesNotExist:
        messages.error(request, 'Honorario no encontrado o ya fue pagado.')
        return redirect('dashboard_gerente')

    now = timezone.now()
    metodo_pago = request.POST.get('metodo_pago', 'Transferencia')
    referencia_pago = request.POST.get('referencia_pago', f'PAGO-{now.strftime("%Y%m%d%H%M%S")}')

    # Actualizar honorario
    honorario.estado_pago = HonorarioMedico.ESTADO_PAGADO
    honorario.fecha_pago = now
    honorario.metodo_pago = metodo_pago
    honorario.referencia_pago = referencia_pago
    honorario.save()

    # Registrar egreso en caja
    doctor_nombre = f"{honorario.id_doctor.nombre_1 or ''} {honorario.id_doctor.apellido_1 or ''}".strip() or 'Médico'
    MovimientoCaja.objects.create(
        tipo_movimiento=MovimientoCaja.TIPO_EGRESO,
        monto=honorario.monto_honorario,
        concepto=f'Pago honorario médico - Dr. {doctor_nombre}',
        metodo_pago=metodo_pago,
        id_sede=honorario.id_sede,
        id_usuario_registro=user.id_user_admin if user else None,
        observaciones=f'Honorario #{honorario.id_honorario} | Ref: {referencia_pago}',
    )

    # Generar comprobante PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Heading1'],
                                   fontSize=18, textColor=colors.HexColor('#0070F3'),
                                   spaceAfter=6, alignment=1)
    normal_style = ParagraphStyle('Normal', parent=styles['Normal'],
                                    fontSize=10, textColor=colors.HexColor('#334155'),
                                    spaceAfter=4)
    label_style = ParagraphStyle('Label', parent=styles['Normal'],
                                 fontSize=9, textColor=colors.HexColor('#64748B'),
                                 spaceAfter=2)
    value_style = ParagraphStyle('Value', parent=styles['Normal'],
                                fontSize=11, textColor=colors.HexColor('#0F172A'),
                                spaceAfter=6)

    elements = []
    elements.append(Paragraph('COMPROBANTE DE PAGO A MÉDICO', title_style))
    elements.append(Spacer(1, 0.3*cm))
    elements.append(Paragraph(f'Fecha de emisión: {now.strftime("%d/%m/%Y %H:%M")}', normal_style))
    elements.append(Paragraph(f'Referencia: <b>{referencia_pago}</b>', normal_style))
    elements.append(Spacer(1, 0.4*cm))

    data = [
        [Paragraph('<b>Doctor</b>', label_style), Paragraph(doctor_nombre, value_style)],
        [Paragraph('<b>Especialidad</b>', label_style), Paragraph(str(getattr(honorario.id_doctor, 'especialidad', None) or '—'), value_style)],
        [Paragraph('<b>Monto del honorario</b>', label_style), Paragraph(f"${honorario.monto_honorario}", value_style)],
        [Paragraph('<b>Porcentaje comisión</b>', label_style), Paragraph(f"{honorario.porcentaje_comision or 40}%", value_style)],
        [Paragraph('<b>Fecha de atención</b>', label_style), Paragraph((honorario.fecha_atencion.strftime('%d/%m/%Y %H:%M') if honorario.fecha_atencion else '—'), value_style)],
        [Paragraph('<b>Método de pago</b>', label_style), Paragraph(metodo_pago, value_style)],
        [Paragraph('<b>Estado</b>', label_style), Paragraph('PAGADO', value_style)],
    ]
    t = Table(data, colWidths=[5*cm, 10*cm])
    t.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LINEABOVE', (0, 0), (-1, 0), 0.5, colors.HexColor('#E2E8F0')),
        ('LINEBELOW', (0, -1), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 0.6*cm))

    elements.append(Paragraph(f'<b>Total pagado:</b> ${honorario.monto_honorario}', ParagraphStyle('Total', parent=styles['Normal'],
                               fontSize=14, textColor=colors.HexColor('#059669'), spaceAfter=8)))
    elements.append(Paragraph('Este documento certifica que el honorario fue pagado y registrado en el sistema.', normal_style))

    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(content_type='application/pdf')
    filename = f"comprobante_pago_medico_{honorario.id_honorario}_{now.strftime('%Y%m%d')}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.write(pdf)
    return response
