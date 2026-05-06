from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.views import LogoutView
from django.db.models import Sum
from datetime import date
from .forms import RegistroPacienteForm, RegistroStaffForm
from .decorators import rol_requerido
from citas.models import Cita

def home(request):
    return render(request, 'home.html')

def login_rol(request, rol_esperado, template_name, dashboard_name):
    if request.user.is_authenticated:
        return redirect(dashboard_name)
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.userprofile.rol == rol_esperado:
                login(request, user)
                messages.success(request, f"Bienvenido {user.username}")
                return redirect(dashboard_name)
            else:
                messages.error(request, f"Esta cuenta no tiene perfil de {rol_esperado}")
        else:
            messages.error(request, "Credenciales incorrectas")
    
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
    if request.method == 'POST':
        form = RegistroPacienteForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard_paciente')
    else:
        form = RegistroPacienteForm()
    return render(request, 'usuarios/registro_paciente.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            rol = user.userprofile.rol
            
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
@rol_requerido('paciente')
def dashboard_paciente(request):
    citas = Cita.objects.filter(paciente=request.user).order_by('-fecha_solicitud')
    return render(request, 'usuarios/dashboard_paciente.html', {
        'nombre': request.user.get_full_name() or request.user.username,
        'citas': citas,
        'citas_pendientes': citas.filter(estado='pendiente').count(),
        'citas_aprobadas': citas.filter(estado='aprobada').count(),
        'citas_rechazadas': citas.filter(estado='rechazada').count(),
    })

@login_required
@rol_requerido('medico')
def dashboard_medico(request):
    citas_hoy = Cita.objects.filter(medico=request.user, fecha=date.today(), estado='aprobada')
    citas_pendientes = Cita.objects.filter(medico=request.user, estado='pendiente')
    total_citas = Cita.objects.filter(medico=request.user).count()
    return render(request, 'usuarios/dashboard_medico.html', {
        'nombre': request.user.get_full_name() or request.user.username,
        'citas_hoy': citas_hoy,
        'citas_pendientes': citas_pendientes,
        'total_citas': total_citas,
    })

@login_required
@rol_requerido('recepcionista')
def dashboard_recepcionista(request):
    from .models import UserProfile
    citas_pendientes = Cita.objects.filter(estado='pendiente').count()
    citas_hoy = Cita.objects.filter(fecha=date.today()).count()
    total_pacientes = UserProfile.objects.filter(rol='paciente').count()
    return render(request, 'usuarios/dashboard_recepcionista.html', {
        'nombre': request.user.get_full_name() or request.user.username,
        'citas_pendientes': citas_pendientes,
        'citas_hoy': citas_hoy,
        'total_pacientes': total_pacientes,
    })

@login_required
@rol_requerido('gerente')
def dashboard_gerente(request):
    from .models import UserProfile
    from citas.models import Servicio
    total_citas = Cita.objects.count()
    total_pacientes = UserProfile.objects.filter(rol='paciente').count()
    total_medicos = UserProfile.objects.filter(rol='medico').count()
    total_ingresos = Servicio.objects.aggregate(total=Sum('precio'))['total'] or 0
    citas_por_estado = {
        'pendientes': Cita.objects.filter(estado='pendiente').count(),
        'aprobadas': Cita.objects.filter(estado='aprobada').count(),
        'rechazadas': Cita.objects.filter(estado='rechazada').count(),
        'completadas': Cita.objects.filter(estado='completada').count(),
    }
    
    # Calcular porcentajes para el dashboard
    porcentajes = {}
    if total_citas > 0:
        porcentajes = {
            'pendientes': round((citas_por_estado['pendientes'] / total_citas) * 100),
            'aprobadas': round((citas_por_estado['aprobadas'] / total_citas) * 100),
            'rechazadas': round((citas_por_estado['rechazadas'] / total_citas) * 100),
            'completadas': round((citas_por_estado['completadas'] / total_citas) * 100),
        }
    else:
        porcentajes = {
            'pendientes': 0,
            'aprobadas': 0,
            'rechazadas': 0,
            'completadas': 0,
        }
    
    return render(request, 'usuarios/dashboard_gerente.html', {
        'nombre': request.user.get_full_name() or request.user.username,
        'total_citas': total_citas,
        'total_pacientes': total_pacientes,
        'total_medicos': total_medicos,
        'total_ingresos': total_ingresos,
        'citas_por_estado': citas_por_estado,
        'porcentajes': porcentajes,
    })

@login_required
@rol_requerido('gerente')
def registro_staff(request):
    if request.method == 'POST':
        form = RegistroStaffForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Staff registrado exitosamente')
            return redirect('dashboard_gerente')
    else:
        form = RegistroStaffForm()
    return render(request, 'usuarios/registro_staff.html', {'form': form})
