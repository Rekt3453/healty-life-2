from django.shortcuts import redirect
from django.contrib import messages
from .authentication import CustomAuthBackend

def rol_requerido(*roles):
    """
    Decorador para requerir uno o más roles específicos usando los modelos de Supabase.
    Uso: @rol_requerido('medico')
         @rol_requerido('recepcionista', 'gerente')
    """
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, "Debes iniciar sesión para acceder a esta página")
                return redirect('home')
            
            # Usar el backend de autenticación para verificar el rol
            auth_backend = CustomAuthBackend()
            user_rol = auth_backend.get_rol(request.user)
            
            # Mapeo de roles para compatibilidad
            rol_mapping = {
                'paciente': 'paciente',
                'medico': 'medico',
                'recepcionista': 'recepcionista',
                'gerente': 'gerente',
                'administrador': 'gerente',
            }
            
            # Verificar si el rol del usuario está en cualquiera de los roles requeridos
            mapped_roles = [rol_mapping.get(r, r) for r in roles]
            if user_rol in mapped_roles:
                return view_func(request, *args, **kwargs)
            
            messages.error(request, f"No tienes permiso para acceder a esta sección.")

            # Si ya está autenticado, redirigir a SU propio dashboard
            dashboard_redirects = {
                'paciente': 'dashboard_paciente',
                'medico': 'dashboard_medico',
                'recepcionista': 'dashboard_recepcionista',
                'gerente': 'dashboard_gerente',
                'administrador': 'dashboard_gerente',
            }
            if user_rol and user_rol in dashboard_redirects:
                return redirect(dashboard_redirects[user_rol])
            return redirect('home')
        return wrapper
    return decorator

def roles_requeridos(roles):
    """
    Decorador para requerir uno de varios roles específicos
    """
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, "Debes iniciar sesión para acceder a esta página")
                return redirect('home')
            
            # Usar el backend de autenticación para verificar el rol
            auth_backend = CustomAuthBackend()
            user_rol = auth_backend.get_rol(request.user)
            
            # Mapeo de roles para compatibilidad
            rol_mapping = {
                'paciente': 'paciente',
                'medico': 'medico',
                'recepcionista': 'recepcionista',
                'gerente': 'gerente',
                'administrador': 'gerente',  # Mapear administrador a gerente
            }
            
            # Verificar si el rol del usuario está en la lista de roles permitidos
            mapped_roles = [rol_mapping.get(r, r) for r in roles]
            if user_rol in mapped_roles:
                return view_func(request, *args, **kwargs)
            
            messages.error(request, f"No tienes permiso para acceder a esta página. Se requiere uno de estos roles: {', '.join(roles)}")
            return redirect('home')
        return wrapper
    return decorator

def sede_requerida(view_func):
    """
    Decorador para requerir que el usuario tenga una sede asignada
    """
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Debes iniciar sesión para acceder a esta página")
            return redirect('home')
        
        # Verificar si el usuario tiene sede asignada
        from .middleware import get_current_sede
        current_sede = get_current_sede()
        
        if not current_sede:
            messages.error(request, "No tienes una sede asignada. Contacta al administrador.")
            return redirect('home')
        
        return view_func(request, *args, **kwargs)
    return wrapper
