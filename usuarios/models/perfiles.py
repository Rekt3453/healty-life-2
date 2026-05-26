from django.db import models
from .ubicacion import Estado, Municipio, Ciudad, Parroquia
from .direcciones import DireccionPaciente, DireccionDoctor, DireccionRecepcionista, DireccionAdmin
from .clinica import Sede
from .usuarios import UserPaciente, UserDoctor, UserRecepcionista, UserAdmin, UserSuperAdmin, UserRoot


class PacienteDatosPersonales(models.Model):
    id_datos_paciente = models.BigAutoField(primary_key=True)
    nombre_1 = models.TextField()
    nombre_2 = models.TextField(blank=True, null=True)
    apellido_1 = models.TextField()
    apellido_2 = models.TextField(blank=True, null=True)
    id_historial_medico_paciente = models.BigIntegerField(blank=True, null=True)
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
    id_horario = models.BigIntegerField(blank=True, null=True)

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


class PacienteEspecial(models.Model):
    id_paciente_especial = models.AutoField(primary_key=True)
    id_paciente_tutor = models.ForeignKey(
        PacienteDatosPersonales, on_delete=models.CASCADE,
        db_column='id_paciente_tutor', null=True, blank=True,
        related_name='tutores'
    )
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
