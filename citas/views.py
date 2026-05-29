from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_GET
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from datetime import date, datetime, time, timedelta
from usuarios.decorators import rol_requerido
from usuarios.models import PacienteDatosPersonales, Doctor, PacienteEspecial
from .models import (
    Cita, PagoCita, Sede, Especialidad, Horario,
    ServicioEspecialidad, EspecialidadDoctor, Consultorio, ConsultaMedica, Factura,
)
from .services import CitaService, FacturacionService
from .forms import ConsultaMedicaForm, RegistrarAdelantoForm

@login_required(login_url='/login/paciente/')
@rol_requerido('paciente')
def solicitar_cita(request):
    """Flujo: Paciente Objetivo → Sede → Especialidad → Doctor → Fecha/Hora → Servicio → Motivo.

    Si el tutor selecciona un paciente especial (menor), se valida en el servidor
    que la especialidad elegida tenga clasificación 'Pediatría' o 'General'.
    El motivo lleva un prefijo automático con el nombre del menor.
    """
    user     = request.user
    paciente = PacienteDatosPersonales.objects.filter(id_user_paciente=user).first()

    # Obtener los menores activos del tutor para el selector
    menores = []
    if paciente:
        menores = list(
            PacienteEspecial.objects.filter(
                id_paciente_tutor=paciente, status=True
            ).order_by('nombre_1', 'apellido_1')
        )

    if request.method == 'POST':
        sede_id          = request.POST.get('sede')
        especialidad_id  = request.POST.get('especialidad')
        doctor_id        = request.POST.get('doctor') or request.POST.get('medico')
        servicio_id      = request.POST.get('servicio') or None
        fecha            = request.POST.get('fecha')
        hora             = request.POST.get('hora') or request.POST.get('hora_solicitada')
        motivo_raw       = request.POST.get('motivo', '').strip()
        # paciente_objetivo: 'self' | 'especial_<id>'
        paciente_objetivo = request.POST.get('paciente_objetivo', 'self')

        if not all([sede_id, especialidad_id, doctor_id, fecha, hora, motivo_raw]):
            messages.error(request, "Todos los campos obligatorios deben completarse.")
        else:
            try:
                fecha_hora = datetime.strptime(f"{fecha} {hora}", "%Y-%m-%d %H:%M")

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

                    # Resolver a quién pertenece la cita y construir el motivo
                    menor_obj = None
                    if paciente_objetivo.startswith('especial_'):
                        # La cita es en nombre de un paciente especial (menor)
                        try:
                            menor_id  = int(paciente_objetivo.split('_', 1)[1])
                            menor_obj = PacienteEspecial.objects.get(
                                id_paciente_especial=menor_id,
                                id_paciente_tutor=paciente,
                                status=True,
                            )
                        except (PacienteEspecial.DoesNotExist, ValueError):
                            messages.error(request, "El paciente especial seleccionado no es válido.")
                            raise ValueError("menor inválido")

                        # Validación servidor: clasificación de especialidad para menores
                        clasificacion = especialidad.clasificacion_especialidad or ''
                        permitidas_menor = _CLASIFICACIONES_POR_TIPO['menor']
                        if clasificacion not in permitidas_menor:
                            messages.error(
                                request,
                                f"Para un menor de edad debes seleccionar una especialidad de "
                                f"Pediatría o General. La especialidad ‘{especialidad.tipo_especialidad}’ "
                                f"está clasificada como ‘{clasificacion or 'Sin clasificar'}’."
                            )
                            raise ValueError("especialidad no válida para menor")

                        nombre_menor = f"{menor_obj.nombre_1} {menor_obj.apellido_1}"
                        motivo = f"[Cita para {nombre_menor}] {motivo_raw}"
                    else:
                        # Validación servidor: clasificación de especialidad para adultos
                        clasificacion = especialidad.clasificacion_especialidad or ''
                        permitidas_adulto = _CLASIFICACIONES_POR_TIPO['adulto']
                        if clasificacion and clasificacion not in permitidas_adulto:
                            messages.error(
                                request,
                                f"Para un paciente adulto debes seleccionar una especialidad de "
                                f"Adultos o General. La especialidad ‘{especialidad.tipo_especialidad}’ "
                                f"está clasificada como ‘{clasificacion}’."
                            )
                            raise ValueError("especialidad no válida para adulto")
                        motivo = motivo_raw

                    servicio_obj = None
                    if servicio_id:
                        servicio_obj = ServicioEspecialidad.objects.filter(
                            id_servicios_especialidad=servicio_id
                        ).first()

                    pago = PagoCita.objects.create(
                        id_paciente=paciente,
                        id_sede=sede,
                        fecha_consulta=fecha_hora,
                        status=False,
                        estado_pago=PagoCita.ESTADO_PENDIENTE,
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
                        estado=Cita.ESTADO_SOLICITADA,
                    )

                    nombre_destino = nombre_menor if menor_obj else "ti"
                    messages.success(
                        request,
                        f"✅ Cita solicitada para {nombre_destino} el {fecha} a las {hora}. "
                        f"Espera confirmación."
                    )
                    return redirect('dashboard_paciente')

            except ValueError:
                pass  # los mensajes de error ya fueron añadidos arriba
            except Exception as e:
                messages.error(request, f"Error al registrar la cita: {e}")

    sedes = Sede.objects.filter(status__in=[True, None]).order_by('nombre_sede')
    return render(request, 'citas/solicitar_cita.html', {
        'sedes':   sedes,
        'hoy':     date.today().isoformat(),
        'paciente': paciente,
        'menores': menores,   # lista de PacienteEspecial del tutor
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
    from usuarios.authentication import CustomAuthBackend
    datos_medico = CustomAuthBackend().get_datos_personales(request.user)

    citas_pendientes = Cita.objects.none()
    citas_asignadas  = Cita.objects.none()
    if datos_medico:
        base_qs = Cita.objects.filter(
            id_doctor=datos_medico,
            status=True,
        ).select_related(
            'id_paciente', 'id_especialidades', 'id_sede', 'id_pago_cita'
        ).order_by('fecha_consulta')

        # Confirmadas: pago aprobado por recepcionista, listas para consulta
        citas_pendientes = base_qs.filter(
            Q(estado=Cita.ESTADO_CONFIRMADA) |
            Q(estado__isnull=True, id_pago_cita__status=True)
        ).exclude(estado=Cita.ESTADO_EN_CONSULTA)

        # En consulta: médico ya inició la consulta
        citas_asignadas = base_qs.filter(estado=Cita.ESTADO_EN_CONSULTA)

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
    """Recepcionista/gerente: dos secciones — solicitudes nuevas y pagos por confirmar."""
    _base = Cita.objects.select_related(
        'id_paciente', 'id_doctor', 'id_sede',
        'id_especialidades', 'id_servicio_especialidad', 'id_pago_cita'
    ).order_by('-fecha_consulta')

    try:
        citas_solicitud = _base.filter(estado=Cita.ESTADO_SOLICITADA)
    except Exception:
        citas_solicitud = Cita.objects.none()

    try:
        citas_pago = _base.filter(estado=Cita.ESTADO_PAGO_PENDIENTE)
    except Exception:
        citas_pago = Cita.objects.none()

    return render(request, 'citas/gestionar_citas.html', {
        'citas_solicitud': citas_solicitud,
        'citas_pago':      citas_pago,
        'total': citas_solicitud.count() + citas_pago.count(),
    })


@rol_requerido('recepcionista', 'gerente')
def confirmar_pago(request, cita_id):
    """Recepcionista confirma que el pago del paciente fue verificado → estado='confirmada'."""
    if request.method == 'POST':
        cita = get_object_or_404(
            Cita.objects.select_related('id_pago_cita'), id_citas=cita_id
        )
        try:
            CitaService.confirmar_pago(cita)
            messages.success(request, f"✅ Pago de cita #{cita_id} confirmado. Cita lista para consulta.")
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f"Error al confirmar pago: {e}")
    return redirect('gestionar_citas')


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
    if estado_filtro in dict(Cita.ESTADOS):
        citas_qs = citas_qs.filter(estado=estado_filtro)
    elif estado_filtro == 'activa':
        citas_qs = citas_qs.exclude(estado__in=[
            Cita.ESTADO_CANCELADA, Cita.ESTADO_RECHAZADA, Cita.ESTADO_NO_ASISTIO
        ])
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
    """Recepcionista aprueba la solicitud de cita → estado='aprobada'."""
    if request.method == 'POST':
        cita = get_object_or_404(Cita, id_citas=cita_id)
        try:
            CitaService.aprobar_cita(cita)
            messages.success(request, f"✅ Cita #{cita_id} aprobada correctamente.")
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
def registrar_adelanto(request, cita_id):
    """Recepcionista registra un adelanto de pago sin generar factura inmediata."""
    cita = get_object_or_404(Cita.objects.select_related('id_paciente', 'id_sede'), id_citas=cita_id)
    if request.method == 'POST':
        form = RegistrarAdelantoForm(request.POST)
        if form.is_valid():
            try:
                CitaService.registrar_adelanto(
                    cita,
                    monto=form.cleaned_data['monto'],
                    metodo_pago=form.cleaned_data['metodo_pago'],
                    referencia=form.cleaned_data.get('referencia'),
                )
                messages.success(request, f"✅ Adelanto registrado. Cita #{cita_id} marcada como pagada con adelanto.")
                return redirect('gestionar_citas')
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


# ─── Consulta médica ──────────────────────────────────────────────────────────

@login_required(login_url='/login/medico/')
@rol_requerido('medico')
def iniciar_consulta(request, cita_id):
    """Médico inicia o continúa una consulta médica."""
    cita = get_object_or_404(Cita, pk=cita_id)
    try:
        consulta, _ = CitaService.iniciar_consulta(cita)
    except ValueError as e:
        messages.error(request, str(e))
        return redirect('citas_pendientes_medico')

    if request.method == 'POST':
        form = ConsultaMedicaForm(request.POST, instance=consulta)
        if form.is_valid():
            form.save()
            messages.success(request, 'Consulta guardada.')
            return redirect('iniciar_consulta', cita_id=cita_id)
    else:
        form = ConsultaMedicaForm(instance=consulta)

    return render(request, 'citas/consulta_medica.html', {
        'form':     form,
        'cita':     cita,
        'consulta': consulta,
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
            CitaService.cerrar_consulta(cita)
            messages.success(request, '✅ Consulta cerrada. Cita marcada como atendida.')
            return redirect('citas_pendientes_medico')
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
