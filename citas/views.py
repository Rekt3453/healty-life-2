from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import date, datetime, time, timedelta
from usuarios.decorators import rol_requerido
from usuarios.models import PacienteDatosPersonales, Doctor
from .models import (
    Cita, PagoCita, Sede, Especialidad, Horario,
    ServicioEspecialidad, EspecialidadDoctor, Consultorio,
)

@login_required(login_url='/login/paciente/')
@rol_requerido('paciente')
def solicitar_cita(request):
    """Flujo: Sede → Especialidad → Doctor → Fecha/Hora → Servicio → Motivo."""
    user = request.user
    paciente = PacienteDatosPersonales.objects.filter(id_user_paciente=user).first()

    if request.method == 'POST':
        sede_id         = request.POST.get('sede')
        especialidad_id = request.POST.get('especialidad')
        # Acepta 'doctor' o 'medico' (nombre alternativo usado en el template)
        doctor_id       = request.POST.get('doctor') or request.POST.get('medico')
        servicio_id     = request.POST.get('servicio') or None
        fecha           = request.POST.get('fecha')
        # Acepta 'hora' o 'hora_solicitada'
        hora            = request.POST.get('hora') or request.POST.get('hora_solicitada')
        motivo          = request.POST.get('motivo', '').strip()

        if not all([sede_id, especialidad_id, doctor_id, fecha, hora, motivo]):
            messages.error(request, "Todos los campos obligatorios deben completarse.")
        else:
            try:
                fecha_hora = datetime.strptime(f"{fecha} {hora}", "%Y-%m-%d %H:%M")

                # Validación: no se permiten citas en fechas/horas pasadas
                if fecha_hora < datetime.now():
                    messages.error(
                        request,
                        "No puedes solicitar una cita en una fecha/hora que ya ha pasado. "
                        "Elige una fecha y hora futura."
                    )
                else:
                    sede         = get_object_or_404(Sede, id_sede=sede_id)
                    especialidad = get_object_or_404(Especialidad, id_especialidad=especialidad_id)
                    doctor       = get_object_or_404(Doctor, id_doctor=doctor_id)

                    servicio_obj = None
                    if servicio_id:
                        servicio_obj = ServicioEspecialidad.objects.filter(
                            id_servicios_especialidad=servicio_id
                        ).first()

                    # Crear registro de pago pendiente (status=False) antes de la cita
                    pago = PagoCita.objects.create(
                        id_paciente=paciente,
                        id_sede=sede,
                        fecha_consulta=fecha_hora,
                        status=False,
                    )

                    Cita.objects.create(
                        id_paciente=paciente,
                        id_doctor=doctor,
                        id_sede=sede,
                        id_especialidades=especialidad,
                        id_servicio_especialidad=servicio_obj,
                        id_pago_cita=pago,
                        fecha_consulta=fecha_hora,
                        fecha_emision=timezone.now(),
                        motivo=motivo,
                        status=True,
                    )
                    messages.success(
                        request,
                        f"✅ Cita solicitada para el {fecha} a las {hora}. Espera confirmación."
                    )
                    return redirect('dashboard_paciente')

            except Exception as e:
                messages.error(request, f"Error al registrar la cita: {e}")

    sedes = Sede.objects.filter(status__in=[True, None]).order_by('nombre_sede')
    return render(request, 'citas/solicitar_cita.html', {
        'sedes': sedes,
        'hoy': date.today().isoformat(),
        'paciente': paciente,
    })


@login_required(login_url='/login/medico/')
@rol_requerido('medico')
def citas_pendientes_medico(request):
    """Citas pendientes y asignadas para el médico autenticado."""
    from usuarios.authentication import CustomAuthBackend
    datos_medico = CustomAuthBackend().get_datos_personales(request.user)

    citas_pendientes = Cita.objects.none()
    citas_asignadas  = Cita.objects.none()
    if datos_medico:
        base_qs = Cita.objects.filter(id_doctor=datos_medico).select_related(
            'id_paciente', 'id_especialidades', 'id_sede'
        ).order_by('fecha_consulta')
        citas_pendientes = base_qs.filter(status=True,  fecha_consulta__gte=datetime.now())
        citas_asignadas  = base_qs.filter(status=False, fecha_consulta__gte=datetime.now())

    return render(request, 'citas/citas_pendientes_medico.html', {
        'citas_pendientes': citas_pendientes,
        'citas_asignadas':  citas_asignadas,
        'datos_medico':     datos_medico,
    })


@login_required(login_url='/login/medico/')
@rol_requerido('medico')
def confirmar_cita(request, cita_id):
    """Médico confirma/acepta una cita pendiente."""
    from usuarios.authentication import CustomAuthBackend
    datos_medico = CustomAuthBackend().get_datos_personales(request.user)
    cita = get_object_or_404(Cita, id_citas=cita_id, id_doctor=datos_medico)
    if request.method == 'POST':
        cita.status = True
        cita.save()
        messages.success(request, f"Cita #{cita_id} confirmada.")
    return redirect('citas_pendientes_medico')


