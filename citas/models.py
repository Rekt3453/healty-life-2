from django.db import models
from django.conf import settings

class Sede(models.Model):
    nombre = models.CharField(max_length=100)
    direccion = models.CharField(max_length=255)
    telefono = models.CharField(max_length=20)
    
    def __str__(self):
        return self.nombre

class Especialidad(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    
    def __str__(self):
        return self.nombre

class Servicio(models.Model):
    nombre = models.CharField(max_length=100)
    especialidad = models.ForeignKey(Especialidad, on_delete=models.CASCADE)
    sede = models.ForeignKey(Sede, on_delete=models.CASCADE)
    precio = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    def __str__(self):
        return f"{self.nombre} - {self.sede.nombre}"

class HorarioMedico(models.Model):
    DIAS_SEMANA = [
        ('lunes', 'Lunes'),
        ('martes', 'Martes'),
        ('miercoles', 'Miércoles'),
        ('jueves', 'Jueves'),
        ('viernes', 'Viernes'),
        ('sabado', 'Sábado'),
        ('domingo', 'Domingo'),
    ]
    
    medico = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='horarios')
    dia_semana = models.CharField(max_length=10, choices=DIAS_SEMANA)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    activo = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['medico', 'dia_semana', 'hora_inicio']
    
    def __str__(self):
        return f"{self.medico.username} - {self.get_dia_semana_display()} {self.hora_inicio} a {self.hora_fin}"

class Cita(models.Model):
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('asignada', 'Asignada'),
        ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada'),
        ('cancelada', 'Cancelada'),
        ('completada', 'Completada'),
    ]
    
    paciente = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='citas_paciente')
    medico = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='citas_medico', null=True, blank=True)
    especialidad = models.ForeignKey(Especialidad, on_delete=models.CASCADE, default=1)
    servicio = models.ForeignKey(Servicio, on_delete=models.CASCADE, null=True, blank=True)
    sede = models.ForeignKey(Sede, on_delete=models.CASCADE, null=True, blank=True)
    fecha = models.DateField()
    hora_solicitada = models.TimeField()  # Hora solicitada por el paciente
    hora_confirmada = models.TimeField(null=True, blank=True)  # Hora confirmada por el médico
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    motivo = models.TextField(blank=True)
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_atencion = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Cita {self.id} - {self.paciente.username} - {self.estado}"
    
    def esta_disponible(self):
        """Verifica si el médico tiene disponibilidad para esta fecha y hora"""
        if not self.medico or not self.hora_confirmada:
            return False
            
        # Obtener el día de la semana de la fecha
        dias_semana = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
        dia_semana = dias_semana[self.fecha.weekday()]
        
        # Buscar horario del médico para ese día
        try:
            horario = HorarioMedico.objects.get(
                medico=self.medico,
                dia_semana=dia_semana,
                activo=True,
                hora_inicio__lte=self.hora_confirmada,
                hora_fin__gt=self.hora_confirmada
            )
            
            # Verificar que no tenga otra cita a la misma hora
            citas_existentes = Cita.objects.filter(
                medico=self.medico,
                fecha=self.fecha,
                hora_confirmada=self.hora_confirmada,
                estado__in=['asignada', 'aprobada', 'completada']
            ).exclude(id=self.id)
            
            return not citas_existentes.exists()
            
        except HorarioMedico.DoesNotExist:
            return False
