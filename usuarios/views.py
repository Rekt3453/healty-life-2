from datetime import date
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.http import JsonResponse
from .forms import RegistroPacienteForm, RegistroStaffForm, RegistrarPacienteEspecialForm, EditarPacienteEspecialForm
from .models import (
    UserPaciente, UserDoctor, UserRecepcionista, UserAdmin, UserSuperAdmin,
    PacienteDatosPersonales, Doctor, Recepcionista, Administrador,
    Estado, Municipio, Ciudad, Parroquia, PacienteEspecial, Sede,
    DireccionPaciente, DireccionDoctor, DireccionRecepcionista,
    RecuperacionContrasenaPaciente, RecuperacionContrasenaDoctor,
    RecuperacionContrasenaRecepcionista, RecuperacionContrasenaAdmin,
    RecuperacionContrasenaSuperadmin,
)
from usuarios.decorators import rol_requerido
from citas.models import Cita, PagoCita, HistorialMedicoPaciente, Alergias, TipoSangre, Vacunas, EspecialidadDoctor, Especialidad, Consultorio, Horario
from .authentication import CustomAuthBackend, is_rate_limited
from .email_config import enviar_correo_confirmacion
from .services.auth_service import resolve_and_check
from .services.user_service import (
    update_perfil_paciente, change_password, update_direccion_paciente,
    get_paciente_dashboard_context, get_medico_dashboard_context,
    get_recepcionista_dashboard_context, get_gerente_dashboard_context,
    calcular_edad,
)
from .services.email_service import send_welcome_email

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
            if is_rate_limited(username):
                messages.error(request, "Demasiados intentos fallidos. Espere 1 minuto e intente de nuevo.")
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
                datos_paciente = PacienteDatosPersonales.objects.filter(id_user_paciente=user).first()
                password_plana = form.cleaned_data.get('password1', '')
                send_welcome_email(user, datos_paciente, password_plana)

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
            ok, msg = update_perfil_paciente(user, paciente, request.POST)
            if ok:
                messages.success(request, f'✅ {msg}')
            else:
                messages.error(request, msg)
            return redirect('perfil_paciente')

        elif action == 'update_password':
            ok, msg = change_password(
                user,
                request.POST.get('password_actual', ''),
                request.POST.get('password_nuevo', ''),
                request.POST.get('password_confirmar', ''),
            )
            if ok:
                messages.success(request, f'✅ {msg}')
            else:
                messages.error(request, msg)
            return redirect('perfil_paciente')

        elif action == 'update_direccion':
            ok, msg = update_direccion_paciente(paciente, request.POST)
            if ok:
                messages.success(request, f'✅ {msg}')
            else:
                messages.error(request, msg)
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
    print(f"DEBUG dashboard_paciente: user={request.user}, tipo={type(request.user).__name__}, datos_paciente={datos_paciente}")
    stats = get_paciente_dashboard_context(datos_paciente)
    return render(request, 'usuarios/dashboard_paciente.html', {
        'nombre':           nombre,
        'citas':            stats['citas'],
        'citas_pendientes': stats['citas_activas'],
        'citas_aprobadas':  stats['citas_activas'],
        'citas_rechazadas': stats['citas_canceladas'],
        'total_citas':      stats['total_citas'],
    })

