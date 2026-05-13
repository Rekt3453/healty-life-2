from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.http import JsonResponse
from .forms_local import RegistroPacienteFormLocal

def registro_paciente(request):
    """Vista de registro de pacientes con datos locales"""
    if request.method == 'POST':
        form = RegistroPacienteFormLocal(request.POST)
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
        form = RegistroPacienteFormLocal()
    
    return render(request, 'usuarios/registro_paciente_new.html', {'form': form})

def cargar_municipios(request):
    """API endpoint para cargar municipios según estado (datos locales)"""
    estado_id = request.GET.get('estado_id')
    
    # Datos locales de municipios por estado
    municipios_data = {
        '1': [
            {'id_municipio': '1', 'municipio': 'Libertador'},
            {'id_municipio': '2', 'municipio': 'Baruta'},
        ],
        '2': [
            {'id_municipio': '3', 'municipio': 'Valencia'},
            {'id_municipio': '4', 'municipio': 'Guacara'},
        ],
        '3': [
            {'id_municipio': '5', 'municipio': 'Maracaibo'},
            {'id_municipio': '6', 'municipio': 'San Francisco'},
        ],
        '4': [
            {'id_municipio': '7', 'municipio': 'Sucre'},
            {'id_municipio': '8', 'municipio': 'Baruta'},
        ],
        '5': [
            {'id_municipio': '9', 'municipio': 'Anaco'},
            {'id_municipio': '10', 'municipio': 'Barcelona'},
        ],
    }
    
    if estado_id in municipios_data:
        return JsonResponse(municipios_data[estado_id], safe=False)
    return JsonResponse([], safe=False)

def cargar_ciudades(request):
    """API endpoint para cargar ciudades según estado (datos locales)"""
    estado_id = request.GET.get('estado_id')
    
    # Datos locales de ciudades por estado
    ciudades_data = {
        '1': [
            {'id_ciudad': '1', 'ciudad': 'Caracas'},
            {'id_ciudad': '2', 'ciudad': 'Los Teques'},
        ],
        '2': [
            {'id_ciudad': '3', 'ciudad': 'Valencia'},
            {'id_ciudad': '4', 'ciudad': 'Naguanagua'},
        ],
        '3': [
            {'id_ciudad': '5', 'ciudad': 'Maracaibo'},
            {'id_ciudad': '6', 'ciudad': 'San Francisco'},
        ],
        '4': [
            {'id_ciudad': '7', 'ciudad': 'Los Teques'},
            {'id_ciudad': '8', 'ciudad': 'Baruta'},
        ],
        '5': [
            {'id_ciudad': '9', 'ciudad': 'Barcelona'},
            {'id_ciudad': '10', 'ciudad': 'Puerto La Cruz'},
        ],
    }
    
    if estado_id in ciudades_data:
        return JsonResponse(ciudades_data[estado_id], safe=False)
    return JsonResponse([], safe=False)

def cargar_parroquias(request):
    """API endpoint para cargar parroquias según municipio (datos locales)"""
    municipio_id = request.GET.get('municipio_id')
    
    # Datos locales de parroquias por municipio
    parroquias_data = {
        '1': [
            {'id_parroquia': '1', 'parroquia': 'Altagracia'},
            {'id_parroquia': '2', 'parroquia': 'Catedral'},
            {'id_parroquia': '3', 'parroquia': 'San Juan'},
            {'id_parroquia': '4', 'parroquia': 'Santa Rosalía'},
        ],
        '2': [
            {'id_parroquia': '5', 'parroquia': 'Baruta'},
            {'id_parroquia': '6', 'parroquia': 'El Cafetal'},
        ],
        '3': [
            {'id_parroquia': '7', 'parroquia': 'San José'},
            {'id_parroquia': '8', 'parroquia': 'Catedral'},
        ],
        '4': [
            {'id_parroquia': '9', 'parroquia': 'San Francisco'},
            {'id_parroquia': '10', 'parroquia': 'Maracaibo'},
        ],
        '5': [
            {'id_parroquia': '11', 'parroquia': 'Petare'},
            {'id_parroquia': '12', 'parroquia': 'La Dolorita'},
        ],
        '6': [
            {'id_parroquia': '13', 'parroquia': 'Anaco'},
            {'id_parroquia': '14', 'parroquia': 'Santa Rosa'},
        ],
        '7': [
            {'id_parroquia': '15', 'parroquia': 'Barcelona'},
            {'id_parroquia': '16', 'parroquia': 'Guanta'},
        ],
    }
    
    if municipio_id in parroquias_data:
        return JsonResponse(parroquias_data[municipio_id], safe=False)
    return JsonResponse([], safe=False)
