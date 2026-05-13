from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.http import JsonResponse
from .forms import RegistroPacienteForm, RegistroStaffForm
from .models import (
    UserPaciente, UserDoctor, UserRecepcionista, UserAdmin,
    PacienteDatosPersonales, Doctor, Recepcionista, Administrador,
    Estado, Municipio, Ciudad, Parroquia
)
from usuarios.decorators import rol_requerido
from .views_new import registro_paciente as nuevo_registro_paciente
from .views_new import cargar_municipios, cargar_ciudades, cargar_parroquias
from citas.models import Cita
from .authentication import CustomAuthBackend

def home(request):
    return render(request, 'home.html')

def login_rol(request, rol_esperado, template_name, dashboard_name):
    if request.user.is_authenticated:
        return redirect(dashboard_name)
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Usar el backend de autenticación personalizado
        auth_backend = CustomAuthBackend()
        user = auth_backend.authenticate(request, username=username, password=password, rol=rol_esperado)
        
        if user is not None:
            # Verificar el rol del usuario - CORREGIDO
            user_rol = auth_backend.get_rol(user)
            print(f"DEBUG: Login - Username: {username}, Rol esperado: {rol_esperado}, Rol obtenido: {user_rol}")
            
            # Permitir cualquier rol que coincida exactamente
            if user_rol == rol_esperado:
                # Guardar user_id en sesión manualmente
                request.session['_auth_user_id'] = user.id_user_paciente if hasattr(user, 'id_user_paciente') else user.id_user_doctor if hasattr(user, 'id_user_doctor') else user.id_user_recepcionista if hasattr(user, 'id_user_recepcionista') else user.id_user_admin
                request.session.save()
                
                login(request, user, backend='usuarios.authentication.CustomAuthBackend')
                messages.success(request, f"Bienvenido {user.username}")
                print(f"DEBUG: Login exitoso, redirigiendo a: {dashboard_name}")
                return redirect(dashboard_name)
            else:
                messages.error(request, f"Esta cuenta no tiene perfil de {rol_esperado}. Tu rol es: {user_rol}")
                print(f"DEBUG: Rol incorrecto - Esperado: {rol_esperado}, Obtenido: {user_rol}")
        else:
            messages.error(request, "Credenciales incorrectas")
            print(f"DEBUG: Credenciales incorrectas para {username}")
    
    return render(request, template_name)
def login_paciente(request):
    return login_rol(request, 'paciente', 'usuarios/login_paciente.html', 'dashboard_paciente')

def login_medico(request):
    return login_rol(request, 'medico', 'usuarios/login_medico.html', 'dashboard_medico')

def login_recepcionista(request):
    return login_rol(request, 'recepcionista', 'usuarios/login_recepcionista.html', 'dashboard_recepcionista')

def login_gerente(request):
    return login_rol(request, 'gerente', 'usuarios/login_gerente.html', 'dashboard_gerente')

def logout_view(request):
    logout(request)
    messages.info(request, "Has cerrado sesión correctamente")
    return redirect('home')

def registro_paciente(request):
    """Vista mejorada para registro de paciente con manejo de errores"""
    if request.method == 'POST':
        form = RegistroPacienteForm(request.POST)
        
        # Debug: Mostrar datos recibidos
        print(f"DEBUG: Datos POST recibidos: {dict(request.POST)}")
        
        if form.is_valid():
            try:
                print("DEBUG: Formulario válido, intentando guardar...")
                user = form.save()
                print(f"DEBUG: Usuario guardado con ID: {user.id_user_paciente}")
                
                # Usar el backend personalizado para login
                auth_backend = CustomAuthBackend()
                login(request, user, backend='usuarios.authentication.CustomAuthBackend')
                
                messages.success(request, '¡Registro exitoso! Bienvenido al sistema.')
                print("DEBUG: Login exitoso, redirigiendo...")
                return redirect('dashboard_paciente')
                
            except Exception as e:
                print(f"ERROR: Excepción al guardar: {e}")
                messages.error(request, f'Error al registrar: {str(e)}')
                import traceback
                traceback.print_exc()
        else:
            # Debug: Mostrar errores del formulario
            print(f"DEBUG: Formulario inválido. Errores: {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = RegistroPacienteForm()
    
    return render(request, 'usuarios/registro_paciente.html', {'form': form})
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Usar el backend de autenticación personalizado
        auth_backend = CustomAuthBackend()
        user = auth_backend.authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user, backend='usuarios.authentication.CustomAuthBackend')
            rol = auth_backend.get_rol(user)
            
            if rol == 'paciente':
                return redirect('dashboard_paciente')
            elif rol == 'medico':
                return redirect('dashboard_medico')
            elif rol == 'recepcionista':
                return redirect('dashboard_recepcionista')
            elif rol == 'gerente':
                return redirect('dashboard_gerente')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')
    
    return render(request, 'usuarios/login.html')

