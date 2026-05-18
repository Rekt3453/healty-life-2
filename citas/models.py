from django.db import models
from usuarios.models import Sede, Doctor, PacienteDatosPersonales, CentroMedico


class Consultorio(models.Model):
    id_consultorio = models.BigAutoField(primary_key=True)
    id_sede = models.ForeignKey(Sede, on_delete=models.SET_NULL, null=True, blank=True, db_column='id_sede')
    id_cm = models.ForeignKey(CentroMedico, on_delete=models.SET_NULL, null=True, blank=True, db_column='id_cm')
    consultorios = models.CharField(max_length=255, blank=True, null=True)
    status = models.BooleanField(null=True, blank=True, default=True)

    class Meta:
        managed = False
        db_table = 'consultorio'
        verbose_name = 'Consultorio'
        verbose_name_plural = 'Consultorios'

    def __str__(self):
        return self.consultorios or f"Consultorio {self.id_consultorio}"


class Especialidad(models.Model):
    id_especialidad = models.BigAutoField(primary_key=True)
    tipo_especialidad = models.TextField(blank=True, null=True)
    id_sede = models.ForeignKey(Sede, on_delete=models.SET_NULL, null=True, blank=True, db_column='id_sede')
    status = models.BooleanField(null=True, blank=True, default=True)

    class Meta:
        managed = False
        db_table = 'especialidades'
        verbose_name = 'Especialidad'
        verbose_name_plural = 'Especialidades'

    def __str__(self):
        return self.tipo_especialidad or f"Especialidad {self.id_especialidad}"


class EspecialidadDoctor(models.Model):
    id_especialidad_doctor = models.BigAutoField(primary_key=True)
    id_especialidad = models.ForeignKey(
        Especialidad, on_delete=models.CASCADE,
        db_column='id_especialidad', null=True, blank=True
    )

    class Meta:
        managed = False
        db_table = 'especialidad_doctor'

    def __str__(self):
        return f"EspDoc {self.id_especialidad_doctor}"


class Horario(models.Model):
    id_horario = models.BigAutoField(primary_key=True)
    id_sede = models.ForeignKey(Sede, on_delete=models.SET_NULL, null=True, blank=True, db_column='id_sede')
    hora_inicio = models.TimeField(blank=True, null=True)
    hora_fin = models.TimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'horario'

    def __str__(self):
        return f"Horario {self.id_horario}: {self.hora_inicio} - {self.hora_fin}"


class PreciosServicios(models.Model):
    id_precios_servicios = models.BigAutoField(primary_key=True)
    id_sede = models.ForeignKey(Sede, on_delete=models.SET_NULL, null=True, blank=True, db_column='id_sede')
    id_doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True, db_column='id_doctor')
    precios = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'precios_servicios'

    def __str__(self):
        return f"Precio {self.id_precios_servicios}"


class ServicioEspecialidad(models.Model):
    id_servicios_especialidad = models.BigAutoField(primary_key=True)
    servicios = models.CharField(max_length=255, blank=True, null=True)
    id_especialidad = models.ForeignKey(
        Especialidad, on_delete=models.SET_NULL, null=True, blank=True, db_column='id_especialidad'
    )
    id_doctor = models.ForeignKey(
        Doctor, on_delete=models.SET_NULL, null=True, blank=True, db_column='id_doctor'
    )
    id_sede = models.ForeignKey(Sede, on_delete=models.SET_NULL, null=True, blank=True, db_column='id_sede')
    status = models.BooleanField(null=True, blank=True, default=True)
    id_precios_servicios = models.ForeignKey(
        PreciosServicios, on_delete=models.SET_NULL, null=True, blank=True,
        db_column='id_precios_servicios'
    )

    class Meta:
        managed = False
        db_table = 'servicios_especialidad'
        verbose_name = 'Servicio Especialidad'
        verbose_name_plural = 'Servicios Especialidad'

    def __str__(self):
        return self.servicios or f"Servicio {self.id_servicios_especialidad}"


