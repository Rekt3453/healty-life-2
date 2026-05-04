from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse

class Sede(models.Model):
    nombre = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, help_text="URL amigable para la sede")
    direccion = models.TextField()
    telefono = models.CharField(max_length=20)
    email = models.EmailField()
    activa = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre
    
    def get_absolute_url(self):
        return f'/{self.slug}/'

class UserProfile(models.Model):
    ROLES_CHOICES = [
        ('paciente', 'Paciente'),
        ('paciente_especial', 'Paciente Especial'),
        ('medico', 'Médico'),
        ('recepcionista', 'Recepcionista'),
        ('gerente', 'Gerente'),
        ('gerente_general', 'Gerente General'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile')
    rol = models.CharField(max_length=20, choices=ROLES_CHOICES)
    sede = models.ForeignKey(Sede, on_delete=models.SET_NULL, null=True, blank=True, 
                            help_text="Sede asignada (no aplica para Gerente General)")
    telefono = models.CharField(max_length=20, blank=True)
    cedula = models.CharField(max_length=15, unique=True, help_text="Cédula de identidad")
    fecha_nacimiento = models.DateField(null=True, blank=True)
    direccion = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['user__username']
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.get_rol_display()}"
    
    @property
    def nombre_completo(self):
        return self.user.get_full_name() or self.user.username
    
    def puede_registrar_pacientes(self):
        return self.rol in ['recepcionista', 'gerente', 'gerente_general']
    
    def puede_registrar_medicos(self):
        return self.rol in ['gerente', 'gerente_general']
    
    def puede_registrar_recepcionistas(self):
        return self.rol in ['gerente', 'gerente_general']
    
    def puede_registrar_gerentes(self):
        return self.rol == 'gerente_general'
    
    def puede_ver_calendario_general(self):
        return self.rol in ['medico', 'recepcionista', 'gerente', 'gerente_general']
    
    def puede_ver_reportes(self):
        return self.rol in ['gerente', 'gerente_general']

class Especialidad(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    activa = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre

class MedicoProfile(models.Model):
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE)
    especialidad = models.ForeignKey(Especialidad, on_delete=models.PROTECT)
    numero_matricula = models.CharField(max_length=50, unique=True, help_text="Matricula profesional")
    experiencia_anios = models.PositiveIntegerField(default=0)
    biografia = models.TextField(blank=True)
    consulta_precio_base = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    def __str__(self):
        return f"Dr. {self.user_profile.nombre_completo} - {self.especialidad.nombre}"

class PacienteProfile(models.Model):
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE)
    historia_clinica_numero = models.CharField(max_length=50, unique=True, blank=True, null=True)
    alergias = models.TextField(blank=True, help_text="Alergias conocidas")
    medicamentos_actuales = models.TextField(blank=True, help_text="Medicamentos que toma actualmente")
    condiciones_cronicas = models.TextField(blank=True, help_text="Condiciones crónicas")
    contacto_emergencia_nombre = models.CharField(max_length=200, blank=True)
    contacto_emergencia_telefono = models.CharField(max_length=20, blank=True)
    contacto_emergencia_parentesco = models.CharField(max_length=50, blank=True)
    
    def __str__(self):
        return f"Paciente: {self.user_profile.nombre_completo}"
    
    def save(self, *args, **kwargs):
        if not self.historia_clinica_numero:
            import uuid
            self.historia_clinica_numero = f"HC-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)