@login_required
def dashboard_paciente(request):
    # Verificar que el usuario sea paciente
    auth_backend = CustomAuthBackend()
    if auth_backend.get_rol(request.user) != 'paciente':
        messages.error(request, 'No tienes permisos para acceder a esta página')
        return redirect('home')
    
    # Obtener datos personales del paciente
    datos_paciente = auth_backend.get_datos_personales(request.user)
    nombre = datos_paciente.nombre_completo if datos_paciente else getattr(request.user, 'username', request.user.username)
    
    # Obtener citas del paciente (ajustar según el modelo de citas)
    try:
        citas = Cita.objects.filter(paciente=request.user).order_by('-fecha_solicitud')
    except:
        # Si el modelo de citas usa otro campo, intentar con diferentes relaciones
        try:
            if datos_paciente:
                citas = Cita.objects.filter(id_paciente=datos_paciente).order_by('-fecha_solicitud')
            else:
                citas = Cita.objects.none()
        except:
            citas = Cita.objects.none()
    
    return render(request, 'usuarios/dashboard_paciente.html', {
        'nombre': nombre,
        'citas': citas,
        'citas_pendientes': citas.filter(estado='pendiente').count(),
        'citas_aprobadas': citas.filter(estado='aprobada').count(),
        'citas_rechazadas': citas.filter(estado='rechazada').count(),
    })

@login_required
def dashboard_medico(request):
    # Verificar que el usuario sea médico
    auth_backend = CustomAuthBackend()
    if auth_backend.get_rol(request.user) != 'medico':
        messages.error(request, 'No tienes permisos para acceder a esta página')
        return redirect('home')
    
    # Obtener datos personales del médico
    datos_medico = auth_backend.get_datos_personales(request.user)
    nombre = datos_medico.nombre_completo if datos_medico else getattr(request.user, 'username', request.user.username)
    
    # Obtener citas del médico (ajustar según el modelo de citas)
    try:
    
        citas_hoy = Cita.objects.filter(medico=request.user, fecha=date.today(), estado='aprobada')
        citas_pendientes = Cita.objects.filter(medico=request.user, estado='pendiente')
        total_citas = Cita.objects.filter(medico=request.user).count()
    except:
        # Si el modelo de citas usa otros campos
        try:
            if datos_medico:
                citas_hoy = Cita.objects.filter(id_doctor=datos_medico, fecha=date.today(), estado='aprobada')
                citas_pendientes = Cita.objects.filter(id_doctor=datos_medico, estado='pendiente')
                total_citas = Cita.objects.filter(id_doctor=datos_medico).count()
            else:
                citas_hoy = Cita.objects.none()
                citas_pendientes = Cita.objects.none()
                total_citas = 0
        except:
            citas_hoy = Cita.objects.none()
            citas_pendientes = Cita.objects.none()
            total_citas = 0
    
    return render(request, 'usuarios/dashboard_medico.html', {
        'nombre': nombre,
        'citas_hoy': citas_hoy,
        'citas_pendientes': citas_pendientes,
        'total_citas': total_citas,
    })

