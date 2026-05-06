from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from django.http import JsonResponse
from datetime import date, datetime, time, timedelta
from usuarios.decorators import rol_requerido
from usuarios.models import UserProfile
from .models import Cita, HorarioMedico, Especialidad
from .forms import SolicitudCitaForm, AsignarMedicoForm, HorarioMedicoForm, ConfirmarCitaForm, HorarioSelectorForm
import calendar

@login_required
@rol_requerido('paciente')
def solicitar_cita(request):
    if request.method == 'POST':
        form = SolicitudCitaForm(request.POST)
        if form.is_valid():
            cita = form.save(commit=False)
            cita.paciente = request.user
            cita.estado = 'pendiente'
            cita.save()
            messages.success(request, 'Cita solicitada con éxito. Espera aprobación de la recepción.')
            return redirect('dashboard_paciente')
    else:
        form = SolicitudCitaForm()
    
    return render(request, 'citas/solicitar_cita.html', {'form': form})

@login_required
@rol_requerido('paciente')
def solicitar_cita_con_horario(request):
    """Nueva vista para solicitar cita con selector de horarios laborables"""
    if request.method == 'POST':
        form = HorarioSelectorForm(request.POST)
        if form.is_valid():
            fecha = form.cleaned_data['fecha']
            especialidad = form.cleaned_data['especialidad']
            horario_seleccionado = form.cleaned_data['horario_disponible']
            
            if horario_seleccionado:
                # Parsear el horario seleccionado (formato: medico_id_hora)
                medico_id, hora_str = horario_seleccionado.split('_')
                medico = UserProfile.objects.get(user__id=medico_id).user
                hora = datetime.strptime(hora_str, '%H:%M').time()
                
                # Crear la cita
                cita = Cita.objects.create(
                    paciente=request.user,
                    medico=medico,
                    especialidad=especialidad,
                    fecha=fecha,
                    hora_solicitada=hora,
                    hora_confirmada=hora,
                    estado='aprobada',  # Directamente aprobada ya que se seleccionó horario disponible
                    motivo='Cita solicitada con horario disponible'
                )
                
                messages.success(request, f'Cita confirmada para el {fecha} a las {hora} con el Dr. {medico.username}.')
                return redirect('dashboard_paciente')
            else:
                messages.error(request, 'Por favor selecciona un horario disponible.')
    else:
        form = HorarioSelectorForm()
    
    return render(request, 'citas/solicitar_cita_horario.html', {'form': form})

@login_required
@rol_requerido('recepcionista')
def gestionar_citas(request):
    citas_pendientes = Cita.objects.filter(estado='pendiente').order_by('fecha', 'hora_solicitada')
    return render(request, 'citas/gestionar_citas.html', {
        'citas_pendientes': citas_pendientes
    })

@login_required
@rol_requerido('recepcionista')
def asignar_medico(request, cita_id):
    cita = get_object_or_404(Cita, id=cita_id)
    
    if request.method == 'POST':
        form = AsignarMedicoForm(request.POST)
        if form.is_valid():
            cita.medico = form.cleaned_data['medico']
            cita.estado = 'asignada'  # Cambiar a estado asignada
            cita.save()
            messages.success(request, f'Médico asignado a la cita {cita.id}. Ahora el médico debe confirmar la hora.')
            return redirect('gestionar_citas')
    else:
        form = AsignarMedicoForm()
    
    return render(request, 'citas/asignar_medico.html', {
        'form': form,
        'cita': cita
    })

@login_required
@rol_requerido('medico')
def confirmar_cita(request, cita_id):
    """Vista para que el médico confirme la hora de la cita"""
    cita = get_object_or_404(Cita, id=cita_id, medico=request.user, estado='asignada')
    
    if request.method == 'POST':
        form = ConfirmarCitaForm(request.POST, cita=cita)
        if form.is_valid():
            hora_confirmada = form.cleaned_data.get('horarios_disponibles') or form.cleaned_data.get('hora_confirmada')
            
            if hora_confirmada:
                if isinstance(hora_confirmada, str):
                    hora_confirmada = datetime.strptime(hora_confirmada, '%H:%M').time()
                
                cita.hora_confirmada = hora_confirmada
                cita.save()  # Guardar antes de verificar disponibilidad
                
                # Verificar disponibilidad final
                if cita.esta_disponible():
                    cita.estado = 'aprobada'
                    cita.save()
                    messages.success(request, f'Cita {cita.id} confirmada para el {cita.fecha} a las {hora_confirmada}.')
                    return redirect('dashboard_medico')
                else:
                    messages.error(request, 'La hora seleccionada ya no está disponible. Por favor, selecciona otra.')
                    return render(request, 'citas/confirmar_cita.html', {
                        'form': form,
                        'cita': cita
                    })
            else:
                messages.error(request, 'Debes seleccionar una hora para la cita.')
    else:
        form = ConfirmarCitaForm(cita=cita)
    
    return render(request, 'citas/confirmar_cita.html', {
        'form': form,
        'cita': cita
    })

