from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_GET
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from usuarios.decorators import rol_requerido
from usuarios.models import PacienteDatosPersonales, Doctor, PacienteEspecial
from .models import (
    Cita, PagoCita, Sede, Especialidad, Horario,
    ServicioEspecialidad, EspecialidadDoctor, Consultorio, ConsultaMedica, Factura,
    MovimientoCaja, HonorarioMedico, ServicioMedico, ConsultaServicio, CitaServicioSolicitado,
)
from .services import CitaService, FacturacionService
from .reportes import ReportesService
from .forms import ConsultaMedicaForm, RegistrarAdelantoForm

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

    if request.method == 'POST':
        cedula = request.POST.get('cedula', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        banco_emisor = request.POST.get('banco_emisor', '').strip()
        referencia = request.POST.get('referencia', '').strip()

        import re
        errores = []
        if not all([cedula, telefono, banco_emisor, referencia]):
            errores.append("Todos los campos de datos bancarios son obligatorios.")
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
                    servicios_seleccionados=reserva.get('servicios_seleccionados', []),
                )
                del request.session['reserva_cita']
                request.session.modified = True
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
    })


@login_required(login_url='/login/medico/')
@rol_requerido('medico')
def citas_pendientes_medico(request):
    """Citas pendientes y asignadas para el médico autenticado.

    Pendientes  → activas, pago aún NO aprobado por recepcionista.
    Asignadas   → activas, pago YA aprobado por recepcionista (listas para consulta).

    Se eliminó el filtro de fecha porque excluía citas pasadas y usaba
    datetime.now() sin zona horaria (bug de TZ con USE_TZ=True).
    """
    try:
        citas_pendientes, citas_asignadas, datos_medico = CitaService.listar_citas_medico(request.user)
    except PermissionError as e:
        messages.error(request, str(e))
        return redirect('home')

    return render(request, 'citas/citas_pendientes_medico.html', {
        'citas_pendientes': citas_pendientes,
        'citas_asignadas':  citas_asignadas,
        'datos_medico':     datos_medico,
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
    hoy = date.today()
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
                    'es_pasado_o_hoy': dia_fecha <= hoy,
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


@rol_requerido('recepcionista', 'gerente')
def gestionar_citas(request):
    """Recepcionista/gerente: solicitudes nuevas, pagos por confirmar y citas aceptadas."""
    _base = Cita.objects.select_related(
        'id_paciente', 'id_doctor', 'id_sede',
        'id_especialidades', 'id_servicio_especialidad', 'id_pago_cita',
        'reserva_pago',
    ).order_by('-fecha_consulta')

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
    })


