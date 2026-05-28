from django.db import models
from usuarios.models import Sede, Doctor, PacienteDatosPersonales, CentroMedico, PacienteEspecial


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
    # Nuevo campo agregado al esquema: categoriza la especialidad en Pediatría, Adultos o General
    clasificacion_especialidad = models.TextField(blank=True, null=True, db_column='clasificacion_especialidad')

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
        if self.id_especialidad and self.id_especialidad.tipo_especialidad:
            return self.id_especialidad.tipo_especialidad
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

    ESTADO_PENDIENTE = 'pendiente'
    ESTADO_APROBADO  = 'aprobado'
    ESTADO_RECHAZADO = 'rechazado'
    ESTADOS_PAGO = [
        (ESTADO_PENDIENTE, 'Pendiente'),
        (ESTADO_APROBADO,  'Aprobado'),
        (ESTADO_RECHAZADO, 'Rechazado'),
    ]
    estado_pago = models.CharField(
        max_length=20, choices=ESTADOS_PAGO,
        default=ESTADO_PENDIENTE, blank=True, null=True,
    )

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

    ESTADO_SOLICITADA    = 'solicitada'
    ESTADO_APROBADA      = 'aprobada'
    ESTADO_PAGO_PENDIENTE = 'pago_pendiente'
    ESTADO_CONFIRMADA    = 'confirmada'
    ESTADO_EN_CONSULTA   = 'en_consulta'
    ESTADO_ATENDIDA      = 'atendida'
    ESTADO_CANCELADA     = 'cancelada'
    ESTADO_RECHAZADA     = 'rechazada'
    ESTADO_NO_ASISTIO    = 'no_asistio'

    ESTADOS = [
        (ESTADO_SOLICITADA,     'Solicitada'),
        (ESTADO_APROBADA,       'Aprobada'),
        (ESTADO_PAGO_PENDIENTE, 'Pago Pendiente'),
        (ESTADO_CONFIRMADA,     'Confirmada'),
        (ESTADO_EN_CONSULTA,    'En Consulta'),
        (ESTADO_ATENDIDA,       'Atendida'),
        (ESTADO_CANCELADA,      'Cancelada'),
        (ESTADO_RECHAZADA,      'Rechazada'),
        (ESTADO_NO_ASISTIO,     'No Asistió'),
    ]

    estado = models.CharField(
        max_length=30, choices=ESTADOS,
        default=ESTADO_PAGO_PENDIENTE, blank=True, null=True,
    )
    motivo_cancelacion = models.TextField(blank=True, null=True)
    fecha_cancelacion  = models.DateTimeField(blank=True, null=True)
    cancelada_por      = models.CharField(max_length=100, blank=True, null=True)
    fecha_atencion     = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'citas'
        verbose_name = 'Cita'
        verbose_name_plural = 'Citas'
        ordering = ['-fecha_consulta']

    def __str__(self):
        return f"Cita {self.id_citas}"

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


class Enfermedades(models.Model):
    """Catálogo de enfermedades → tabla enfermedades"""
    id_enfermedades = models.BigAutoField(primary_key=True)
    enfermedades = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'enfermedades'

    def __str__(self):
        return self.enfermedades or f"Enfermedad {self.id_enfermedades}"


class HistorialMedicoPaciente(models.Model):
    """
    Historial médico de un paciente adulto o menor.

    Regla del esquema: solo uno de id_paciente ó id_paciente_especial
    tendrá valor; el otro será NULL.
    Alergias, vacunas y enfermedades se relacionan mediante tablas
    intermedias (M2M) definidas más abajo.
    """
    id_historial_medico = models.BigAutoField(primary_key=True)
    # Tipo de sangre: selección única, FK directa
    id_tipo_sangre = models.ForeignKey(
        TipoSangre, on_delete=models.SET_NULL, null=True, blank=True, db_column='id_tipo_sangre'
    )
    # FK al paciente adulto (NULL cuando el historial pertenece a un menor)
    id_paciente = models.ForeignKey(
        PacienteDatosPersonales, on_delete=models.CASCADE,
        null=True, blank=True, db_column='id_paciente'
    )
    # FK al paciente especial / menor (NULL cuando el historial pertenece a un adulto)
    id_paciente_especial = models.ForeignKey(
        PacienteEspecial, on_delete=models.CASCADE,
        null=True, blank=True, db_column='id_paciente_especial'
    )
    id_sede = models.ForeignKey(Sede, on_delete=models.SET_NULL, null=True, blank=True, db_column='id_sede')
    status = models.BooleanField(null=True, blank=True, default=True)
    # Relaciones M2M a catálogos mediante tablas intermedias existentes en la BD
    alergias = models.ManyToManyField(
        Alergias, through='HistorialAlergias', related_name='historiales', blank=True
    )
    vacunas = models.ManyToManyField(
        Vacunas, through='HistoriaVacunas', related_name='historiales', blank=True
    )
    enfermedades = models.ManyToManyField(
        Enfermedades, through='HistorialEnfermedades', related_name='historiales', blank=True
    )

    class Meta:
        managed = False
        db_table = 'historial_medico_paciente'

    def __str__(self):
        return f"Historial {self.id_historial_medico}"


