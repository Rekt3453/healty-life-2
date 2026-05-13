from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.http import JsonResponse
from .forms_new import RegistroPacienteForm
from .models import Estado, Municipio, Ciudad, Parroquia

def registro_paciente(request):
    """Vista de registro de pacientes con selectores dependientes de Supabase"""
    if request.method == 'POST':
        form = RegistroPacienteForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                # Autenticar al usuario después del registro
                user_obj = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password1'])
                if user_obj:
                    login(request, user_obj)
                    messages.success(request, "Cuenta creada con éxito")
                    return redirect('dashboard_paciente')
            except Exception as e:
                messages.error(request, f"Error al crear cuenta: {str(e)}")
        else:
            messages.error(request, "Corrige los errores del formulario")
    else:
        form = RegistroPacienteForm()
    
    return render(request, 'usuarios/registro_paciente_new.html', {'form': form})

def cargar_municipios(request):
    """API endpoint para cargar municipios según estado desde Supabase"""
    estado_id = request.GET.get('estado_id')
    if estado_id:
        municipios = Municipio.objects.filter(id_estado=estado_id).values('id_municipio', 'municipio')
        return JsonResponse(list(municipios), safe=False)
    return JsonResponse([], safe=False)

def cargar_ciudades(request):
    """API endpoint para cargar ciudades según estado desde Supabase"""
    estado_id = request.GET.get('estado_id')
    if estado_id:
        ciudades = Ciudad.objects.filter(id_estado=estado_id).values('id_ciudad', 'ciudad')
        return JsonResponse(list(ciudades), safe=False)
    return JsonResponse([], safe=False)

def cargar_parroquias(request):
    """API endpoint para cargar parroquias según municipio desde Supabase"""
    municipio_id = request.GET.get('municipio_id')
    if municipio_id:
        parroquias = Parroquia.objects.filter(id_municipio=municipio_id).values('id_parroquia', 'parroquia')
        return JsonResponse(list(parroquias), safe=False)
    return JsonResponse([], safe=False)
