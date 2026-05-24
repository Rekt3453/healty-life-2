from .authentication import CustomAuthBackend
from .models import (
    UserPaciente, UserDoctor, UserRecepcionista, UserAdmin,
    PacienteDatosPersonales, Doctor, Recepcionista, Administrador
)


def get_user_model_hint(request=None):
    """
    Devuelve el hint de modelo guardado en el request por UserModelHintMiddleware.
    Acepta request=None para compatibilidad con llamadas antiguas (devuelve None).
    """
    if request is None:
        return None
    return getattr(request, '_user_model_hint', None)


class UserModelHintMiddleware:
    """
    Debe ir ANTES de AuthenticationMiddleware en MIDDLEWARE.
    Lee _hl_user_model de la sesión y lo guarda en request._user_model_hint
    para que CustomAuthBackend.get_user() sepa en qué tabla buscar.
    Usa el request (sin thread-local) para evitar race conditions en producción.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        hint = None
        try:
            if hasattr(request, 'session'):
                hint = request.session.get('_hl_user_model')
        except Exception:
            pass
        request._user_model_hint = hint
        return self.get_response(request)

def get_current_sede(request=None):
    """
    Devuelve el id de sede del request actual.
    El valor lo establece SedeMiddleware en request.sede_id_actual.
    """
    if request is None:
        return None
    return getattr(request, 'sede_id_actual', None)

def set_current_sede(sede_id, request=None):
    """No-op conservado por compatibilidad. SedeMiddleware escribe directamente en request."""
    pass

def get_current_sede_object(request=None):
    """
    Devuelve el objeto Sede del request actual.
    El valor lo establece SedeMiddleware en request.sede_actual.
    """
    if request is None:
        return None
    return getattr(request, 'sede_actual', None)

def set_current_sede_object(sede, request=None):
    """No-op conservado por compatibilidad. SedeMiddleware escribe directamente en request."""
    pass

class SedeMiddleware:
    """
    Middleware para establecer automáticamente la sede del usuario autenticado
    usando los nuevos modelos de Supabase
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.auth_backend = CustomAuthBackend()
    
    def __call__(self, request):
        request.sede_actual    = None
        request.sede_id_actual = None

        if request.user.is_authenticated:
            try:
                sede = None
                user_rol = self.auth_backend.get_rol(request.user)

                if user_rol in ('paciente', 'medico', 'recepcionista', 'gerente'):
                    if hasattr(request.user, 'id_sede'):
                        sede = request.user.id_sede
                    else:
                        datos = self.auth_backend.get_datos_personales(request.user)
                        if datos and hasattr(datos, 'id_sede'):
                            sede = datos.id_sede

                if sede:
                    request.sede_actual    = sede
                    request.sede_id_actual = getattr(sede, 'id_sede', None) or getattr(sede, 'id', None)

            except Exception as e:
                print(f'Error en SedeMiddleware: {e}')

        return self.get_response(request)
