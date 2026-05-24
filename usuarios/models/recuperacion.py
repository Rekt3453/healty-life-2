from django.db import models
from .usuarios import UserPaciente, UserDoctor, UserRecepcionista, UserAdmin, UserSuperAdmin


class RecuperacionContrasenaPaciente(models.Model):
    id_recuperar_contrasena_paciente = models.BigAutoField(primary_key=True)
    preguntas_seguridad = models.CharField(max_length=500, blank=True, null=True)
    respuestas_seguridad = models.CharField(max_length=500, blank=True, null=True)
    id_user_paciente = models.ForeignKey(
        UserPaciente, on_delete=models.CASCADE, db_column='id_user_paciente'
    )

    class Meta:
        managed = False
        db_table = 'recuperacion_contrasena_paciente'


class RecuperacionContrasenaDoctor(models.Model):
    id_recuperacion_contrasena_doctor = models.BigAutoField(primary_key=True)
    preguntas_seguridad = models.CharField(max_length=500, blank=True, null=True)
    respuestas_seguridad = models.CharField(max_length=500, blank=True, null=True)
    id_user_doctor = models.ForeignKey(
        UserDoctor, on_delete=models.CASCADE, db_column='id_user_doctor'
    )

    class Meta:
        managed = False
        db_table = 'recuperacion_contrasena_doctor'


class RecuperacionContrasenaRecepcionista(models.Model):
    id_recuperacion_recepcionista = models.BigAutoField(primary_key=True)
    preguntas_seguridad = models.CharField(max_length=500, blank=True, null=True)
    respuestas_seguridad = models.CharField(max_length=500, blank=True, null=True)
    id_user_recepcionista = models.ForeignKey(
        UserRecepcionista, on_delete=models.CASCADE, db_column='id_user_recepcionista'
    )

    class Meta:
        managed = False
        db_table = 'recuperacion_contrasena_recepcionista'


class RecuperacionContrasenaAdmin(models.Model):
    id_recuperacion_contrasena_admin = models.BigAutoField(primary_key=True)
    preguntas_seguridad = models.CharField(max_length=500, blank=True, null=True)
    respuestas_seguridad = models.CharField(max_length=500, blank=True, null=True)
    id_user_admin = models.ForeignKey(
        UserAdmin, on_delete=models.CASCADE, db_column='id_user_admin'
    )

    class Meta:
        managed = False
        db_table = 'recuperacion_contrasena_admin'


class RecuperacionContrasenaSuperadmin(models.Model):
    id_recuperacion_contrasena_superadmin = models.BigAutoField(primary_key=True)
    preguntas_seguridad = models.CharField(max_length=500, blank=True, null=True)
    respuestas_seguridad = models.CharField(max_length=500, blank=True, null=True)
    id_user_superadmin = models.ForeignKey(
        UserSuperAdmin, on_delete=models.CASCADE, db_column='id_user_superadmin'
    )

    class Meta:
        managed = False
        db_table = 'recuperacion_contrasena_superadmin'