@login_required(login_url='/login/paciente/')
@rol_requerido('paciente')
def registrar_paciente_especial(request):
    """
    Vista para que el paciente-tutor registre a un menor de edad.
    No se crean credenciales de acceso; el menor queda vinculado al tutor.
    """
    from django.db import transaction
    from django.utils import timezone as tz

    auth_backend = CustomAuthBackend()
    paciente_tutor = auth_backend.get_datos_personales(request.user)

    if not paciente_tutor:
        messages.error(request, 'No se encontró tu perfil de paciente.')
        return redirect('dashboard_paciente')

    form = RegistrarPacienteEspecialForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        # Guardar en tabla paciente_especial dentro de una transacción atómica
        # (la validación de edad < 18 ya fue verificada en el formulario)
        with transaction.atomic():
            PacienteEspecial.objects.create(
                id_paciente_tutor=paciente_tutor,
                id_sede=paciente_tutor.id_sede,
                nombre_1=form.cleaned_data['nombre_1'],
                nombre_2=form.cleaned_data.get('nombre_2') or '',
                apellido_1=form.cleaned_data['apellido_1'],
                apellido_2=form.cleaned_data.get('apellido_2') or '',
                sexo=form.cleaned_data['sexo'],
                fecha_nacimiento=form.cleaned_data['fecha_nacimiento'],
                telefono=form.cleaned_data.get('telefono') or '',
                fecha_registro=tz.now(),
                status=True,
            )

        nombre_menor = (
            f"{form.cleaned_data['nombre_1']} {form.cleaned_data['apellido_1']}"
        )
        messages.success(
            request, f'✅ Paciente especial "{nombre_menor}" registrado correctamente.'
        )
        return redirect('lista_pacientes_especiales')

    return render(request, 'usuarios/registrar_paciente_especial.html', {
        'form':   form,
        'nombre': paciente_tutor.nombre_completo,
    })


@login_required(login_url='/login/paciente/')
@rol_requerido('paciente')
def lista_pacientes_especiales(request):
    """
    Lista los menores de edad (pacientes especiales) vinculados al tutor.
    """
    auth_backend = CustomAuthBackend()
    paciente_tutor = auth_backend.get_datos_personales(request.user)

    menores = PacienteEspecial.objects.none()
    if paciente_tutor:
        menores = PacienteEspecial.objects.filter(
            id_paciente_tutor=paciente_tutor,
            status=True,
        ).order_by('nombre_1', 'apellido_1')

    return render(request, 'usuarios/lista_pacientes_especiales.html', {
        'menores':         menores,
        'nombre':          paciente_tutor.nombre_completo if paciente_tutor else request.user.username,
        'paciente_tutor':  paciente_tutor,
    })


