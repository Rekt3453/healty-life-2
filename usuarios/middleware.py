from threading import local

_thread_locals = local()

def get_current_sede():
    """
    Obtener la sede actual del contexto del hilo
    """
    return getattr(_thread_locals, 'sede_id', None)

def set_current_sede(sede_id):
    """
    Establecer la sede actual en el contexto del hilo
    """
    _thread_locals.sede_id = sede_id

class SedeMiddleware:
    """
    Middleware para establecer automáticamente la sede del usuario autenticado
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Limpiar el contexto anterior
        set_current_sede(None)
        
        # Si el usuario está autenticado, establecer su sede
        if request.user.is_authenticated:
            try:
                # Obtener el perfil del usuario
                user_profile = getattr(request.user, 'userprofile', None)
                if user_profile and user_profile.sede:
                    set_current_sede(user_profile.sede.id)
            except:
                pass
        
        response = self.get_response(request)
        
        # Limpiar el contexto después de la respuesta
        set_current_sede(None)
        
        return response
