# NOTA IMPORTANTE — Base de datos externa (Supabase / PostgreSQL)
# Los modelos marcados con `managed = False` en su clase Meta reflejan tablas
# que existen en la base de datos Supabase y son gestionadas externamente.
# NO uses migraciones de Django para modificar esas tablas; hazlo directamente
# en Supabase (SQL Editor o migrations manuales).  Solo los modelos sin Meta
# managed=False (o con managed=True) son gestionados por Django.
from django.db import models
from django.core.exceptions import ValidationError
import hashlib

# Tablas de ubicación (referenciadas por las tablas principales)
class Estado(models.Model):
    id_estado = models.AutoField(primary_key=True)
    estado = models.CharField(max_length=100)
    iso_3166_2 = models.CharField(max_length=10, blank=True, null=True, db_column='iso_3166-2')

    class Meta:
        managed = False
        db_table = 'estados'
        verbose_name = 'Estado'
        verbose_name_plural = 'Estados'

    def __str__(self):
        return self.estado

class Municipio(models.Model):
    id_municipio = models.AutoField(primary_key=True)
    id_estado = models.ForeignKey(Estado, on_delete=models.CASCADE, db_column='id_estado')
    municipio = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'municipios'
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
        managed = False
        db_table = 'ciudades'
        verbose_name = 'Ciudad'
        verbose_name_plural = 'Ciudades'

    def __str__(self):
        return self.ciudad

class Parroquia(models.Model):
    id_parroquia = models.AutoField(primary_key=True)
    id_municipio = models.ForeignKey(Municipio, on_delete=models.CASCADE, db_column='id_municipio')
    parroquia = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'parroquias'
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
        managed = False
        db_table = 'direccion_paciente'
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
        managed = False
        db_table = 'direccion_doctor'
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
        managed = False
        db_table = 'direccion_recepcionista'
        verbose_name = 'Dirección de Recepcionista'
        verbose_name_plural = 'Direcciones de Recepcionistas'

class DireccionSuperadmin(models.Model):
    id_direccion_superadmin = models.BigAutoField(primary_key=True)
    id_estado = models.ForeignKey(Estado, on_delete=models.CASCADE, db_column='id_estado')
    id_municipio = models.ForeignKey(Municipio, on_delete=models.CASCADE, db_column='id_municipio')
    id_parroquia = models.ForeignKey(Parroquia, on_delete=models.CASCADE, db_column='id_parroquia')
    id_ciudad = models.ForeignKey(Ciudad, on_delete=models.CASCADE, db_column='id_ciudad')
    direccion = models.TextField()
    referencia = models.TextField(blank=True, null=True)
    latitud = models.CharField(max_length=100, blank=True, null=True)
    longitud = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'direccion_superadmin'

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
        managed = False
        db_table = 'direccion_admin'
        verbose_name = 'Dirección de Administrador'
        verbose_name_plural = 'Direcciones de Administradores'


class DireccionSede(models.Model):
    id_direccion_sede = models.BigAutoField(primary_key=True)
    id_estado = models.ForeignKey(Estado, on_delete=models.SET_NULL, null=True, blank=True, db_column='id_estado')
    id_municipio = models.ForeignKey(Municipio, on_delete=models.SET_NULL, null=True, blank=True, db_column='id_municipio')
    id_parroquia = models.ForeignKey(Parroquia, on_delete=models.SET_NULL, null=True, blank=True, db_column='id_parroquia')
    id_ciudad = models.ForeignKey(Ciudad, on_delete=models.SET_NULL, null=True, blank=True, db_column='id_ciudad')
    direccion = models.TextField(blank=True, null=True)
    referencia = models.TextField(blank=True, null=True)
    latitud = models.CharField(max_length=100, blank=True, null=True)
    longitud = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'direccion_sede'


class CentroMedico(models.Model):
    id_cm = models.BigAutoField(primary_key=True)
    nombre_cm = models.TextField()
    rif_cm = models.CharField(max_length=50, blank=True, null=True)
    status = models.BooleanField(null=True, blank=True, default=True)

    class Meta:
        managed = False
        db_table = 'centro_medico'

    def __str__(self):
        return self.nombre_cm