@login_required(login_url='/login/paciente/')
@rol_requerido('paciente')
def editar_paciente_especial(request, id_paciente_especial):
    """
    Permite al tutor-paciente editar los datos de un menor ya registrado.
    Sólo el tutor propietario del registro puede editarlo (verificación de
    id_paciente_tutor contra el perfil del usuario autenticado).

    GET:  precarga el formulario con los datos actuales del menor.
    POST: valida y guarda los cambios; redirige a la lista de menores.
    """
    from django.shortcuts import get_object_or_404

    auth_backend = CustomAuthBackend()
    paciente_tutor = auth_backend.get_datos_personales(request.user)

    if not paciente_tutor:
        messages.error(request, 'No se encontró tu perfil de paciente.')
        return redirect('dashboard_paciente')

    # Obtener el menor; exige que pertenezca al tutor autenticado
    menor = get_object_or_404(
        PacienteEspecial,
        id_paciente_especial=id_paciente_especial,
        id_paciente_tutor=paciente_tutor,
        status=True,
    )

    # Convertir DateTimeField a date para el DateInput del formulario
    fecha_inicial = (
        menor.fecha_nacimiento.date()
        if hasattr(menor.fecha_nacimiento, 'date')
        else menor.fecha_nacimiento
    )

    initial = {
        'nombre_1':        menor.nombre_1,
        'nombre_2':        menor.nombre_2 or '',
        'apellido_1':      menor.apellido_1,
        'apellido_2':      menor.apellido_2 or '',
        'sexo':            menor.sexo or '',
        'fecha_nacimiento': fecha_inicial,
        'telefono':        menor.telefono or '',
    }

    if request.method == 'POST':
        form = EditarPacienteEspecialForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            # Actualizar sólo los campos editables; el resto queda intacto
            menor.nombre_1         = cd['nombre_1']
            menor.nombre_2         = cd.get('nombre_2') or ''
            menor.apellido_1       = cd['apellido_1']
            menor.apellido_2       = cd.get('apellido_2') or ''
            menor.sexo             = cd['sexo']
            menor.fecha_nacimiento = cd['fecha_nacimiento']
            menor.telefono         = cd.get('telefono') or ''
            menor.save()

            nombre_menor = f"{menor.nombre_1} {menor.apellido_1}"
            messages.success(
                request,
                f'✅ Datos de "{nombre_menor}" actualizados correctamente.'
            )
            return redirect('lista_pacientes_especiales')
    else:
        form = EditarPacienteEspecialForm(initial=initial)

    return render(request, 'usuarios/editar_paciente_especial.html', {
        'form':   form,
        'menor':  menor,
        'nombre': paciente_tutor.nombre_completo,
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
    
    stats = get_medico_dashboard_context(datos_medico)
    return render(request, 'usuarios/dashboard_medico.html', {'nombre': nombre, **stats})

def dashboard_recepcionista(request):
    """Dashboard de recepcionista — datos reales de citas"""
    user, backend, err = resolve_and_check(
        request, UserRecepcionista, 'id_user_recepcionista', 'recepcionista', 'login_recepcionista'
    )
    if err:
        return err
    datos = backend.get_datos_personales(user)
    nombre = datos.nombre_completo if datos else user.username
    stats  = get_recepcionista_dashboard_context()
    return render(request, 'usuarios/dashboard_recepcionista.html', {'nombre': nombre, **stats})
def dashboard_gerente(request):
    """Dashboard de gerente — datos reales"""
    user, backend, err = resolve_and_check(
        request, UserAdmin, 'id_user_admin', 'gerente', 'login_gerente'
    )
    if err:
        return err
    datos  = backend.get_datos_personales(user)
    nombre = datos.nombre_completo if datos else user.username
    stats  = get_gerente_dashboard_context()
    return render(request, 'usuarios/dashboard_gerente.html', {'nombre': nombre, **stats})
def login_admin(request):
    """Login para administradores (alias de login_gerente en esta instalación)"""
    return login_rol(request, 'gerente', 'usuarios/login_gerente.html', 'dashboard_gerente')


def registro_staff(request):
    """Registro de staff - solo gerente"""
    user, backend, err = resolve_and_check(
        request, UserAdmin, 'id_user_admin', 'gerente', 'login_gerente'
    )
    if err:
        return err

    try:
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
    user, _, err = resolve_and_check(
        request, UserAdmin, 'id_user_admin', 'gerente', 'login_gerente'
    )
    if err:
        return err
    try:
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
    user, _, err = resolve_and_check(
        request, UserAdmin, 'id_user_admin', 'gerente', 'login_gerente'
    )
    if err:
        return err
    try:
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
                sede_id=sede.pk if sede else None,
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
                # Precarga el horario actual de la recepcionista
                'id_horario': Horario.objects.filter(pk=recepcionista.id_horario).first() if recepcionista.id_horario else None,
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
                sede_id=sede.pk if sede else None,
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
            form = RegistrarRecepcionistaForm(request.POST, sede_id=sede.id_sede if sede else None)
            if form.is_valid():
                try:
                    password_plana = form.cleaned_data['password1']
                    user_rec = form.save(sede)
                    try:
                        from .email_config import enviar_correo_recepcionista
                        enviar_correo_recepcionista({
                            'primer_nombre':   form.cleaned_data.get('nombre_1', ''),
                            'segundo_nombre':  form.cleaned_data.get('nombre_2', ''),
                            'primer_apellido': form.cleaned_data.get('apellido_1', ''),
                            'segundo_apellido': form.cleaned_data.get('apellido_2', ''),
                            'email':    form.cleaned_data.get('email', ''),
                            'username': user_rec.username,
                            'password': password_plana,
                        })
                    except Exception as mail_err:
                        print(f'WARN: No se pudo enviar correo a la recepcionista: {mail_err}')
                    messages.success(request, f'Recepcionista {user_rec.username} registrada. Se envió un correo con sus credenciales.')
                    return redirect('dashboard_gerente')
                except Exception as e:
                    messages.error(request, f'Error al registrar la recepcionista: {str(e)}')
                    print(f"Error guardando recepcionista: {e}")
            else:
                messages.error(request, 'Por favor corrige los errores en el formulario.')
                print(f"Errores formulario recepcionista: {form.errors}")
        else:
            from usuarios.forms import RegistrarRecepcionistaForm
            form = RegistrarRecepcionistaForm(sede_id=sede.id_sede if sede else None)
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


# ── RECUPERACIÓN DE CONTRASEÑA (SOLO PACIENTES) ───────────────────────────────

import hashlib as _hashlib
import random as _random

PREGUNTAS_SEGURIDAD = [
    (1,  '¿Cuál es el nombre de tu primera mascota?'),
    (2,  '¿En qué ciudad naciste?'),
    (3,  '¿Nombre de tu madre?'),
    (4,  '¿Cómo se llama tu mejor amigo de la infancia?'),
    (5,  '¿Cuál es el segundo nombre de tu madre?'),
    (6,  '¿Cuál fue tu primer trabajo?'),
    (7,  '¿Cuál es tu comida favorita?'),
    (8,  '¿A qué lugar te gustaría viajar?'),
    (9,  '¿Cuál es el nombre de tu profesora favorita?'),
    (10, '¿Nombre de tu padre?'),
]

def _preg_texto(id_preg):
    return next((p[1] for p in PREGUNTAS_SEGURIDAD if p[0] == id_preg), None)


# ── HELPER EMAIL ─────────────────────────────────────────────────────────────

def _enviar_correo_config_preguntas(user, request):
    from usuarios.email_config import SMTP_HOST_NAME, SMTP_PORT, SMTP_USER, SMTP_PASS
    import smtplib, ssl
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    destinatario = user.email or ''
    if not destinatario or not SMTP_USER or not SMTP_PASS:
        raise ValueError('Credenciales de correo no configuradas en .env')

    token  = _hashlib.md5(f"{user.pk}-{user.email}-config".encode()).hexdigest()
    enlace = request.build_absolute_uri(f'/configurar-preguntas/{user.pk}/{token}/')
    asunto = 'Healthy Life — Configura tus preguntas de seguridad'
    cuerpo = (
        'Hola,\n\n'
        'Para poder recuperar tu contraseña en el futuro, configura tus preguntas de seguridad:\n\n'
        f'{enlace}\n\n'
        'Si no solicitaste esto, ignora este mensaje.\n\n'
        '— Healthy Life'
    )
    msg = MIMEMultipart()
    msg['From']    = SMTP_USER
    msg['To']      = destinatario
    msg['Subject'] = asunto
    msg.attach(MIMEText(cuerpo, 'plain', 'utf-8'))

    # Contexto SSL sin verificación de certificado (compatible con servidores custom)
    ctx = ssl._create_unverified_context()
    port = int(SMTP_PORT)
    print(f'[EMAIL] Enviando a {destinatario} via {SMTP_HOST_NAME}:{port}')
    if port == 465:
        with smtplib.SMTP_SSL(SMTP_HOST_NAME, port, context=ctx, timeout=15) as server:
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, destinatario, msg.as_string())
    else:
        with smtplib.SMTP(SMTP_HOST_NAME, port, timeout=15) as server:
            server.ehlo()
            server.starttls(context=ctx)
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, destinatario, msg.as_string())
    print(f'[EMAIL] Enviado correctamente a {destinatario}')


