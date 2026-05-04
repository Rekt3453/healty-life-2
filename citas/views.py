from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Q, Count, Sum
from django.core.paginator import Paginator
from datetime import datetime, timedelta
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch
import io
import json

from .models import Cita, Servicio, DisponibilidadMedica, Factura, HistoriaClinica, Reporte
from .forms import AgendarCitaForm, CancelarCitaForm, HistoriaClinicaForm, BusquedaCitasForm
from usuarios.models import UserProfile, MedicoProfile, PacienteProfile, Sede, Especialidad

@login_required
def agendar_cita(request):
    """Vista para agendar nuevas citas"""
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.rol not in ['paciente', 'paciente_especial']:
        messages.error(request, "Solo los pacientes pueden agendar citas.")
        return redirect('dashboard_paciente')
    
    if request.method == 'POST':
        form = AgendarCitaForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                # Crear la cita
                cita = Cita.objects.create(
                    paciente=request.user,
                    medico=form.cleaned_data['medico'],
                    sede=form.cleaned_data['sede'],
                    servicio=form.cleaned_data['servicio'],
                    fecha_hora=datetime.combine(
                        form.cleaned_data['fecha'], 
                        form.cleaned_data['hora']
                    ),
                    notas_paciente=form.cleaned_data['notas_paciente'],
                    estado='pendiente'
                )
                
                # Crear factura
                Factura.objects.create(
                    cita=cita,
                    monto_total=cita.precio_total
                )
                
                messages.success(request, f"Cita agendada exitosamente para el {cita.fecha_hora.strftime('%d/%m/%Y %H:%M')}")
                return redirect('mis_citas')
                
            except Exception as e:
                messages.error(request, f"Error al agendar la cita: {str(e)}")
        else:
            messages.error(request, "Por favor corrige los errores en el formulario.")
    else:
        form = AgendarCitaForm(user=request.user)
    
    return render(request, 'citas/agendar_cita.html', {'form': form})

@login_required
def mis_citas(request):
    """Vista para ver las citas del paciente actual"""
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.rol not in ['paciente', 'paciente_especial']:
        return redirect('dashboard_paciente')
    
    citas = Cita.objects.filter(paciente=request.user).order_by('-fecha_hora')
    
    # Filtros
    estado = request.GET.get('estado')
    if estado:
        citas = citas.filter(estado=estado)
    
    # Paginación
    paginator = Paginator(citas, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'estados_choices': Cita.ESTADOS_CHOICES,
        'estado_actual': estado
    }
    return render(request, 'citas/mis_citas.html', context)

@login_required
def detalle_cita(request, pk):
    """Vista para ver detalles de una cita específica"""
    cita = get_object_or_404(Cita, pk=pk)
    
    # Verificar permisos
    if request.user.userprofile.rol in ['paciente', 'paciente_especial']:
        if cita.paciente != request.user:
            raise Http404("No tienes permiso para ver esta cita")
    elif request.user.userprofile.rol == 'medico':
        if cita.medico.user_profile.user != request.user:
            raise Http404("No tienes permiso para ver esta cita")
    elif request.user.userprofile.rol in ['recepcionista', 'gerente', 'gerente_general']:
        if cita.sede != request.user.userprofile.sede and request.user.userprofile.rol != 'gerente_general':
            raise Http404("No tienes permiso para ver esta cita")
    
    # Intentar obtener factura e historia clínica
    try:
        factura = cita.factura
    except Factura.DoesNotExist:
        factura = None
    
    try:
        historia = cita.historia_clinica
    except HistoriaClinica.DoesNotExist:
        historia = None
    
    context = {
        'cita': cita,
        'factura': factura,
        'historia': historia,
        'puede_cancelar': cita.puede_cancelar
    }
    return render(request, 'citas/detalle_cita.html', context)

@login_required
def cancelar_cita(request, pk):
    """Vista para cancelar una cita"""
    cita = get_object_or_404(Cita, pk=pk)
    
    # Verificar permisos
    if request.user.userprofile.rol in ['paciente', 'paciente_especial']:
        if cita.paciente != request.user:
            raise Http404("No tienes permiso para cancelar esta cita")
    elif request.user.userprofile.rol == 'medico':
        if cita.medico.user_profile.user != request.user:
            raise Http404("No tienes permiso para cancelar esta cita")
    
    if not cita.puede_cancelar:
        messages.error(request, "Esta cita no se puede cancelar. Las citas deben cancelarse con al menos 2 horas de antelación.")
        return redirect('detalle_cita', pk=pk)
    
    if request.method == 'POST':
        form = CancelarCitaForm(request.POST, instance=cita)
        if form.is_valid():
            cita.estado = 'cancelada'
            cita.motivo_cancelacion = form.cleaned_data['motivo_cancelacion']
            cita.save()
            
            # Cancelar factura si existe
            try:
                factura = cita.factura
                factura.estado = 'cancelada'
                factura.save()
            except Factura.DoesNotExist:
                pass
            
            messages.success(request, "Cita cancelada exitosamente.")
            return redirect('mis_citas')
    else:
        form = CancelarCitaForm(instance=cita)
    
    return render(request, 'citas/cancelar_cita.html', {'form': form, 'cita': cita})

