from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.exceptions import ValidationError
import hashlib

# Tablas de ubicación (referenciadas por las tablas principales)
class Estado(models.Model):
    id_estado = models.AutoField(primary_key=True)
    estado = models.CharField(max_length=100)
    iso_3166_2 = models.CharField(max_length=10, blank=True, null=True)

    class Meta:
        db_table = 'public.estados'
        verbose_name = 'Estado'
        verbose_name_plural = 'Estados'

    def __str__(self):
        return self.estado

class Municipio(models.Model):
    id_municipio = models.AutoField(primary_key=True)
    id_estado = models.ForeignKey(Estado, on_delete=models.CASCADE, db_column='id_estado')
    municipio = models.CharField(max_length=100)

    class Meta:
        db_table = 'public.municipios'
        verbose_name = 'Municipio'
        verbose_name_plural = 'Municipios'

    def __str__(self):
        return self.municipio

class Ciudad(models.Model):
    id_ciudad = models.AutoField(primary_key=True)
    id_estado = models.ForeignKey(Estado, on_delete=models.CASCADE, db_column='id_estado')
    ciudad = models.CharField(max_length=100)
    capital = models.SmallIntegerField(default=0)

    class Meta:
        db_table = 'public.ciudades'
        verbose_name = 'Ciudad'
        verbose_name_plural = 'Ciudades'

    def __str__(self):
        return self.ciudad

class Parroquia(models.Model):
    id_parroquia = models.AutoField(primary_key=True)
    id_municipio = models.ForeignKey(Municipio, on_delete=models.CASCADE, db_column='id_municipio')
    parroquia = models.CharField(max_length=100)

    class Meta:
        db_table = 'public.parroquias'
        verbose_name = 'Parroquia'
        verbose_name_plural = 'Parroquias'

    def __str__(self):
        return self.parroquia

# Tablas de direcciones
class DireccionPaciente(models.Model):
    id_direccion_paciente = models.AutoField(primary_key=True)
    id_estado = models.ForeignKey(Estado, on_delete=models.CASCADE, db_column='id_estado')
    id_municipio = models.ForeignKey(Municipio, on_delete=models.CASCADE, db_column='id_municipio')
    id_parroquia = models.ForeignKey(Parroquia, on_delete=models.CASCADE, db_column='id_parroquia')
    id_ciudad = models.ForeignKey(Ciudad, on_delete=models.CASCADE, db_column='id_ciudad')
    direccion = models.TextField()
    referencia = models.TextField(blank=True, null=True)
    latitud = models.CharField(max_length=100, blank=True, null=True)
    longitud = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = 'public.direccion_paciente'
        verbose_name = 'Dirección de Paciente'
        verbose_name_plural = 'Direcciones de Pacientes'

class DireccionDoctor(models.Model):
    id = models.AutoField(primary_key=True)  # Nota: en la BD es 'id' no 'id_direccion_doctor'
    id_estado = models.ForeignKey(Estado, on_delete=models.CASCADE, db_column='id_estado')
    id_municipio = models.ForeignKey(Municipio, on_delete=models.CASCADE, db_column='id_municipio')
    id_ciudad = models.ForeignKey(Ciudad, on_delete=models.CASCADE, db_column='id_ciudad')
    id_parroquia = models.ForeignKey(Parroquia, on_delete=models.CASCADE, db_column='id_parroquia')
    direccion = models.TextField()
    referencia = models.TextField(blank=True, null=True)
    latitud = models.CharField(max_length=100, blank=True, null=True)
    longitud = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = 'public.direccion_doctor'
        verbose_name = 'Dirección de Doctor'
        verbose_name_plural = 'Direcciones de Doctores'

class DireccionRecepcionista(models.Model):
    id_direccion_recepcionista = models.AutoField(primary_key=True)
    id_estado = models.ForeignKey(Estado, on_delete=models.CASCADE, db_column='id_estado')
    id_municipio = models.ForeignKey(Municipio, on_delete=models.CASCADE, db_column='id_municipio')
    id_parroquia = models.ForeignKey(Parroquia, on_delete=models.CASCADE, db_column='id_parroquia')
    id_ciudad = models.ForeignKey(Ciudad, on_delete=models.CASCADE, db_column='id_ciudad')
    direccion = models.TextField()
    referencia = models.TextField(blank=True, null=True)
    latitud = models.CharField(max_length=100, blank=True, null=True)
    longitud = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = 'public.direccion_recepcionista'
        verbose_name = 'Dirección de Recepcionista'
        verbose_name_plural = 'Direcciones de Recepcionistas'

