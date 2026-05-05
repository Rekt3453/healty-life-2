from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from usuarios.models import UserProfile, MedicoProfile, PacienteProfile, Sede, Especialidad
from usuarios.managers import CitaManager
from decimal import Decimal

class Servicio(models.Model):
    """Servicios médicos que se pueden ofrecer"""
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    especialidad = models.ForeignKey(Especialidad, on_delete=models.CASCADE)
    precio_base = models.DecimalField(max_digits=10, decimal_places=2)
    duracion_minutos = models.PositiveIntegerField(default=30, help_text="Duración en minutos")
    activo = models.BooleanField(default=True)
    
    class Meta:
        managed = False
        db_table = 'citas_servicio'
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.nombre} - {self.especialidad.nombre}"

class DisponibilidadMedica(models.Model):
    """Horarios de disponibilidad de los médicos"""
    DIAS_SEMANA = [
        (1, 'Lunes'),
        (2, 'Martes'),
        (3, 'Miércoles'),
        (4, 'Jueves'),
        (5, 'Viernes'),
        (6, 'Sábado'),
        (7, 'Domingo'),
    ]
    
    medico = models.ForeignKey(MedicoProfile, on_delete=models.CASCADE)
    dia_semana = models.PositiveIntegerField(choices=DIAS_SEMANA)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    activo = models.BooleanField(default=True)
    
    class Meta:
        managed = False
        db_table = 'citas_disponibilidadmedica'
        ordering = ['dia_semana', 'hora_inicio']
        unique_together = ['medico', 'dia_semana', 'hora_inicio']
    
    def __str__(self):
        return f"{self.medico} - {self.get_dia_semana_display()} {self.hora_inicio} a {self.hora_fin}"

class Cita(models.Model):
    """Citas médicas agendadas"""
    ESTADOS_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('en_progreso', 'En Progreso'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada'),
        ('no_asistio', 'No Asistió'),
    ]
    
    paciente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='citas_paciente')
    medico = models.ForeignKey(MedicoProfile, on_delete=models.CASCADE, related_name='citas_medico')
    sede = models.ForeignKey(Sede, on_delete=models.CASCADE)
    servicio = models.ForeignKey(Servicio, on_delete=models.CASCADE)
    fecha_hora = models.DateTimeField()
    estado = models.CharField(max_length=20, choices=ESTADOS_CHOICES, default='pendiente')
    notas_paciente = models.TextField(blank=True, help_text="Notas del paciente para la cita")
    notas_medico = models.TextField(blank=True, help_text="Notas del médico después de la cita")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    motivo_cancelacion = models.TextField(blank=True)
    
    objects = CitaManager()
    
    class Meta:
        managed = False
        db_table = 'citas_cita'
        ordering = ['fecha_hora']
    
    def __str__(self):
        return f"Cita {self.id} - {self.paciente.get_full_name()} con Dr. {self.medico} - {self.fecha_hora}"
    
    @property
    def puede_cancelar(self):
        """Verificar si se puede cancelar (mínimo 2 horas antes)"""
        if self.estado in ['completada', 'cancelada', 'en_progreso']:
            return False
        tiempo_restante = self.fecha_hora - timezone.now()
        return tiempo_restante.total_seconds() > 7200  # 2 horas en segundos
    
    @property
    def precio_total(self):
        """Calcular precio total de la cita"""
        return self.servicio.precio_base
    
    def get_absolute_url(self):
        return reverse('detalle_cita', kwargs={'pk': self.pk})

class Factura(models.Model):
    """Facturas asociadas a las citas"""
    ESTADOS_CHOICES = [
        ('pendiente', 'Pendiente de Pago'),
        ('pagada', 'Pagada'),
        ('vencida', 'Vencida'),
        ('cancelada', 'Cancelada'),
    ]
    
    cita = models.OneToOneField(Cita, on_delete=models.CASCADE, related_name='factura')
    numero_factura = models.CharField(max_length=50, unique=True)
    fecha_emision = models.DateTimeField(auto_now_add=True)
    fecha_vencimiento = models.DateTimeField()
    monto_total = models.DecimalField(max_digits=10, decimal_places=2)
    monto_pagado = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estado = models.CharField(max_length=20, choices=ESTADOS_CHOICES, default='pendiente')
    metodo_pago = models.CharField(max_length=50, blank=True, help_text="Método de pago utilizado")
    referencia_pago = models.CharField(max_length=100, blank=True, help_text="Referencia de pago")
    
    class Meta:
        managed = False
        db_table = 'citas_factura'
        ordering = ['-fecha_emision']
    
    def __str__(self):
        return f"Factura {self.numero_factura} - {self.cita}"
    
    @property
    def saldo_pendiente(self):
        return self.monto_total - self.monto_pagado
    
    @property
    def esta_pagada(self):
        return self.monto_pagado >= self.monto_total
    
    def save(self, *args, **kwargs):
        if not self.numero_factura:
            import uuid
            self.numero_factura = f"FAC-{uuid.uuid4().hex[:8].upper()}"
        
        if not self.fecha_vencimiento:
            from datetime import timedelta
            self.fecha_vencimiento = timezone.now() + timedelta(days=3)
        
        super().save(*args, **kwargs)

