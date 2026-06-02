import hashlib
import re
import logging
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from .models import (
    UserRoot, Root, UserSuperAdmin, Superadmin, CentroMedico,
    Sede, UserAdmin, Administrador, Estado, Municipio, Ciudad, Parroquia,
    DireccionSuperadmin, AuditLog,
)
from .audit_services import registrar_evento
from .authentication import is_rate_limited, _record_failed, get_client_ip

logger = logging.getLogger('usuarios')

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
    centros_all = CentroMedico.objects.all().order_by('nombre_cm')
    superadmins_all = Superadmin.objects.select_related(
        'id_user_superadmin', 'id_sede', 'id_sede__id_cm'
    ).all().order_by('nombre_1')

    context = {
        'root_user': user,
        'centros': centros_all[:5],
        'superadmins': superadmins_all[:5],
        'total_centros': centros_all.count(),
        'total_superadmins': superadmins_all.count(),
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
                    logger.warning(f"No se pudo enviar correo de activación al super admin: {mail_err}")
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


# ── EDITAR CENTRO MÉDICO ──────────────────────────────────────────────────────

@_root_required
def editar_centro_medico(request, id_cm):
    centro = get_object_or_404(CentroMedico, pk=id_cm)
    if request.method == 'POST':
        nombre_cm = request.POST.get('nombre_cm', '').strip()
        rif_cm = request.POST.get('rif_cm', '').strip()

        if not nombre_cm:
            messages.error(request, 'El nombre del centro médico es obligatorio.')
        elif len(nombre_cm) > 30:
            messages.error(request, 'El nombre no puede superar los 30 caracteres.')
        elif rif_cm and not _validar_rif_cm(rif_cm):
            messages.error(request, 'El RIF debe tener el formato J-12345678-9.')
        elif rif_cm and CentroMedico.objects.filter(rif_cm=rif_cm).exclude(pk=id_cm).exists():
            messages.error(request, 'Ya existe otro centro médico con ese RIF.')
        else:
            centro.nombre_cm = nombre_cm
            centro.rif_cm = rif_cm or None
            centro.save()
            messages.success(request, f'Centro médico "{nombre_cm}" actualizado.')
            return redirect('dashboard_root')

    return render(request, 'usuarios/editar_centro_medico.html', {'centro': centro})


# ── TOGGLE CENTRO MÉDICO STATUS ───────────────────────────────────────────────

@_root_required
def toggle_centro_medico_status(request, id_cm):
    centro = get_object_or_404(CentroMedico, pk=id_cm)
    centro.status = not centro.status if centro.status is not None else True
    centro.save()
    estado = 'activado' if centro.status else 'desactivado'
    messages.success(request, f'Centro médico "{centro.nombre_cm}" {estado}.')
    return redirect('dashboard_root')


# ── ELIMINAR CENTRO MÉDICO ──────────────────────────────────────────────────────

@_root_required
def eliminar_centro_medico(request, id_cm):
    centro = get_object_or_404(CentroMedico, pk=id_cm)
    if request.method == 'POST':
        nombre = centro.nombre_cm
        centro.delete()
        messages.success(request, f'Centro médico "{nombre}" eliminado permanentemente.')
        return redirect('dashboard_root')
    return render(request, 'usuarios/eliminar_centro_medico.html', {'centro': centro})


# ── EDITAR SUPER ADMIN ────────────────────────────────────────────────────────

@_root_required
def editar_superadmin(request, id_superadmin):
    sa = get_object_or_404(Superadmin, pk=id_superadmin)
    user_sa = sa.id_user_superadmin
    if request.method == 'POST':
        nombre_1 = request.POST.get('nombre_1', '').strip().upper()
        nombre_2 = request.POST.get('nombre_2', '').strip().upper() or None
        apellido_1 = request.POST.get('apellido_1', '').strip().upper()
        apellido_2 = request.POST.get('apellido_2', '').strip().upper() or None
        cedula = request.POST.get('cedula', '').strip()
        tipo_cedula = request.POST.get('tipo_cedula', 'V')
        id_cm = request.POST.get('id_cm')

        if not nombre_1 or not apellido_1:
            messages.error(request, 'Nombre y apellido son obligatorios.')
        elif cedula and Superadmin.objects.filter(cedula=cedula).exclude(pk=id_superadmin).exists():
            messages.error(request, 'Esta cédula ya está registrada en otro super admin.')
        else:
            sa.nombre_1 = nombre_1
            sa.nombre_2 = nombre_2
            sa.apellido_1 = apellido_1
            sa.apellido_2 = apellido_2
            sa.cedula = cedula
            sa.tipo_cedula = tipo_cedula
            if id_cm:
                sede = Sede.objects.filter(id_cm_id=id_cm, status=True).first()
                sa.id_sede = sede
            sa.save()
            messages.success(request, f'Super Admin actualizado correctamente.')
            return redirect('dashboard_root')

    centros = CentroMedico.objects.filter(status=True).order_by('nombre_cm')
    return render(request, 'usuarios/editar_superadmin.html', {
        'sa': sa,
        'user_sa': user_sa,
        'centros': centros,
    })


# ── TOGGLE SUPER ADMIN STATUS ─────────────────────────────────────────────────

@_root_required
def toggle_superadmin_status(request, id_superadmin):
    sa = get_object_or_404(Superadmin, pk=id_superadmin)
    sa.status = not sa.status if sa.status is not None else True
    sa.save()
    if sa.id_user_superadmin:
        sa.id_user_superadmin.status = sa.status
        sa.id_user_superadmin.save()
    estado = 'activado' if sa.status else 'desactivado'
    messages.success(request, f'Super Admin "{sa}" {estado}.')
    return redirect('dashboard_root')


# ── ELIMINAR SUPER ADMIN ────────────────────────────────────────────────────────

@_root_required
def eliminar_superadmin(request, id_superadmin):
    sa = get_object_or_404(Superadmin, pk=id_superadmin)
    if request.method == 'POST':
        nombre = str(sa)
        user_sa = sa.id_user_superadmin
        sa.delete()
        if user_sa:
            user_sa.delete()
        messages.success(request, f'Super Admin "{nombre}" eliminado permanentemente.')
        return redirect('dashboard_root')
    return render(request, 'usuarios/eliminar_superadmin.html', {'sa': sa})


# ── LISTA CENTROS MÉDICOS (ROOT) ──────────────────────────────────────────────

@_root_required
def lista_centros_root(request):
    user = _get_root_user(request)
    centros = CentroMedico.objects.all().order_by('nombre_cm')
    context = {
        'root_user': user,
        'centros': centros,
        'total_centros': centros.count(),
    }
    return render(request, 'usuarios/lista_centros_root.html', context)


# ── LISTA SUPER ADMINS (ROOT) ──────────────────────────────────────────────────

@_root_required
def lista_superadmins_root(request):
    user = _get_root_user(request)
    superadmins = Superadmin.objects.select_related(
        'id_user_superadmin', 'id_sede', 'id_sede__id_cm'
    ).all().order_by('nombre_1')
    context = {
        'root_user': user,
        'superadmins': superadmins,
        'total_superadmins': superadmins.count(),
    }
    return render(request, 'usuarios/lista_superadmins_root.html', context)


# ── AUDITORÍA COMPLETA (ROOT) ─────────────────────────────────────────────────

@_root_required
def auditoria_root(request):
    """Auditoria completa del sistema para Root — sin filtros de centro médico."""
    root_user = _get_root_user(request)

    queryset = AuditLog.objects.all().order_by('-timestamp')

    # Filtros GET
    filtro_user_id = request.GET.get('user_id', '').strip()
    filtro_role = request.GET.get('role', '').strip()
    filtro_action = request.GET.get('action', '').strip()
    filtro_model = request.GET.get('model', '').strip()
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
    if filtro_model:
        queryset = queryset.filter(model_affected__iexact=filtro_model)
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

    # Estadísticas
    today = timezone.now().date()
    total_registros = queryset.count()
    hoy_count = AuditLog.objects.filter(timestamp__date=today).count()

    # Breakdown por rol (con porcentajes)
    total_all = AuditLog.objects.count()
    roles_stats_raw = list(
        AuditLog.objects.values('role')
        .annotate(count=Count('id_log'))
        .order_by('-count')
    )
    roles_stats = []
    for rs in roles_stats_raw:
        rs['pct'] = round((rs['count'] / total_all) * 100) if total_all else 0
        roles_stats.append(rs)

    # Breakdown por acción (top 10, con porcentajes)
    acciones_stats_raw = list(
        AuditLog.objects.values('action')
        .annotate(count=Count('id_log'))
        .order_by('-count')[:10]
    )
    acciones_stats = []
    for a in acciones_stats_raw:
        a['pct'] = round((a['count'] / total_all) * 100) if total_all else 0
        acciones_stats.append(a)

    # Valores únicos para filtros
    roles_unicos = AuditLog.objects.values_list('role', flat=True).distinct().order_by('role')
    acciones_unicas = AuditLog.objects.values_list('action', flat=True).distinct().order_by('action')
    modelos_unicos = AuditLog.objects.exclude(model_affected__isnull=True).exclude(model_affected='').values_list('model_affected', flat=True).distinct().order_by('model_affected')

    # Paginacion
    paginator = Paginator(queryset, 50)
    page_number = request.GET.get('page', 1)
    try:
        page_obj = paginator.page(page_number)
    except Exception:
        page_obj = paginator.page(1)

    context = {
        'root_user': root_user,
        'page_obj': page_obj,
        'total_registros': total_registros,
        'hoy_count': hoy_count,
        'roles_stats': roles_stats,
        'acciones_stats': acciones_stats,
        'roles': roles_unicos,
        'acciones': acciones_unicas,
        'modelos': modelos_unicos,
        'filtro_user_id': filtro_user_id,
        'filtro_role': filtro_role,
        'filtro_action': filtro_action,
        'filtro_model': filtro_model,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
    }
    return render(request, 'usuarios/dashboard_root_auditoria.html', context)


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
