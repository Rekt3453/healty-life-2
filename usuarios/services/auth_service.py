"""
Servicio de autenticación.
Encapsula la lógica de login por rol y la resolución de usuario desde sesión,
eliminando el patrón repetido en los dashboards de gerente y recepcionista.
"""
from django.contrib import messages
from django.shortcuts import redirect


def resolve_session_user(request, Model, pk_field, login_url):
    """
    Obtiene y valida el usuario actual desde la sesión Django.

    Args:
        request:    HttpRequest actual.
        Model:      Clase del modelo (UserAdmin, UserRecepcionista, …).
        pk_field:   Nombre del campo PK del modelo (ej. 'id_user_admin').
        login_url:  URL de login a la que redirigir si falla.

    Returns:
        (user, None)           cuando el usuario es válido.
        (None, HttpResponse)   cuando hay que redirigir por error.
    """
    user_id = request.session.get('_auth_user_id')
    if not user_id:
        messages.error(request, 'Debes iniciar sesión primero')
        return None, redirect(login_url)

    user = Model.objects.filter(**{pk_field: user_id}).first()
    if not user:
        messages.error(request, 'Usuario no encontrado')
        return None, redirect(login_url)

    return user, None


def check_role(request, user, required_rol, home_url='home'):
    """
    Verifica que el usuario tenga el rol requerido.

    Returns:
        (True, None)            cuando el rol es correcto.
        (False, HttpResponse)   cuando no coincide.
    """
    from usuarios.authentication import CustomAuthBackend
    backend = CustomAuthBackend()
    actual_rol = backend.get_rol(user)
    if actual_rol != required_rol:
        messages.error(request, f'Acceso denegado. Tu rol es: {actual_rol}')
        return False, redirect(home_url)
    return True, None


def resolve_and_check(request, Model, pk_field, required_rol, login_url):
    """
    Combina resolve_session_user + check_role en una sola llamada.

    Returns:
        (user, backend, None)            cuando todo es válido.
        (None, None, HttpResponse)       cuando hay que redirigir.
    """
    from usuarios.authentication import CustomAuthBackend
    user, err = resolve_session_user(request, Model, pk_field, login_url)
    if err:
        return None, None, err

    backend = CustomAuthBackend()
    ok, err = check_role(request, user, required_rol)
    if not ok:
        return None, None, err

    return user, backend, None