@login_required
def calendario_medico(request):
    """Vista del calendario para médicos"""
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.rol != 'medico':
        raise Http404("No tienes permiso para ver esta página")
    
    try:
        medico_profile = request.user.userprofile.medicoprofile
    except MedicoProfile.DoesNotExist:
        messages.error(request, "Tu perfil de médico no está configurado correctamente.")
        return redirect('dashboard_medico')
    
    # Obtener fecha del parámetro o usar fecha actual
    fecha_str = request.GET.get('fecha')
    if fecha_str:
        try:
            fecha_actual = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            fecha_actual = timezone.now().date()
    else:
        fecha_actual = timezone.now().date()
    
    # Obtener citas del médico para la semana actual
    inicio_semana = fecha_actual - timedelta(days=fecha_actual.weekday())
    fin_semana = inicio_semana + timedelta(days=6)
    
    citas = Cita.objects.filter(
        medico=medico_profile,
        fecha_hora__gte=inicio_semana,
        fecha_hora__lte=fin_semana,
        estado__in=['pendiente', 'confirmada', 'en_progreso']
    ).order_by('fecha_hora')
    
    # Generar matriz de calendario
    calendario = {}
    for i in range(7):
        dia = inicio_semana + timedelta(days=i)
        calendario[dia] = []
    
    for cita in citas:
        dia_cita = cita.fecha_hora.date()
        if dia_cita in calendario:
            calendario[dia_cita].append(cita)
    
    context = {
        'calendario': calendario,
        'fecha_actual': fecha_actual,
        'inicio_semana': inicio_semana,
        'fin_semana': fin_semana,
        'medico_profile': medico_profile
    }
    return render(request, 'citas/calendario_medico.html', context)

@login_required
def calendario_general(request):
    """Vista del calendario general para recepcionistas y gerentes"""
    if not hasattr(request.user, 'userprofile') or not request.user.userprofile.puede_ver_calendario_general():
        raise Http404("No tienes permiso para ver esta página")
    
    # Obtener parámetros
    fecha_str = request.GET.get('fecha')
    especialidad_id = request.GET.get('especialidad')
    medico_id = request.GET.get('medico')
    
    if fecha_str:
        try:
            fecha_actual = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            fecha_actual = timezone.now().date()
    else:
        fecha_actual = timezone.now().date()
    
    # Filtrar por sede
    if request.user.userprofile.rol == 'gerente_general':
        citas_query = Cita.objects.all()
    else:
        citas_query = Cita.objects.filter(sede=request.user.userprofile.sede)
    
    # Aplicar filtros adicionales
    if especialidad_id:
        citas_query = citas_query.filter(medico__especialidad_id=especialidad_id)
    
    if medico_id:
        citas_query = citas_query.filter(medico_id=medico_id)
    
    # Obtener citas del día
    citas_dia = citas_query.filter(
        fecha_hora__date=fecha_actual,
        estado__in=['pendiente', 'confirmada', 'en_progreso']
    ).order_by('fecha_hora')
    
    context = {
        'citas_dia': citas_dia,
        'fecha_actual': fecha_actual,
        'especialidades': Especialidad.objects.filter(activa=True),
        'medicos': MedicoProfile.objects.all(),
        'especialidad_actual': especialidad_id,
        'medico_actual': medico_id
    }
    return render(request, 'citas/calendario_general.html', context)