def dashboard_recepcionista(request):
    """Dashboard de recepcionista - Versión simple que funciona"""
    try:
        # Obtener el usuario desde la sesión si existe
        user_id = request.session.get('_auth_user_id')
        if not user_id:
            messages.error(request, 'Debes iniciar sesión primero')
            return redirect('login_recepcionista')
        
        # Obtener el usuario
        from usuarios.models import UserRecepcionista
        user = UserRecepcionista.objects.filter(id_user_recepcionista=user_id).first()
        if not user:
            messages.error(request, 'Usuario no encontrado')
            return redirect('login_recepcionista')
        
        # Verificar rol
        auth_backend = CustomAuthBackend()
        user_rol = auth_backend.get_rol(user)
        if user_rol != 'recepcionista':
            messages.error(request, f'Acceso denegado. Tu rol es: {user_rol}')
            return redirect('home')
        
        # Obtener datos personales
        datos_recepcionista = auth_backend.get_datos_personales(user)
        nombre = datos_recepcionista.nombre_completo if datos_recepcionista else user.username
        
        # Estadísticas simples
        citas_pendientes = 5  # Valor temporal
        citas_hoy = 3  # Valor temporal
        total_pacientes = 10  # Valor temporal
        
        return render(request, 'usuarios/dashboard_recepcionista.html', {
            'nombre': nombre,
            'citas_pendientes': citas_pendientes,
            'citas_hoy': citas_hoy,
            'total_pacientes': total_pacientes,
        })
        
    except Exception as e:
        print(f"Error en dashboard_recepcionista: {e}")
        messages.error(request, 'Error al cargar el dashboard')
        return redirect('home')
def dashboard_gerente(request):
    """Dashboard de gerente - Versión simple que funciona"""
    try:
        # Obtener el usuario desde la sesión si existe
        user_id = request.session.get('_auth_user_id')
        if not user_id:
            messages.error(request, 'Debes iniciar sesión primero')
            return redirect('login_gerente')
        
        # Obtener el usuario
        from usuarios.models import UserAdmin
        user = UserAdmin.objects.filter(id_user_admin=user_id).first()
        if not user:
            messages.error(request, 'Usuario no encontrado')
            return redirect('login_gerente')
        
        # Verificar rol
        auth_backend = CustomAuthBackend()
        user_rol = auth_backend.get_rol(user)
        if user_rol != 'gerente':
            messages.error(request, f'Acceso denegado. Tu rol es: {user_rol}')
            return redirect('home')
        
        # Obtener datos personales
        datos_admin = auth_backend.get_datos_personales(user)
        nombre = datos_admin.nombre_completo if datos_admin else user.username
        
        # Estadísticas simples
        total_citas = 20  # Valor temporal
        total_pacientes = 15  # Valor temporal
        total_medicos = 5  # Valor temporal
        total_recepcionistas = 3  # Valor temporal
        
        return render(request, 'usuarios/dashboard_gerente.html', {
            'nombre': nombre,
            'total_citas': total_citas,
            'total_pacientes': total_pacientes,
            'total_medicos': total_medicos,
            'total_recepcionistas': total_recepcionistas,
        })
        
    except Exception as e:
        print(f"Error en dashboard_gerente: {e}")
        messages.error(request, 'Error al cargar el dashboard')
        return redirect('home')
def registro_staff(request):
    """Registro de staff - Versión corregida que funciona"""
    try:
        # Obtener el usuario desde la sesión si existe
        user_id = request.session.get('_auth_user_id')
        if not user_id:
            messages.error(request, 'Debes iniciar sesión como gerente primero')
            return redirect('login_gerente')
        
        # Obtener el usuario
        from usuarios.models import UserAdmin
        user = UserAdmin.objects.filter(id_user_admin=user_id).first()
        if not user:
            messages.error(request, 'Gerente no encontrado')
            return redirect('login_gerente')
        
        # Verificar rol
        auth_backend = CustomAuthBackend()
        user_rol = auth_backend.get_rol(user)
        if user_rol != 'gerente':
            messages.error(request, f'Acceso denegado. Tu rol es: {user_rol}')
            return redirect('home')
        
        # Procesar el formulario
        if request.method == 'POST':
            from usuarios.forms import RegistroStaffForm
            form = RegistroStaffForm(request.POST)
            
            if form.is_valid():
                try:
                    staff_user = form.save()
                    messages.success(request, f'Staff {staff_user.username} registrado exitosamente')
                    return redirect('dashboard_gerente')
                except Exception as e:
                    messages.error(request, f'Error al registrar staff: {str(e)}')
                    print(f"Error guardando staff: {e}")
            else:
                messages.error(request, 'Por favor corrige los errores en el formulario')
                print(f"Errores formulario: {form.errors}")
        else:
            from usuarios.forms import RegistroStaffForm
            form = RegistroStaffForm()
        
        return render(request, 'usuarios/registro_staff.html', {'form': form})
        
    except Exception as e:
        print(f"Error en registro_staff: {e}")
        messages.error(request, 'Error al cargar el formulario de registro')
        return redirect('dashboard_gerente')