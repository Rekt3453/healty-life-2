import hashlib
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from .models import (
    UserSuperAdmin, Superadmin, Sede, DireccionSede, CentroMedico,
    UserAdmin, Administrador, DireccionAdmin,
    Estado, Municipio, Ciudad, Parroquia, AuditLog,
)
from .audit_services import registrar_evento

# Obtener el CentroMedico del superadmin a través de su sede
def _get_centro(sa):
    if sa and sa.id_sede and sa.id_sede.id_cm:
        return sa.id_sede.id_cm
    return None

# ── helpers ──────────────────────────────────────────────────────────────────

def _get_superadmin_user(request):
    uid = request.session.get('_superadmin_user_id')
    if not uid:
        return None, None
    user_sa = UserSuperAdmin.objects.filter(id_superadmin=uid).first()
    if not user_sa:
        return None, None
    sa = Superadmin.objects.filter(id_user_superadmin=user_sa).first()
    return user_sa, sa


def _superadmin_required(view_func):
    def wrapper(request, *args, **kwargs):
        user_sa, sa = _get_superadmin_user(request)
        if not user_sa:
            messages.error(request, 'Acceso restringido. Inicia sesión como Super Admin.')
            return redirect('login_superadmin')
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


# ── LOGIN SUPER ADMIN ─────────────────────────────────────────────────────────

def login_superadmin(request):
    user_sa, _ = _get_superadmin_user(request)
    if user_sa:
        return redirect('dashboard_superadmin')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        password_hash = hashlib.md5(password.encode()).hexdigest()

        user = UserSuperAdmin.objects.filter(
            username=username, contrasena=password_hash, status=True
        ).first()
        if user:
            request.session['_superadmin_user_id'] = user.id_superadmin
            request.session['_superadmin_username'] = user.username
            registrar_evento(
                user=user,
                role='superadmin',
                action='LOGIN',
                model_affected='UserSuperAdmin',
                object_id=user.id_superadmin,
                details={'username': user.username},
                request=request,
            )
            messages.success(request, f'Bienvenido, {user.username}')
            return redirect('dashboard_superadmin')
        else:
            messages.error(request, 'Credenciales incorrectas.')

    return render(request, 'usuarios/login_superadmin.html')


# ── DASHBOARD SUPER ADMIN ─────────────────────────────────────────────────────

@_superadmin_required
def dashboard_superadmin(request):
    user_sa, sa = _get_superadmin_user(request)
    centro = _get_centro(sa)

    sedes = Sede.objects.filter(
        id_cm=centro
    ).select_related('id_direccion').order_by('nombre_sede') if centro else Sede.objects.none()

    sede_ids = list(sedes.values_list('id_sede', flat=True))
    gerentes = Administrador.objects.filter(
        id_sede__in=sede_ids
    ).select_related('id_user_admin', 'id_sede').order_by('nombre_1') if sede_ids else Administrador.objects.none()

    context = {
        'superadmin': sa,
        'user_sa': user_sa,
        'centro': centro,
        'sedes': sedes,
        'gerentes': gerentes,
        'total_sedes': sedes.count(),
        'total_gerentes': gerentes.count(),
    }
    return render(request, 'usuarios/dashboard_superadmin.html', context)


# ── REGISTRAR SEDE ────────────────────────────────────────────────────────────

