"""
Generación y verificación de tokens seguros.
Usa secrets.token_urlsafe() + caché con TTL de 24 horas.
Tokens de un solo uso.
"""
import secrets
from django.core.cache import cache

_TOKEN_TTL = 86400  # 24 horas


def generar_token_seguro(user_pk, proposito):
    """
    Genera un token criptográficamente seguro.
    Lo guarda en caché con tiempo de vida de 15 minutos.
    """
    token = secrets.token_urlsafe(32)
    cache_key = f"token:{proposito}:{user_pk}"
    cache.set(cache_key, token, timeout=_TOKEN_TTL)
    return token


def verificar_token_seguro(user_pk, proposito, token_recibido, invalidar=True):
    """
    Verifica el token. Retorna True si coincide y no ha expirado.
    Por defecto lo invalida tras el primer uso exitoso (un solo uso).
    Usa invalidar=False para verificar sin consumir el token.
    """
    cache_key = f"token:{proposito}:{user_pk}"
    token_guardado = cache.get(cache_key)

    if not token_guardado:
        return False  # expirado o ya usado

    if not secrets.compare_digest(token_guardado, token_recibido):
        return False

    if invalidar:
        cache.delete(cache_key)
    return True