# ── RECUPERAR CONTRASEÑA — PASO 1 ────────────────────────────────────────────

def recuperar_password(request):
    if request.method == 'POST':
        correo = request.POST.get('correo', '').strip().lower()
        if not correo:
            messages.error(request, 'Ingresa tu correo electrónico.')
            return render(request, 'usuarios/recuperar_password.html')

        user = UserPaciente.objects.filter(email=correo, status=True).first()
        if not user:
            messages.error(request, 'No se encontró una cuenta con ese correo electrónico.')
            return render(request, 'usuarios/recuperar_password.html')

        recuperacion = RecuperacionContrasenaPaciente.objects.filter(
            id_user_paciente=user
        ).first()

        if not recuperacion or not recuperacion.preguntas_seguridad:
            try:
                _enviar_correo_config_preguntas(user, request)
                messages.info(
                    request,
                    'No tienes preguntas configuradas. Hemos enviado un enlace a tu correo.',
                )
            except Exception as _e:
                print(f'[EMAIL ERROR] {type(_e).__name__}: {_e}')
                from django.conf import settings as _s
                if _s.DEBUG:
                    token  = _hashlib.md5(f"{user.pk}-{user.email}-config".encode()).hexdigest()
                    enlace = request.build_absolute_uri(f'/configurar-preguntas/{user.pk}/{token}/')
                    messages.warning(
                        request,
                        f'[DEBUG] No se pudo enviar el correo ({type(_e).__name__}). '
                        f'Enlace directo: {enlace}',
                    )
                else:
                    messages.warning(
                        request,
                        'No tienes preguntas configuradas. '
                        'Contacta al administrador de tu sede.',
                    )
            return redirect('login_paciente')

        request.session['recuperacion_user_id'] = user.pk
        return redirect('verificar_preguntas')

    return render(request, 'usuarios/recuperar_password.html')