@_superadmin_required
def registrar_sede(request):
    user_sa, sa = _get_superadmin_user(request)
    centro = _get_centro(sa)
    estados = Estado.objects.all().order_by('estado')

    if request.method == 'POST':
        nombre_sede = request.POST.get('nombre_sede', '').strip()
        rif_sede = request.POST.get('rif_sede', '').strip() or None
        telefono = request.POST.get('telefono', '').strip() or None
        id_estado = request.POST.get('id_estado')
        id_municipio = request.POST.get('id_municipio')
        id_ciudad = request.POST.get('id_ciudad')
        id_parroquia = request.POST.get('id_parroquia')
        direccion = request.POST.get('direccion', '').strip()
        referencia = request.POST.get('referencia', '').strip() or None

        if not nombre_sede:
            messages.error(request, 'El nombre de la sede es obligatorio.')
        elif not all([id_estado, id_municipio, id_ciudad, id_parroquia, direccion]):
            messages.error(request, 'Completa los campos de dirección.')
        else:
            try:
                dir_sede = DireccionSede.objects.create(
                    id_estado_id=id_estado,
                    id_municipio_id=id_municipio,
                    id_ciudad_id=id_ciudad,
                    id_parroquia_id=id_parroquia,
                    direccion=direccion,
                    referencia=referencia,
                )
                Sede.objects.create(
                    nombre_sede=nombre_sede,
                    rif_sede=rif_sede,
                    telefono=telefono,
                    id_direccion=dir_sede,
                    id_cm=centro,
                    status=True,
                )
                messages.success(request, f'Sede "{nombre_sede}" registrada exitosamente.')
                return redirect('dashboard_superadmin')
            except Exception as e:
                messages.error(request, f'Error al registrar la sede: {e}')

    context = {'estados': estados}
    return render(request, 'usuarios/registrar_sede.html', context)


# ── REGISTRAR GERENTE ─────────────────────────────────────────────────────────

@_superadmin_required
def registrar_gerente(request):
    user_sa, sa = _get_superadmin_user(request)
    centro = _get_centro(sa)
    sedes = Sede.objects.filter(
        id_cm=centro, status=True
    ).order_by('nombre_sede') if centro else Sede.objects.none()
    estados = Estado.objects.all().order_by('estado')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        correo = request.POST.get('correo', '').strip()
        password = request.POST.get('password', '')
        nombre_1 = request.POST.get('nombre_1', '').strip().upper()
        nombre_2 = request.POST.get('nombre_2', '').strip().upper() or None
        apellido_1 = request.POST.get('apellido_1', '').strip().upper()
        apellido_2 = request.POST.get('apellido_2', '').strip().upper() or None
        cedula = request.POST.get('cedula', '').strip()
        tipo_cedula = request.POST.get('tipo_cedula', 'V')
        sexo = request.POST.get('sexo', '')
        fecha_nacimiento = request.POST.get('fecha_nacimiento') or None
        telefono = request.POST.get('telefono', '').strip()
        id_sede = request.POST.get('id_sede')
        id_estado = request.POST.get('id_estado')
        id_municipio = request.POST.get('id_municipio')
        id_ciudad = request.POST.get('id_ciudad')
        id_parroquia = request.POST.get('id_parroquia')
        direccion = request.POST.get('direccion', '').strip()
        referencias = request.POST.get('referencia', '').strip() or None

        errors = []
        if not all([username, correo, password, nombre_1, apellido_1, cedula, id_sede]):
            errors.append('Completa todos los campos obligatorios.')
        if UserAdmin.objects.filter(username=username).exists():
            errors.append('El username ya está en uso.')
        if UserAdmin.objects.filter(email=correo).exists():
            errors.append('El correo ya está en uso.')
        if Administrador.objects.filter(cedula=cedula).exists():
            errors.append('La cédula ya está registrada.')
        if len(password) < 8:
            errors.append('La contraseña debe tener mínimo 8 caracteres.')

        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            try:
                password_hash = hashlib.md5(password.encode()).hexdigest()
                user_admin = UserAdmin.objects.create(
                    username=username,
                    email=correo,
                    password=password_hash,
                    id_sede_id=id_sede,
                    status=True,
                )

                dir_admin = None
                if id_estado and id_municipio and id_ciudad and id_parroquia and direccion:
                    dir_admin = DireccionAdmin.objects.create(
                        id_estado_id=id_estado,
                        id_municipio_id=id_municipio,
                        id_ciudad_id=id_ciudad,
                        id_parroquia_id=id_parroquia,
                        direccion=direccion,
                        referencias=referencias,
                    )

                Administrador.objects.create(
                    nombre_1=nombre_1,
                    nombre_2=nombre_2,
                    apellido_1=apellido_1,
                    apellido_2=apellido_2,
                    cedula=cedula,
                    tipo_cedula=tipo_cedula,
                    sexo=sexo,
                    fecha_nacimiento=fecha_nacimiento,
                    fecha_registro=timezone.now(),
                    telefono=telefono,
                    id_user_admin=user_admin,
                    id_sede_id=id_sede,
                    id_direccion_admin=dir_admin,
                    status=True,
                )
                messages.success(request, f'Gerente {username} registrado exitosamente.')
                return redirect('dashboard_superadmin')
            except Exception as e:
                messages.error(request, f'Error al registrar el gerente: {e}')

    context = {
        'sedes': sedes,
        'estados': estados,
        'TIPO_CEDULA': [('V','V'),('E','E'),('J','J'),('C','C'),('G','G'),('P','P'),('F','F')],
        'SEXO': [('M','Masculino'),('F','Femenino'),('NB','No Binario'),('O','Otro'),('PN','Prefiero no decir')],
    }
    return render(request, 'usuarios/registrar_gerente.html', context)


