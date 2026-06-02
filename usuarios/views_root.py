import hashlib
import re
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from .models import (
    UserRoot, Root, UserSuperAdmin, Superadmin, CentroMedico,
    Sede, UserAdmin, Administrador, Estado, Municipio, Ciudad, Parroquia,
    DireccionSuperadmin,
)
from .audit_services import registrar_evento
from .authentication import is_rate_limited, _record_failed, get_client_ip

# ── helpers ──────────────────────────────────────────────────────────────────

def _get_root_user(request):
    uid = request.session.get('_root_user_id')
    if not uid:
        return None
    return UserRoot.objects.filter(id_user_root=uid).first()


def _root_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not _get_root_user(request):
            messages.error(request, 'Acceso restringido. Inicia sesión como Root.')
            return redirect('login_root')
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


def _validar_rif_cm(rif_cm):
    """Valida formato estricto J-12345678-9 (u otros prefijos VEJ/G)."""
    if not rif_cm:
        return True
    return bool(re.fullmatch(r'^[VJEG]-\d{8}-\d$', rif_cm))


# ── LOGIN ROOT ────────────────────────────────────────────────────────────────

def login_root(request):
    if _get_root_user(request):
        return redirect('dashboard_root')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        ip = get_client_ip(request)

        if is_rate_limited(username, ip):
            messages.error(request, 'Demasiados intentos fallidos. Espere 1 minuto e intente de nuevo.')
            return render(request, 'usuarios/login_root.html')

        password_hash = hashlib.md5(password.encode()).hexdigest()

        user = UserRoot.objects.filter(username=username, contrasena=password_hash).first()
        if user:
            request.session['_root_user_id'] = user.id_user_root
            request.session['_root_username'] = user.username
            registrar_evento(
                user=user,
                role='root',
                action='LOGIN',
                model_affected='UserRoot',
                object_id=user.pk,
                details={'username': user.username},
                request=request,
            )
            messages.success(request, f'Bienvenido, {user.username}')
            return redirect('dashboard_root')
        else:
            _record_failed(username, ip)
            messages.error(request, 'Credenciales incorrectas.')

    return render(request, 'usuarios/login_root.html')


# ── DASHBOARD ROOT ────────────────────────────────────────────────────────────

@_root_required
def dashboard_root(request):
    user = _get_root_user(request)
    centros = CentroMedico.objects.all().order_by('nombre_cm')
    superadmins = Superadmin.objects.select_related(
        'id_user_superadmin', 'id_sede', 'id_sede__id_cm'
    ).all().order_by('nombre_1')

    context = {
        'root_user': user,
        'centros': centros,
        'superadmins': superadmins,
        'total_centros': centros.count(),
        'total_superadmins': superadmins.count(),
        'total_sedes': Sede.objects.count(),
        'total_gerentes': Administrador.objects.count(),
    }
    return render(request, 'usuarios/dashboard_root.html', context)


# ── REGISTRAR CENTRO MÉDICO ───────────────────────────────────────────────────

@_root_required
def registrar_centro_medico(request):
    if request.method == 'POST':
        nombre_cm = request.POST.get('nombre_cm', '').strip()
        rif_cm = request.POST.get('rif_cm', '').strip()

        if not nombre_cm:
            messages.error(request, 'El nombre del centro médico es obligatorio.')
        elif len(nombre_cm) > 30:
            messages.error(request, 'El nombre del centro médico no puede superar los 30 caracteres.')
        elif rif_cm and not _validar_rif_cm(rif_cm):
            messages.error(request, 'El RIF debe tener el formato J-12345678-9.')
        elif CentroMedico.objects.filter(rif_cm=rif_cm).exists() and rif_cm:
            messages.error(request, 'Ya existe un centro médico con ese RIF.')
        else:
            CentroMedico.objects.create(
                nombre_cm=nombre_cm,
                rif_cm=rif_cm or None,
                status=True,
            )
            messages.success(request, f'Centro médico "{nombre_cm}" registrado exitosamente.')
            return redirect('dashboard_root')

    return render(request, 'usuarios/registrar_centro_medico.html')


# ── REGISTRAR SUPER ADMIN ─────────────────────────────────────────────────────

@_root_required
def registrar_superadmin(request):
    from .forms import RegistroSuperAdminForm

    if request.method == 'POST':
        form = RegistroSuperAdminForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            try:
                user_sa = UserSuperAdmin.objects.create(
                    username=cd['username'],
                    correo=cd['correo'],
                    contrasena='',
                    status=False,
                )

                sede_sa = None
                if cd['id_cm']:
                    from usuarios.models import Sede
                    sede_sa = Sede.objects.filter(id_cm_id=cd['id_cm'].id_cm, status=True).first()

                Superadmin.objects.create(
                    id_user_superadmin=user_sa,
                    nombre_1=cd['nombre_1'].upper(),
                    nombre_2=(cd['nombre_2'] or '').upper() or None,
                    apellido_1=cd['apellido_1'].upper(),
                    apellido_2=(cd['apellido_2'] or '').upper() or None,
                    cedula=cd['cedula'],
                    tipo_cedula=cd['tipo_cedula'],
                    id_sede=sede_sa,
                    status=True,
                )

                # Enviar correo de activación
                try:
                    from .email_config import generar_token_activacion, enviar_correo_activacion
                    from django.db import connection
                    token = generar_token_activacion(user_sa.pk, user_sa.correo)
                    with connection.cursor() as c:
                        c.execute("UPDATE user_superadmin SET token_activacion = %s WHERE id_user_superadmin = %s", [token, user_sa.pk])
                    enlace = request.build_absolute_uri(f"/activar-cuenta/{user_sa.pk}/{token}/")
                    sa_profile = Superadmin.objects.filter(id_user_superadmin=user_sa).first()
                    if sa_profile:
                        user_sa.nombre_1 = sa_profile.nombre_1
                        user_sa.nombre_2 = sa_profile.nombre_2
                        user_sa.apellido_1 = sa_profile.apellido_1
                        user_sa.apellido_2 = sa_profile.apellido_2
                    ok = enviar_correo_activacion(user_sa, 'Super Admin', enlace)
                    if ok:
                        messages.success(request, 'Se envió un correo de activación al Super Admin.')
                    else:
                        messages.warning(request, 'El Super Admin se registró pero no se pudo enviar el correo de activación.')
                except Exception as mail_err:
                    print(f'WARN: No se pudo enviar correo de activación al super admin: {mail_err}')
                    messages.warning(request, 'El Super Admin se registró pero no se pudo enviar el correo de activación.')

                messages.success(request, f'Super Admin {cd["username"]} registrado exitosamente.')
                return redirect('dashboard_root')
            except Exception as e:
                messages.error(request, f'Error al registrar: {e}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields[field].label or field}: {error}")
    else:
        form = RegistroSuperAdminForm()

    context = {
        'form': form,
    }
    return render(request, 'usuarios/registrar_superadmin.html', context)


# ── LOGOUT ROOT ───────────────────────────────────────────────────────────────

def logout_root(request):
    user = _get_root_user(request)
    if user:
        registrar_evento(
            user=user,
            role='root',
            action='LOGOUT',
            model_affected='UserRoot',
            object_id=user.pk,
            details={'username': user.username},
            request=request,
        )
    request.session.pop('_root_user_id', None)
    request.session.pop('_root_username', None)
    return redirect('login_root')