class HistoriaClinica(models.Model):
    """Historias clínicas de los pacientes"""
    paciente = models.ForeignKey(PacienteProfile, on_delete=models.CASCADE, related_name='historias')
    medico = models.ForeignKey(MedicoProfile, on_delete=models.CASCADE)
    cita = models.OneToOneField(Cita, on_delete=models.CASCADE, related_name='historia_clinica')
    fecha_consulta = models.DateTimeField(auto_now_add=True)
    
    # Síntomas y diagnóstico
    motivo_consulta = models.TextField(help_text="Motivo principal de la consulta")
    sintomas = models.TextField(help_text="Síntomas descritos por el paciente")
    diagnostico = models.TextField(help_text="Diagnóstico del médico")
    
    # Tratamiento
    tratamiento = models.TextField(blank=True, help_text="Plan de tratamiento")
    medicamentos_recetados = models.TextField(blank=True, help_text="Medicamentos recetados")
    dosis_medicamentos = models.TextField(blank=True, help_text="Dosis y frecuencia")
    
    # Estudios y reposo
    estudios_solicitados = models.TextField(blank=True, help_text="Estudios de laboratorio o imagenología")
    dias_reposo = models.PositiveIntegerField(default=0, help_text="Días de reposo recomendados")
    indicaciones_reposo = models.TextField(blank=True, help_text="Indicaciones específicas del reposo")
    
    # Órdenes médicas
    ordenes_medicas = models.TextField(blank=True, help_text="Órdenes médicas especiales")
    proxima_cita_sugerida = models.DateField(null=True, blank=True, help_text="Fecha sugerida para próxima consulta")
    
    # Firma y validación
    firma_medico = models.BooleanField(default=False, help_text="Firma digital del médico")
    observaciones = models.TextField(blank=True, help_text="Observaciones adicionales")
    
    class Meta:
        managed = False
        db_table = 'citas_historiaclinica'
        ordering = ['-fecha_consulta']
        verbose_name = 'Historia Clínica'
        verbose_name_plural = 'Historias Clínicas'
    
    def __str__(self):
        return f"Historia Clínica - {self.paciente.user_profile.nombre_completo} - {self.fecha_consulta.strftime('%d/%m/%Y')}"

class Reporte(models.Model):
    """Reportes generados por el sistema"""
    TIPOS_REPORTES = [
        ('citas_diarias', 'Citas Diarias'),
        ('citas_semanales', 'Citas Semanales'),
        ('citas_mensuales', 'Citas Mensuales'),
        ('facturacion_mensual', 'Facturación Mensual'),
        ('pacientes_nuevos', 'Pacientes Nuevos'),
        ('medicos_activos', 'Médicos Activos'),
        ('rendimiento_sede', 'Rendimiento por Sede'),
    ]
    
    tipo = models.CharField(max_length=30, choices=TIPOS_REPORTES)
    fecha_generacion = models.DateTimeField(auto_now_add=True)
    fecha_inicio = models.DateField(help_text="Fecha de inicio del período")
    fecha_fin = models.DateField(help_text="Fecha de fin del período")
    sede = models.ForeignKey(Sede, on_delete=models.CASCADE, null=True, blank=True)
    archivo_pdf = models.FileField(upload_to='reportes/', null=True, blank=True)
    datos_json = models.JSONField(default=dict, help_text="Datos del reporte en formato JSON")
    generado_por = models.ForeignKey(User, on_delete=models.CASCADE)
    
    class Meta:
        managed = False
        db_table = 'citas_reporte'
        ordering = ['-fecha_generacion']
    
    def __str__(self):
        return f"Reporte {self.get_tipo_display()} - {self.fecha_generacion.strftime('%d/%m/%Y')}"
