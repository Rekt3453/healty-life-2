from django.db import models


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