class DireccionAdmin(models.Model):
    id_direccion_admin = models.AutoField(primary_key=True)
    id_estado = models.ForeignKey(Estado, on_delete=models.CASCADE, db_column='id_estado')
    id_municipio = models.ForeignKey(Municipio, on_delete=models.CASCADE, db_column='id_municipio')
    id_parroquia = models.ForeignKey(Parroquia, on_delete=models.CASCADE, db_column='id_parroquia')
    id_ciudad = models.ForeignKey(Ciudad, on_delete=models.CASCADE, db_column='id_ciudad')
    direccion = models.TextField()
    referencias = models.TextField(blank=True, null=True)  # Nota: en la BD es 'referencias' no 'referencia'
    latitud = models.CharField(max_length=100, blank=True, null=True)
    longitud = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = 'public.direccion_admin'
        verbose_name = 'Dirección de Administrador'
        verbose_name_plural = 'Direcciones de Administradores'

# Tabla de sedes
class Sede(models.Model):
    id_sede = models.AutoField(primary_key=True)
    id_direccion = models.ForeignKey(DireccionAdmin, on_delete=models.CASCADE, db_column='id_direccion')
    rif_sede = models.CharField(max_length=50, blank=True, null=True)
    telefono = models.CharField(max_length=50, blank=True, null=True)
    status = models.BooleanField(default=True)
    id_cm = models.IntegerField(blank=True, null=True)  # Referencia a centro_medico
    nombre_sede = models.TextField()

    class Meta:
        db_table = 'public.sede'
        verbose_name = 'Sede'
        verbose_name_plural = 'Sedes'

    def __str__(self):
        return self.nombre_sede

# Modelos de usuarios personalizados - SIN PermissionsMixin para evitar conflictos
class UserManager(BaseUserManager):
    def create_user(self, username, correo, password=None, **extra_fields):
        if not username:
            raise ValueError('El nombre de usuario es obligatorio')
        if not correo:
            raise ValueError('El correo electrónico es obligatorio')
        
        user = self.model(
            username=username,
            correo=self.normalize_email(correo),
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, correo, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, correo, password, **extra_fields)

# Tablas de autenticación - Simplificadas sin PermissionsMixin
class UserPaciente(AbstractBaseUser):
    id_user_paceinte = models.AutoField(primary_key=True)  # Nota: en la BD es 'id_user_paceinte' con error tipográfico
    Username = models.CharField(max_length=150, unique=True)
    contrasena = models.CharField(max_length=255)  # Guardará el hash
    correo = models.EmailField(unique=True)
    id_sede = models.ForeignKey(Sede, on_delete=models.CASCADE, db_column='id_sede')
    status = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'Username'
    REQUIRED_FIELDS = ['correo']

    class Meta:
        db_table = 'public.user_paciente'
        verbose_name = 'Usuario Paciente'
        verbose_name_plural = 'Usuarios Pacientes'

    def __str__(self):
        return self.Username

    def set_password(self, password):
        self.contrasena = hashlib.sha256(password.encode()).hexdigest()

    def check_password(self, password):
        return self.contrasena == hashlib.sha256(password.encode()).hexdigest()

class UserDoctor(AbstractBaseUser):
    id_user_doctor = models.AutoField(primary_key=True)
    username = models.CharField(max_length=150, unique=True)
    contrasena = models.CharField(max_length=255)
    correo = models.EmailField(unique=True)
    id_sede = models.ForeignKey(Sede, on_delete=models.CASCADE, db_column='id_sede')
    status = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['correo']

    class Meta:
        db_table = 'public.user_doctor'
        verbose_name = 'Usuario Doctor'
        verbose_name_plural = 'Usuarios Doctores'

    def __str__(self):
        return self.username

    def set_password(self, password):
        self.contrasena = hashlib.sha256(password.encode()).hexdigest()

    def check_password(self, password):
        return self.contrasena == hashlib.sha256(password.encode()).hexdigest()

