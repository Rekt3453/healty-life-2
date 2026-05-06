from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse

class Sede(models.Model):
    id_sede = models.AutoField(primary_key=True)
    id_direccion = models.BigIntegerField()
    rif_sede = models.CharField(max_length=50, blank=True, null=True)
    telefono = models.CharField(max_length=50, blank=True, null=True)
    id_CM = models.BigIntegerField(blank=True, null=True)
    Status = models.BooleanField(default=True)
    
    class Meta:
        managed = False
        db_table = 'Sede'
        ordering = ['id_sede']
    
    def __str__(self):
        return f"Sede {self.id_sede}"
    
    @property
    def nombre(self):
        return f"Sede {self.id_sede}"
    
    @property
    def activa(self):
        return self.Status

class UserProfile(models.Model):
    ROLES_CHOICES = [
        ('administrador', 'Administrador'),
        ('doctor', 'Doctor'),
        ('recepcionista', 'Recepcionista'),
        ('paciente', 'Paciente'),
    ]
    
    id_administrador = models.AutoField(primary_key=True)
    id_user_admin = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile')
    nombre_1 = models.CharField(max_length=50)
    nombre_2 = models.CharField(max_length=50, blank=True)
    apellido_1 = models.CharField(max_length=50)
    apellido_2 = models.CharField(max_length=50, blank=True)
    cedula = models.CharField(max_length=15, unique=True)
    tipo_cedula = models.CharField(max_length=10)
    fecha_nacimiento = models.DateField()
    fecha_registro = models.DateTimeField(auto_now_add=True)
    id_sede = models.ForeignKey(Sede, on_delete=models.SET_NULL, null=True, db_column='id_sede')
    sexo = models.CharField(max_length=10)
    id_direccion_admin = models.IntegerField()
    status = models.CharField(max_length=10, default='activo')
    telefono = models.CharField(max_length=20)
    
    # Campo virtual para compatibilidad con el código existente
    @property
    def rol(self):
        return 'administrador'
    
    @property
    def activo(self):
        return self.status == 'activo'
    
    @property
    def nombre_completo(self):
        nombres = f"{self.nombre_1} {self.nombre_2}".strip()
        apellidos = f"{self.apellido_1} {self.apellido_2}".strip()
        return f"{nombres} {apellidos}".strip()
    
    class Meta:
        managed = False
        db_table = 'administrador'
        ordering = ['id_administrador']
    
    def __str__(self):
        return f"{self.nombre_completo} - {self.rol}"
    
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
        managed = False
        db_table = 'usuarios_especialidad'
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre

class MedicoProfile(models.Model):
    id_doctor = models.AutoField(primary_key=True)
    nombre_1 = models.CharField(max_length=50)
    nombre_2 = models.CharField(max_length=50, blank=True)
    apellido_1 = models.CharField(max_length=50)
    apellido_2 = models.CharField(max_length=50, blank=True)
    id_especialidad_doctor = models.IntegerField()
    id_user_doctor = models.OneToOneField(User, on_delete=models.CASCADE, related_name='medicoprofile')
    id_consultorio = models.IntegerField()
    sexo = models.CharField(max_length=10)
    fecha_nacimiento = models.DateField()
    fecha_registro = models.DateTimeField(auto_now_add=True)
    cedula = models.CharField(max_length=15, unique=True)
    tipo_cedula = models.CharField(max_length=10)
    id_sede = models.ForeignKey(Sede, on_delete=models.SET_NULL, null=True, db_column='id_sede')
    status = models.CharField(max_length=10, default='activo')
    id_direccion_doctor = models.IntegerField()
    telefono = models.CharField(max_length=20)
    id_horario = models.IntegerField()
    
    @property
    def nombre_completo(self):
        nombres = f"{self.nombre_1} {self.nombre_2}".strip()
        apellidos = f"{self.apellido_1} {self.apellido_2}".strip()
        return f"{nombres} {apellidos}".strip()
    
    @property
    def especialidad(self):
        return f"Especialidad {self.id_especialidad_doctor}"
    
    class Meta:
        managed = False
        db_table = 'doctor'
        ordering = ['id_doctor']
    
    def __str__(self):
        return f"Dr. {self.user_profile.nombre_completo} - {self.especialidad.nombre}"

class PacienteProfile(models.Model):
    id_datos_paciente = models.AutoField(primary_key=True)
    nombre_1 = models.CharField(max_length=50)
    nombre_2 = models.CharField(max_length=50, blank=True)
    apellido_1 = models.CharField(max_length=50)
    apellido_2 = models.CharField(max_length=50, blank=True)
    id_historial_medico_paciente = models.IntegerField()
    id_user_paciente = models.IntegerField()  # Referencia a User_paciente, no a auth_user
    cedula = models.CharField(max_length=15, unique=True)
    tipo_cedula = models.CharField(max_length=10)
    sexo = models.CharField(max_length=10)
    
    @property
    def nombre_completo(self):
        nombres = f"{self.nombre_1} {self.nombre_2}".strip()
        apellidos = f"{self.apellido_1} {self.apellido_2}".strip()
        return f"{nombres} {apellidos}".strip()
    
    @property
    def user_profile(self):
        # Para compatibilidad con el código existente
        return self
    
    @property
    def alergias(self):
        return ""  # Podría obtenerse de historial_medico_paciente
    
    @property
    def medicamentos_actuales(self):
        return ""  # Podría obtenerse de historial_medico_paciente
    
    @property
    def condiciones_cronicas(self):
        return ""  # Podría obtenerse de historial_medico_paciente
    
    class Meta:
        managed = False
        db_table = 'paciente_datos_personales'
        ordering = ['id_datos_paciente']
    
    def __str__(self):
        return f"Paciente: {self.nombre_completo}"
    
    # El método save original fue removido porque el campo historia_clinica_numero no existe en la tabla actual
    # def save(self, *args, **kwargs):
    #     if not self.historia_clinica_numero:
    #         import uuid
    #         self.historia_clinica_numero = f"HC-{uuid.uuid4().hex[:8].upper()}"
    #     super().save(*args, **kwargs)
