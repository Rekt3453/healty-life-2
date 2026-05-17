from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from datetime import date, datetime, time, timedelta
from usuarios.decorators import rol_requerido
from usuarios.models import PacienteDatosPersonales, Doctor
from .models import (
    Cita, Sede, Especialidad, Horario,
    ServicioEspecialidad, EspecialidadDoctor, Consultorio,
)

@login_required(login_url='/login/paciente/')
@rol_requerido('paciente')
def solicitar_cita(request):
    """Flujo: Sede → Especialidad → Doctor → Fecha/Hora → Servicio → Motivo."""
    user = request.user

    # Buscar perfil de datos personales (opcional — puede ser None si aún no existe)
    paciente = PacienteDatosPersonales.objects.filter(id_user_paciente=user).first()

    if request.method == 'POST':
        sede_id         = request.POST.get('sede')
        especialidad_id = request.POST.get('especialidad')
        doctor_id       = request.POST.get('doctor')
        servicio_id     = request.POST.get('servicio') or None
        fecha           = request.POST.get('fecha')
        hora            = request.POST.get('hora')
        motivo          = request.POST.get('motivo', '').strip()

        if not all([sede_id, especialidad_id, doctor_id, fecha, hora, motivo]):
            messages.error(request, "Todos los campos obligatorios deben completarse.")
        else:
            try:
                fecha_hora = datetime.strptime(f"{fecha} {hora}", "%Y-%m-%d %H:%M")

                sede         = get_object_or_404(Sede, id_sede=sede_id)
                especialidad = get_object_or_404(Especialidad, id_especialidad=especialidad_id)
                doctor       = get_object_or_404(Doctor, id_doctor=doctor_id)

                servicio_obj = None
                if servicio_id:
                    servicio_obj = ServicioEspecialidad.objects.filter(
                        id_servicios_especialidad=servicio_id
                    ).first()

                Cita.objects.create(
                    id_paciente=paciente,   # puede ser None si no tiene datos personales aún
                    id_doctor=doctor,
                    id_sede=sede,
                    id_especialidades=especialidad,
                    id_servicio_especialidad=servicio_obj,
                    fecha_consulta=fecha_hora,
                    fecha_emision=datetime.now(),
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

    sedes = Sede.objects.filter(status=True).order_by('nombre_sede')
    return render(request, 'citas/solicitar_cita.html', {
        'sedes': sedes,
        'hoy': date.today().isoformat(),
        'paciente': paciente,
    })


@rol_requerido('recepcionista', 'gerente')
def gestionar_citas(request):
    """Recepcionista/gerente: listado de citas activas."""
    try:
        citas = Cita.objects.filter(status=True).select_related(
            'id_paciente', 'id_doctor', 'id_sede', 'id_especialidades', 'id_servicio_especialidad'
        ).order_by('-fecha_consulta')
        total = citas.count()
    except Exception:
        citas = []
        total = 0
    return render(request, 'citas/gestionar_citas.html', {
        'citas_pendientes': citas,
        'total': total,
    })


@rol_requerido('recepcionista', 'gerente')
def aprobar_cita(request, cita_id):
    """Aprobar cita (status=True ya está, sólo confirma)."""
    if request.method == 'POST':
        cita = get_object_or_404(Cita, id_citas=cita_id)
        cita.status = True
        cita.save()
        messages.success(request, f"✅ Cita #{cita_id} aprobada.")
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


# ─── Endpoints AJAX ───────────────────────────────────────────────────────────

@require_GET
def ajax_especialidades(request):
    """Especialidades activas en una sede."""
    sede_id = request.GET.get('sede_id')
    if not sede_id:
        return JsonResponse([], safe=False)
    try:
        esp = Especialidad.objects.filter(
            id_sede_id=sede_id, status=True
        ).values('id_especialidad', 'tipo_especialidad')
        data = [{'id': e['id_especialidad'], 'nombre': e['tipo_especialidad']} for e in esp]
    except Exception:
        data = []
    return JsonResponse(data, safe=False)


@require_GET
def ajax_doctores(request):
    """Doctores por especialidad y sede (vía EspecialidadDoctor)."""
    especialidad_id = request.GET.get('especialidad_id')
    sede_id         = request.GET.get('sede_id')
    if not especialidad_id or not sede_id:
        return JsonResponse([], safe=False)
    try:
        esp_doc_ids = EspecialidadDoctor.objects.filter(
            id_especialidad_id=especialidad_id
        ).values_list('id_especialidad_doctor', flat=True)
        doctores = Doctor.objects.filter(
            id_especialidad_doctor__in=esp_doc_ids,
            id_sede_id=sede_id,
            status=True,
        )
        data = [
            {
                'id': d.id_doctor,
                'nombre': f"Dr/a. {(d.nombre_1 or '')} {(d.apellido_1 or '')}".strip(),
            }
            for d in doctores
        ]
    except Exception:
        data = []
    return JsonResponse(data, safe=False)


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
            id_doctor_id=doctor_id, status=True
        ).values('id_servicios_especialidad', 'servicios')
        data = [{'id': s['id_servicios_especialidad'], 'nombre': s['servicios']} for s in servicios]
    except Exception:
        data = []
    return JsonResponse(data, safe=False)