@rol_requerido('recepcionista', 'gerente')
def confirmar_pago(request, cita_id):
    """Recepcionista confirma que el pago del paciente fue verificado → estado='confirmada'."""
    if request.method == 'POST':
        cita = get_object_or_404(
            Cita.objects.select_related('id_pago_cita'), id_citas=cita_id
        )
        try:
            CitaService.confirmar_pago(request.user, cita)
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
    """Calendario mensual de citas del médico autenticado."""
    from usuarios.authentication import CustomAuthBackend
    from calendar import Calendar
    from django.utils.timezone import localtime
    datos_medico = CustomAuthBackend().get_datos_personales(request.user)

    hoy = date.today()
    try:
        año = int(request.GET.get('año', hoy.year))
        mes = int(request.GET.get('mes', hoy.month))
    except ValueError:
        año, mes = hoy.year, hoy.month
    if mes < 1:
        mes, año = 12, año - 1
    elif mes > 12:
        mes, año = 1, año + 1

    # Rango del mes
    inicio_mes = date(año, mes, 1)
    if mes == 12:
        fin_mes = date(año + 1, 1, 1)
    else:
        fin_mes = date(año, mes + 1, 1)

    # Citas del médico en este mes (excluir canceladas/rechazadas/no_asistio)
    citas_por_dia = {}
    if datos_medico:
        citas = Cita.objects.filter(
            id_doctor=datos_medico,
            fecha_consulta__date__gte=inicio_mes,
            fecha_consulta__date__lt=fin_mes,
            status=True,
        ).exclude(estado__in=[
            Cita.ESTADO_CANCELADA, Cita.ESTADO_RECHAZADA, Cita.ESTADO_NO_ASISTIO
        ]).select_related('id_paciente', 'id_especialidades').order_by('fecha_consulta')

        for c in citas:
            dia = localtime(c.fecha_consulta).day
            if dia not in citas_por_dia:
                citas_por_dia[dia] = []
            citas_por_dia[dia].append(c)

    # Calendario
    cal = Calendar(firstweekday=0)
    semanas = cal.monthdayscalendar(año, mes)

    mes_nombres = [
        'Enero','Febrero','Marzo','Abril','Mayo','Junio',
        'Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre'
    ]

    total_citas = sum(len(v) for v in citas_por_dia.values())
    dias_con_citas = len(citas_por_dia)
    promedio_citas = round(total_citas / dias_con_citas, 1) if dias_con_citas > 0 else 0

    return render(request, 'citas/calendario_citas.html', {
        'calendar':       semanas,
        'citas_por_dia':  citas_por_dia,
        'total_citas':    total_citas,
        'promedio_citas': promedio_citas,
        'month_name':     mes_nombres[mes - 1],
        'year':           año,
        'today':          hoy.day if hoy.year == año and hoy.month == mes else None,
        'hoy':            hoy.isoformat(),
        'prev_month':     mes - 1 if mes > 1 else 12,
        'prev_year':      año if mes > 1 else año - 1,
        'next_month':     mes + 1 if mes < 12 else 1,
        'next_year':      año if mes < 12 else año + 1,
        'datos_medico':   datos_medico,
    })


@rol_requerido('recepcionista', 'gerente')
def aprobar_cita(request, cita_id):
    """Recepcionista aprueba la solicitud de cita → estado='aprobada'."""
    if request.method == 'POST':
        cita = get_object_or_404(Cita, id_citas=cita_id)
        try:
            CitaService.aprobar_cita(request.user, cita)
            messages.success(request, f"✅ Cita #{cita_id} aprobada correctamente.")
        except PermissionError as e:
            messages.error(request, str(e))
        except ValueError as e:
            messages.error(request, str(e))
    return redirect('gestionar_citas')


