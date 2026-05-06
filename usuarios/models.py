from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    ROLES = (
        ('paciente', 'Paciente'),
        ('medico', 'Médico'),
        ('recepcionista', 'Recepcionista'),
        ('gerente', 'Gerente'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Usuario")
    rol = models.CharField(max_length=20, choices=ROLES, verbose_name="Rol")
    cedula = models.CharField(max_length=20, unique=True, verbose_name="Cédula")
    telefono = models.CharField(max_length=20, verbose_name="Teléfono")
    fecha_nacimiento = models.DateField(verbose_name="Fecha de Nacimiento", null=True, blank=True)
    direccion = models.TextField(verbose_name="Dirección")
    
    class Meta:
        verbose_name = "Perfil de Usuario"
        verbose_name_plural = "Perfiles de Usuarios"
    
    def __str__(self):
        return f"{self.user.username} - {self.get_rol_display()}"
