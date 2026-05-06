from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.http import Http404
from .models import Sede, UserProfile, PacienteProfile, MedicoProfile
from .forms import (
    CustomLoginForm, 
    PacienteRegistroForm, 
    MedicoRegistroForm, 
    RecepcionistaRegistroForm,
    UserProfileForm
)

class CustomLoginView(LoginView):
    form_class = CustomLoginForm
    template_name = 'usuarios/login.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Obtener sede_slug de los kwargs si existe
        self.sede_slug = kwargs.pop('sede_slug', None)
        if self.sede_slug:
            # Guardar la sede en la sesión
            request.session['sede_slug'] = self.sede_slug
            try:
                sede = Sede.objects.get(slug=self.sede_slug)
                request.session['sede_nombre'] = sede.nombre
            except Sede.DoesNotExist:
                pass
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.sede_slug:
            try:
                context['sede'] = Sede.objects.get(slug=self.sede_slug)
            except Sede.DoesNotExist:
                pass
        return context
    
    def get_success_url(self):
        user = self.request.user
        if hasattr(user, 'userprofile'):
            rol = user.userprofile.rol
            if rol == 'paciente' or rol == 'paciente_especial':
                return reverse_lazy('dashboard_paciente')
            elif rol == 'medico':
                return reverse_lazy('dashboard_medico')
            elif rol == 'recepcionista':
                return reverse_lazy('dashboard_recepcion')
            elif rol == 'gerente':
                return reverse_lazy('dashboard_gerente')
            elif rol == 'gerente_general':
                return reverse_lazy('dashboard_general')
        return reverse_lazy('dashboard_paciente')

def homepage(request):
    """Homepage principal del sitio"""
    return render(request, 'homepage_new.html', {})

def selector_sede(request, sede_slug=None):
    """Vista principal que muestra la nueva homepage o redirige a una sede específica"""
    if sede_slug:
        # Si se especifica una sede, buscarla y mostrar la página de la sede
        sede = get_object_or_404(Sede, slug=sede_slug, activa=True)
        return render(request, 'home_sede.html', {'sede': sede})
    else:
        # Si no se especifica sede, mostrar la nueva homepage profesional
        return render(request, 'homepage_simple.html', {})

def home_sede(request, sede_slug):
    """Página de bienvenida para cada sede específica"""
    sede = get_object_or_404(Sede, slug=sede_slug, activa=True)
    return render(request, 'home_sede.html', {'sede': sede})

@login_required
def dashboard_paciente(request):
    """Dashboard para pacientes"""
    # Buscar el perfil de paciente usando la nueva estructura
    from django.db import connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id_user_paceinte FROM \"User_paciente\" WHERE \"Usename\" = %s;", [request.user.username])
            result = cursor.fetchone()
            if not result:
                raise Http404("No se encontró tu perfil de paciente")
            
            user_paciente_id = result[0]
            paciente = PacienteProfile.objects.filter(id_user_paciente=user_paciente_id).first()
            if not paciente:
                raise Http404("No se encontró tu perfil de paciente")
    except Exception:
        raise Http404("No tienes permiso para ver esta página")
    
    context = {
        'paciente': paciente,
        'user': request.user
    }
    return render(request, 'dashboard/paciente.html', context)

@login_required
def dashboard_medico(request):
    """Dashboard para médicos"""
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.rol != 'medico':
        raise Http404("No tienes permiso para ver esta página")
    
    try:
        medico_profile = request.user.userprofile.medicoprofile
    except MedicoProfile.DoesNotExist:
        messages.error(request, "Tu perfil de médico no está completo. Contacta al administrador.")
        return redirect('perfil')
    
    context = {
        'user_profile': request.user.userprofile,
        'medico_profile': medico_profile,
        'sede_actual': request.user.userprofile.sede
    }
    return render(request, 'dashboard/medico.html', context)

@login_required
def dashboard_recepcion(request):
    """Dashboard para recepcionistas"""
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.rol != 'recepcionista':
        raise Http404("No tienes permiso para ver esta página")
    
    context = {
        'user_profile': request.user.userprofile,
        'sede_actual': request.user.userprofile.sede
    }
    return render(request, 'dashboard/recepcionista.html', context)

@login_required
def dashboard_gerente(request):
    """Dashboard para gerentes de sede"""
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.rol != 'gerente':
        raise Http404("No tienes permiso para ver esta página")
    
    context = {
        'user_profile': request.user.userprofile,
        'sede_actual': request.user.userprofile.sede
    }
    return render(request, 'dashboard/gerente.html', context)

@login_required
def dashboard_general(request):
    """Dashboard para gerente general"""
    if not hasattr(request.user, 'userprofile') or request.user.userprofile.rol != 'gerente_general':
        raise Http404("No tienes permiso para ver esta página")
    
    context = {
        'user_profile': request.user.userprofile,
        'sedes': Sede.objects.all()
    }
    return render(request, 'dashboard/general.html', context)

def registro_paciente(request, sede_slug=None):
    """Registro de nuevos pacientes"""
    if request.method == 'POST':
        form = PacienteRegistroForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                username = form.cleaned_data.get('username')
                messages.success(request, f'Cuenta creada para {username}!')
                
                # Autenticar y redirigir al dashboard
                user = authenticate(username=user.username, password=form.cleaned_data.get('password1'))
                if user:
                    login(request, user)
                    return redirect('dashboard_paciente')
                return redirect('login')
            except Exception as e:
                messages.error(request, f'Error al crear la cuenta: {str(e)}')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        initial = {}
        if sede_slug:
            try:
                # Intentar encontrar una sede existente
                sedes = Sede.objects.all()
                if sedes.exists():
                    initial['sede'] = sedes.first()
            except Exception:
                pass
        
        form = PacienteRegistroForm(initial=initial)
    
    return render(request, 'usuarios/registro_paciente.html', {'form': form})

@login_required
def registrar_medico(request):
    """Registro de médicos (solo gerentes)"""
    if not hasattr(request.user, 'userprofile') or not request.user.userprofile.puede_registrar_medicos():
        raise Http404("No tienes permiso para realizar esta acción")
    
    if request.method == 'POST':
        form = MedicoRegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Médico {user.get_full_name()} registrado exitosamente!')
            return redirect('gestion_usuarios')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = MedicoRegistroForm()
    
    return render(request, 'usuarios/registrar_medico.html', {'form': form})

@login_required
def registrar_recepcionista(request):
    """Registro de recepcionistas (solo gerentes)"""
    if not hasattr(request.user, 'userprofile') or not request.user.userprofile.puede_registrar_recepcionistas():
        raise Http404("No tienes permiso para realizar esta acción")
    
    if request.method == 'POST':
        form = RecepcionistaRegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Recepcionista {user.get_full_name()} registrado exitosamente!')
            return redirect('gestion_usuarios')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = RecepcionistaRegistroForm()
    
    return render(request, 'usuarios/registrar_recepcionista.html', {'form': form})

@login_required
def perfil(request):
    """Ver y editar perfil de usuario"""
    if not hasattr(request.user, 'userprofile'):
        messages.error(request, 'Tu perfil de usuario no está configurado correctamente.')
        return redirect('login')
    
    user_profile = request.user.userprofile
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado exitosamente!')
            return redirect('perfil')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = UserProfileForm(instance=user_profile)
    
    context = {
        'form': form,
        'user_profile': user_profile
    }
    return render(request, 'usuarios/perfil.html', context)

def logout_view(request):
    """Cerrar sesión"""
    logout(request)
    messages.success(request, 'Has cerrado sesión exitosamente.')
    return redirect('selector_sede')