@rol_requerido('recepcionista', 'gerente')
def rechazar_cita(request, cita_id):
    """Rechazar cita → estado='rechazada'."""
    cita = get_object_or_404(Cita, id_citas=cita_id)
    if request.method == 'POST':
        try:
            CitaService.transicionar(cita, Cita.ESTADO_RECHAZADA)
            cita.status = False
            cita.save(update_fields=['status'])
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
            messages.info(request, f"Cita #{cita_id} cancelada correctamente.")
        except ValueError as e:
            messages.error(request, str(e))
    return redirect('gestionar_citas')


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
        return JsonResponse({'fechas': []})
    try:
        año = int(request.GET.get('año', date.today().year))
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
    """Lista paginada de citas del paciente autenticado."""
    user = request.user
    paciente = PacienteDatosPersonales.objects.filter(id_user_paciente=user).first()

    citas_qs = Cita.objects.none()
    if paciente:
        citas_qs = Cita.objects.filter(id_paciente=paciente).select_related(
            'id_doctor', 'id_especialidades', 'id_sede', 'id_servicio_especialidad'
        ).order_by('-fecha_emision')

    estado_filtro = request.GET.get('estado', '')
    if estado_filtro == 'activa':
        citas_qs = citas_qs.filter(status=True)
    elif estado_filtro == 'cancelada':
        citas_qs = citas_qs.filter(status=False)

    paginator = Paginator(citas_qs, 10)
    page_obj  = paginator.get_page(request.GET.get('page', 1))

    estados_choices = [('activa', 'Activa'), ('cancelada', 'Cancelada')]
    return render(request, 'citas/mis_citas.html', {
        'page_obj':       page_obj,
        'estados_choices': estados_choices,
        'estado_actual':  estado_filtro,
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

    estados_choices = [
        ('pagado', 'Pagadas'),
        ('pendiente', 'Por pagar'),
        ('solicitada', 'En proceso'),
    ]
    return render(request, 'citas/mis_facturas.html', {
        'page_obj':       page_obj,
        'estados_choices': estados_choices,
        'estado_actual':  estado_filtro,
    })


@login_required(login_url='/login/paciente/')
@rol_requerido('paciente')
def detalle_cita(request, cita_id):
    """Detalle de una cita específica del paciente."""
    user = request.user
    paciente = PacienteDatosPersonales.objects.filter(id_user_paciente=user).first()
    cita = get_object_or_404(
        Cita.objects.select_related(
            'id_doctor', 'id_especialidades', 'id_sede',
            'id_servicio_especialidad', 'id_consultorio', 'id_pago_cita'
        ),
        id_citas=cita_id,
        id_paciente=paciente,
    )
    consulta = None
    try:
        consulta = cita.consulta_medica
    except ConsultaMedica.DoesNotExist:
        pass
    return render(request, 'citas/detalle_cita.html', {'cita': cita, 'consulta': consulta})


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
            messages.info(request, f"Cita #{cita_id} cancelada correctamente.")
        except ValueError as e:
            messages.warning(request, str(e))
        return redirect('mis_citas')
    return render(request, 'citas/cancelar_cita.html', {'cita': cita})


@login_required(login_url='/login/paciente/')
@rol_requerido('paciente')
def pagar_cita(request, cita_id):
    """Paciente registra el pago de una cita aprobada por la recepcionista."""
    user = request.user
    paciente = PacienteDatosPersonales.objects.filter(id_user_paciente=user).first()
    cita = get_object_or_404(
        Cita.objects.select_related('id_pago_cita'),
        id_citas=cita_id,
        id_paciente=paciente,
    )

    estados_pagables = [Cita.ESTADO_APROBADA, Cita.ESTADO_SOLICITADA]
    if cita.estado not in estados_pagables:
        messages.warning(request, "Esta cita no está disponible para pago.")
        return redirect('mis_citas')

    METODOS_PAGO = [
        ('transferencia', 'Transferencia bancaria'),
        ('tarjeta',       'Tarjeta de crédito/débito'),
        ('efectivo',      'Efectivo'),
        ('otro',          'Otro'),
    ]

    if request.method == 'POST':
        metodo    = request.POST.get('metodo_pago', '').strip()
        referencia = request.POST.get('referencia_pago', '').strip()
        if not metodo:
            messages.error(request, "Debes seleccionar un método de pago.")
        else:
            try:
                from django.db import transaction as _tx
                with _tx.atomic():
                    pago = cita.id_pago_cita
                    if pago:
                        pago.metodo_pago      = metodo
                        pago.referencia_pago  = referencia
                        pago.estado_pago      = PagoCita.ESTADO_PENDIENTE
                        pago.save(update_fields=['metodo_pago', 'referencia_pago', 'estado_pago'])

                    cita.estado = Cita.ESTADO_PAGO_PENDIENTE
                    cita.save(update_fields=['estado'])

                messages.success(
                    request,
                    "✅ Pago registrado. La recepcionista verificará y confirmará tu cita."
                )
                return redirect('mis_citas')
            except Exception as e:
                messages.error(request, f"Error al registrar el pago: {e}")

    return render(request, 'citas/pagar_cita.html', {
        'cita':         cita,
        'metodos_pago': METODOS_PAGO,
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

                messages.success(
                    request,
                    f"✅ Receta #{recipe.pk} generada exitosamente para "
                    f"{paciente.nombre_completo if paciente else 'el paciente'}."
                )
                return redirect('citas_pendientes_medico')

            except Exception as exc:
                messages.error(request, f"Error al guardar la receta: {exc}")
                print(f"ERROR realizar_receta cita_id={cita_id}: {exc}")
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
    cita = get_object_or_404(Cita, pk=cita_id)

    # Verificar que la cita pertenezca al médico autenticado
    if cita.id_doctor_id != datos_medico.pk:
        messages.error(request, "No puedes iniciar consulta de una cita que no te pertenece.")
        return redirect('citas_pendientes_medico')

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

            try:
                CitaService.cerrar_consulta(request.user, cita)
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
    })


@login_required(login_url='/login/medico/')
@rol_requerido('medico')
def cerrar_consulta(request, cita_id):
    """Médico cierra la consulta y marca la cita como atendida."""
    cita = get_object_or_404(Cita, pk=cita_id)
    consulta = get_object_or_404(ConsultaMedica, id_cita=cita)

    if consulta.estado == ConsultaMedica.ESTADO_CERRADA:
        messages.warning(request, 'Esta consulta ya está cerrada.')
        return redirect('iniciar_consulta', cita_id=cita_id)

    if request.method == 'POST':
        try:
            CitaService.cerrar_consulta(request.user, cita)
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
    })


