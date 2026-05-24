import logging
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from django.core.cache import cache
from .models import UserPaciente, UserDoctor, UserRecepcionista, UserAdmin

logger = logging.getLogger('usuarios.auth')

# ── Rate limiting ─────────────────────────────────────────────────────────────
_RL_MAX     = 5   # intentos máximos
_RL_WINDOW  = 60  # ventana en segundos

def _rl_key(username):
    """Clave de caché para contar intentos de login de un username."""
    return f'login_attempts:{username}'

def is_rate_limited(username):
    """Devuelve True si el username superó el límite de intentos."""
    return cache.get(_rl_key(username), 0) >= _RL_MAX

def _record_failed(username):
    """Incrementa el contador de intentos fallidos en la ventana definida."""
    key = _rl_key(username)
    cache.set(key, cache.get(key, 0) + 1, timeout=_RL_WINDOW)

def _reset_attempts(username):
    """Elimina el contador de intentos (login exitoso)."""
    cache.delete(_rl_key(username))

class CustomAuthBackend(BaseBackend):
    """
    Backend de autenticación personalizado para manejar múltiples tipos de
    usuarios (paciente, médico, recepcionista, gerente) almacenados en tablas
    separadas de Supabase.

    Mejoras incluidas:
    - Rate limiting: máximo 5 intentos por username en 60 segundos.
    - Logging: registra intentos fallidos y exitosos con IP y hora.
    - Validación de status activo antes de aceptar credenciales.
    """

    def _get_ip(self, request):
        """Extrae la IP del cliente desde el request, considerando proxies."""
        x_forwarded = request and request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded:
            return x_forwarded.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown') if request else 'unknown'

    def _try_auth(self, Model, username, password):
        """
        Intenta autenticar username/password contra un Model concreto.
        Devuelve la instancia si las credenciales son correctas y el usuario
        está activo; None en caso contrario.
        """
        try:
            user = Model.objects.get(username=username)
        except Model.DoesNotExist:
            return None
        if hasattr(user, 'status') and not user.status:
            return None
        if user.check_password(password):
            return user
        return None

    def authenticate(self, request=None, username=None, password=None, rol=None, **kwargs):
        """
        Autentica al usuario según el rol especificado.

        Flujo:
        1. Valida que username y password no estén vacíos.
        2. Verifica el rate limit; bloquea si se superaron los intentos.
        3. Busca al usuario en la(s) tabla(s) correspondiente(s).
        4. Registra el resultado (éxito o fallo) en el log y actualiza el contador.
        """
        if not username or not password:
            return None

        ip = self._get_ip(request)

        # ── Rate limiting ─────────────────────────────────────────────────────
        if is_rate_limited(username):
            logger.warning(
                'LOGIN BLOQUEADO | usuario=%s | ip=%s | motivo=rate_limit',
                username, ip
            )
            return None

        # ── Mapa rol → modelo ─────────────────────────────────────────────────
        ROL_MAP = {
            'paciente':      [UserPaciente],
            'medico':        [UserDoctor],
            'recepcionista': [UserRecepcionista],
            'gerente':       [UserAdmin],
            'administrador': [UserAdmin],
        }
        models_to_try = ROL_MAP.get(rol) if rol else [
            UserPaciente, UserDoctor, UserRecepcionista, UserAdmin
        ]

        for Model in models_to_try:
            user = self._try_auth(Model, username, password)
            if user:
                _reset_attempts(username)
                logger.info(
                    'LOGIN OK | usuario=%s | rol=%s | ip=%s',
                    username, type(user).__name__, ip
                )
                return user

        # ── Fallo de autenticación ────────────────────────────────────────────
        _record_failed(username)
        remaining = max(0, _RL_MAX - cache.get(_rl_key(username), 0))
        logger.warning(
            'LOGIN FALLIDO | usuario=%s | ip=%s | intentos_restantes=%d',
            username, ip, remaining
        )
        return None
    
    def get_user(self, user_id):
        """
        Obtiene el usuario por ID buscando en todas las tablas de usuario.
        El hint de thread-local fue eliminado; se itera en orden fijo.
        El orden es suficiente porque cada tabla usa PKs independientes.
        """
        for Model in [UserPaciente, UserDoctor, UserRecepcionista, UserAdmin]:
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
        Obtiene los datos personales del usuario.
        Fuerza la evaluación del SimpleLazyObject usando user.pk.
        """
        try:
            pk = user.pk  # Fuerza evaluación del SimpleLazyObject
        except Exception:
            return None

        if isinstance(user, UserPaciente):
            from .models import PacienteDatosPersonales
            return PacienteDatosPersonales.objects.filter(id_user_paciente_id=pk).first()

        elif isinstance(user, UserDoctor):
            from .models import Doctor
            return Doctor.objects.filter(id_user_doctor_id=pk).first()

        elif isinstance(user, UserRecepcionista):
            from .models import Recepcionista
            return Recepcionista.objects.filter(id_user_recepcionista_id=pk).first()

        elif isinstance(user, UserAdmin):
            from .models import Administrador
            return Administrador.objects.filter(id_user_admin_id=pk).first()

        return None