# Tabla de sedes
class Sede(models.Model):
    id_sede = models.BigAutoField(primary_key=True)
    id_direccion = models.ForeignKey(DireccionSede, on_delete=models.CASCADE, db_column='id_direccion')
    rif_sede = models.CharField(max_length=50, blank=True, null=True)
    telefono = models.CharField(max_length=50, blank=True, null=True)
    status = models.BooleanField(null=True, blank=True, default=True)
    id_cm = models.ForeignKey(CentroMedico, on_delete=models.SET_NULL, null=True, blank=True, db_column='id_cm')
    nombre_sede = models.TextField()

    class Meta:
        managed = False
        db_table = 'sede'
        verbose_name = 'Sede'
        verbose_name_plural = 'Sedes'

    def __str__(self):
        return self.nombre_sede

# Modelos de usuarios personalizados - SIN herencia de AbstractBaseUser
class CustomUserManager(models.Manager):
    def create_user(self, username, correo, password=None, **extra_fields):
        if not username:
            raise ValueError('El nombre de usuario es obligatorio')
        if not correo:
            raise ValueError('El correo electrónico es obligatorio')
        
        from django.core.validators import validate_email
        from django.core.exceptions import ValidationError
        try:
            validate_email(correo)
            correo_normalizado = correo.lower().strip()
        except ValidationError:
            correo_normalizado = correo
        
        # Mapear los campos estándar a los campos de la BD
        user_data = {
            'username': username,  # Mapear a 'Username' en la BD
            'email': correo_normalizado,  # Mapear a 'correo' en la BD
        }
        
        # Agregar campos adicionales según el tipo de modelo
        model_name = self.model._meta.model_name.lower()
        if model_name == 'userpaciente':
            user_data.update({
                'password': '',  # Se agregará después con set_password
                'id_sede': extra_fields.get('id_sede'),
                'status': extra_fields.get('status', True)
            })
        elif model_name == 'userdoctor':
            user_data.update({
                'password': '',  # Se agregará después con set_password
                'id_sede': extra_fields.get('id_sede'),
                'status': extra_fields.get('status', True)
            })
        elif model_name == 'userrecepcionista':
            user_data.update({
                'password': '',  # Se agregará después con set_password
                'id_sede': extra_fields.get('id_sede'),
                'status': extra_fields.get('status', True)
            })
        elif model_name == 'useradmin':
            user_data.update({
                'password': '',  # Se agregará después con set_password
                'id_sede': extra_fields.get('id_sede'),
                'status': extra_fields.get('status', True)
            })
        
        user = self.model(**user_data)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, correo, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, correo, password, **extra_fields)
class UserPaciente(models.Model):
    id_user_paciente = models.BigAutoField(primary_key=True)
    username = models.CharField(max_length=150, unique=True, db_column='username')
    password = models.CharField(max_length=255, db_column='contrasena')  # Guardará el hash
    email = models.EmailField(unique=True, db_column='correo')
    id_sede = models.ForeignKey(Sede, on_delete=models.CASCADE, db_column='id_sede')
    status = models.BooleanField(default=True)
    last_login = models.DateTimeField(null=True, blank=True, db_column='last_login')

    objects = CustomUserManager()

    class Meta:
        managed = False
        db_table = 'user_paciente'
        verbose_name = 'Usuario Paciente'
        verbose_name_plural = 'Usuarios Pacientes'

    def __str__(self):
        return self.username

    def set_password(self, password):
        self.password = hashlib.md5(password.encode()).hexdigest()

    def check_password(self, password):
        return self.password == hashlib.md5(password.encode()).hexdigest()

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return self.status

    @property
    def is_staff(self):
        return False

class UserDoctor(models.Model):
    id_user_doctor = models.BigAutoField(primary_key=True)
    username = models.CharField(max_length=150, unique=True, db_column='username')
    password = models.CharField(max_length=255, db_column='contrasena')
    email = models.EmailField(unique=True, db_column='correo')
    id_sede = models.ForeignKey(Sede, on_delete=models.CASCADE, db_column='id_sede')
    status = models.BooleanField(default=True)
    token_activacion = models.CharField(max_length=64, blank=True, null=True, db_column='token_activacion')
    last_login = models.DateTimeField(null=True, blank=True, db_column='last_login')

    objects = CustomUserManager()

    class Meta:
        managed = False
        db_table = 'user_doctor'
        verbose_name = 'Usuario Doctor'
        verbose_name_plural = 'Usuarios Doctores'

    def __str__(self):
        return self.username

    def set_password(self, password):
        self.password = hashlib.md5(password.encode()).hexdigest()

    def check_password(self, password):
        return self.password == hashlib.md5(password.encode()).hexdigest()

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return self.status

    @property
    def is_staff(self):
        return False