# ── RECUPERAR CONTRASEÑA — PASO 2 ────────────────────────────────────────────

def verificar_preguntas(request):
    user_id = request.session.get('recuperacion_user_id')
    if not user_id:
        return redirect('recuperar_password')

    recuperacion = RecuperacionContrasenaPaciente.objects.filter(
        id_user_paciente_id=user_id
    ).first()
    if not recuperacion:
        return redirect('recuperar_password')

    ids_guardados    = [int(x) for x in recuperacion.preguntas_seguridad.split(',')]
    resps_guardadas  = recuperacion.respuestas_seguridad.split('||')

    todas = [
        {'id': id_preg, 'pregunta': _preg_texto(id_preg), 'respuesta': resps_guardadas[i]}
        for i, id_preg in enumerate(ids_guardados)
        if _preg_texto(id_preg) and i < len(resps_guardadas)
    ]

    # Seleccionar 2 y guardar en sesión para consistencia entre GET y POST
    if 'verificacion_ids' not in request.session:
        sel = _random.sample(todas, min(2, len(todas)))
        request.session['verificacion_ids'] = [item['id'] for item in sel]
    else:
        ids_sel = request.session['verificacion_ids']
        sel = [item for item in todas if item['id'] in ids_sel]

    if request.method == 'POST':
        aciertos = sum(
            1 for item in sel
            if request.POST.get(f'respuesta_{item["id"]}', '').strip().lower()
               == item['respuesta'].strip().lower()
        )
        if aciertos == len(sel):
            request.session['preguntas_verificadas'] = True
            request.session.pop('verificacion_ids', None)
            return redirect('cambiar_password')
        else:
            messages.error(request, f'Acertaste {aciertos} de {len(sel)}. Intenta de nuevo.')
            request.session.pop('verificacion_ids', None)

    return render(request, 'usuarios/verificar_preguntas.html', {'preguntas': sel})


# ── RECUPERAR CONTRASEÑA — PASO 3 ────────────────────────────────────────────

