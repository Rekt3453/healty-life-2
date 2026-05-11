from threading import local
from .authentication import CustomAuthBackend
from .models import (
    UserPaciente, UserDoctor, UserRecepcionista, UserAdmin,
    PacienteDatosPersonales, Doctor, Recepcionista, Administrador
)

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

def get_current_sede_object():
    """
    Obtener el objeto Sede actual del contexto del hilo
    """
    return getattr(_thread_locals, 'sede_object', None)

def set_current_sede_object(sede):
    """
    Establecer el objeto Sede actual en el contexto del hilo
    """
    _thread_locals.sede_object = sede

class SedeMiddleware:
    """
    Middleware para establecer automáticamente la sede del usuario autenticado
    usando los nuevos modelos de Supabase
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.auth_backend = CustomAuthBackend()
    
    def __call__(self, request):
        # Limpiar el contexto anterior
        set_current_sede(None)
        set_current_sede_object(None)
        
        # Si el usuario está autenticado, establecer su sede
        if request.user.is_authenticated:
            try:
                # Determinar el tipo de usuario y obtener su sede
                user_rol = self.auth_backend.get_rol(request.user)
                sede = None
                
                if user_rol == 'paciente':
                    # Obtener sede desde UserPaciente
                    if hasattr(request.user, 'id_sede'):
                        sede = request.user.id_sede
                    else:
                        # Intentar desde datos personales
                        datos_paciente = self.auth_backend.get_datos_personales(request.user)
                        if datos_paciente and hasattr(datos_paciente, 'id_sede'):
                            sede = datos_paciente.id_sede
                            
                elif user_rol == 'medico':
                    # Obtener sede desde UserDoctor
                    if hasattr(request.user, 'id_sede'):
                        sede = request.user.id_sede
                    else:
                        # Intentar desde datos personales
                        datos_medico = self.auth_backend.get_datos_personales(request.user)
                        if datos_medico and hasattr(datos_medico, 'id_sede'):
                            sede = datos_medico.id_sede
                            
                elif user_rol == 'recepcionista':
                    # Obtener sede desde UserRecepcionista
                    if hasattr(request.user, 'id_sede'):
                        sede = request.user.id_sede
                    else:
                        # Intentar desde datos personales
                        datos_recepcionista = self.auth_backend.get_datos_personales(request.user)
                        if datos_recepcionista and hasattr(datos_recepcionista, 'id_sede'):
                            sede = datos_recepcionista.id_sede
                            
                elif user_rol == 'gerente':
                    # Obtener sede desde UserAdmin
                    if hasattr(request.user, 'id_sede'):
                        sede = request.user.id_sede
                    else:
                        # Intentar desde datos personales
                        datos_admin = self.auth_backend.get_datos_personales(request.user)
                        if datos_admin and hasattr(datos_admin, 'id_sede'):
                            sede = datos_admin.id_sede
                
                # Establecer la sede en el contexto
                if sede:
                    set_current_sede(sede.id_sede if hasattr(sede, 'id_sede') else sede.id)
                    set_current_sede_object(sede)
                    
                    # Agregar la sede al request para fácil acceso
                    request.sede_actual = sede
                    
            except Exception as e:
                # En caso de error, no interrumpir el flujo
                print(f"Error en SedeMiddleware: {e}")
                pass
        
        response = self.get_response(request)
        
        # Limpiar el contexto después de la respuesta
        set_current_sede(None)
        set_current_sede_object(None)
        
        return response