class UserRecepcionista(models.Model):
    id_user_recepcionista = models.BigAutoField(primary_key=True)
    username = models.CharField(max_length=150, unique=True, db_column='username')
    password = models.CharField(max_length=255, db_column='contrasena')
    email = models.EmailField(unique=True, db_column='correo')
    id_sede = models.ForeignKey(Sede, on_delete=models.CASCADE, db_column='id_sede')
    status = models.BooleanField(default=True)
    token_activacion = models.CharField(max_length=64, blank=True, null=True, db_column='token_activacion')
    last_login = models.DateTimeField(null=True, blank=True, db_column='last_login')

    objects = CustomUserManager()

    class Meta:
        managed = False
        db_table = 'user_recepcionista'
        verbose_name = 'Usuario Recepcionista'
        verbose_name_plural = 'Usuarios Recepcionistas'

    def __str__(self):
        return self.username

    def set_password(self, password):
        self.password = hashlib.md5(password.encode()).hexdigest()

    def check_password(self, password):
        return self.password == hashlib.md5(password.encode()).hexdigest()

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return self.status

    @property
    def is_staff(self):
        return False

class UserAdmin(models.Model):
    id_user_admin = models.BigAutoField(primary_key=True)
    username = models.CharField(max_length=150, unique=True, db_column='username')
    email = models.EmailField(unique=True, db_column='correo')
    id_sede = models.ForeignKey(Sede, on_delete=models.CASCADE, db_column='id_sede')
    status = models.BooleanField(default=True)
    password = models.CharField(max_length=255, db_column='contrasena')
    token_activacion = models.CharField(max_length=64, blank=True, null=True, db_column='token_activacion')
    last_login = models.DateTimeField(null=True, blank=True, db_column='last_login')

    objects = CustomUserManager()

    class Meta:
        managed = False
        db_table = 'user_admin'
        verbose_name = 'Usuario Administrador'
        verbose_name_plural = 'Usuarios Administradores'

    def __str__(self):
        return self.username

    def set_password(self, password):
        self.password = hashlib.md5(password.encode()).hexdigest()

    def check_password(self, password):
        return self.password == hashlib.md5(password.encode()).hexdigest()

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return self.status

    @property
    def is_staff(self):
        return True

    @property
    def is_superuser(self):
        return True