class UserRecepcionista(AbstractBaseUser):
    id_user_recepcionista = models.AutoField(primary_key=True)
    username = models.CharField(max_length=150, unique=True)
    contrasena = models.CharField(max_length=255)
    correo = models.EmailField(unique=True)
    id_sede = models.ForeignKey(Sede, on_delete=models.CASCADE, db_column='id_sede')
    status = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['correo']

    class Meta:
        db_table = 'public.user_recepcionista'
        verbose_name = 'Usuario Recepcionista'
        verbose_name_plural = 'Usuarios Recepcionistas'

    def __str__(self):
        return self.username

    def set_password(self, password):
        self.contrasena = hashlib.sha256(password.encode()).hexdigest()

    def check_password(self, password):
        return self.contrasena == hashlib.sha256(password.encode()).hexdigest()

class UserAdmin(AbstractBaseUser):
    id_user_admin = models.AutoField(primary_key=True)
    username = models.CharField(max_length=150, unique=True)
    correo = models.EmailField(unique=True)
    contrasena = models.CharField(max_length=255)
    id_sede = models.ForeignKey(Sede, on_delete=models.CASCADE, db_column='id_sede')
    status = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=True)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['correo']

    class Meta:
        db_table = 'public.user_admin'
        verbose_name = 'Usuario Administrador'
        verbose_name_plural = 'Usuarios Administradores'

    def __str__(self):
        return self.username

    def set_password(self, password):
        self.contrasena = hashlib.sha256(password.encode()).hexdigest()

    def check_password(self, password):
        return self.contrasena == hashlib.sha256(password.encode()).hexdigest()