# ── LOGOUT SUPER ADMIN ────────────────────────────────────────────────────────

def logout_superadmin(request):
    user_sa, _ = _get_superadmin_user(request)
    if user_sa:
        registrar_evento(
            user=user_sa,
            role='superadmin',
            action='LOGOUT',
            model_affected='UserSuperAdmin',
            object_id=user_sa.id_superadmin,
            details={'username': user_sa.username},
            request=request,
        )
    request.session.pop('_superadmin_user_id', None)
    request.session.pop('_superadmin_username', None)
    return redirect('login_superadmin')


# ── AUDITORÍA (SUPER ADMIN) ───────────────────────────────────────────────────

@_superadmin_required
def audit_log_list(request):
    user_sa, sa = _get_superadmin_user(request)
    centro = _get_centro(sa)

    queryset = AuditLog.objects.all()

    # Filtros GET
    filtro_user_id = request.GET.get('user_id', '').strip()
    filtro_role = request.GET.get('role', '').strip()
    filtro_action = request.GET.get('action', '').strip()
    fecha_inicio = request.GET.get('fecha_inicio', '').strip()
    fecha_fin = request.GET.get('fecha_fin', '').strip()

    if filtro_user_id:
        try:
            queryset = queryset.filter(id_user=int(filtro_user_id))
        except ValueError:
            pass

    if filtro_role:
        queryset = queryset.filter(role=filtro_role)

    if filtro_action:
        queryset = queryset.filter(action=filtro_action)

    if fecha_inicio:
        try:
            from datetime import datetime
            fi = datetime.strptime(fecha_inicio, '%Y-%m-%d')
            queryset = queryset.filter(timestamp__date__gte=fi.date())
        except ValueError:
            pass

    if fecha_fin:
        try:
            from datetime import datetime
            ff = datetime.strptime(fecha_fin, '%Y-%m-%d')
            queryset = queryset.filter(timestamp__date__lte=ff.date())
        except ValueError:
            pass

    # Paginación simple (últimos 100 registros por defecto, o todos si se filtra)
    total_registros = queryset.count()
    logs = queryset[:200]

    # Valores únicos para selects
    roles_unicos = AuditLog.objects.values_list('role', flat=True).distinct().order_by('role')
    acciones_unicas = AuditLog.objects.values_list('action', flat=True).distinct().order_by('action')

    context = {
        'logs': logs,
        'total_registros': total_registros,
        'roles': roles_unicos,
        'acciones': acciones_unicas,
        'filtro_user_id': filtro_user_id,
        'filtro_role': filtro_role,
        'filtro_action': filtro_action,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'user_sa': user_sa,
        'centro': centro,
    }
    return render(request, 'usuarios/audit_log.html', context)