# Tablas de datos personales
class PacienteDatosPersonales(models.Model):
    id_datos_paciente = models.BigAutoField(primary_key=True)
    nombre_1 = models.TextField()
    nombre_2 = models.TextField(blank=True, null=True)
    apellido_1 = models.TextField()
    apellido_2 = models.TextField(blank=True, null=True)
    id_user_paciente = models.ForeignKey(UserPaciente, on_delete=models.CASCADE, db_column='id_user_paciente')
    cedula = models.CharField(max_length=20, unique=True)
    tipo_cedula = models.CharField(max_length=20, blank=True, null=True)
    sexo = models.CharField(max_length=20, blank=True, null=True)
    id_sede = models.ForeignKey(Sede, on_delete=models.SET_NULL, null=True, blank=True, db_column='id_sede')
    fecha_nacimiento = models.DateTimeField(blank=True, null=True)
    fecha_registro = models.DateTimeField(null=True, blank=True)
    status = models.BooleanField(null=True, blank=True, default=True)
    id_direccion_paciente = models.ForeignKey(DireccionPaciente, on_delete=models.SET_NULL, null=True, blank=True, db_column='id_direccion_paciente')
    telefono = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'paciente_datos_personales'
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
    id_doctor = models.BigAutoField(primary_key=True)
    nombre_1 = models.TextField(blank=True, null=True)
    nombre_2 = models.TextField(blank=True, null=True)
    apellido_1 = models.TextField(blank=True, null=True)
    apellido_2 = models.TextField(blank=True, null=True)
    id_especialidad_doctor = models.BigIntegerField(blank=True, null=True)
    id_user_doctor = models.ForeignKey(UserDoctor, on_delete=models.CASCADE, db_column='id_user_doctor')
    id_consultorio = models.BigIntegerField(blank=True, null=True)
    sexo = models.CharField(max_length=20, blank=True, null=True)
    fecha_nacimiento = models.DateTimeField(blank=True, null=True)
    fecha_registro = models.DateTimeField(null=True, blank=True)
    cedula = models.CharField(max_length=20, blank=True, null=True)
    tipo_cedula = models.CharField(max_length=20, blank=True, null=True)
    id_sede = models.ForeignKey(Sede, on_delete=models.SET_NULL, null=True, blank=True, db_column='id_sede')
    status = models.BooleanField(null=True, blank=True, default=True)
    id_direccion_doctor = models.ForeignKey(DireccionDoctor, on_delete=models.SET_NULL, null=True, blank=True, db_column='id_direccion_doctor')
    telefono = models.CharField(max_length=50, blank=True, null=True)
    id_horario = models.BigIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'doctor'
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
    id_recepcionista = models.BigAutoField(primary_key=True)
    id_user_recepcionista = models.ForeignKey(UserRecepcionista, on_delete=models.CASCADE, db_column='id_user_recepcionista')
    nombre_1 = models.TextField()
    nombre_2 = models.TextField(blank=True, null=True)
    apellido_1 = models.TextField()
    apellido_2 = models.TextField(blank=True, null=True)
    cedula = models.CharField(max_length=20, unique=True)
    tipo_cedula = models.CharField(max_length=20, blank=True, null=True)
    fecha_nacimiento = models.DateTimeField(blank=True, null=True)
    fecha_registro = models.DateTimeField(null=True, blank=True)
    id_sede = models.ForeignKey(Sede, on_delete=models.SET_NULL, null=True, blank=True, db_column='id_sede')
    sexo = models.CharField(max_length=20, blank=True, null=True)
    id_direccion_recepcionista = models.ForeignKey(DireccionRecepcionista, on_delete=models.SET_NULL, null=True, blank=True, db_column='id_direccion_recepcionista')
    status = models.BooleanField(default=True)
    telefono = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'recepcionista'
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
    id_administrador = models.BigAutoField(primary_key=True)
    id_user_admin = models.ForeignKey(UserAdmin, on_delete=models.CASCADE, db_column='id_user_admin')
    nombre_1 = models.TextField()
    nombre_2 = models.TextField(blank=True, null=True)
    apellido_1 = models.TextField()
    apellido_2 = models.TextField(blank=True, null=True)
    cedula = models.CharField(max_length=20, unique=True)
    tipo_cedula = models.CharField(max_length=20, blank=True, null=True)
    fecha_nacimiento = models.DateTimeField(blank=True, null=True)
    fecha_registro = models.DateTimeField(null=True, blank=True)
    id_sede = models.ForeignKey(Sede, on_delete=models.SET_NULL, null=True, blank=True, db_column='id_sede')
    sexo = models.CharField(max_length=20, blank=True, null=True)
    id_direccion_admin = models.ForeignKey(DireccionAdmin, on_delete=models.SET_NULL, null=True, blank=True, db_column='id_direccion_admin')
    status = models.BooleanField(default=True)
    telefono = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'administrador'
        verbose_name = 'Administrador'
        verbose_name_plural = 'Administradores'

    def __str__(self):
        return f"{self.nombre_1} {self.apellido_1}"

    @property
    def nombre_completo(self):
        nombres = f"{self.nombre_1} {self.nombre_2 or ''}".strip()
        apellidos = f"{self.apellido_1} {self.apellido_2 or ''}".strip()
        return f"{nombres} {apellidos}".strip()