def cambiar_password(request):
    if not request.session.get('preguntas_verificadas'):
        return redirect('recuperar_password')

    user_id = request.session.get('recuperacion_user_id')
    if not user_id:
        return redirect('recuperar_password')

    if request.method == 'POST':
        p1 = request.POST.get('password1', '')
        p2 = request.POST.get('password2', '')
        if len(p1) < 8:
            messages.error(request, 'Mínimo 8 caracteres.')
        elif p1 != p2:
            messages.error(request, 'Las contraseñas no coinciden.')
        else:
            user = UserPaciente.objects.filter(pk=user_id).first()
            if user:
                user.password = _hashlib.md5(p1.encode()).hexdigest()
                user.save()
                for key in ('recuperacion_user_id', 'preguntas_verificadas'):
                    request.session.pop(key, None)
                messages.success(request, 'Contraseña actualizada. Inicia sesión.')
                return redirect('login_paciente')

    return render(request, 'usuarios/cambiar_password.html')


# ── CONFIGURAR PREGUNTAS (TOKEN O PERFIL) ────────────────────────────────────

def configurar_preguntas_paciente(request, user_id=None, token=None):
    # Resolver quién es el usuario
    if user_id and token:
        user = UserPaciente.objects.filter(pk=user_id, status=True).first()
        if not user:
            messages.error(request, 'Usuario no encontrado.')
            return redirect('home')
        esperado = _hashlib.md5(f"{user.pk}-{user.email}-config".encode()).hexdigest()
        if token != esperado:
            messages.error(request, 'Enlace inválido o expirado.')
            return redirect('home')
        via_token = True
    else:
        if not (hasattr(request, 'user') and request.user.is_authenticated
                and request.session.get('_hl_user_model') == 'UserPaciente'):
            messages.error(request, 'Debes iniciar sesión como paciente.')
            return redirect('login_paciente')
        user = request.user
        via_token = False

    # Si ya tiene preguntas → solo lectura
    recuperacion = RecuperacionContrasenaPaciente.objects.filter(
        id_user_paciente=user
    ).first()
    if recuperacion and recuperacion.preguntas_seguridad:
        ids = [int(x) for x in recuperacion.preguntas_seguridad.split(',')]
        preguntas_cfg = [(pid, _preg_texto(pid)) for pid in ids if _preg_texto(pid)]
        return render(request, 'usuarios/ver_preguntas.html', {'preguntas': preguntas_cfg})

    # Seleccionar 5 aleatorias (o restaurar del POST)
    if request.method == 'POST':
        ids_post  = request.POST.get('ids_preguntas', '').split(',')
        seleccionadas = [
            (int(pid), _preg_texto(int(pid)))
            for pid in ids_post
            if pid.strip().isdigit() and _preg_texto(int(pid))
        ]
        respuestas = [
            request.POST.get(f'respuesta_{i}', '').strip().lower()
            for i in range(len(seleccionadas))
        ]
        if not all(respuestas):
            messages.error(request, 'Debes responder todas las preguntas.')
        else:
            RecuperacionContrasenaPaciente.objects.create(
                id_user_paciente=user,
                preguntas_seguridad=','.join(str(p[0]) for p in seleccionadas),
                respuestas_seguridad='||'.join(respuestas),
            )
            messages.success(request, 'Preguntas de seguridad configuradas correctamente.')
            return redirect('login_paciente' if via_token else 'dashboard_paciente')

        ids_mostrar = [str(p[0]) for p in seleccionadas]
    else:
        seleccionadas = _random.sample(PREGUNTAS_SEGURIDAD, 5)
        ids_mostrar   = [str(p[0]) for p in seleccionadas]

    return render(request, 'usuarios/configurar_preguntas.html', {
        'preguntas':     seleccionadas,
        'ids_preguntas': ','.join(ids_mostrar),
    })


# ==================== GESTIÓN DE ESPECIALIDADES (GERENTE) ====================

def _get_gerente_sede(request):
    """Devuelve (user, sede) si la sesión es válida con rol gerente, o (None, None)."""
    user_id = request.session.get('_auth_user_id')
    if not user_id:
        return None, None
    user = UserAdmin.objects.filter(id_user_admin=user_id).first()
    if not user:
        return None, None
    if CustomAuthBackend().get_rol(user) != 'gerente':
        return None, None
    return user, user.id_sede