@login_required
@rol_requerido('medico')
def gestionar_horarios(request):
    """Vista para que los médicos gestionen sus horarios de disponibilidad"""
    if request.method == 'POST':
        form = HorarioMedicoForm(request.POST)
        if form.is_valid():
            horario = form.save(commit=False)
            horario.medico = request.user
            horario.save()
            messages.success(request, 'Horario agregado correctamente.')
            return redirect('gestionar_horarios')
    else:
        form = HorarioMedicoForm()
    
    horarios = HorarioMedico.objects.filter(medico=request.user).order_by('dia_semana', 'hora_inicio')
    
    return render(request, 'citas/gestionar_horarios.html', {
        'form': form,
        'horarios': horarios
    })

@login_required
@rol_requerido('medico')
def eliminar_horario(request, horario_id):
    """Eliminar un horario de disponibilidad"""
    horario = get_object_or_404(HorarioMedico, id=horario_id, medico=request.user)
    horario.delete()
    messages.success(request, 'Horario eliminado correctamente.')
    return redirect('gestionar_horarios')

@login_required
@rol_requerido('medico')
def calendario_citas(request):
    """Vista de calendario para médicos con citas pendientes y confirmadas"""
    # Obtener parámetros de mes y año
    year = request.GET.get('year', datetime.now().year)
    month = request.GET.get('month', datetime.now().month)
    
    try:
        year = int(year)
        month = int(month)
    except (ValueError, TypeError):
        year = datetime.now().year
        month = datetime.now().month
    
    # Obtener primer y último día del mes
    first_day = date(year, month, 1)
    if month == 12:
        last_day = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)
    
    # Obtener citas del médico en el mes
    citas_mes = Cita.objects.filter(
        medico=request.user,
        fecha__gte=first_day,
        fecha__lte=last_day
    ).order_by('fecha', 'hora_confirmada')
    
    # Organizar citas por día
    calendario_citas = {}
    for cita in citas_mes:
        dia = cita.fecha.day
        if dia not in calendario_citas:
            calendario_citas[dia] = []
        calendario_citas[dia].append(cita)
    
    # Crear matriz del calendario
    cal = calendar.monthcalendar(year, month)
    
    # Navegación
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1
    
    context = {
        'year': year,
        'month': month,
        'month_name': calendar.month_name[month],
        'calendar': cal,
        'citas_calendario': calendario_citas,
        'prev_month': prev_month,
        'prev_year': prev_year,
        'next_month': next_month,
        'next_year': next_year,
    }
    
    return render(request, 'citas/calendario_citas.html', context)

@login_required
@rol_requerido('medico')
def citas_pendientes_medico(request):
    """Vista para que los médicos vean sus citas pendientes"""
    citas_pendientes = Cita.objects.filter(
        medico=request.user,
        estado='pendiente'
    ).order_by('fecha', 'hora_solicitada')
    
    citas_asignadas = Cita.objects.filter(
        medico=request.user,
        estado='asignada'
    ).order_by('fecha', 'hora_solicitada')
    
    return render(request, 'citas/citas_pendientes_medico.html', {
        'citas_pendientes': citas_pendientes,
        'citas_asignadas': citas_asignadas
    })

@login_required
@rol_requerido('recepcionista')
def rechazar_cita(request, cita_id):
    cita = get_object_or_404(Cita, id=cita_id)
    cita.estado = 'rechazada'
    cita.save()
    messages.success(request, f'Cita {cita.id} rechazada.')
    return redirect('gestionar_citas')

def api_horarios_disponibles(request):
    """API endpoint para obtener horarios disponibles dinámicamente"""
    fecha = request.GET.get('fecha')
    especialidad_id = request.GET.get('especialidad')
    
    if not fecha or not especialidad_id:
        return JsonResponse({'horarios': []})
    
    try:
        from datetime import datetime
        fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()
        
        from .models import Especialidad
        especialidad = Especialidad.objects.get(id=especialidad_id)
        
        form = HorarioSelectorForm()
        horarios = form.get_horarios_disponibles(fecha_obj, especialidad)
        
        # Convertir a formato para el frontend
        horarios_list = []
        for value, text in horarios:
            if value:  # Skip empty option
                horarios_list.append({
                    'value': value,
                    'text': text
                })
        
        return JsonResponse({'horarios': horarios_list})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
