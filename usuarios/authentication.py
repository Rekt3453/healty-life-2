from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from .models import UserPaciente, UserDoctor, UserRecepcionista, UserAdmin

class CustomAuthBackend(BaseBackend):
    """
    Backend de autenticación personalizado para manejar múltiples tipos de usuarios
    """
    
    def authenticate(self, request=None, username=None, password=None, rol=None, **kwargs):
        """
        Autentica al usuario según el rol especificado
        """
        if not username or not password:
            return None
            
        # Si no se especifica rol, intentar en todas las tablas
        if rol is None:
            # Intentar autenticar como paciente
            try:
                user_paciente = UserPaciente.objects.get(username=username)
                if user_paciente.check_password(password):
                    return user_paciente
            except UserPaciente.DoesNotExist:
                pass
            
            # Intentar autenticar como doctor
            try:
                user_doctor = UserDoctor.objects.get(username=username)
                if user_doctor.check_password(password):
                    return user_doctor
            except UserDoctor.DoesNotExist:
                pass
            
            # Intentar autenticar como recepcionista
            try:
                user_recepcionista = UserRecepcionista.objects.get(username=username)
                if user_recepcionista.check_password(password):
                    return user_recepcionista
            except UserRecepcionista.DoesNotExist:
                pass
            
            # Intentar autenticar como administrador
            try:
                user_admin = UserAdmin.objects.get(username=username)
                if user_admin.check_password(password):
                    return user_admin
            except UserAdmin.DoesNotExist:
                pass
                
        else:
            # Autenticar según el rol específico
            if rol == 'paciente':
                try:
                    user_paciente = UserPaciente.objects.get(username=username)
                    if user_paciente.check_password(password):
                        return user_paciente
                except UserPaciente.DoesNotExist:
                    pass
                    
            elif rol == 'medico':
                try:
                    user_doctor = UserDoctor.objects.get(username=username)
                    if user_doctor.check_password(password):
                        return user_doctor
                except UserDoctor.DoesNotExist:
                    pass
                    
            elif rol == 'recepcionista':
                try:
                    user_recepcionista = UserRecepcionista.objects.get(username=username)
                    if user_recepcionista.check_password(password):
                        return user_recepcionista
                except UserRecepcionista.DoesNotExist:
                    pass
                    
            elif rol == 'gerente' or rol == 'administrador':
                try:
                    user_admin = UserAdmin.objects.get(username=username)
                    if user_admin.check_password(password):
                        return user_admin
                except UserAdmin.DoesNotExist:
                    pass
        
        return None
    
    def get_user(self, user_id):
        """
        Obtiene el usuario por ID priorizando la tabla correcta según el
        hint guardado en sesión por UserModelHintMiddleware.
        """
        try:
            from .middleware import get_user_model_hint
            hint = get_user_model_hint()
        except Exception:
            hint = None

        _MODEL_MAP = {
            'UserPaciente':      UserPaciente,
            'UserDoctor':        UserDoctor,
            'UserRecepcionista': UserRecepcionista,
            'UserAdmin':         UserAdmin,
        }
        default_order = [UserPaciente, UserDoctor, UserRecepcionista, UserAdmin]

        if hint and hint in _MODEL_MAP:
            priority = _MODEL_MAP[hint]
            order = [priority] + [m for m in default_order if m is not priority]
        else:
            order = default_order

        for Model in order:
            try:
                return Model.objects.get(pk=user_id)
            except (Model.DoesNotExist, ValueError, TypeError):
                pass

        return None
    
    def get_rol(self, user):
        """
        Determina el rol del usuario
        """
        if isinstance(user, UserPaciente):
            return 'paciente'
        elif isinstance(user, UserDoctor):
            return 'medico'
        elif isinstance(user, UserRecepcionista):
            return 'recepcionista'
        elif isinstance(user, UserAdmin):
            return 'gerente'
        return None
    
    def get_datos_personales(self, user):
        """
        Obtiene los datos personales del usuario
        """
        if isinstance(user, UserPaciente):
            try:
                from .models import PacienteDatosPersonales
                return PacienteDatosPersonales.objects.get(id_user_paciente=user)
            except PacienteDatosPersonales.DoesNotExist:
                return None
                
        elif isinstance(user, UserDoctor):
            try:
                from .models import Doctor
                return Doctor.objects.get(id_user_doctor=user)
            except Doctor.DoesNotExist:
                return None
                
        elif isinstance(user, UserRecepcionista):
            try:
                from .models import Recepcionista
                return Recepcionista.objects.get(id_user_recepcionista=user)
            except Recepcionista.DoesNotExist:
                return None
                
        elif isinstance(user, UserAdmin):
            try:
                from .models import Administrador
                return Administrador.objects.get(id_user_admin=user)
            except Administrador.DoesNotExist:
                return None
                
        return None