@login_required
def crear_historia_clinica(request, cita_id):
    """Vista para crear historia clínica de una cita"""
    cita = get_object_or_404(Cita, pk=cita_id)
    
    # Solo médicos pueden crear historias clínicas
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.rol != 'medico':
        raise Http404("Solo los médicos pueden crear historias clínicas")
    
    if cita.medico.user_profile.user != request.user:
        raise Http404("No tienes permiso para crear historia clínica de esta cita")
    
    # Verificar que la cita esté completada
    if cita.estado != 'completada':
        messages.error(request, "Solo se pueden crear historias clínicas de citas completadas.")
        return redirect('detalle_cita', pk=cita_id)
    
    # Verificar que no exista ya una historia clínica
    if HistoriaClinica.objects.filter(cita=cita).exists():
        messages.error(request, "Esta cita ya tiene una historia clínica.")
        return redirect('detalle_cita', pk=cita_id)
    
    try:
        paciente_profile = cita.paciente.userprofile.paciente_profile
    except PacienteProfile.DoesNotExist:
        messages.error(request, "El paciente no tiene perfil configurado.")
        return redirect('detalle_cita', pk=cita_id)
    
    if request.method == 'POST':
        form = HistoriaClinicaForm(request.POST)
        if form.is_valid():
            historia = form.save(commit=False)
            historia.paciente = paciente_profile
            historia.medico = request.user.userprofile.medicoprofile
            historia.cita = cita
            historia.save()
            
            messages.success(request, "Historia clínica creada exitosamente.")
            return redirect('detalle_cita', pk=cita_id)
    else:
        form = HistoriaClinicaForm()
    
    context = {
        'form': form,
        'cita': cita,
        'paciente': cita.paciente
    }
    return render(request, 'citas/crear_historia_clinica.html', context)

@login_required
def ver_historia_clinica(request, pk):
    """Vista para ver una historia clínica específica"""
    historia = get_object_or_404(HistoriaClinica, pk=pk)
    
    # Verificar permisos
    if request.user.userprofile.rol in ['paciente', 'paciente_especial']:
        if historia.paciente.user_profile.user != request.user:
            raise Http404("No tienes permiso para ver esta historia clínica")
    elif request.user.userprofile.rol == 'medico':
        if historia.medico.user_profile.user != request.user:
            raise Http404("No tienes permiso para ver esta historia clínica")
    elif request.user.userprofile.rol in ['recepcionista', 'gerente', 'gerente_general']:
        if historia.cita.sede != request.user.userprofile.sede and request.user.userprofile.rol != 'gerente_general':
            raise Http404("No tienes permiso para ver esta historia clínica")
    
    context = {'historia': historia}
    return render(request, 'citas/ver_historia_clinica.html', context)

@login_required
def mis_facturas(request):
    """Vista para ver las facturas del paciente"""
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.rol not in ['paciente', 'paciente_especial']:
        raise Http404("No tienes permiso para ver esta página")
    
    facturas = Factura.objects.filter(cita__paciente=request.user).order_by('-fecha_emision')
    
    # Filtros
    estado = request.GET.get('estado')
    if estado:
        facturas = facturas.filter(estado=estado)
    
    # Paginación
    paginator = Paginator(facturas, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'estados_choices': Factura.ESTADOS_CHOICES,
        'estado_actual': estado
    }
    return render(request, 'citas/mis_facturas.html', context)

