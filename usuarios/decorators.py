from django.shortcuts import redirect
from django.contrib import messages
from .authentication import CustomAuthBackend

def rol_requerido(rol):
    """
    Decorador para requerir un rol específico usando los nuevos modelos de Supabase
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
            
            if user_rol == rol_mapping.get(rol, rol):
                return view_func(request, *args, **kwargs)
            
            messages.error(request, f"No tienes permiso para acceder a esta página. Se requiere rol: {rol}")
            
            # Redirigir al login apropiado según el rol requerido
            login_redirects = {
                'paciente': 'login_paciente',
                'medico': 'login_medico',
                'recepcionista': 'login_recepcionista',
                'gerente': 'login_gerente',
                'administrador': 'login_gerente',
            }
            
            return redirect(login_redirects.get(rol, 'home'))
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
