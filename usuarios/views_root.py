import hashlib
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from .models import (
    UserRoot, Root, UserSuperAdmin, Superadmin, CentroMedico,
    Sede, UserAdmin, Administrador, Estado, Municipio, Ciudad, Parroquia,
    DireccionSuperadmin,
)

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


# ── LOGIN ROOT ────────────────────────────────────────────────────────────────

def login_root(request):
    if _get_root_user(request):
        return redirect('dashboard_root')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        password_hash = hashlib.md5(password.encode()).hexdigest()

        user = UserRoot.objects.filter(username=username, contrasena=password_hash).first()
        if user:
            request.session['_root_user_id'] = user.id_user_root
            request.session['_root_username'] = user.username
            messages.success(request, f'Bienvenido, {user.username}')
            return redirect('dashboard_root')
        else:
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
    centros = CentroMedico.objects.filter(status=True).order_by('nombre_cm')
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
        id_cm = request.POST.get('id_cm')
        id_estado = request.POST.get('id_estado')
        id_municipio = request.POST.get('id_municipio')
        id_ciudad = request.POST.get('id_ciudad')
        id_parroquia = request.POST.get('id_parroquia')
        direccion = request.POST.get('direccion', '').strip()
        referencia = request.POST.get('referencia', '').strip() or None

        errors = []
        if not all([username, correo, password, nombre_1, apellido_1, cedula, id_cm]):
            errors.append('Completa todos los campos obligatorios.')
        if UserSuperAdmin.objects.filter(username=username).exists():
            errors.append('El username ya está en uso.')
        if UserSuperAdmin.objects.filter(correo=correo).exists():
            errors.append('El correo ya está en uso.')
        if Superadmin.objects.filter(cedula=cedula).exists():
            errors.append('La cédula ya está registrada.')
        if len(password) < 8:
            errors.append('La contraseña debe tener mínimo 8 caracteres.')

        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            try:
                password_hash = hashlib.md5(password.encode()).hexdigest()
                user_sa = UserSuperAdmin.objects.create(
                    username=username,
                    correo=correo,
                    contrasena=password_hash,
                    status=True,
                )

                dir_sa = None
                if id_estado and id_municipio and id_ciudad and id_parroquia and direccion:
                    dir_sa = DireccionSuperadmin.objects.create(
                        id_estado_id=id_estado,
                        id_municipio_id=id_municipio,
                        id_ciudad_id=id_ciudad,
                        id_parroquia_id=id_parroquia,
                        direccion=direccion,
                        referencia=referencia,
                    )

                sede_sa = None
                if id_cm:
                    from usuarios.models import Sede
                    sede_sa = Sede.objects.filter(id_cm_id=id_cm, status=True).first()

                Superadmin.objects.create(
                    id_user_superadmin=user_sa,
                    nombre_1=nombre_1,
                    nombre_2=nombre_2,
                    apellido_1=apellido_1,
                    apellido_2=apellido_2,
                    cedula=cedula,
                    tipo_cedula=tipo_cedula,
                    id_sede=sede_sa,
                    status=True,
                )
                messages.success(request, f'Super Admin {username} registrado exitosamente.')
                return redirect('dashboard_root')
            except Exception as e:
                messages.error(request, f'Error al registrar: {e}')

    municipios = Municipio.objects.none()
    ciudades = Ciudad.objects.none()
    parroquias = Parroquia.objects.none()

    context = {
        'centros': centros,
        'estados': estados,
        'municipios': municipios,
        'ciudades': ciudades,
        'parroquias': parroquias,
        'TIPO_CEDULA': [('V','V'),('E','E'),('J','J'),('C','C'),('G','G'),('P','P'),('F','F')],
        'SEXO': [('M','Masculino'),('F','Femenino'),('NB','No Binario'),('O','Otro'),('PN','Prefiero no decir')],
    }
    return render(request, 'usuarios/registrar_superadmin.html', context)


# ── LOGOUT ROOT ───────────────────────────────────────────────────────────────

def logout_root(request):
    request.session.pop('_root_user_id', None)
    request.session.pop('_root_username', None)
    return redirect('login_root')
