from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.http import JsonResponse
from .forms_validado import RegistroPacienteForm
from .authentication import CustomAuthBackend
from .email_config import enviar_correo_confirmacion

def registro_paciente(request):
    """Vista de registro de pacientes con campos de ubicación como texto"""
    if hasattr(request, 'user') and request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = RegistroPacienteForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                
                # Preparar datos para el correo de confirmación
                datos_correo = {
                    'primer_nombre': form.cleaned_data.get('primer_nombre'),
                    'segundo_nombre': form.cleaned_data.get('segundo_nombre', ''),
                    'primer_apellido': form.cleaned_data.get('primer_apellido'),
                    'segundo_apellido': form.cleaned_data.get('segundo_apellido', ''),
                    'email': form.cleaned_data.get('email'),
                    'username': form.cleaned_data.get('username'),
                    'password': form.cleaned_data.get('password1'),
                    'cedula': form.cleaned_data.get('cedula'),
                    'fecha_registro': user.fecha_nacimiento.strftime('%Y-%m-%d') if hasattr(user, 'fecha_nacimiento') and user.fecha_nacimiento else None
                }
                
                # Enviar correo de confirmación
                correo_enviado = enviar_correo_confirmacion(datos_correo)
                if correo_enviado:
                    messages.success(request, "Registro exitoso. Se ha enviado un correo de confirmación a tu email.")
                else:
                    messages.warning(request, "Registro exitoso, pero hubo un error al enviar el correo de confirmación.")
                
                # Autenticar al usuario después del registro
                username = form.cleaned_data.get('username')
                password = form.cleaned_data.get('password1')
                
                # Usar el backend personalizado para autenticación
                auth_backend = CustomAuthBackend()
                user_obj = auth_backend.authenticate(request, username=username, password=password)
                
                if user_obj:
                    login(request, user_obj, backend='usuarios.authentication.CustomAuthBackend')
                    return redirect('dashboard_paciente')
                else:
                    return redirect('login_paciente')
            except Exception as e:
                messages.error(request, f"Error al crear cuenta: {str(e)}")
        else:
            messages.error(request, "Corrige los errores del formulario")
    else:
        form = RegistroPacienteForm()
    
    return render(request, 'usuarios/registro_paciente_validado.html', {'form': form})