class HistorialAlergias(models.Model):
    """Tabla intermedia historial_alergias → relaciona historial ↔ alergias (M2M)."""
    id_historial_alergias = models.BigAutoField(primary_key=True)
    id_alergias = models.ForeignKey(
        Alergias, on_delete=models.CASCADE, db_column='id_alergias'
    )
    id_historial_medico = models.ForeignKey(
        HistorialMedicoPaciente, on_delete=models.CASCADE,
        null=True, blank=True, db_column='id_historial_medico'
    )

    class Meta:
        managed = False
        db_table = 'historial_alergias'


class HistorialEnfermedades(models.Model):
    """Tabla intermedia historial_enfermedades → relaciona historial ↔ enfermedades (M2M)."""
    id_historial_enfermedades = models.BigAutoField(primary_key=True)
    id_enfermedades = models.ForeignKey(
        Enfermedades, on_delete=models.CASCADE, db_column='id_enfermedades'
    )
    id_historial_medico = models.ForeignKey(
        HistorialMedicoPaciente, on_delete=models.CASCADE,
        null=True, blank=True, db_column='id_historial_medico'
    )

    class Meta:
        managed = False
        db_table = 'historial_enfermedades'


class HistoriaVacunas(models.Model):
    """Tabla intermedia historia_vacunas → relaciona historial ↔ vacunas (M2M)."""
    id_historial_vacunas = models.BigAutoField(primary_key=True)
    id_vacunas = models.ForeignKey(
        Vacunas, on_delete=models.CASCADE, db_column='id_vacunas'
    )
    id_historial_medico = models.ForeignKey(
        HistorialMedicoPaciente, on_delete=models.CASCADE,
        null=True, blank=True, db_column='id_historial_medico'
    )

    class Meta:
        managed = False
        db_table = 'historia_vacunas'


# ── Modelos de Recetas ────────────────────────────────────────────────────────
# Cada tabla hija almacena un único apartado de la receta médica.
# managed = False garantiza que no se generen migraciones.