@login_required(login_url='/login/medico/')
@rol_requerido('medico')
def gestionar_horarios(request):
    """Vista de gestión de horarios del médico (solo lectura por ahora)."""
    from usuarios.authentication import CustomAuthBackend
    from usuarios.models import Doctor
    datos_medico = CustomAuthBackend().get_datos_personales(request.user)

    horario = None
    if datos_medico and datos_medico.id_horario:
        try:
            horario = Horario.objects.get(id_horario=datos_medico.id_horario)
        except Horario.DoesNotExist:
            pass

    return render(request, 'citas/gestionar_horarios.html', {
        'datos_medico': datos_medico,
        'horario':      horario,
    })


@rol_requerido('recepcionista', 'gerente')
def gestionar_citas(request):
    """Recepcionista/gerente: citas activas pendientes de aprobación de pago."""
    try:
        citas = Cita.objects.filter(
            status=True,
            id_pago_cita__status=False
        ).select_related(
            'id_paciente', 'id_doctor', 'id_sede',
            'id_especialidades', 'id_servicio_especialidad', 'id_pago_cita'
        ).order_by('-fecha_consulta')
        total = citas.count()
    except Exception:
        citas = []
        total = 0
    return render(request, 'citas/gestionar_citas.html', {
        'citas_pendientes': citas,
        'total': total,
    })


@login_required(login_url='/login/medico/')
@rol_requerido('medico')
def calendario_citas(request):
    """Lista/calendario de citas del médico autenticado."""
    from usuarios.authentication import CustomAuthBackend
    datos_medico = CustomAuthBackend().get_datos_personales(request.user)

    citas_qs = Cita.objects.none()
    if datos_medico:
        citas_qs = Cita.objects.filter(id_doctor=datos_medico).select_related(
            'id_paciente', 'id_especialidades', 'id_sede'
        ).order_by('fecha_consulta')

    estado_filtro = request.GET.get('estado', '')
    fecha_filtro  = request.GET.get('fecha', '')
    if estado_filtro == 'activa':
        citas_qs = citas_qs.filter(status=True)
    elif estado_filtro == 'cancelada':
        citas_qs = citas_qs.filter(status=False)
    if fecha_filtro:
        try:
            from datetime import datetime as _dt
            fecha_obj = _dt.strptime(fecha_filtro, '%Y-%m-%d').date()
            citas_qs = citas_qs.filter(fecha_consulta__date=fecha_obj)
        except ValueError:
            pass

    paginator = Paginator(citas_qs, 15)
    page_obj  = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'citas/calendario_citas.html', {
        'page_obj':       page_obj,
        'estado_actual':  estado_filtro,
        'fecha_actual':   fecha_filtro,
        'hoy':            date.today().isoformat(),
        'datos_medico':   datos_medico,
    })


@rol_requerido('recepcionista', 'gerente')
def aprobar_cita(request, cita_id):
    """Aprobar cita: marca el pago como confirmado (status=True)."""
    if request.method == 'POST':
        cita = get_object_or_404(Cita, id_citas=cita_id)
        if cita.id_pago_cita:
            cita.id_pago_cita.status = True
            cita.id_pago_cita.save()
        messages.success(request, f"✅ Cita #{cita_id} aprobada correctamente.")
    return redirect('gestionar_citas')


@rol_requerido('recepcionista', 'gerente')
def rechazar_cita(request, cita_id):
    """Rechazar/cancelar cita (status=False)."""
    cita = get_object_or_404(Cita, id_citas=cita_id)
    if request.method == 'POST':
        cita.status = False
        cita.save()
        messages.info(request, f"Cita #{cita_id} rechazada.")
    return redirect('gestionar_citas')


# ─── Endpoints AJAX ─────────────────────────────────────────────

@require_GET
def ajax_especialidades(request):
    """Especialidades activas en una sede."""
    sede_id = request.GET.get('sede_id')
    if not sede_id:
        return JsonResponse([], safe=False)
    try:
        esp = Especialidad.objects.filter(
            id_sede_id=sede_id, status__in=[True, None]
        ).values('id_especialidad', 'tipo_especialidad')
        data = [{'id': e['id_especialidad'], 'nombre': e['tipo_especialidad']} for e in esp]
    except Exception as exc:
        return JsonResponse({'error': str(exc)}, safe=False, status=500)
    return JsonResponse(data, safe=False)


