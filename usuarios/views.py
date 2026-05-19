from datetime import date
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
    Estado, Municipio, Ciudad, Parroquia, PacienteEspecial, Sede,
    DireccionPaciente, DireccionDoctor, DireccionRecepcionista,
)
from usuarios.decorators import rol_requerido
from .views_new import registro_paciente as nuevo_registro_paciente
from .views_new import cargar_municipios, cargar_ciudades, cargar_parroquias
from citas.models import Cita, PagoCita, HistorialMedicoPaciente, Alergias, TipoSangre, Vacunas, EspecialidadDoctor, Consultorio, Horario
from .authentication import CustomAuthBackend
from .email_config import enviar_correo_confirmacion

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
                login(request, user, backend='usuarios.authentication.CustomAuthBackend')
                request.session['_hl_user_model'] = type(user).__name__
                messages.success(request, f"Bienvenido {user.username}")
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
    """
    Vista de registro de pacientes.
    Maneja pacientes menores de edad, pacientes especiales y selección de sede.
    """
    if request.user.is_authenticated:
        try:
            auth_backend = CustomAuthBackend()
            rol = auth_backend.get_rol(request.user)
            return redirect(f'dashboard_{rol}')
        except:
            logout(request)
    
    if request.method == 'POST':
        form = RegistroPacienteForm(request.POST)
        
        if form.is_valid():
            try:
                user = form.save()
                
                # Determinar si es paciente especial
                fecha_nacimiento = form.cleaned_data.get('fecha_nacimiento')
                tiene_condicion = form.cleaned_data.get('tiene_condicion_especial', False)
                hoy = date.today()
                edad = hoy.year - fecha_nacimiento.year - ((hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
                es_menor = edad < 18
                es_paciente_especial = es_menor or tiene_condicion
                
                # Enviar correo de bienvenida
                try:
                    datos_paciente = PacienteDatosPersonales.objects.filter(id_user_paciente=user).first()
                    password_plana = form.cleaned_data.get('password1', '')
                    enviar_correo_confirmacion({
                        'primer_nombre':   datos_paciente.nombre_1   if datos_paciente else '',
                        'segundo_nombre':  datos_paciente.nombre_2   if datos_paciente else '',
                        'primer_apellido': datos_paciente.apellido_1 if datos_paciente else '',
                        'segundo_apellido':datos_paciente.apellido_2 if datos_paciente else '',
                        'email':    user.email,
                        'username': user.username,
                        'password': password_plana,
                        'cedula':   datos_paciente.cedula if datos_paciente else '',
                    })
                except Exception as mail_err:
                    print(f'WARN: No se pudo enviar correo de bienvenida: {mail_err}')

                # Usar el backend personalizado para login
                auth_backend = CustomAuthBackend()
                login(request, user, backend='usuarios.authentication.CustomAuthBackend')

                # Mensaje personalizado según tipo de paciente
                if es_paciente_especial:
                    if es_menor:
                        messages.success(request,
                            "Cuenta creada con éxito. Has sido registrado como paciente especial (menor de edad). "
                            "Los datos de tu tutor han sido guardados. Revisa tu correo electrónico.")
                    else:
                        messages.success(request,
                            "Cuenta creada con éxito. Has sido registrado como paciente especial. "
                            "Revisa tu correo electrónico.")
                else:
                    messages.success(request,
                        "Cuenta creada con éxito. Bienvenido al sistema. Revisa tu correo electrónico.")

                return redirect('dashboard_paciente')
                
            except Exception as e:
                messages.error(request, f'Error al registrar: {str(e)}')
                import traceback
                traceback.print_exc()
        else:
            # Mostrar errores específicos
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = RegistroPacienteForm()
    
    # Pasar sedes disponibles al template
    from .models import Sede
    sedes = Sede.objects.filter(status=True).order_by('nombre_sede')
    
    context = {
        'form': form,
        'sedes': sedes,
    }
    
    return render(request, 'usuarios/registro_paciente.html', context)
# ==================== PERFIL PACIENTE ====================

@login_required(login_url='/login/paciente/')
@rol_requerido('paciente')
def perfil_paciente(request):
    user = request.user
    paciente = PacienteDatosPersonales.objects.filter(id_user_paciente=user).first()

    # ---- POST handlers ----
    if request.method == 'POST':
        action = request.POST.get('action', '')

        if action == 'update_perfil':
            try:
                nuevo_email = request.POST.get('email', '').strip()
                if nuevo_email and nuevo_email != user.email:
                    user.email = nuevo_email
                    user.save()

                fn_raw = request.POST.get('fecha_nacimiento', '').strip()
                fecha_nac = None
                if fn_raw:
                    try:
                        from datetime import datetime as _dt
                        fecha_nac = _dt.strptime(fn_raw, '%Y-%m-%d')
                    except ValueError:
                        pass

                datos = {
                    'nombre_1':     request.POST.get('nombre_1', '').strip(),
                    'nombre_2':     request.POST.get('nombre_2', '').strip() or None,
                    'apellido_1':   request.POST.get('apellido_1', '').strip(),
                    'apellido_2':   request.POST.get('apellido_2', '').strip() or None,
                    'telefono':     request.POST.get('telefono', '').strip() or None,
                    'sexo':         request.POST.get('sexo', '').strip() or None,
                    'cedula':       request.POST.get('cedula', '').strip(),
                    'tipo_cedula':  request.POST.get('tipo_cedula', '').strip() or None,
                    'fecha_nacimiento': fecha_nac,
                    'id_sede':      user.id_sede,
                    'id_user_paciente': user,
                    'status':       True,
                }
                if paciente:
                    for k, v in datos.items():
                        setattr(paciente, k, v)
                    paciente.save()
                    messages.success(request, '✅ Perfil actualizado correctamente.')
                else:
                    if datos['nombre_1'] and datos['apellido_1'] and datos['cedula']:
                        PacienteDatosPersonales.objects.create(**datos)
                        messages.success(request, '✅ Perfil creado correctamente.')
                    else:
                        messages.error(request, 'Nombre, apellido y cédula son obligatorios.')
            except Exception as e:
                messages.error(request, f'Error al actualizar perfil: {e}')
            return redirect('perfil_paciente')

        elif action == 'update_password':
            pwd_actual   = request.POST.get('password_actual', '')
            pwd_nuevo    = request.POST.get('password_nuevo', '')
            pwd_confirm  = request.POST.get('password_confirmar', '')
            if not user.check_password(pwd_actual):
                messages.error(request, 'La contraseña actual es incorrecta.')
            elif pwd_nuevo != pwd_confirm:
                messages.error(request, 'Las contraseñas nuevas no coinciden.')
            elif len(pwd_nuevo) < 6:
                messages.error(request, 'Mínimo 6 caracteres.')
            else:
                try:
                    user.set_password(pwd_nuevo)
                    user.save()
                    messages.success(request, '✅ Contraseña actualizada.')
                except Exception as e:
                    messages.error(request, f'Error: {e}')
            return redirect('perfil_paciente')

        elif action == 'update_direccion':
            try:
                dir_data = {
                    'id_estado_id':    request.POST.get('id_estado') or None,
                    'id_municipio_id': request.POST.get('id_municipio') or None,
                    'id_parroquia_id': request.POST.get('id_parroquia') or None,
                    'id_ciudad_id':    request.POST.get('id_ciudad') or None,
                    'direccion':       request.POST.get('direccion', '').strip(),
                    'referencia':      request.POST.get('referencia', '').strip() or None,
                }
                if paciente and paciente.id_direccion_paciente_id:
                    DireccionPaciente.objects.filter(
                        pk=paciente.id_direccion_paciente_id
                    ).update(**dir_data)
                elif paciente:
                    nueva_dir = DireccionPaciente(**dir_data)
                    nueva_dir.save()
                    paciente.id_direccion_paciente = nueva_dir
                    paciente.save()
                messages.success(request, '✅ Dirección actualizada.')
            except Exception as e:
                messages.error(request, f'Error al actualizar dirección: {e}')
            return redirect('perfil_paciente')

    # ---- GET: recopilar datos ----
    historial = None
    direccion = None
    tipo_sangre_obj = alergia_obj = vacuna_obj = tutor = None

    if paciente:
        historial = HistorialMedicoPaciente.objects.filter(id_paciente=paciente).first()
        if paciente.id_direccion_paciente_id:
            try:
                direccion = DireccionPaciente.objects.get(pk=paciente.id_direccion_paciente_id)
            except DireccionPaciente.DoesNotExist:
                pass
        if historial:
            tipo_sangre_obj = historial.id_tipo_sangre
            alergia_obj     = historial.id_alergias
            vacuna_obj      = historial.id_vacunas
        tutor = PacienteEspecial.objects.filter(id_paciente_tutor=paciente).first()

    citas_qs = Cita.objects.none()
    pagos_qs = PagoCita.objects.none()
    if paciente:
        citas_qs = Cita.objects.filter(id_paciente=paciente).select_related(
            'id_doctor', 'id_especialidades', 'id_sede'
        ).order_by('-fecha_emision')
        pagos_qs = PagoCita.objects.filter(id_paciente=paciente).order_by('-fecha_consulta')

    try:
        citas_activas   = citas_qs.filter(status=True).count()
        citas_inactivas = citas_qs.filter(status=False).count()
        total_citas     = citas_qs.count()
    except Exception:
        citas_activas = citas_inactivas = total_citas = 0

    proxima_cita = None
    try:
        from datetime import datetime as _dt2
        proxima_cita = citas_qs.filter(
            status=True, fecha_consulta__gte=_dt2.now()
        ).order_by('fecha_consulta').first()
    except Exception:
        pass

    try:
        pagos_lista = list(pagos_qs[:20])
        total_pagado    = sum((p.monto_pagar or 0) for p in pagos_lista if p.status)
        pendiente_pago  = sum((p.monto_pagar or 0) for p in pagos_lista if not p.status)
    except Exception:
        pagos_lista = []
        total_pagado = pendiente_pago = 0

    edad = None
    if paciente and paciente.fecha_nacimiento:
        from datetime import date as _date
        hoy = _date.today()
        fn = paciente.fecha_nacimiento.date() if hasattr(paciente.fecha_nacimiento, 'date') else paciente.fecha_nacimiento
        edad = hoy.year - fn.year - ((hoy.month, hoy.day) < (fn.month, fn.day))

    municipios_dir = []
    parroquias_dir = []
    ciudades_dir   = []
    if direccion:
        try:
            municipios_dir = list(Municipio.objects.filter(id_estado=direccion.id_estado_id))
            parroquias_dir = list(Parroquia.objects.filter(id_municipio=direccion.id_municipio_id))
            ciudades_dir   = list(Ciudad.objects.filter(id_estado=direccion.id_estado_id))
        except Exception:
            pass

    context = {
        'user':              user,
        'paciente':          paciente,
        'historial':         historial,
        'direccion':         direccion,
        'tipo_sangre':       tipo_sangre_obj,
        'alergia':           alergia_obj,
        'vacuna':            vacuna_obj,
        'tutor':             tutor,
        'citas_recientes':   citas_qs[:10],
        'proxima_cita':      proxima_cita,
        'pagos_recientes':   pagos_lista[:10],
        'citas_activas':     citas_activas,
        'citas_inactivas':   citas_inactivas,
        'total_citas':       total_citas,
        'total_pagado':      total_pagado,
        'pendiente_pago':    pendiente_pago,
        'edad':              edad,
        'estados':           Estado.objects.all().order_by('estado'),
        'municipios_dir':    municipios_dir,
        'parroquias_dir':    parroquias_dir,
        'ciudades_dir':      ciudades_dir,
        'tipos_sangre':      TipoSangre.objects.all(),
        'alergias_opciones': Alergias.objects.all(),
        'vacunas_opciones':  Vacunas.objects.all(),
    }
    return render(request, 'usuarios/perfil_paciente.html', context)


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

@login_required(login_url='/login/paciente/')
def dashboard_paciente(request):
    # Verificar que el usuario sea paciente
    auth_backend = CustomAuthBackend()
    if auth_backend.get_rol(request.user) != 'paciente':
        messages.error(request, 'No tienes permisos para acceder a esta página')
        return redirect('home')
    
    # Obtener datos personales del paciente
    datos_paciente = auth_backend.get_datos_personales(request.user)
    nombre = datos_paciente.nombre_completo if datos_paciente else getattr(request.user, 'username', request.user.username)
    
    # Obtener citas del paciente usando los campos reales del esquema Supabase
    try:
        if datos_paciente:
            citas = Cita.objects.filter(id_paciente=datos_paciente).order_by('-fecha_emision')
        else:
            citas = Cita.objects.none()
    except Exception:
        citas = Cita.objects.none()

    try:
        citas_activas   = citas.filter(status=True).count()
        citas_canceladas = citas.filter(status=False).count()
        total_citas     = citas.count()
    except Exception:
        citas_activas = citas_canceladas = total_citas = 0

    return render(request, 'usuarios/dashboard_paciente.html', {
        'nombre': nombre,
        'citas': citas,
        'citas_pendientes': citas_activas,
        'citas_aprobadas': citas_activas,
        'citas_rechazadas': citas_canceladas,
        'total_citas': total_citas,
    })

@login_required(login_url='/login/medico/')
def dashboard_medico(request):
    # Verificar que el usuario sea médico
    auth_backend = CustomAuthBackend()
    if auth_backend.get_rol(request.user) != 'medico':
        messages.error(request, 'No tienes permisos para acceder a esta página')
        return redirect('home')
    
    # Obtener datos personales del médico
    datos_medico = auth_backend.get_datos_personales(request.user)
    nombre = datos_medico.nombre_completo if datos_medico else getattr(request.user, 'username', request.user.username)
    
    # Obtener citas del médico usando los campos reales del esquema Supabase
    try:
        if datos_medico:
            citas_hoy = Cita.objects.filter(
                id_doctor=datos_medico,
                fecha_consulta__date=date.today(),
                status=True
            )
            citas_pendientes = Cita.objects.filter(id_doctor=datos_medico, status=True)
            total_citas = Cita.objects.filter(id_doctor=datos_medico).count()
        else:
            citas_hoy = Cita.objects.none()
            citas_pendientes = Cita.objects.none()
            total_citas = 0
    except Exception:
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
    """Dashboard de recepcionista — datos reales de citas"""
    try:
        user_id = request.session.get('_auth_user_id')
        if not user_id:
            messages.error(request, 'Debes iniciar sesión primero')
            return redirect('login_recepcionista')
        
        from usuarios.models import UserRecepcionista
        user = UserRecepcionista.objects.filter(id_user_recepcionista=user_id).first()
        if not user:
            messages.error(request, 'Usuario no encontrado')
            return redirect('login_recepcionista')
        
        auth_backend = CustomAuthBackend()
        user_rol = auth_backend.get_rol(user)
        if user_rol != 'recepcionista':
            messages.error(request, f'Acceso denegado. Tu rol es: {user_rol}')
            return redirect('home')
        
        datos_recepcionista = auth_backend.get_datos_personales(user)
        nombre = datos_recepcionista.nombre_completo if datos_recepcionista else user.username
        
        # Datos reales — esquema Supabase: status bool, fecha_consulta datetime
        try:
            hoy = date.today()
            citas_pendientes = Cita.objects.filter(status=True).count()
            citas_hoy = Cita.objects.filter(fecha_consulta__date=hoy).count()
            citas_recientes = Cita.objects.select_related(
                'id_paciente', 'id_doctor'
            ).order_by('-fecha_emision')[:10]
        except Exception:
            citas_pendientes = 0
            citas_hoy = 0
            citas_recientes = []
        
        try:
            total_pacientes = UserPaciente.objects.filter(status=True).count()
        except Exception:
            total_pacientes = 0
        
        return render(request, 'usuarios/dashboard_recepcionista.html', {
            'nombre': nombre,
            'citas_pendientes': citas_pendientes,
            'citas_hoy': citas_hoy,
            'total_pacientes': total_pacientes,
            'citas_recientes': citas_recientes,
        })
        
    except Exception as e:
        print(f"Error en dashboard_recepcionista: {e}")
        messages.error(request, 'Error al cargar el dashboard')
        return redirect('home')
def dashboard_gerente(request):
    """Dashboard de gerente — datos reales"""
    try:
        user_id = request.session.get('_auth_user_id')
        if not user_id:
            messages.error(request, 'Debes iniciar sesión primero')
            return redirect('login_gerente')
        
        from usuarios.models import UserAdmin
        user = UserAdmin.objects.filter(id_user_admin=user_id).first()
        if not user:
            messages.error(request, 'Usuario no encontrado')
            return redirect('login_gerente')
        
        auth_backend = CustomAuthBackend()
        user_rol = auth_backend.get_rol(user)
        if user_rol != 'gerente':
            messages.error(request, f'Acceso denegado. Tu rol es: {user_rol}')
            return redirect('home')
        
        datos_admin = auth_backend.get_datos_personales(user)
        nombre = datos_admin.nombre_completo if datos_admin else user.username
        
        # Datos reales — Cita puede no existir en Supabase aún
        try:
            total_citas = Cita.objects.count()
        except Exception:
            total_citas = 0
        
        try:
            total_pacientes = UserPaciente.objects.count()
            total_medicos = UserDoctor.objects.count()
            total_recepcionistas = UserRecepcionista.objects.count()
        except Exception:
            total_pacientes = total_medicos = total_recepcionistas = 0
        
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
def login_admin(request):
    """Login para administradores (alias de login_gerente en esta instalación)"""
    return login_rol(request, 'gerente', 'usuarios/login_gerente.html', 'dashboard_gerente')

@login_required(login_url='/login/gerente/')
def dashboard_root(request):
    """Dashboard root — redirige al panel de gerente (no existen roles super_admin/root)"""
    auth_backend = CustomAuthBackend()
    if auth_backend.get_rol(request.user) != 'gerente':
        messages.error(request, 'Acceso denegado.')
        return redirect('home')
    return redirect('dashboard_gerente')

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
        return redirect('home')

def lista_personal(request):
    """Lista doctores y recepcionistas de la sede del gerente."""
    try:
        user_id = request.session.get('_auth_user_id')
        if not user_id:
            messages.error(request, 'Debes iniciar sesión como gerente primero')
            return redirect('login_gerente')
        user = UserAdmin.objects.filter(id_user_admin=user_id).first()
        if not user:
            messages.error(request, 'Gerente no encontrado')
            return redirect('login_gerente')
        auth_backend = CustomAuthBackend()
        if auth_backend.get_rol(user) != 'gerente':
            messages.error(request, 'Acceso denegado')
            return redirect('home')
        sede = user.id_sede

        doctores = Doctor.objects.filter(id_sede=sede).select_related(
            'id_user_doctor', 'id_direccion_doctor'
        )
        recepcionistas = Recepcionista.objects.filter(id_sede=sede).select_related(
            'id_user_recepcionista', 'id_direccion_recepcionista'
        )

        espec_ids = {d.id_especialidad_doctor for d in doctores if d.id_especialidad_doctor}
        especialidades = {}
        if espec_ids:
            for e in EspecialidadDoctor.objects.select_related('id_especialidad').filter(pk__in=espec_ids):
                especialidades[e.pk] = e.id_especialidad.tipo_especialidad if e.id_especialidad else '-'
        for d in doctores:
            d.especialidad_nombre = especialidades.get(d.id_especialidad_doctor, '-')

        return render(request, 'usuarios/lista_personal.html', {
            'doctores': doctores,
            'recepcionistas': recepcionistas,
            'sede': sede,
        })
    except Exception as e:
        print(f"Error en lista_personal: {e}")
        messages.error(request, 'Error al cargar la lista de personal')
        return redirect('dashboard_gerente')


def editar_doctor_view(request, id_doctor):
    """Editar datos de un doctor existente (solo gerente de su sede)."""
    try:
        user_id = request.session.get('_auth_user_id')
        if not user_id:
            messages.error(request, 'Debes iniciar sesión como gerente primero')
            return redirect('login_gerente')
        user = UserAdmin.objects.filter(id_user_admin=user_id).first()
        if not user:
            messages.error(request, 'Gerente no encontrado')
            return redirect('login_gerente')
        auth_backend = CustomAuthBackend()
        if auth_backend.get_rol(user) != 'gerente':
            messages.error(request, 'Acceso denegado')
            return redirect('home')
        sede = user.id_sede

        doctor = Doctor.objects.filter(
            pk=id_doctor, id_sede=sede
        ).select_related('id_user_doctor', 'id_direccion_doctor').first()
        if not doctor:
            messages.error(request, 'Doctor no encontrado o no pertenece a esta sede.')
            return redirect('lista_personal')

        user_doctor = doctor.id_user_doctor
        direccion   = doctor.id_direccion_doctor

        from usuarios.forms import EditarDoctorForm
        if request.method == 'POST':
            form = EditarDoctorForm(
                request.POST,
                doctor_pk=doctor.pk,
                user_doctor_pk=user_doctor.pk if user_doctor else None,
                sede_id=sede.pk if sede else None,
            )
            if form.is_valid():
                try:
                    form.save(doctor, user_doctor, direccion)
                    messages.success(request, 'Doctor actualizado correctamente.')
                    return redirect('lista_personal')
                except Exception as e:
                    messages.error(request, f'Error al guardar: {str(e)}')
                    print(f"Error guardando doctor {id_doctor}: {e}")
            else:
                messages.error(request, 'Por favor corrige los errores en el formulario.')
                print(f"Errores editar_doctor: {form.errors}")
        else:
            initial = {}
            if user_doctor:
                initial.update({
                    'username': user_doctor.username,
                    'email':    user_doctor.email,
                    'status':   user_doctor.status,
                })
            initial.update({
                'nombre_1':   doctor.nombre_1 or '',
                'nombre_2':   doctor.nombre_2 or '',
                'apellido_1': doctor.apellido_1 or '',
                'apellido_2': doctor.apellido_2 or '',
                'cedula':     doctor.cedula or '',
                'tipo_cedula': doctor.tipo_cedula or 'V',
                'sexo':       doctor.sexo or 'M',
                'telefono':   doctor.telefono or '',
                'fecha_nacimiento': doctor.fecha_nacimiento.date() if doctor.fecha_nacimiento else None,
                'id_especialidad_doctor': EspecialidadDoctor.objects.filter(pk=doctor.id_especialidad_doctor).first() if doctor.id_especialidad_doctor else None,
                'id_consultorio': Consultorio.objects.filter(pk=doctor.id_consultorio).first() if doctor.id_consultorio else None,
                'id_horario': Horario.objects.filter(pk=doctor.id_horario).first() if doctor.id_horario else None,
            })
            if direccion:
                initial.update({
                    'id_estado':    direccion.id_estado,
                    'id_municipio': direccion.id_municipio,
                    'id_ciudad':    direccion.id_ciudad,
                    'id_parroquia': direccion.id_parroquia,
                    'direccion':    direccion.direccion or '',
                    'referencia':   direccion.referencia or '',
                    'latitud':      direccion.latitud or '',
                    'longitud':     direccion.longitud or '',
                })
            form = EditarDoctorForm(
                initial=initial,
                doctor_pk=doctor.pk,
                user_doctor_pk=user_doctor.pk if user_doctor else None,
                sede_id=sede.pk if sede else None,
            )

        return render(request, 'usuarios/editar_doctor.html', {
            'form': form, 'doctor': doctor, 'sede': sede,
        })
    except Exception as e:
        print(f"Error en editar_doctor_view: {e}")
        messages.error(request, 'Error al cargar el formulario de edición')
        return redirect('lista_personal')


def editar_recepcionista_view(request, id_recepcionista):
    """Editar datos de una recepcionista existente (solo gerente de su sede)."""
    try:
        user_id = request.session.get('_auth_user_id')
        if not user_id:
            messages.error(request, 'Debes iniciar sesión como gerente primero')
            return redirect('login_gerente')
        user = UserAdmin.objects.filter(id_user_admin=user_id).first()
        if not user:
            messages.error(request, 'Gerente no encontrado')
            return redirect('login_gerente')
        auth_backend = CustomAuthBackend()
        if auth_backend.get_rol(user) != 'gerente':
            messages.error(request, 'Acceso denegado')
            return redirect('home')
        sede = user.id_sede

        recepcionista = Recepcionista.objects.filter(
            pk=id_recepcionista, id_sede=sede
        ).select_related('id_user_recepcionista', 'id_direccion_recepcionista').first()
        if not recepcionista:
            messages.error(request, 'Recepcionista no encontrada o no pertenece a esta sede.')
            return redirect('lista_personal')

        user_recepcionista = recepcionista.id_user_recepcionista
        direccion          = recepcionista.id_direccion_recepcionista

        from usuarios.forms import EditarRecepcionistaForm
        if request.method == 'POST':
            form = EditarRecepcionistaForm(
                request.POST,
                recepcionista_pk=recepcionista.pk,
                user_recepcionista_pk=user_recepcionista.pk if user_recepcionista else None,
            )
            if form.is_valid():
                try:
                    form.save(recepcionista, user_recepcionista, direccion)
                    messages.success(request, 'Recepcionista actualizada correctamente.')
                    return redirect('lista_personal')
                except Exception as e:
                    messages.error(request, f'Error al guardar: {str(e)}')
                    print(f"Error guardando recepcionista {id_recepcionista}: {e}")
            else:
                messages.error(request, 'Por favor corrige los errores en el formulario.')
                print(f"Errores editar_recepcionista: {form.errors}")
        else:
            initial = {}
            if user_recepcionista:
                initial.update({
                    'username': user_recepcionista.username,
                    'email':    user_recepcionista.email,
                    'status':   user_recepcionista.status,
                })
            initial.update({
                'nombre_1':   recepcionista.nombre_1 or '',
                'nombre_2':   recepcionista.nombre_2 or '',
                'apellido_1': recepcionista.apellido_1 or '',
                'apellido_2': recepcionista.apellido_2 or '',
                'cedula':     recepcionista.cedula or '',
                'tipo_cedula': recepcionista.tipo_cedula or 'V',
                'sexo':       recepcionista.sexo or 'M',
                'telefono':   recepcionista.telefono or '',
                'fecha_nacimiento': recepcionista.fecha_nacimiento.date() if recepcionista.fecha_nacimiento else None,
            })
            if direccion:
                initial.update({
                    'id_estado':    direccion.id_estado,
                    'id_municipio': direccion.id_municipio,
                    'id_ciudad':    direccion.id_ciudad,
                    'id_parroquia': direccion.id_parroquia,
                    'direccion':    direccion.direccion or '',
                    'referencia':   direccion.referencia or '',
                    'latitud':      direccion.latitud or '',
                    'longitud':     direccion.longitud or '',
                })
            form = EditarRecepcionistaForm(
                initial=initial,
                recepcionista_pk=recepcionista.pk,
                user_recepcionista_pk=user_recepcionista.pk if user_recepcionista else None,
            )

        return render(request, 'usuarios/editar_recepcionista.html', {
            'form': form, 'recepcionista': recepcionista, 'sede': sede,
        })
    except Exception as e:
        print(f"Error en editar_recepcionista_view: {e}")
        messages.error(request, 'Error al cargar el formulario de edición')
        return redirect('lista_personal')


def registrar_doctor(request):
    """Registro exclusivo de doctores con credenciales propias."""
    try:
        user_id = request.session.get('_auth_user_id')
        if not user_id:
            messages.error(request, 'Debes iniciar sesión como gerente primero')
            return redirect('login_gerente')
        from usuarios.models import UserAdmin
        user = UserAdmin.objects.filter(id_user_admin=user_id).first()
        if not user:
            messages.error(request, 'Gerente no encontrado')
            return redirect('login_gerente')
        auth_backend = CustomAuthBackend()
        if auth_backend.get_rol(user) != 'gerente':
            messages.error(request, 'Acceso denegado')
            return redirect('home')
        sede = user.id_sede
        if request.method == 'POST':
            from usuarios.forms import RegistrarDoctorForm
            form = RegistrarDoctorForm(request.POST, sede_id=sede.id_sede if sede else None)
            if form.is_valid():
                try:
                    password_plana = form.cleaned_data['password1']
                    user_doctor = form.save(sede)
                    try:
                        from .email_config import enviar_correo_doctor
                        enviar_correo_doctor({
                            'primer_nombre':  form.cleaned_data.get('nombre_1', ''),
                            'segundo_nombre': form.cleaned_data.get('nombre_2', ''),
                            'primer_apellido': form.cleaned_data.get('apellido_1', ''),
                            'segundo_apellido': form.cleaned_data.get('apellido_2', ''),
                            'email':    form.cleaned_data.get('email', ''),
                            'username': user_doctor.username,
                            'password': password_plana,
                        })
                    except Exception as mail_err:
                        print(f'WARN: No se pudo enviar correo al médico: {mail_err}')
                    messages.success(request, f'Doctor {user_doctor.username} registrado. Se envió un correo con sus credenciales.')
                    return redirect('dashboard_gerente')
                except Exception as e:
                    messages.error(request, f'Error al registrar el doctor: {str(e)}')
                    print(f"Error guardando doctor: {e}")
            else:
                messages.error(request, 'Por favor corrige los errores en el formulario.')
                print(f"Errores formulario doctor: {form.errors}")
        else:
            from usuarios.forms import RegistrarDoctorForm
            form = RegistrarDoctorForm(sede_id=sede.id_sede if sede else None)
        return render(request, 'usuarios/registrar_doctor.html', {'form': form, 'sede': sede})
    except Exception as e:
        print(f"Error en registrar_doctor: {e}")
        messages.error(request, 'Error al cargar el formulario')
        return redirect('home')


def registrar_recepcionista(request):
    """Registro exclusivo de recepcionistas con credenciales propias."""
    try:
        user_id = request.session.get('_auth_user_id')
        if not user_id:
            messages.error(request, 'Debes iniciar sesión como gerente primero')
            return redirect('login_gerente')
        from usuarios.models import UserAdmin
        user = UserAdmin.objects.filter(id_user_admin=user_id).first()
        if not user:
            messages.error(request, 'Gerente no encontrado')
            return redirect('login_gerente')
        auth_backend = CustomAuthBackend()
        if auth_backend.get_rol(user) != 'gerente':
            messages.error(request, 'Acceso denegado')
            return redirect('home')
        sede = user.id_sede
        if request.method == 'POST':
            from usuarios.forms import RegistrarRecepcionistaForm
            form = RegistrarRecepcionistaForm(request.POST)
            if form.is_valid():
                try:
                    user_rec = form.save(sede)
                    messages.success(request, f'Recepcionista {user_rec.username} registrada exitosamente.')
                    return redirect('dashboard_gerente')
                except Exception as e:
                    messages.error(request, f'Error al registrar la recepcionista: {str(e)}')
                    print(f"Error guardando recepcionista: {e}")
            else:
                messages.error(request, 'Por favor corrige los errores en el formulario.')
                print(f"Errores formulario recepcionista: {form.errors}")
        else:
            from usuarios.forms import RegistrarRecepcionistaForm
            form = RegistrarRecepcionistaForm()
        return render(request, 'usuarios/registrar_recepcionista.html', {'form': form, 'sede': sede})
    except Exception as e:
        print(f"Error en registrar_recepcionista: {e}")
        messages.error(request, 'Error al cargar el formulario')
        return redirect('home')


# ==================== VISTAS AJAX PARA SELECTORES DEPENDIENTES ====================

def cargar_municipios(request):
    """Retorna municipios filtrados por estado desde Supabase"""
    estado_id = request.GET.get('estado_id')
    if estado_id:
        municipios = Municipio.objects.filter(id_estado_id=estado_id).values('id_municipio', 'municipio')
        return JsonResponse(list(municipios), safe=False)
    return JsonResponse([], safe=False)

def cargar_ciudades(request):
    """Retorna ciudades filtradas por estado desde Supabase"""
    estado_id = request.GET.get('estado_id')
    if estado_id:
        ciudades = Ciudad.objects.filter(id_estado_id=estado_id).values('id_ciudad', 'ciudad')
        return JsonResponse(list(ciudades), safe=False)
    return JsonResponse([], safe=False)

def cargar_parroquias(request):
    """Retorna parroquias filtradas por municipio desde Supabase"""
    municipio_id = request.GET.get('municipio_id')
    if municipio_id:
        parroquias = Parroquia.objects.filter(id_municipio_id=municipio_id).values('id_parroquia', 'parroquia')
        return JsonResponse(list(parroquias), safe=False)
    return JsonResponse([], safe=False)

# ==================== VISTAS AJAX PARA VALIDACIÓN EN TIEMPO REAL ====================

def validar_username(request):
    """Valida si el username ya existe"""
    username = request.GET.get('username', '').strip()
    if username:
        existe = UserPaciente.objects.filter(username=username).exists()
        return JsonResponse({'existe': existe})
    return JsonResponse({'existe': False})

def validar_email(request):
    """Valida si el email ya existe"""
    email = request.GET.get('email', '').strip().lower()
    if email:
        existe = UserPaciente.objects.filter(email=email).exists()
        return JsonResponse({'existe': existe})
    return JsonResponse({'existe': False})

def validar_cedula(request):
    """Valida si la cédula ya existe"""
    cedula = request.GET.get('cedula', '').strip()
    if cedula:
        existe = PacienteDatosPersonales.objects.filter(cedula=cedula).exists()
        return JsonResponse({'existe': existe})
    return JsonResponse({'existe': False})