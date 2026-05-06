# Temporalmente comentado para evitar conflictos durante el registro
# from django.db.models.signals import post_save
# from django.contrib.auth.models import User
# from django.dispatch import receiver
# from .models import UserProfile

# @receiver(post_save, sender=User)
# def create_user_profile(sender, instance, created, **kwargs):
#     if created:
#         # Usar get_or_create para evitar duplicados
#         UserProfile.objects.get_or_create(
#             user=instance,
#             defaults={
#                 'rol': 'paciente',  # Rol por defecto
#                 'cedula': f'temp-{instance.id}',  # Cedula temporal única
#                 'activo': True
#             }
#         )

# @receiver(post_save, sender=User)
# def save_user_profile(sender, instance, **kwargs):
#     try:
#         if hasattr(instance, 'userprofile'):
#             instance.userprofile.save()
#     except UserProfile.DoesNotExist:
#         pass  # No crear automáticamente aquí para evitar duplicados
