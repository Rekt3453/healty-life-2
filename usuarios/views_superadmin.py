import hashlib
import re
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
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

    if centro:
        sedes = Sede.objects.filter(
            id_cm=centro
        ).select_related('id_direccion').order_by('nombre_sede')
    else:
        sedes = Sede.objects.all().select_related('id_direccion').order_by('nombre_sede')

    sede_ids = list(sedes.values_list('id_sede', flat=True))
    if sede_ids:
        gerentes = Administrador.objects.filter(
            id_sede__in=sede_ids
        ).select_related('id_user_admin', 'id_sede').order_by('nombre_1')
    else:
        gerentes = Administrador.objects.all().select_related('id_user_admin', 'id_sede').order_by('nombre_1')

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
        rif_sede = request.POST.get('rif_sede', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        id_estado = request.POST.get('id_estado')
        id_municipio = request.POST.get('id_municipio')
        id_ciudad = request.POST.get('id_ciudad')
        id_parroquia = request.POST.get('id_parroquia')
        direccion = request.POST.get('direccion', '').strip()
        referencia = request.POST.get('referencia', '').strip() or None

        errors = []
        if not nombre_sede:
            errors.append('El nombre de la sede es obligatorio.')
        elif len(nombre_sede) > 30:
            errors.append('El nombre de la sede no puede exceder 30 caracteres.')

        if not rif_sede:
            errors.append('El RIF es obligatorio.')
        elif not re.match(r'^J-\d{8}-\d$', rif_sede):
            errors.append('El RIF debe tener el formato J-12345678-9.')

        if not telefono:
            errors.append('El telefono es obligatorio.')
        elif not re.match(r'^(0412|0426|0424|0422)-\d{3}-\d{4}$', telefono):
            errors.append('El telefono debe tener el formato 0412-123-4567.')

        if not direccion:
            errors.append('La direccion es obligatoria.')
        elif len(direccion) > 100:
            errors.append('La direccion no puede exceder 100 caracteres.')

        if referencia and len(referencia) > 100:
            errors.append('La referencia no puede exceder 100 caracteres.')

        if not all([id_estado, id_municipio, id_ciudad, id_parroquia]):
            errors.append('Completa todos los campos de ubicacion.')

        if errors:
            for e in errors:
                messages.error(request, e)
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

    context = {'estados': estados, 'user_sa': user_sa}
    return render(request, 'usuarios/registrar_sede.html', context)


# ── REGISTRAR GERENTE ─────────────────────────────────────────────────────────

@_superadmin_required
def registrar_gerente(request):
    user_sa, sa = _get_superadmin_user(request)
    centro = _get_centro(sa)
    if centro:
        sedes = Sede.objects.filter(
            id_cm=centro, status=True
        ).order_by('nombre_sede')
    else:
        sedes = Sede.objects.filter(status=True).order_by('nombre_sede')
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

        errors = []
        if not all([username, correo, password, nombre_1, apellido_1, cedula, id_sede, telefono]):
            errors.append('Completa todos los campos obligatorios.')
        if len(username) > 30:
            errors.append('El username no puede exceder 30 caracteres.')
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', correo):
            errors.append('El correo no tiene un formato valido.')
        if not re.match(r'^[A-Za-z\s]+$', nombre_1) or len(nombre_1) > 30:
            errors.append('Nombre 1: solo letras, maximo 30 caracteres.')
        if nombre_2 and (not re.match(r'^[A-Za-z\s]+$', nombre_2) or len(nombre_2) > 30):
            errors.append('Nombre 2: solo letras, maximo 30 caracteres.')
        if not re.match(r'^[A-Za-z\s]+$', apellido_1) or len(apellido_1) > 30:
            errors.append('Apellido 1: solo letras, maximo 30 caracteres.')
        if apellido_2 and (not re.match(r'^[A-Za-z\s]+$', apellido_2) or len(apellido_2) > 30):
            errors.append('Apellido 2: solo letras, maximo 30 caracteres.')
        if tipo_cedula not in ('V', 'E', 'J'):
            errors.append('Tipo de cedula invalido.')
        if not re.match(r'^\d{7,9}$', cedula):
            errors.append('La cedula debe tener entre 7 y 9 digitos numericos.')
        if not re.match(r'^(0412|0426|0424|0422)-\d{3}-\d{4}$', telefono):
            errors.append('El telefono debe tener el formato 0412-123-4567.')
        if len(password) < 8:
            errors.append('La contrasena debe tener minimo 8 caracteres.')
        if UserAdmin.objects.filter(username=username).exists():
            errors.append('El username ya esta en uso.')
        if UserAdmin.objects.filter(email=correo).exists():
            errors.append('El correo ya esta en uso.')
        if Administrador.objects.filter(cedula=cedula).exists():
            errors.append('La cedula ya esta registrada.')

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

                try:
                    send_mail(
                        subject='Bienvenido a Healthy Life - Tu cuenta ha sido creada',
                        message=f"""Hola {nombre_1} {apellido_1},

Tu cuenta de gerente ha sido creada exitosamente en Healthy Life.

Usuario: {username}
Sede asignada: {Sede.objects.filter(id_sede=id_sede).first() or 'N/A'}

Puedes iniciar sesion con tu usuario y contrasena.

Saludos,
Equipo Healthy Life""",
                        from_email=None,
                        recipient_list=[correo],
                        fail_silently=True,
                    )
                except Exception:
                    pass

                messages.success(request, f'Gerente {username} registrado exitosamente.')
                return redirect('dashboard_superadmin')
            except Exception as e:
                messages.error(request, f'Error al registrar el gerente: {e}')

    context = {
        'sedes': sedes,
        'estados': estados,
        'user_sa': user_sa,
        'TIPO_CEDULA': [('V','V'),('E','E'),('J','J')],
        'SEXO': [('M','Masculino'),('F','Femenino'),('NB','No Binario'),('O','Otro'),('PN','Prefiero no decir')],
    }
    return render(request, 'usuarios/registrar_gerente.html', context)


# ── LISTA SEDES ───────────────────────────────────────────────────────────────

@_superadmin_required
def lista_sedes(request):
    user_sa, sa = _get_superadmin_user(request)
    filtro = request.GET.get('filtro', 'todos')

    queryset = Sede.objects.all().select_related('id_cm').order_by('nombre_sede')
    if filtro == 'activos':
        queryset = queryset.filter(status=True)
    elif filtro == 'inactivos':
        queryset = queryset.filter(status=False)

    paginator = Paginator(queryset, 10)
    page = request.GET.get('page')
    page_obj = paginator.get_page(page)

    context = {
        'user_sa': user_sa,
        'page_obj': page_obj,
        'filtro': filtro,
    }
    return render(request, 'usuarios/lista_sedes.html', context)


@_superadmin_required
def toggle_sede_status(request, id_sede):
    sede = get_object_or_404(Sede, pk=id_sede)
    sede.status = not sede.status if sede.status is not None else True
    sede.save()
    estado = 'activada' if sede.status else 'desactivada'
    messages.success(request, f'Sede "{sede.nombre_sede}" {estado} exitosamente.')
    return redirect('lista_sedes')


@_superadmin_required
def editar_sede(request, id_sede):
    user_sa, sa = _get_superadmin_user(request)
    sede = get_object_or_404(Sede, pk=id_sede)

    if request.method == 'POST':
        nombre_sede = request.POST.get('nombre_sede', '').strip()
        rif_sede = request.POST.get('rif_sede', '').strip()
        telefono = request.POST.get('telefono', '').strip()

        errors = []
        if not nombre_sede:
            errors.append('El nombre de la sede es obligatorio.')
        elif len(nombre_sede) > 30:
            errors.append('El nombre no puede exceder 30 caracteres.')
        if rif_sede and not re.match(r'^J-\d{8}-\d$', rif_sede):
            errors.append('El RIF debe tener el formato J-12345678-9.')
        if telefono and not re.match(r'^(0412|0426|0424|0422)-\d{3}-\d{4}$', telefono):
            errors.append('El telefono debe tener el formato 0412-123-4567.')

        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            sede.nombre_sede = nombre_sede
            sede.rif_sede = rif_sede or None
            sede.telefono = telefono or None
            sede.save()
            messages.success(request, f'Sede "{nombre_sede}" actualizada exitosamente.')
            return redirect('lista_sedes')

    context = {
        'user_sa': user_sa,
        'sede': sede,
    }
    return render(request, 'usuarios/editar_sede.html', context)


# ── LISTA GERENTES ──────────────────────────────────────────────────────────────

@_superadmin_required
def lista_gerentes(request):
    user_sa, sa = _get_superadmin_user(request)
    filtro = request.GET.get('filtro', 'todos')

    queryset = Administrador.objects.all().select_related('id_user_admin', 'id_sede').order_by('nombre_1')
    if filtro == 'activos':
        queryset = queryset.filter(status=True)
    elif filtro == 'inactivos':
        queryset = queryset.filter(status=False)

    paginator = Paginator(queryset, 10)
    page = request.GET.get('page')
    page_obj = paginator.get_page(page)

    context = {
        'user_sa': user_sa,
        'page_obj': page_obj,
        'filtro': filtro,
    }
    return render(request, 'usuarios/lista_gerentes.html', context)


@_superadmin_required
def toggle_gerente_status(request, id_administrador):
    gerente = get_object_or_404(Administrador, pk=id_administrador)
    gerente.status = not gerente.status if gerente.status is not None else True
    gerente.save()
    estado = 'activado' if gerente.status else 'desactivado'
    messages.success(request, f'Gerente "{gerente}" {estado} exitosamente.')
    return redirect('lista_gerentes')


@_superadmin_required
def editar_gerente(request, id_administrador):
    user_sa, sa = _get_superadmin_user(request)
    gerente = get_object_or_404(Administrador, pk=id_administrador)
    sedes = Sede.objects.filter(status=True).order_by('nombre_sede')

    if request.method == 'POST':
        nombre_1 = request.POST.get('nombre_1', '').strip().upper()
        nombre_2 = request.POST.get('nombre_2', '').strip().upper() or None
        apellido_1 = request.POST.get('apellido_1', '').strip().upper()
        apellido_2 = request.POST.get('apellido_2', '').strip().upper() or None
        telefono = request.POST.get('telefono', '').strip()
        id_sede = request.POST.get('id_sede')
        status = request.POST.get('status', '1') == '1'

        errors = []
        if not nombre_1:
            errors.append('El nombre es obligatorio.')
        elif not re.match(r'^[A-Za-z\s]+$', nombre_1) or len(nombre_1) > 30:
            errors.append('Nombre 1: solo letras, maximo 30 caracteres.')
        if nombre_2 and (not re.match(r'^[A-Za-z\s]+$', nombre_2) or len(nombre_2) > 30):
            errors.append('Nombre 2: solo letras, maximo 30 caracteres.')
        if not apellido_1:
            errors.append('El apellido es obligatorio.')
        elif not re.match(r'^[A-Za-z\s]+$', apellido_1) or len(apellido_1) > 30:
            errors.append('Apellido 1: solo letras, maximo 30 caracteres.')
        if apellido_2 and (not re.match(r'^[A-Za-z\s]+$', apellido_2) or len(apellido_2) > 30):
            errors.append('Apellido 2: solo letras, maximo 30 caracteres.')
        if telefono and not re.match(r'^(0412|0426|0424|0422)-\d{3}-\d{4}$', telefono):
            errors.append('El telefono debe tener el formato 0412-123-4567.')

        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            gerente.nombre_1 = nombre_1
            gerente.nombre_2 = nombre_2
            gerente.apellido_1 = apellido_1
            gerente.apellido_2 = apellido_2
            gerente.telefono = telefono
            gerente.id_sede_id = id_sede or None
            gerente.status = status
            gerente.save()
            messages.success(request, f'Gerente "{gerente}" actualizado exitosamente.')
            return redirect('lista_gerentes')

    context = {
        'user_sa': user_sa,
        'gerente': gerente,
        'sedes': sedes,
    }
    return render(request, 'usuarios/editar_gerente.html', context)


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
