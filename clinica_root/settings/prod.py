from .base import *
import os

DEBUG = False
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost").split(",")
CSRF_TRUSTED_ORIGINS = [
    o for o in os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",") if o
]

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
CORS_ALLOW_ALL_ORIGINS = False

# PENDIENTE para prod real (security.W004):
# Activar HSTS solo cuando el host tenga HTTPS configurado y certificado válido.
# Ejemplo: SECURE_HSTS_SECONDS = 31536000
#          SECURE_HSTS_INCLUDE_SUBDOMAINS = True
#          SECURE_HSTS_PRELOAD = True
#          SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
#
# PENDIENTE para prod real (security.W009):
# Regenerar SECRET_KEY con: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
# y asignar el valor generado en la variable de entorno SECRET_KEY del servidor.