class PagoCita(models.Model):
    id_pagos_cita = models.BigAutoField(primary_key=True)
    id_paciente = models.ForeignKey(
        PacienteDatosPersonales, on_delete=models.SET_NULL,
        null=True, blank=True, db_column='id_paciente'
    )
    monto_pagar = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    referencia_pago = models.CharField(max_length=255, blank=True, null=True)
    metodo_pago = models.CharField(max_length=100, blank=True, null=True)
    id_sede = models.ForeignKey(Sede, on_delete=models.SET_NULL, null=True, blank=True, db_column='id_sede')
    fecha_consulta = models.DateTimeField(blank=True, null=True)
    status = models.BooleanField(null=True, blank=True, default=True)
    id_cita = models.BigIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'pagos_cita'
        verbose_name = 'Pago de Cita'
        verbose_name_plural = 'Pagos de Citas'

    def __str__(self):
        return f"Pago {self.id_pagos_cita}"


class Cita(models.Model):
    id_citas = models.BigAutoField(primary_key=True)
    id_consultorio = models.ForeignKey(
        Consultorio, on_delete=models.SET_NULL, null=True, blank=True, db_column='id_consultorio'
    )
    id_doctor = models.ForeignKey(
        Doctor, on_delete=models.SET_NULL, null=True, blank=True, db_column='id_doctor'
    )
    id_especialidades = models.ForeignKey(
        Especialidad, on_delete=models.SET_NULL, null=True, blank=True, db_column='id_especialidades'
    )
    motivo = models.TextField(blank=True, null=True)
    id_paciente = models.ForeignKey(
        PacienteDatosPersonales, on_delete=models.CASCADE,
        null=True, blank=True, db_column='id_paciente'
    )
    id_sede = models.ForeignKey(Sede, on_delete=models.SET_NULL, null=True, blank=True, db_column='id_sede')
    id_pago_cita = models.ForeignKey(
        PagoCita, on_delete=models.SET_NULL, null=True, blank=True, db_column='id_pago_cita'
    )
    fecha_consulta = models.DateTimeField(blank=True, null=True)
    fecha_emision = models.DateTimeField(blank=True, null=True)
    status = models.BooleanField(null=True, blank=True, default=True)
    id_servicio_especialidad = models.ForeignKey(
        ServicioEspecialidad, on_delete=models.SET_NULL, null=True, blank=True,
        db_column='id_servicio_especialidad'
    )

    class Meta:
        managed = False
        db_table = 'citas'
        verbose_name = 'Cita'
        verbose_name_plural = 'Citas'
        ordering = ['-fecha_consulta']

    def __str__(self):
        return f"Cita {self.id_citas}"

    @property
    def estado(self):
        return 'activa' if self.status else 'cancelada'

    @property
    def fecha(self):
        return self.fecha_consulta.date() if self.fecha_consulta else None


# ── Modelos auxiliares ────────────────────────────────────────────────────────

class Alergias(models.Model):
    id_alergias = models.BigAutoField(primary_key=True)
    alergias = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'alergias'

    def __str__(self):
        return self.alergias or f"Alergia {self.id_alergias}"


class TipoSangre(models.Model):
    id_tipo_sangre = models.BigAutoField(primary_key=True)
    tipo_sangre = models.CharField(max_length=10, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tipo_sangre'

    def __str__(self):
        return self.tipo_sangre or f"Tipo {self.id_tipo_sangre}"


class Vacunas(models.Model):
    id_vacunas = models.BigAutoField(primary_key=True)
    vacunas_cumplidas = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'vacunas'

    def __str__(self):
        return self.vacunas_cumplidas or f"Vacuna {self.id_vacunas}"


class HistorialMedicoPaciente(models.Model):
    id_historial_medico = models.BigAutoField(primary_key=True)
    id_alergias = models.ForeignKey(
        Alergias, on_delete=models.SET_NULL, null=True, blank=True, db_column='id_alergias'
    )
    id_tipo_sangre = models.ForeignKey(
        TipoSangre, on_delete=models.SET_NULL, null=True, blank=True, db_column='id_tipo_sangre'
    )
    id_vacunas = models.ForeignKey(
        Vacunas, on_delete=models.SET_NULL, null=True, blank=True, db_column='id_vacunas'
    )
    id_paciente = models.ForeignKey(
        PacienteDatosPersonales, on_delete=models.CASCADE,
        null=True, blank=True, db_column='id_paciente'
    )
    id_enfermedades = models.BigIntegerField(blank=True, null=True)
    id_sede = models.ForeignKey(Sede, on_delete=models.SET_NULL, null=True, blank=True, db_column='id_sede')
    status = models.BooleanField(null=True, blank=True, default=True)

    class Meta:
        managed = False
        db_table = 'historial_medico_paciente'

    def __str__(self):
        return f"Historial {self.id_historial_medico}"