# Tablas de datos personales
class PacienteDatosPersonales(models.Model):
    id_datos_paciente = models.AutoField(primary_key=True)
    nombre_1 = models.TextField()
    nombre_2 = models.TextField(blank=True, null=True)
    apellido_1 = models.TextField()
    apellido_2 = models.TextField(blank=True, null=True)
    id_historial_medico_paciente = models.BigIntegerField(blank=True, null=True)
    id_user_paciente = models.ForeignKey(UserPaciente, on_delete=models.CASCADE, db_column='id_user_paciente')
    cedula = models.CharField(max_length=20, unique=True)
    tipo_cedula = models.CharField(max_length=20, blank=True, null=True)
    sexo = models.CharField(max_length=20, blank=True, null=True)
    id_recipe = models.BigIntegerField(blank=True, null=True)
    id_sede = models.ForeignKey(Sede, on_delete=models.CASCADE, db_column='id_sede')
    fecha_nacimiento = models.DateTimeField(blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    status = models.BooleanField(default=True)
    id_direccion_paciente = models.ForeignKey(DireccionPaciente, on_delete=models.CASCADE, db_column='id_direccion_paciente')
    telefono = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        db_table = 'public.paciente_datos_personales'
        verbose_name = 'Datos Personales de Paciente'
        verbose_name_plural = 'Datos Personales de Pacientes'

    def __str__(self):
        return f"{self.nombre_1} {self.apellido_1}"

    @property
    def nombre_completo(self):
        nombres = f"{self.nombre_1} {self.nombre_2 or ''}".strip()
        apellidos = f"{self.apellido_1} {self.apellido_2 or ''}".strip()
        return f"{nombres} {apellidos}".strip()

class Doctor(models.Model):
    id_doctor = models.AutoField(primary_key=True)
    nombre_1 = models.TextField()  # En la BD es ARRAY, pero lo manejaremos como texto
    nombre_2 = models.TextField(blank=True, null=True)
    apellido_1 = models.TextField()
    apellido_2 = models.TextField(blank=True, null=True)
    id_especialidad_doctor = models.BigIntegerField(blank=True, null=True)
    id_user_doctor = models.ForeignKey(UserDoctor, on_delete=models.CASCADE, db_column='id_user_doctor')
    id_consultorio = models.BigIntegerField(blank=True, null=True)
    sexo = models.CharField(max_length=20, blank=True, null=True)
    fecha_nacimiento = models.DateTimeField(blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    cedula = models.CharField(max_length=20, unique=True)
    tipo_cedula = models.CharField(max_length=20, blank=True, null=True)
    id_sede = models.ForeignKey(Sede, on_delete=models.CASCADE, db_column='id_sede')
    status = models.BooleanField(default=True)
    id_direccion_doctor = models.ForeignKey(DireccionDoctor, on_delete=models.CASCADE, db_column='id_direccion_doctor')
    telefono = models.CharField(max_length=50, blank=True, null=True)
    id_horario = models.BigIntegerField(blank=True, null=True)

    class Meta:
        db_table = 'public.doctor'
        verbose_name = 'Doctor'
        verbose_name_plural = 'Doctores'

    def __str__(self):
        return f"Dr. {self.nombre_1} {self.apellido_1}"

    @property
    def nombre_completo(self):
        nombres = f"{self.nombre_1} {self.nombre_2 or ''}".strip()
        apellidos = f"{self.apellido_1} {self.apellido_2 or ''}".strip()
        return f"Dr. {nombres} {apellidos}".strip()

class Recepcionista(models.Model):
    id_recepcionista = models.AutoField(primary_key=True)
    id_user_recepcionista = models.ForeignKey(UserRecepcionista, on_delete=models.CASCADE, db_column='id_user_recepcionista')
    nombre_1 = models.TextField()
    nombre_2 = models.TextField(blank=True, null=True)
    apellido_1 = models.TextField()
    apellido_2 = models.TextField(blank=True, null=True)
    cedula = models.CharField(max_length=20, unique=True)
    tipo_cedula = models.CharField(max_length=20, blank=True, null=True)
    fecha_nacimiento = models.DateTimeField(blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    id_sede = models.ForeignKey(Sede, on_delete=models.CASCADE, db_column='id_sede')
    sexo = models.CharField(max_length=20, blank=True, null=True)
    id_direccion_recepcionista = models.ForeignKey(DireccionRecepcionista, on_delete=models.CASCADE, db_column='id_direccion_recepcionista')
    status = models.BooleanField(default=True)
    telefono = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        db_table = 'public.recepcionista'
        verbose_name = 'Recepcionista'
        verbose_name_plural = 'Recepcionistas'

    def __str__(self):
        return f"{self.nombre_1} {self.apellido_1}"

    @property
    def nombre_completo(self):
        nombres = f"{self.nombre_1} {self.nombre_2 or ''}".strip()
        apellidos = f"{self.apellido_1} {self.apellido_2 or ''}".strip()
        return f"{nombres} {apellidos}".strip()

class Administrador(models.Model):
    id_administrador = models.AutoField(primary_key=True)
    id_user_admin = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, db_column='id_user_admin')
    nombre_1 = models.TextField()
    nombre_2 = models.TextField(blank=True, null=True)
    apellido_1 = models.TextField()
    apellido_2 = models.TextField(blank=True, null=True)
    cedula = models.CharField(max_length=20, unique=True)
    tipo_cedula = models.CharField(max_length=20, blank=True, null=True)
    fecha_nacimiento = models.DateTimeField(blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    id_sede = models.ForeignKey(Sede, on_delete=models.CASCADE, db_column='id_sede')
    sexo = models.CharField(max_length=20, blank=True, null=True)
    id_direccion_admin = models.ForeignKey(DireccionAdmin, on_delete=models.CASCADE, db_column='id_direccion_admin')
    status = models.BooleanField(default=True)
    telefono = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        db_table = 'public.administrador'
        verbose_name = 'Administrador'
        verbose_name_plural = 'Administradores'

    def __str__(self):
        return f"{self.nombre_1} {self.apellido_1}"

    @property
    def nombre_completo(self):
        nombres = f"{self.nombre_1} {self.nombre_2 or ''}".strip()
        apellidos = f"{self.apellido_1} {self.apellido_2 or ''}".strip()
        return f"{nombres} {apellidos}".strip()

# Modelo temporal para compatibilidad durante la migración
class UserProfile(models.Model):
    ROLES = (
        ('paciente', 'Paciente'),
        ('medico', 'Médico'),
        ('recepcionista', 'Recepcionista'),
        ('gerente', 'Gerente'),
    )
    
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE, verbose_name="Usuario")
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
