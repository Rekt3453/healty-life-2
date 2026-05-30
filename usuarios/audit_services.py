# ============================================================
# Servicio de Auditoría — Healthy Life
# ============================================================
import json
from django.utils import timezone
from .models import AuditLog


def get_client_ip(request):
    """Obtiene la IP real del cliente desde los headers."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '')
    return ip


def registrar_evento(
    user=None,
    role=None,
    action=None,
    model_affected=None,
    object_id=None,
    details=None,
    request=None,
):
    """
    Registra un evento en la tabla audit_log.

    Parámetros:
      user        — instancia de usuario o None (sistema)
      role        — str: 'root', 'superadmin', 'gerente', 'medico', 'recepcionista', 'paciente'
      action      — str: 'LOGIN', 'LOGOUT', 'CREATE', 'UPDATE', 'DELETE', 'STATUS_CHANGE', 'PAYMENT', etc.
      model_affected — str: nombre del modelo afectado (ej. 'Cita', 'PacienteDatosPersonales')
      object_id   — int: ID del registro afectado
      details     — dict o str: datos adicionales del evento
      request     — HttpRequest: para extraer IP y session_id
    """
    if not action or not role:
        raise ValueError("Los parámetros 'action' y 'role' son obligatorios.")

    id_user = None
    session_id = None
    ip_address = None

    if user is not None:
        # Intentar obtener el ID genérico del usuario
        id_user = getattr(user, 'pk', None) or getattr(user, 'id', None)

    if request is not None:
        ip_address = get_client_ip(request)
        session_id = request.session.session_key or request.session.get('_session_key')

    # Serializar details si es dict
    if isinstance(details, dict):
        details = json.dumps(details, default=str)
    elif details is not None and not isinstance(details, str):
        details = str(details)

    AuditLog.objects.create(
        id_user=id_user,
        role=role,
        action=action,
        model_affected=model_affected,
        object_id=object_id,
        details=details,
        ip_address=ip_address,
        session_id=session_id,
    )
