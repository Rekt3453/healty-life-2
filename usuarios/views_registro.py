from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.http import JsonResponse
from .forms_registro import RegistroPacienteForm
from .models import Municipio, Ciudad, Parroquia

def registro_paciente(request):
    """Vista de registro de pacientes con selectores dependientes de Supabase"""
    if request.method == 'POST':
        form = RegistroPacienteForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                # Autenticar al usuario después del registro
                user_paciente = form.cleaned_data.get('user_paciente')
                if user_paciente:
                    user_obj = authenticate(
                        username=user_paciente.username, 
                        password=request.POST.get('password1')
                    )
                    if user_obj:
                        login(request, user_obj)
                        messages.success(request, "Cuenta creada con éxito")
                        return redirect('dashboard_paciente')
                else:
                    messages.success(request, "Cuenta creada con éxito")
                    return redirect('login_paciente')
            except Exception as e:
                messages.error(request, f"Error al crear cuenta: {str(e)}")
        else:
            messages.error(request, "Corrige los errores del formulario")
    else:
        form = RegistroPacienteForm()
    
    return render(request, 'usuarios/registro_paciente.html', {'form': form})

def cargar_municipios(request):
    """Retorna municipios filtrados por estado desde Supabase"""
    estado_id = request.GET.get('id_estado')
    if estado_id:
        municipios = Municipio.objects.filter(
            id_estado=estado_id
        ).order_by('municipio').values('id_municipio', 'municipio')
        return JsonResponse(list(municipios), safe=False)
    return JsonResponse([], safe=False)

def cargar_ciudades(request):
    """Retorna ciudades filtradas por municipio desde Supabase"""
    municipio_id = request.GET.get('id_municipio')
    if municipio_id:
        ciudades = Ciudad.objects.filter(
            id_municipio=municipio_id
        ).order_by('ciudad').values('id_ciudad', 'ciudad')
        return JsonResponse(list(ciudades), safe=False)
    return JsonResponse([], safe=False)

def cargar_parroquias(request):
    """Retorna parroquias filtradas por municipio desde Supabase"""
    municipio_id = request.GET.get('id_municipio')
    if municipio_id:
        parroquias = Parroquia.objects.filter(
            id_municipio=municipio_id
        ).order_by('parroquia').values('id_parroquia', 'parroquia')
        return JsonResponse(list(parroquias), safe=False)
    return JsonResponse([], safe=False)
