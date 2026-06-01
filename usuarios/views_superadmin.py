import hashlib
import re
from datetime import datetime
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse
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
                sede_obj = Sede.objects.create(
                    nombre_sede=nombre_sede,
                    rif_sede=rif_sede,
                    telefono=telefono,
                    id_direccion=dir_sede,
                    id_cm=centro,
                    status=True,
                )
                registrar_evento(
                    user=user_sa,
                    role='superadmin',
                    action='CREATE',
                    model_affected='Sede',
                    object_id=sede_obj.pk,
                    details={'nombre_sede': nombre_sede, 'rif': rif_sede},
                    request=request,
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
        if fecha_nacimiento:
            try:
                from datetime import date as _date
                fn = datetime.strptime(fecha_nacimiento, '%Y-%m-%d').date()
                if fn > _date.today():
                    errors.append('La fecha de nacimiento no puede ser futura.')
                else:
                    edad = _date.today().year - fn.year - ((_date.today().month, _date.today().day) < (fn.month, fn.day))
                    if edad < 18:
                        errors.append('El gerente debe tener al menos 18 años.')
            except ValueError:
                errors.append('La fecha de nacimiento no es valida.')
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
                registrar_evento(
                    user=user_sa,
                    role='superadmin',
                    action='CREATE',
                    model_affected='UserAdmin',
                    object_id=user_admin.pk,
                    details={'username': username, 'sede_id': id_sede, 'rol': 'gerente'},
                    request=request,
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
    user_sa, _ = _get_superadmin_user(request)
    sede = get_object_or_404(Sede, pk=id_sede)
    sede.status = not sede.status if sede.status is not None else True
    sede.save()
    estado = 'activada' if sede.status else 'desactivada'
    registrar_evento(
        user=user_sa,
        role='superadmin',
        action='STATUS_CHANGE',
        model_affected='Sede',
        object_id=sede.pk,
        details={'sede': sede.nombre_sede, 'nuevo_estado': estado},
        request=request,
    )
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
    user_sa, _ = _get_superadmin_user(request)
    gerente = get_object_or_404(Administrador, pk=id_administrador)
    gerente.status = not gerente.status if gerente.status is not None else True
    gerente.save()
    estado = 'activado' if gerente.status else 'desactivado'
    registrar_evento(
        user=user_sa,
        role='superadmin',
        action='STATUS_CHANGE',
        model_affected='Administrador',
        object_id=gerente.pk,
        details={'gerente': str(gerente), 'nuevo_estado': estado},
        request=request,
    )
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


# ── REPORTES SUPER ADMIN ──────────────────────────────────────────────────────

@_superadmin_required
def reportes_superadmin(request):
    user_sa, sa = _get_superadmin_user(request)
    from datetime import datetime
    from citas.reportes import ReportesService

    hoy = timezone.now().date()
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    id_sede = request.GET.get('id_sede')

    if not fecha_inicio:
        fecha_inicio = hoy.replace(day=1)
    else:
        fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()

    if not fecha_fin:
        fecha_fin = hoy
    else:
        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()

    # Obtener sedes del centro médico del superadmin
    centro = _get_centro(sa)
    if centro:
        sedes = Sede.objects.filter(id_cm=centro, status=True).order_by('nombre_sede')
    else:
        sedes = Sede.objects.none()
    mis_sede_ids = list(sedes.values_list('id_sede', flat=True))

    if id_sede:
        id_sede = int(id_sede)
        if id_sede not in mis_sede_ids:
            id_sede = None

    # Métricas generales
    datos_atencion = ReportesService.reporte_diario_atencion(fecha_inicio, fecha_fin, id_sede)
    datos_balance = ReportesService.reporte_balance(fecha_inicio, fecha_fin, id_sede)
    datos_honorarios = ReportesService.reporte_pagos_medicos(fecha_inicio, fecha_fin, id_sede)
    datos_pacientes = ReportesService.reporte_pacientes_nuevos(fecha_inicio, fecha_fin, id_sede)
    datos_doctores = ReportesService.reporte_doctores(id_sede)

    # Desglose por sede (solo cuando no se filtra una sede específica)
    breakdown = []
    if not id_sede:
        for sede in sedes:
            atencion_sede = ReportesService.reporte_diario_atencion(fecha_inicio, fecha_fin, sede.id_sede)
            balance_sede = ReportesService.reporte_balance(fecha_inicio, fecha_fin, sede.id_sede)
            honorarios_sede = ReportesService.reporte_pagos_medicos(fecha_inicio, fecha_fin, sede.id_sede)
            pacientes_sede = ReportesService.reporte_pacientes_nuevos(fecha_inicio, fecha_fin, sede.id_sede)
            doctores_sede = ReportesService.reporte_doctores(sede.id_sede)
            breakdown.append({
                'sede': sede,
                'total_citas': atencion_sede['total_citas'],
                'atendidas': atencion_sede['atendidas'],
                'canceladas': atencion_sede['canceladas'],
                'facturacion': balance_sede['facturacion']['total'],
                'honorarios': honorarios_sede['totales']['total_honorarios'],
                'pacientes_nuevos': pacientes_sede['total'],
                'doctores': doctores_sede['total'],
            })

    # Desglose por doctor (solo cuando se filtra una sede específica)
    breakdown_doctors = []
    sede_obj = None
    if id_sede:
        sede_obj = get_object_or_404(Sede, pk=id_sede)
        from citas.models import Cita
        from django.db.models import Count
        from decimal import Decimal
        doctores = ReportesService.obtener_medicos(id_sede)
        for doc in doctores:
            citas_doc = Cita.objects.filter(
                id_doctor_id=doc['id_doctor'],
                fecha_consulta__date__gte=fecha_inicio,
                fecha_consulta__date__lte=fecha_fin,
                status=True
            )
            atendidas_doc = citas_doc.filter(estado=Cita.ESTADO_ATENDIDA).count()
            canceladas_doc = citas_doc.filter(estado=Cita.ESTADO_CANCELADA).count()
            # Honorarios del doctor
            honor_doc = ReportesService.reporte_pagos_medicos(fecha_inicio, fecha_fin, id_sede, doc['id_doctor'])
            total_hon = honor_doc['totales']['total_honorarios']
            total_pagado = honor_doc['totales']['total_pagado']
            total_pendiente = honor_doc['totales']['total_pendiente']
            breakdown_doctors.append({
                'nombre': f"Dr. {doc['nombre_1'] or ''} {doc['apellido_1'] or ''}".strip(),
                'total_citas': citas_doc.count(),
                'atendidas': atendidas_doc,
                'canceladas': canceladas_doc,
                'honorarios': total_hon,
                'pagado': total_pagado,
                'pendiente': total_pendiente,
            })

    context = {
        'user_sa': user_sa,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'id_sede': id_sede,
        'sede_obj': sede_obj,
        'sedes': sedes,
        'datos_atencion': datos_atencion,
        'datos_balance': datos_balance,
        'datos_honorarios': datos_honorarios,
        'datos_pacientes': datos_pacientes,
        'datos_doctores': datos_doctores,
        'breakdown': breakdown,
        'breakdown_doctors': breakdown_doctors,
    }
    return render(request, 'usuarios/reportes_superadmin.html', context)


# ── PDF REPORTES SUPER ADMIN ──────────────────────────────────────────────────

def _generar_pdf_reportes(fecha_inicio, fecha_fin, id_sede, sede_obj,
                          datos_atencion, datos_balance, datos_honorarios,
                          datos_pacientes, datos_doctores,
                          breakdown, breakdown_doctors):
    """Genera un PDF de reportes usando ReportLab y devuelve el contenido binario."""
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from io import BytesIO

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    elements = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle', parent=styles['Heading1'], fontSize=18,
        textColor=colors.HexColor('#1f2937'), spaceAfter=12, alignment=1
    )
    subtitle_style = ParagraphStyle(
        'CustomSubtitle', parent=styles['Normal'], fontSize=10,
        textColor=colors.HexColor('#6b7280'), spaceAfter=20, alignment=1
    )
    header_style = ParagraphStyle(
        'TableHeader', parent=styles['Normal'], fontSize=9,
        textColor=colors.whitesmoke, alignment=1, fontName='Helvetica-Bold'
    )
    cell_style = ParagraphStyle(
        'TableCell', parent=styles['Normal'], fontSize=9,
        textColor=colors.HexColor('#374151'), alignment=1
    )
    left_cell_style = ParagraphStyle(
        'LeftTableCell', parent=styles['Normal'], fontSize=9,
        textColor=colors.HexColor('#374151'), alignment=0
    )

    # Titulo
    elements.append(Paragraph("Healthy Life - Reporte de Operaciones", title_style))
    elements.append(Paragraph(
        f"Periodo: {fecha_inicio.strftime('%d/%m/%Y')} - {fecha_fin.strftime('%d/%m/%Y')}"
        f"{' | Sede: ' + sede_obj.nombre_sede if sede_obj else ' | Todas las sedes'}",
        subtitle_style
    ))
    elements.append(Spacer(1, 0.3*cm))

    # Metricas generales
    metric_data = [
        ['Citas Agendadas', 'Citas Atendidas', 'Doctores Activos'],
        [str(datos_atencion['total_citas']), str(datos_atencion['atendidas']), str(datos_doctores['total'])],
        ['Facturacion Total', 'Honorarios Medicos', 'Pacientes Nuevos'],
        [f"${float(datos_balance['facturacion']['total']):,.2f}",
         f"${float(datos_honorarios['totales']['total_honorarios']):,.2f}",
         str(datos_pacientes['total'])],
    ]
    metric_table = Table(metric_data, colWidths=[5.5*cm, 5.5*cm, 5.5*cm])
    metric_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
        ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#10b981')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('TEXTCOLOR', (0, 2), (-1, 2), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 2), (-1, 2), 8),
        ('TOPPADDING', (0, 2), (-1, 2), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#f9fafb')),
        ('BACKGROUND', (0, 3), (-1, 3), colors.HexColor('#f9fafb')),
    ]))
    elements.append(metric_table)
    elements.append(Spacer(1, 0.6*cm))

    # Tabla de desglose
    if not id_sede and breakdown:
        elements.append(Paragraph("Desglose por Sede", styles['Heading2']))
        elements.append(Spacer(1, 0.2*cm))
        bd_data = [['Sede', 'Citas', 'Atend.', 'Cancel.', 'Doctores', 'Facturacion', 'Honorarios', 'Pac. Nuevos']]
        for item in breakdown:
            bd_data.append([
                item['sede'].nombre_sede,
                str(item['total_citas']),
                str(item['atendidas']),
                str(item['canceladas']),
                str(item['doctores']),
                f"${float(item['facturacion']):,.2f}",
                f"${float(item['honorarios']):,.2f}",
                str(item['pacientes_nuevos']),
            ])
        bd_table = Table(bd_data, colWidths=[4.5*cm, 1.5*cm, 1.5*cm, 1.5*cm, 1.8*cm, 2.5*cm, 2.5*cm, 1.8*cm])
        bd_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f2937')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('TOPPADDING', (0, 0), (-1, 0), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f9fafb'), colors.white]),
        ]))
        elements.append(bd_table)
        elements.append(Spacer(1, 0.4*cm))

    if id_sede and breakdown_doctors:
        elements.append(Paragraph(f"Desglose por Doctor - {sede_obj.nombre_sede}", styles['Heading2']))
        elements.append(Spacer(1, 0.2*cm))
        doc_data = [['Doctor', 'Citas', 'Atend.', 'Cancel.', 'Honorarios', 'Pagado', 'Pendiente']]
        for item in breakdown_doctors:
            doc_data.append([
                item['nombre'],
                str(item['total_citas']),
                str(item['atendidas']),
                str(item['canceladas']),
                f"${float(item['honorarios']):,.2f}",
                f"${float(item['pagado']):,.2f}",
                f"${float(item['pendiente']):,.2f}",
            ])
        doc_table = Table(doc_data, colWidths=[5.5*cm, 1.5*cm, 1.5*cm, 1.5*cm, 2.5*cm, 2.5*cm, 2.5*cm])
        doc_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f2937')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('TOPPADDING', (0, 0), (-1, 0), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f9fafb'), colors.white]),
        ]))
        elements.append(doc_table)

    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