# Modelo PacienteEspecial para pacientes especiales y tutores
class PacienteEspecial(models.Model):
    id_paciente_especial = models.AutoField(primary_key=True)
    id_paciente_tutor = models.ForeignKey('PacienteDatosPersonales', on_delete=models.CASCADE, 
                                         db_column='id_paciente_tutor', null=True, blank=True,
                                         related_name='tutores')
    nombre_1 = models.TextField(blank=True, null=True)
    nombre_2 = models.TextField(blank=True, null=True)
    apellido_1 = models.TextField(blank=True, null=True)
    apellido_2 = models.TextField(blank=True, null=True)
    status = models.BooleanField(default=True)
    id_sede = models.ForeignKey(Sede, on_delete=models.CASCADE, db_column='id_sede', null=True, blank=True)
    sexo = models.CharField(max_length=20, blank=True, null=True)
    fecha_nacimiento = models.DateTimeField(blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    telefono = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'paciente_especial'
        verbose_name = 'Paciente Especial'
        verbose_name_plural = 'Pacientes Especiales'

    def __str__(self):
        if self.nombre_1 and self.apellido_1:
            return f"{self.nombre_1} {self.apellido_1}"
        return f"Paciente Especial {self.id_paciente_especial}"

# Modelo UserProfile para compatibilidad con el nuevo formulario
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
    
    # Campos de ubicación
    id_estado = models.ForeignKey(Estado, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Estado")
    id_municipio = models.ForeignKey(Municipio, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Municipio")
    id_ciudad = models.ForeignKey(Ciudad, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Ciudad")
    id_parroquia = models.ForeignKey(Parroquia, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Parroquia")
    
    class Meta:
        managed = False
        verbose_name = "Perfil de Usuario"
        verbose_name_plural = "Perfiles de Usuarios"
    
    def __str__(self):
        return f"{self.user.username} - {self.get_rol_display()}"


# ── Nuevos modelos: SuperAdmin, Root ─────────────────────────────────────────

class UserSuperAdmin(models.Model):
    id_superadmin = models.BigAutoField(primary_key=True, db_column='id_user_superadmin')
    username = models.TextField(blank=True, null=True)
    correo = models.CharField(max_length=255, blank=True, null=True)
    id_sede = models.ForeignKey(Sede, on_delete=models.SET_NULL, null=True, blank=True, db_column='id_sede')
    status = models.BooleanField(default=True)
    contrasena = models.TextField(blank=True, null=True)
    token_activacion = models.CharField(max_length=64, blank=True, null=True, db_column='token_activacion')

    objects = CustomUserManager()

    class Meta:
        managed = False
        db_table = 'user_superadmin'
        verbose_name = 'Usuario SuperAdmin'
        verbose_name_plural = 'Usuarios SuperAdmin'

    def __str__(self):
        return self.username or f'SuperAdmin {self.id_superadmin}'

    def set_password(self, password):
        self.contrasena = hashlib.md5(password.encode()).hexdigest()

    def check_password(self, password):
        return self.contrasena == hashlib.md5(password.encode()).hexdigest()

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return self.status

    @property
    def is_staff(self):
        return True

    @property
    def is_superuser(self):
        return True


class UserRoot(models.Model):
    id_user_root = models.BigAutoField(primary_key=True)
    username = models.CharField(max_length=255, blank=True, null=True)
    correo = models.CharField(max_length=255, blank=True, null=True)
    contrasena = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'user_root'
        verbose_name = 'Usuario Root'
        verbose_name_plural = 'Usuarios Root'

    def __str__(self):
        return self.username or f'Root {self.id_user_root}'

    def set_password(self, password):
        self.contrasena = hashlib.md5(password.encode()).hexdigest()

    def check_password(self, password):
        return self.contrasena == hashlib.md5(password.encode()).hexdigest()

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_staff(self):
        return True

    @property
    def is_superuser(self):
        return True


class Superadmin(models.Model):
    id_superadmin = models.BigAutoField(primary_key=True)
    id_user_superadmin = models.ForeignKey(
        UserSuperAdmin, on_delete=models.SET_NULL,
        null=True, blank=True, db_column='id_user_superadmin'
    )
    nombre_1 = models.TextField(blank=True, null=True)
    nombre_2 = models.TextField(blank=True, null=True)
    apellido_1 = models.TextField(blank=True, null=True)
    apellido_2 = models.TextField(blank=True, null=True)
    cedula = models.CharField(max_length=50, blank=True, null=True)
    tipo_cedula = models.CharField(max_length=50, blank=True, null=True)
    id_sede = models.ForeignKey(Sede, on_delete=models.SET_NULL, null=True, blank=True, db_column='id_sede')
    status = models.BooleanField(default=True)

    class Meta:
        managed = False
        db_table = 'superadmin'
        verbose_name = 'Superadmin'
        verbose_name_plural = 'Superadmins'

    def __str__(self):
        return f"{self.nombre_1 or ''} {self.apellido_1 or ''}".strip()

    @property
    def nombre_completo(self):
        return f"{self.nombre_1 or ''} {self.nombre_2 or ''} {self.apellido_1 or ''} {self.apellido_2 or ''}".strip()


class Root(models.Model):
    id_root = models.BigAutoField(primary_key=True)
    nombre = models.TextField(blank=True, null=True)
    apellido = models.TextField(blank=True, null=True)
    id_user_root = models.ForeignKey(
        UserRoot, on_delete=models.SET_NULL,
        null=True, blank=True, db_column='id_user_root'
    )
    status = models.BooleanField(default=True)
    id_sede = models.ForeignKey(Sede, on_delete=models.SET_NULL, null=True, blank=True, db_column='id_sede')

    class Meta:
        managed = False
        db_table = 'root'
        verbose_name = 'Root'
        verbose_name_plural = 'Roots'

    def __str__(self):
        return f"{self.nombre or ''} {self.apellido or ''}".strip()