@login_required
def descargar_factura_pdf(request, pk):
    """Vista para descargar factura en PDF"""
    factura = get_object_or_404(Factura, pk=pk)
    
    # Verificar permisos
    if request.user.userprofile.rol in ['paciente', 'paciente_especial']:
        if factura.cita.paciente != request.user:
            raise Http404("No tienes permiso para descargar esta factura")
    elif request.user.userprofile.rol in ['recepcionista', 'gerente', 'gerente_general']:
        if factura.cita.sede != request.user.userprofile.sede and request.user.userprofile.rol != 'gerente_general':
            raise Http404("No tienes permiso para descargar esta factura")
    
    # Crear PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Contenido del PDF
    story = []
    
    # Título
    title_style = styles['Title']
    story.append(Paragraph("FACTURA", title_style))
    story.append(Spacer(1, 12))
    
    # Información de la factura
    data = [
        ['Número de Factura:', factura.numero_factura],
        ['Fecha de Emisión:', factura.fecha_emision.strftime('%d/%m/%Y %H:%M')],
        ['Fecha de Vencimiento:', factura.fecha_vencimiento.strftime('%d/%m/%Y')],
        ['Estado:', factura.get_estado_display()],
        ['Monto Total:', f"${factura.monto_total:.2f}"],
        ['Monto Pagado:', f"${factura.monto_pagado:.2f}"],
        ['Saldo Pendiente:', f"${factura.saldo_pendiente:.2f}"],
    ]
    
    table = Table(data, colWidths=[2*inch, 3*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    
    story.append(table)
    story.append(Spacer(1, 20))
    
    # Información de la cita
    story.append(Paragraph("Información de la Cita", styles['Heading2']))
    story.append(Spacer(1, 12))
    
    cita_data = [
        ['Paciente:', f"{factura.cita.paciente.get_full_name()}"],
        ['Médico:', f"Dr. {factura.cita.medico.user_profile.nombre_completo}"],
        ['Especialidad:', factura.cita.medico.especialidad.nombre],
        ['Servicio:', factura.cita.servicio.nombre],
        ['Sede:', factura.cita.sede.nombre],
        ['Fecha y Hora:', factura.cita.fecha_hora.strftime('%d/%m/%Y %H:%M')],
    ]
    
    cita_table = Table(cita_data, colWidths=[2*inch, 3*inch])
    cita_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    
    story.append(cita_table)
    
    # Generar PDF
    doc.build(story)
    
    # Preparar respuesta
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="factura_{factura.numero_factura}.pdf"'
    
    return response

@require_POST
@login_required
def obtener_medicos_por_especialidad(request):
    """AJAX: Obtener médicos filtrados por especialidad y sede"""
    especialidad_id = request.POST.get('especialidad_id')
    sede_id = request.POST.get('sede_id')
    
    if not especialidad_id or not sede_id:
        return JsonResponse({'error': 'Faltan parámetros'}, status=400)
    
    try:
        especialidad = Especialidad.objects.get(id=especialidad_id)
        sede = Sede.objects.get(id=sede_id)
        
        medicos = MedicoProfile.objects.filter(
            especialidad=especialidad,
            user_profile__sede=sede,
            user_profile__activo=True
        ).select_related('user_profile__user')
        
        medicos_data = []
        for medico in medicos:
            medicos_data.append({
                'id': medico.id,
                'nombre': f"Dr. {medico.user_profile.nombre_completo}",
                'experiencia': medico.experiencia_anios,
                'precio': float(medico.consulta_precio_base)
            })
        
        return JsonResponse({'medicos': medicos_data})
        
    except (Especialidad.DoesNotExist, Sede.DoesNotExist):
        return JsonResponse({'error': 'Especialidad o sede no encontrada'}, status=404)

@require_POST
@login_required
def obtener_servicios_por_especialidad(request):
    """AJAX: Obtener servicios filtrados por especialidad"""
    especialidad_id = request.POST.get('especialidad_id')
    
    if not especialidad_id:
        return JsonResponse({'error': 'Falta especialidad'}, status=400)
    
    try:
        especialidad = Especialidad.objects.get(id=especialidad_id)
        servicios = Servicio.objects.filter(
            especialidad=especialidad,
            activo=True
        )
        
        servicios_data = []
        for servicio in servicios:
            servicios_data.append({
                'id': servicio.id,
                'nombre': servicio.nombre,
                'precio': float(servicio.precio_base),
                'duracion': servicio.duracion_minutos
            })
        
        return JsonResponse({'servicios': servicios_data})
        
    except Especialidad.DoesNotExist:
        return JsonResponse({'error': 'Especialidad no encontrada'}, status=404)

@require_POST
@login_required
def verificar_disponibilidad(request):
    """AJAX: Verificar disponibilidad de un médico en fecha y hora específicas"""
    medico_id = request.POST.get('medico_id')
    fecha = request.POST.get('fecha')
    hora = request.POST.get('hora')
    
    if not all([medico_id, fecha, hora]):
        return JsonResponse({'error': 'Faltan parámetros'}, status=400)
    
    try:
        medico = MedicoProfile.objects.get(id=medico_id)
        fecha_hora = datetime.strptime(f"{fecha} {hora}", "%Y-%m-%d %H:%M")
        
        # Verificar día de semana
        dia_semana = fecha_hora.weekday() + 1  # Convertir a nuestro formato
        
        # Verificar disponibilidad del médico
        disponible = DisponibilidadMedica.objects.filter(
            medico=medico,
            dia_semana=dia_semana,
            hora_inicio__lte=hora,
            hora_fin__gte=hora,
            activo=True
        ).exists()
        
        if not disponible:
            return JsonResponse({
                'disponible': False,
                'motivo': 'El médico no está disponible en este horario'
            })
        
        # Verificar si ya tiene cita a esa hora
        cita_existente = Cita.objects.filter(
            medico=medico,
            fecha_hora=fecha_hora,
            estado__in=['pendiente', 'confirmada']
        ).exists()
        
        if cita_existente:
            return JsonResponse({
                'disponible': False,
                'motivo': 'El médico ya tiene una cita agendada a esta hora'
            })
        
        return JsonResponse({'disponible': True})
        
    except MedicoProfile.DoesNotExist:
        return JsonResponse({'error': 'Médico no encontrado'}, status=404)
    except ValueError:
        return JsonResponse({'error': 'Formato de fecha u hora inválido'}, status=400)
