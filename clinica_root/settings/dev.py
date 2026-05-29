from .base import *

DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver"]
CORS_ALLOW_ALL_ORIGINS = True

# En desarrollo no hay HTTPS, DEBUG=True y se usa SECRET_KEY de fallback.
# Estos checks son válidos en producción (prod.py los cumple); aquí se silencian.
SILENCED_SYSTEM_CHECKS = [
    "security.W004",   # HSTS — no aplica sin HTTPS en dev
    "security.W008",   # SECURE_SSL_REDIRECT — no aplica en dev
    "security.W009",   # SECRET_KEY débil — intencional en dev, cambiar en prod
    "security.W012",   # SESSION_COOKIE_SECURE — no aplica sin HTTPS en dev
    "security.W016",   # CSRF_COOKIE_SECURE — no aplica sin HTTPS en dev
    "security.W018",   # DEBUG=True — intencional en dev
]
