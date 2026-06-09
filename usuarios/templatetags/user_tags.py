from django import template
from django.contrib.auth.models import User
from django.utils.translation import gettext as _

register = template.Library()

@register.filter
def trans_str(value):
    """Traduce una cadena de texto usando gettext. Útil para traducir valores de base de datos."""
    if not value:
        return value
    return _(str(value))

@register.filter
def get_item(dictionary, key):
    """Obtiene un valor de un diccionario usando una clave variable."""
    try:
        return dictionary.get(key)
    except (AttributeError, TypeError):
        return None

@register.filter
def has_role(user, role):
    """Verifica si un usuario tiene un rol específico"""
    try:
        return user.userprofile.rol == role
    except (User.userprofile.RelatedObjectDoesNotExist, AttributeError):
        return False

@register.filter
def has_any_role(user, roles):
    """Verifica si un usuario tiene alguno de los roles especificados"""
    try:
        return user.userprofile.rol in roles.split(',')
    except (User.userprofile.RelatedObjectDoesNotExist, AttributeError):
        return False

@register.filter
def can_register_patients(user):
    """Verifica si un usuario puede registrar pacientes"""
    try:
        return user.userprofile.puede_registrar_pacientes()
    except (User.userprofile.RelatedObjectDoesNotExist, AttributeError):
        return False

@register.filter
def can_register_doctors(user):
    """Verifica si un usuario puede registrar médicos"""
    try:
        return user.userprofile.puede_registrar_medicos()
    except (User.userprofile.RelatedObjectDoesNotExist, AttributeError):
        return False

@register.filter
def can_register_receptionists(user):
    """Verifica si un usuario puede registrar recepcionistas"""
    try:
        return user.userprofile.puede_registrar_recepcionistas()
    except (User.userprofile.RelatedObjectDoesNotExist, AttributeError):
        return False

@register.filter
def can_register_managers(user):
    """Verifica si un usuario puede registrar gerentes"""
    try:
        return user.userprofile.puede_registrar_gerentes()
    except (User.userprofile.RelatedObjectDoesNotExist, AttributeError):
        return False

@register.filter
def can_view_calendar(user):
    """Verifica si un usuario puede ver calendario general"""
    try:
        return user.userprofile.puede_ver_calendario_general()
    except (User.userprofile.RelatedObjectDoesNotExist, AttributeError):
        return False

@register.filter
def can_view_reports(user):
    """Verifica si un usuario puede ver reportes"""
    try:
        return user.userprofile.puede_ver_reportes()
    except (User.userprofile.RelatedObjectDoesNotExist, AttributeError):
        return False

@register.simple_tag
def user_role(user):
    """Obtiene el rol del usuario"""
    try:
        return user.userprofile.get_rol_display()
    except (User.userprofile.RelatedObjectDoesNotExist, AttributeError):
        return 'Sin rol'

@register.simple_tag
def user_branch(user):
    """Obtiene la sede del usuario"""
    try:
        return user.userprofile.sede
    except (User.userprofile.RelatedObjectDoesNotExist, AttributeError):
        return None