@_superadmin_required
def reportes_superadmin_pdf(request):
    """Genera y descarga el PDF de reportes con los mismos filtros que la vista HTML."""
    from datetime import datetime
    from citas.reportes import ReportesService

    hoy = timezone.now().date()
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    id_sede = request.GET.get('id_sede')

    if not fecha_inicio:
        fecha_inicio = hoy.replace(day=1)
    else:
        fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()

    if not fecha_fin:
        fecha_fin = hoy
    else:
        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()

    # Obtener sedes del centro médico del superadmin
    user_sa, sa = _get_superadmin_user(request)
    centro = _get_centro(sa)
    if centro:
        sedes = Sede.objects.filter(id_cm=centro, status=True).order_by('nombre_sede')
    else:
        sedes = Sede.objects.none()
    mis_sede_ids = list(sedes.values_list('id_sede', flat=True))

    if id_sede:
        id_sede = int(id_sede)
        if id_sede not in mis_sede_ids:
            id_sede = None

    # Metricas
    datos_atencion = ReportesService.reporte_diario_atencion(fecha_inicio, fecha_fin, id_sede)
    datos_balance = ReportesService.reporte_balance(fecha_inicio, fecha_fin, id_sede)
    datos_honorarios = ReportesService.reporte_pagos_medicos(fecha_inicio, fecha_fin, id_sede)
    datos_pacientes = ReportesService.reporte_pacientes_nuevos(fecha_inicio, fecha_fin, id_sede)
    datos_doctores = ReportesService.reporte_doctores(id_sede)

    sede_obj = None
    if id_sede:
        sede_obj = get_object_or_404(Sede, pk=id_sede)

    # Desglose por sede
    breakdown = []
    if not id_sede:
        for sede in sedes:
            atencion_sede = ReportesService.reporte_diario_atencion(fecha_inicio, fecha_fin, sede.id_sede)
            balance_sede = ReportesService.reporte_balance(fecha_inicio, fecha_fin, sede.id_sede)
            honorarios_sede = ReportesService.reporte_pagos_medicos(fecha_inicio, fecha_fin, sede.id_sede)
            pacientes_sede = ReportesService.reporte_pacientes_nuevos(fecha_inicio, fecha_fin, sede.id_sede)
            doctores_sede = ReportesService.reporte_doctores(sede.id_sede)
            breakdown.append({
                'sede': sede,
                'total_citas': atencion_sede['total_citas'],
                'atendidas': atencion_sede['atendidas'],
                'canceladas': atencion_sede['canceladas'],
                'facturacion': balance_sede['facturacion']['total'],
                'honorarios': honorarios_sede['totales']['total_honorarios'],
                'pacientes_nuevos': pacientes_sede['total'],
                'doctores': doctores_sede['total'],
            })

    # Desglose por doctor
    breakdown_doctors = []
    if id_sede:
        from citas.models import Cita
        doctores = ReportesService.obtener_medicos(id_sede)
        for doc in doctores:
            citas_doc = Cita.objects.filter(
                id_doctor_id=doc['id_doctor'],
                fecha_consulta__date__gte=fecha_inicio,
                fecha_consulta__date__lte=fecha_fin,
                status=True
            )
            atendidas_doc = citas_doc.filter(estado=Cita.ESTADO_ATENDIDA).count()
            canceladas_doc = citas_doc.filter(estado=Cita.ESTADO_CANCELADA).count()
            honor_doc = ReportesService.reporte_pagos_medicos(fecha_inicio, fecha_fin, id_sede, doc['id_doctor'])
            breakdown_doctors.append({
                'nombre': f"Dr. {doc['nombre_1'] or ''} {doc['apellido_1'] or ''}".strip(),
                'total_citas': citas_doc.count(),
                'atendidas': atendidas_doc,
                'canceladas': canceladas_doc,
                'honorarios': honor_doc['totales']['total_honorarios'],
                'pagado': honor_doc['totales']['total_pagado'],
                'pendiente': honor_doc['totales']['total_pendiente'],
            })

    pdf_bytes = _generar_pdf_reportes(
        fecha_inicio, fecha_fin, id_sede, sede_obj,
        datos_atencion, datos_balance, datos_honorarios,
        datos_pacientes, datos_doctores,
        breakdown, breakdown_doctors
    )

    filename = f"reporte_{fecha_inicio.strftime('%Y%m%d')}_{fecha_fin.strftime('%Y%m%d')}"
    if sede_obj:
        filename += f"_{sede_obj.nombre_sede.replace(' ', '_')}"
    filename += ".pdf"

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.write(pdf_bytes)
    return response


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

    # Excluir siempre eventos del rol root
    queryset = AuditLog.objects.exclude(role='root')

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

    # Paginacion
    total_registros = queryset.count()
    paginator = Paginator(queryset.order_by('-timestamp'), 50)
    page_number = request.GET.get('page', 1)
    try:
        page_obj = paginator.page(page_number)
    except Exception:
        page_obj = paginator.page(1)

    # Roles disponibles (todos menos root) para que siempre aparezcan en el filtro
    roles_unicos = ['gerente', 'medico', 'paciente', 'recepcionista', 'superadmin']
    acciones_unicas = AuditLog.objects.exclude(role='root').values_list('action', flat=True).distinct().order_by('action')

    context = {
        'page_obj': page_obj,
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