def lista_especialidades(request):
    """Lista las especialidades de la sede del gerente.
    Además, auto-crea los registros EspecialidadDoctor que falten para que
    el dropdown de doctor los muestre correctamente."""
    user, sede = _get_gerente_sede(request)
    if not user:
        messages.error(request, 'Acceso denegado.')
        return redirect('login_gerente')
    especialidades = Especialidad.objects.filter(id_sede=sede).order_by('tipo_especialidad')
    # Reparación automática: garantiza que cada especialidad tenga su registro puente
    reparadas = 0
    for esp in especialidades:
        if not EspecialidadDoctor.objects.filter(id_especialidad=esp).exists():
            EspecialidadDoctor.objects.create(id_especialidad=esp)
            reparadas += 1
    if reparadas:
        messages.info(request, f'Se crearon {reparadas} vínculo(s) de especialidad faltante(s).')
    return render(request, 'usuarios/lista_especialidades.html', {
        'especialidades': especialidades,
        'sede': sede,
    })


# Opciones fijas de clasificación de especialidad compartidas entre vistas y plantilla
CLASIFICACION_ESPECIALIDAD_CHOICES = [
    ('Pediatría', 'Pediatría'),
    ('Adultos', 'Adultos'),
    ('General', 'General'),
]


def crear_especialidad(request):
    """Crea una Especialidad para la sede y genera automáticamente el registro EspecialidadDoctor.
    Ahora también guarda la clasificación (Pediatría / Adultos / General)."""
    user, sede = _get_gerente_sede(request)
    if not user:
        messages.error(request, 'Acceso denegado.')
        return redirect('login_gerente')
    if request.method == 'POST':
        tipo = request.POST.get('tipo_especialidad', '').strip()
        clasificacion = request.POST.get('clasificacion_especialidad', '').strip()
        valores_validos = [c[0] for c in CLASIFICACION_ESPECIALIDAD_CHOICES]
        errores = []
        if not tipo:
            errores.append('El nombre de la especialidad es obligatorio.')
        if not clasificacion or clasificacion not in valores_validos:
            errores.append('Debes seleccionar una clasificación válida (Pediatría, Adultos o General).')
        if errores:
            for e in errores:
                messages.error(request, e)
        else:
            try:
                # Evitar duplicados por nombre en la misma sede
                if Especialidad.objects.filter(tipo_especialidad__iexact=tipo, id_sede=sede).exists():
                    messages.error(request, f'Ya existe una especialidad con el nombre "{tipo}" en esta sede.')
                else:
                    especialidad = Especialidad.objects.create(
                        tipo_especialidad=tipo,
                        clasificacion_especialidad=clasificacion,
                        id_sede=sede,
                        status=True,
                    )
                    # Crear el registro EspecialidadDoctor vinculado para que el
                    # formulario de doctor pueda seleccionarla
                    EspecialidadDoctor.objects.create(id_especialidad=especialidad)
                    messages.success(request, f'Especialidad "{tipo}" creada correctamente.')
                    return redirect('lista_especialidades')
            except Exception as e:
                messages.error(request, f'Error al crear la especialidad: {e}')
    return render(request, 'usuarios/crear_especialidad.html', {
        'sede': sede,
        'clasificacion_choices': CLASIFICACION_ESPECIALIDAD_CHOICES,
    })


def toggle_especialidad_status(request, id_especialidad):
    """Activa o desactiva una especialidad de la sede del gerente."""
    user, sede = _get_gerente_sede(request)
    if not user:
        messages.error(request, 'Acceso denegado.')
        return redirect('login_gerente')
    especialidad = Especialidad.objects.filter(pk=id_especialidad, id_sede=sede).first()
    if not especialidad:
        messages.error(request, 'Especialidad no encontrada.')
    else:
        especialidad.status = not especialidad.status
        especialidad.save(update_fields=['status'])
        estado_txt = 'activada' if especialidad.status else 'desactivada'
        messages.success(request, f'Especialidad "{especialidad.tipo_especialidad}" {estado_txt}.')
    return redirect('lista_especialidades')