class RecipesOrdenesMedicas(models.Model):
    """Órdenes médicas: radiografías, tomografías, etc. → tabla recipes_ordenes_medicas"""
    id_recipe_ordenes = models.BigAutoField(primary_key=True)
    ordenes_medicas = models.CharField(max_length=5000, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'recipes_ordenes_medicas'

    def __str__(self):
        return f"Órdenes {self.id_recipe_ordenes}"


class RecipeTratamiento(models.Model):
    """Tratamiento prescrito: medicamentos y posología → tabla recipe_tratamiento"""
    id_recipe_tratamiento = models.BigAutoField(primary_key=True)
    tratamiento_necesario = models.CharField(max_length=5000, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'recipe_tratamiento'

    def __str__(self):
        return f"Tratamiento {self.id_recipe_tratamiento}"


class RecipeReposo(models.Model):
    """Indicación de reposo y días → tabla recipe_reposo"""
    id_recipe_reposo = models.BigAutoField(primary_key=True)
    reposo = models.CharField(max_length=5000, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'recipe_reposo'

    def __str__(self):
        return f"Reposo {self.id_recipe_reposo}"


class RecipeMedicamentosEspeciales(models.Model):
    """Medicamentos con prescripción especial/controlada → tabla recipe_medicamentos_especiales"""
    id_recipe_medicamento_especiales = models.BigAutoField(primary_key=True)
    medicamentos_especiales = models.CharField(max_length=5000, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'recipe_medicamentos_especiales'

    def __str__(self):
        return f"Med. Especiales {self.id_recipe_medicamento_especiales}"


class RecipeEstudios(models.Model):
    """Estudios de laboratorio: sangre, orina, heces, etc. → tabla recipe_estudios"""
    id_recipe_estudios = models.BigAutoField(primary_key=True)
    estudios_realizar = models.CharField(max_length=5000, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'recipe_estudios'

    def __str__(self):
        return f"Estudios {self.id_recipe_estudios}"


class RecipeDiagnostico(models.Model):
    """Diagnóstico general del médico → tabla recipe_diagnostico"""
    id_recipe_diagnostico = models.BigAutoField(primary_key=True)
    diagnostico = models.CharField(max_length=5000, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'recipe_diagnostico'

    def __str__(self):
        return f"Diagnóstico {self.id_recipe_diagnostico}"


class Recipe(models.Model):
    """
    Registro principal de la receta médica.
    Relaciona al doctor, la cita, el paciente y la sede con todos los
    apartados de la receta (FK a cada tabla hija).
    → tabla recipes
    """
    id_recipes = models.BigAutoField(primary_key=True)
    id_doctor = models.ForeignKey(
        Doctor, on_delete=models.SET_NULL, null=True, blank=True, db_column='id_doctor'
    )
    id_cita = models.ForeignKey(
        Cita, on_delete=models.SET_NULL, null=True, blank=True, db_column='id_cita'
    )
    id_paciente = models.ForeignKey(
        PacienteDatosPersonales, on_delete=models.SET_NULL,
        null=True, blank=True, db_column='id_paciente'
    )
    # FK a los apartados de la receta (db_column respeta los nombres mixtos del esquema)
    id_Recipe_estudios = models.ForeignKey(
        RecipeEstudios, on_delete=models.SET_NULL, null=True, blank=True,
        db_column='id_Recipe_estudios'
    )
    id_Recipe_medicamentos_especiales = models.ForeignKey(
        RecipeMedicamentosEspeciales, on_delete=models.SET_NULL, null=True, blank=True,
        db_column='id_Recipe_medicamentos_especiales'
    )
    id_Recipe_tratamiento = models.ForeignKey(
        RecipeTratamiento, on_delete=models.SET_NULL, null=True, blank=True,
        db_column='id_Recipe_tratamiento'
    )
    id_Recipe_reposo = models.ForeignKey(
        RecipeReposo, on_delete=models.SET_NULL, null=True, blank=True,
        db_column='id_Recipe_reposo'
    )
    id_Recipes_ordenes_medicas = models.ForeignKey(
        RecipesOrdenesMedicas, on_delete=models.SET_NULL, null=True, blank=True,
        db_column='id_Recipes_ordenes_medicas'
    )
    id_Recipe_diagnostico = models.ForeignKey(
        RecipeDiagnostico, on_delete=models.SET_NULL, null=True, blank=True,
        db_column='id_Recipe_diagnostico'
    )
    id_sede = models.ForeignKey(
        Sede, on_delete=models.SET_NULL, null=True, blank=True, db_column='id_sede'
    )
    status = models.BooleanField(null=True, blank=True, default=True)
    fecha_emision = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'recipes'
        verbose_name = 'Receta'
        verbose_name_plural = 'Recetas'
        ordering = ['-fecha_emision']

    def __str__(self):
        return f"Receta #{self.id_recipes}"


class ConsultaMedica(models.Model):
    ESTADO_ABIERTA = "abierta"
    ESTADO_CERRADA = "cerrada"
    ESTADO_ANULADA = "anulada"

    ESTADOS = [
        (ESTADO_ABIERTA, "Abierta"),
        (ESTADO_CERRADA, "Cerrada"),
        (ESTADO_ANULADA, "Anulada"),
    ]

    id_consulta = models.BigAutoField(primary_key=True)
    id_cita = models.OneToOneField(
        "Cita",
        on_delete=models.PROTECT,
        db_column="id_cita",
        related_name="consulta_medica",
    )
    motivo_consulta = models.TextField()
    enfermedad_actual = models.TextField(blank=True, null=True)
    antecedentes = models.TextField(blank=True, null=True)
    examen_fisico = models.TextField(blank=True, null=True)
    diagnostico = models.TextField(blank=True, null=True)
    plan_tratamiento = models.TextField(blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_cierre = models.DateTimeField(blank=True, null=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default=ESTADO_ABIERTA)

    class Meta:
        managed = False
        db_table = "consultas_medicas"

    def __str__(self):
        return f"Consulta #{self.id_consulta} - {self.get_estado_display()}"


class Factura(models.Model):
    ESTADO_BORRADOR = "borrador"
    ESTADO_EMITIDA  = "emitida"
    ESTADO_PAGADA   = "pagada"
    ESTADO_ANULADA  = "anulada"

    ESTADOS = [
        (ESTADO_BORRADOR, "Borrador"),
        (ESTADO_EMITIDA,  "Emitida"),
        (ESTADO_PAGADA,   "Pagada"),
        (ESTADO_ANULADA,  "Anulada"),
    ]

    id_factura  = models.BigAutoField(primary_key=True)
    numero      = models.CharField(max_length=50, unique=True)
    id_cita     = models.OneToOneField(
        "Cita",
        on_delete=models.PROTECT,
        db_column="id_cita",
        related_name="factura",
    )
    id_pago_cita = models.ForeignKey(
        "PagoCita",
        on_delete=models.PROTECT,
        db_column="id_pago_cita",
    )
    descripcion      = models.CharField(max_length=255)
    subtotal         = models.DecimalField(max_digits=12, decimal_places=2)
    impuesto         = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total            = models.DecimalField(max_digits=12, decimal_places=2)
    estado           = models.CharField(max_length=20, choices=ESTADOS, default=ESTADO_EMITIDA)
    fecha_emision    = models.DateTimeField(auto_now_add=True)
    fecha_anulacion  = models.DateTimeField(blank=True, null=True)
    motivo_anulacion = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "facturas"

    def __str__(self):
        return f"Factura {self.numero} — {self.get_estado_display()}"
