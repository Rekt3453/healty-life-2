from django.db import models
from .ubicacion import Estado, Municipio, Ciudad, Parroquia


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
    id = models.AutoField(primary_key=True)
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
    referencias = models.TextField(blank=True, null=True)
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