def editar_especialidad(request, id_especialidad):
    """Permite al gerente editar el nombre y la clasificación de una especialidad existente.
    No permite cambiar la sede ni el estado (el toggle ya lo cubre)."""
    user, sede = _get_gerente_sede(request)
    if not user:
        messages.error(request, 'Acceso denegado.')
        return redirect('login_gerente')
    especialidad = Especialidad.objects.filter(pk=id_especialidad, id_sede=sede).first()
    if not especialidad:
        messages.error(request, 'Especialidad no encontrada o no pertenece a tu sede.')
        return redirect('lista_especialidades')
    if request.method == 'POST':
        tipo = request.POST.get('tipo_especialidad', '').strip()
        clasificacion = request.POST.get('clasificacion_especialidad', '').strip()
        valores_validos = [c[0] for c in CLASIFICACION_ESPECIALIDAD_CHOICES]
        errores = []
        if not tipo:
            errores.append('El nombre de la especialidad es obligatorio.')
        if not clasificacion or clasificacion not in valores_validos:
            errores.append('Debes seleccionar una clasificación válida (Pediatría, Adultos o General).')
        if errores:
            for e in errores:
                messages.error(request, e)
        else:
            # Verificar duplicado de nombre en la misma sede (excluyendo la especialidad actual)
            if Especialidad.objects.filter(
                tipo_especialidad__iexact=tipo, id_sede=sede
            ).exclude(pk=id_especialidad).exists():
                messages.error(request, f'Ya existe otra especialidad con el nombre "{tipo}" en esta sede.')
            else:
                try:
                    especialidad.tipo_especialidad = tipo
                    especialidad.clasificacion_especialidad = clasificacion
                    especialidad.save(update_fields=['tipo_especialidad', 'clasificacion_especialidad'])
                    messages.success(request, f'Especialidad "{tipo}" actualizada correctamente.')
                    return redirect('lista_especialidades')
                except Exception as e:
                    messages.error(request, f'Error al guardar los cambios: {e}')
    return render(request, 'usuarios/editar_especialidad.html', {
        'sede': sede,
        'especialidad': especialidad,
        'clasificacion_choices': CLASIFICACION_ESPECIALIDAD_CHOICES,
    })


# ==================== GESTIÓN DE HORARIOS (GERENTE) ====================

def lista_horarios(request):
    """Lista los horarios de la sede del gerente."""
    user, sede = _get_gerente_sede(request)
    if not user:
        messages.error(request, 'Acceso denegado.')
        return redirect('login_gerente')
    horarios = Horario.objects.filter(id_sede=sede).order_by('hora_inicio')
    return render(request, 'usuarios/lista_horarios.html', {
        'horarios': horarios,
        'sede': sede,
    })


def crear_horario(request):
    """Crea un Horario para la sede del gerente."""
    user, sede = _get_gerente_sede(request)
    if not user:
        messages.error(request, 'Acceso denegado.')
        return redirect('login_gerente')
    if request.method == 'POST':
        hora_inicio = request.POST.get('hora_inicio', '').strip()
        hora_fin    = request.POST.get('hora_fin', '').strip()
        if not hora_inicio or not hora_fin:
            messages.error(request, 'Hora de inicio y fin son obligatorias.')
        elif hora_inicio >= hora_fin:
            messages.error(request, 'La hora de inicio debe ser anterior a la hora de fin.')
        else:
            try:
                Horario.objects.create(
                    id_sede=sede,
                    hora_inicio=hora_inicio,
                    hora_fin=hora_fin,
                )
                messages.success(request, f'Horario {hora_inicio}–{hora_fin} creado correctamente.')
                return redirect('lista_horarios')
            except Exception as e:
                messages.error(request, f'Error al crear el horario: {e}')
    return render(request, 'usuarios/crear_horario.html', {'sede': sede})