@require_GET
def ajax_doctores(request):
    """Doctores por especialidad y sede.

    Etapa 1: busca mediante ServicioEspecialidad (relación directa).
    Etapa 2 (fallback): si no hay servicios, busca doctores directamente
    por id_sede y vínculo vía EspecialidadDoctor.
    """
    especialidad_id = request.GET.get('especialidad_id')
    sede_id         = request.GET.get('sede_id')
    if not especialidad_id or not sede_id:
        return JsonResponse([], safe=False)

    def _serializar(qs):
        return [
            {
                'id': d.id_doctor,
                'nombre': f"Dr/a. {(d.nombre_1 or '')} {(d.apellido_1 or '')}".strip(),
            }
            for d in qs
        ]

    try:
        # ─ Etapa 1: vía ServicioEspecialidad ───────────────────────────────
        doctor_ids = list(
            ServicioEspecialidad.objects.filter(
                id_especialidad_id=especialidad_id,
                id_sede_id=sede_id,
                status__in=[True, None],
            ).values_list('id_doctor_id', flat=True).distinct()
        )

        if doctor_ids:
            doctores = Doctor.objects.filter(
                id_doctor__in=doctor_ids,
                status__in=[True, None],
            )
            return JsonResponse(_serializar(doctores), safe=False)

        # ─ Etapa 2: fallback directo por sede + EspecialidadDoctor ─────────
        espec_doctor_ids = list(
            EspecialidadDoctor.objects.filter(
                id_especialidad_id=especialidad_id
            ).values_list('id_especialidad_doctor', flat=True)
        )

        if espec_doctor_ids:
            doctores = Doctor.objects.filter(
                id_sede_id=sede_id,
                id_especialidad_doctor__in=espec_doctor_ids,
                status__in=[True, None],
            )
        else:
            # Último recurso: todos los doctores de la sede
            doctores = Doctor.objects.filter(
                id_sede_id=sede_id,
                status__in=[True, None],
            )

        return JsonResponse(_serializar(doctores), safe=False)

    except Exception as exc:
        return JsonResponse({'error': str(exc)}, safe=False, status=500)


@require_GET
def ajax_horas_disponibles(request):
    """Slots de 30 min disponibles para un doctor en una fecha."""
    doctor_id = request.GET.get('medico_id') or request.GET.get('doctor_id')
    fecha     = request.GET.get('fecha')
    if not doctor_id or not fecha:
        return JsonResponse({'horas': []})
    try:
        doctor = Doctor.objects.get(id_doctor=doctor_id)
        if not doctor.id_horario:
            return JsonResponse({'horas': [], 'mensaje': 'Doctor sin horario asignado'})
        horario   = Horario.objects.get(id_horario=doctor.id_horario)
        inicio    = horario.hora_inicio or time(8, 0)
        fin       = horario.hora_fin    or time(20, 0)
        ocupadas  = set()
        for c in Cita.objects.filter(id_doctor_id=doctor_id, fecha_consulta__date=fecha, status=True):
            if c.fecha_consulta:
                ocupadas.add(c.fecha_consulta.strftime('%H:%M'))
        horas  = []
        actual = datetime.combine(date.today(), inicio)
        limite = datetime.combine(date.today(), fin)
        while actual < limite:
            slot = actual.strftime('%H:%M')
            if slot not in ocupadas:
                horas.append(slot)
            actual += timedelta(minutes=30)
        return JsonResponse({'horas': horas})
    except (Doctor.DoesNotExist, Horario.DoesNotExist):
        return JsonResponse({'horas': [], 'mensaje': 'Doctor o horario no encontrado'})
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
    """Lista paginada de pagos/facturas del paciente autenticado."""
    user = request.user
    paciente = PacienteDatosPersonales.objects.filter(id_user_paciente=user).first()

    pagos_qs = PagoCita.objects.none()
    if paciente:
        pagos_qs = PagoCita.objects.filter(id_paciente=paciente).order_by('-fecha_consulta')

    estado_filtro = request.GET.get('estado', '')
    if estado_filtro == 'pagado':
        pagos_qs = pagos_qs.filter(status=True)
    elif estado_filtro == 'pendiente':
        pagos_qs = pagos_qs.filter(status=False)

    paginator = Paginator(pagos_qs, 10)
    page_obj  = paginator.get_page(request.GET.get('page', 1))

    estados_choices = [('pagado', 'Pagado'), ('pendiente', 'Pendiente')]
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
    return render(request, 'citas/detalle_cita.html', {'cita': cita})


@login_required(login_url='/login/paciente/')
@rol_requerido('paciente')
def cancelar_cita_paciente(request, cita_id):
    """Cancela (status=False) una cita activa del paciente."""
    user = request.user
    paciente = PacienteDatosPersonales.objects.filter(id_user_paciente=user).first()
    cita = get_object_or_404(Cita, id_citas=cita_id, id_paciente=paciente)
    if request.method == 'POST':
        if cita.status:
            cita.status = False
            cita.save()
            messages.info(request, f"Cita #{cita_id} cancelada correctamente.")
        else:
            messages.warning(request, "La cita ya estaba cancelada.")
        return redirect('mis_citas')
    return render(request, 'citas/cancelar_cita.html', {'cita': cita})
