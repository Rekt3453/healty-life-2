import hashlib
from django.db import models
from django.core.exceptions import ValidationError
from .clinica import Sede


def _check_password_dual(stored, plain):
    """
    Verifica una contraseña en texto plano contra un hash almacenado.
    Soporta MD5 (32 chars) y SHA256 (64 chars) para la migración gradual.
    Las nuevas contraseñas siempre se guardan como MD5.
    """
    if not stored:
        return False
    if len(stored) == 64:
        return stored == hashlib.sha256(plain.encode()).hexdigest()
    return stored == hashlib.md5(plain.encode()).hexdigest()


class CustomUserManager(models.Manager):
    def create_user(self, username, correo, password=None, **extra_fields):
        if not username:
            raise ValueError('El nombre de usuario es obligatorio')
        if not correo:
            raise ValueError('El correo electrónico es obligatorio')

        from django.core.validators import validate_email
        try:
            validate_email(correo)
            correo_normalizado = correo.lower().strip()
        except ValidationError:
            correo_normalizado = correo

        user_data = {
            'username': username,
            'email': correo_normalizado,
        }

        model_name = self.model._meta.model_name.lower()
        if model_name in ('userpaciente', 'userdoctor', 'userrecepcionista', 'useradmin'):
            user_data.update({
                'password': '',
                'id_sede': extra_fields.get('id_sede'),
                'status': extra_fields.get('status', True),
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
    password = models.CharField(max_length=255, db_column='contrasena')
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
        return _check_password_dual(self.password, password)

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
        return _check_password_dual(self.password, password)

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
        return _check_password_dual(self.password, password)

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
        return _check_password_dual(self.password, password)

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


class UserSuperAdmin(models.Model):
    id_superadmin = models.BigAutoField(primary_key=True)
    username = models.TextField(blank=True, null=True)
    correo = models.CharField(max_length=255, blank=True, null=True)
    id_sede = models.ForeignKey(Sede, on_delete=models.SET_NULL, null=True, blank=True, db_column='id_sede')
    status = models.BooleanField(default=True)
    contrasena = models.TextField(blank=True, null=True)

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
        return _check_password_dual(self.contrasena, password)

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
        return _check_password_dual(self.contrasena, password)

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
