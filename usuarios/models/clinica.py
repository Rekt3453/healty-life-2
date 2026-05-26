from django.db import models
from .direcciones import DireccionSede


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