# ─── Facturación ──────────────────────────────────────────────────────────

@login_required(login_url='/login/')
def detalle_factura(request, cita_id):
    """Devuelve o genera la factura de una cita con pago aprobado."""
    cita = get_object_or_404(Cita.objects.select_related('id_pago_cita'), pk=cita_id)
    try:
        factura = cita.factura
    except Factura.DoesNotExist:
        try:
            factura = FacturacionService.generar_factura_cita(cita)
        except ValueError as e:
            messages.error(request, str(e))
            return redirect('mis_citas')
    return render(request, 'citas/factura_detalle.html', {'factura': factura})


@login_required(login_url='/login/')
def factura_pdf(request, factura_id):
    """Genera y descarga la factura en PDF usando ReportLab."""
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4

    factura = get_object_or_404(Factura, pk=factura_id)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="factura-{factura.numero}.pdf"'

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    # Header verde
    p.setFillColorRGB(0.18, 0.49, 0.20)
    p.rect(0, height - 80, width, 80, fill=True, stroke=False)
    p.setFillColorRGB(1, 1, 1)
    p.setFont('Helvetica-Bold', 22)
    p.drawString(50, height - 48, 'FACTURA')
    p.setFont('Helvetica', 12)
    p.drawString(50, height - 66, str(factura.numero))

    # Datos
    p.setFillColorRGB(0, 0, 0)
    y = height - 115
    lineas = [
        ('Fecha de emisión:', factura.fecha_emision.strftime('%d/%m/%Y %H:%M')),
        ('Paciente:',        str(factura.id_cita.id_paciente)),
        ('Médico:',          str(factura.id_cita.id_doctor)),
        ('Servicio:',        factura.descripcion),
    ]
    for etiqueta, valor in lineas:
        p.setFont('Helvetica-Bold', 11)
        p.drawString(50, y, etiqueta)
        p.setFont('Helvetica', 11)
        p.drawString(200, y, valor)
        y -= 22

    # Montos
    y -= 15
    p.setFont('Helvetica-Bold', 11)
    p.drawString(50, y, 'Subtotal:');  p.setFont('Helvetica', 11); p.drawString(200, y, str(factura.subtotal)); y -= 20
    p.setFont('Helvetica-Bold', 11)
    p.drawString(50, y, 'Impuesto:'); p.setFont('Helvetica', 11); p.drawString(200, y, str(factura.impuesto)); y -= 20
    p.setFont('Helvetica-Bold', 14)
    p.drawString(50, y, 'TOTAL:');    p.drawString(200, y, str(factura.total))

    # Sello ANULADA
    if factura.estado == 'anulada':
        p.saveState()
        p.setFillColorRGB(0.8, 0, 0)
        p.setFont('Helvetica-Bold', 48)
        p.translate(width / 2, height / 2)
        p.rotate(35)
        p.drawCentredString(0, 0, 'ANULADA')
        p.restoreState()

    p.showPage()
    p.save()
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

    return render(request, 'citas/pagar_saldo.html', {
        'cita': cita,
        'factura': factura,
        'pago': pago,
        'monto_pagado': monto_pagado,
        'monto_total': monto_total,
        'saldo': saldo,
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
