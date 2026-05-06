from django.shortcuts import redirect
from django.contrib import messages

def rol_requerido(rol):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if request.user.userprofile.rol == rol:
                return view_func(request, *args, **kwargs)
            messages.error(request, "No tienes permiso para acceder a esta página")
            return redirect('login_paciente')
        return wrapper
    return decorator
