from django import forms
from django.contrib.auth.models import User
from .models import Cita, Servicio, Sede, HorarioMedico, Especialidad

class SolicitudCitaForm(forms.ModelForm):
    class Meta:
        model = Cita
        fields = ['especialidad', 'fecha', 'hora_solicitada', 'motivo']
        widgets = {
            'especialidad': forms.Select(attrs={'class': 'form-select'}),
            'fecha': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'hora_solicitada': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'motivo': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe el motivo de tu consulta...'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar especialidades que tengan médicos disponibles
        especialidades_con_medicos = Especialidad.objects.filter(
            servicio__isnull=False
        ).distinct()
        self.fields['especialidad'].queryset = especialidades_con_medicos

class AsignarMedicoForm(forms.Form):
    medico = forms.ModelChoiceField(
        queryset=None,
        empty_label="Seleccionar médico",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from usuarios.models import UserProfile
        # Obtener usuarios que son médicos
        medicos_user = User.objects.filter(userprofile__rol='medico')
        self.fields['medico'].queryset = medicos_user

class HorarioMedicoForm(forms.ModelForm):
    class Meta:
        model = HorarioMedico
        fields = ['dia_semana', 'hora_inicio', 'hora_fin', 'activo']
        widgets = {
            'dia_semana': forms.Select(attrs={'class': 'form-select'}),
            'hora_inicio': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'hora_fin': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class ConfirmarCitaForm(forms.Form):
    hora_confirmada = forms.TimeField(
        label="Hora de la cita",
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
        required=False
    )
    
    def __init__(self, *args, **kwargs):
        cita = kwargs.pop('cita', None)
        super().__init__(*args, **kwargs)
        if cita and cita.medico:
            self.fields['horarios_disponibles'] = forms.ChoiceField(
                label="Horarios disponibles",
                choices=self._get_horarios_disponibles(cita),
                widget=forms.Select(attrs={'class': 'form-select'}),
                required=False
            )
    
    def _get_horarios_disponibles(self, cita):
        """Obtiene horarios disponibles para el médico en la fecha de la cita"""
        if not cita.medico or not cita.fecha:
            return [('', 'No hay horarios disponibles')]
        
        # Obtener el día de la semana
        dias_semana = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
        dia_semana = dias_semana[cita.fecha.weekday()]
        
        # Obtener horarios del médico para ese día
        horarios = HorarioMedico.objects.filter(
            medico=cita.medico,
            dia_semana=dia_semana,
            activo=True
        )
        
        # Generar opciones de horas (cada 30 minutos)
        opciones = [('', 'Seleccionar hora')]
        for horario in horarios:
            hora_actual = horario.hora_inicio
            while hora_actual < horario.hora_fin:
                # Verificar si esta hora está disponible
                if not self._esta_ocupada(cita.medico, cita.fecha, hora_actual):
                    opciones.append((hora_actual.strftime('%H:%M'), hora_actual.strftime('%H:%M')))
                
                # Avanzar 30 minutos
                from datetime import datetime, timedelta
                hora_actual = (datetime.combine(datetime.today(), hora_actual) + timedelta(minutes=30)).time()
        
        return opciones
    
    def _esta_ocupada(self, medico, fecha, hora):
        """Verifica si el médico ya tiene una cita a esa hora"""
        return Cita.objects.filter(
            medico=medico,
            fecha=fecha,
            hora_confirmada=hora,
            estado__in=['asignada', 'aprobada', 'completada']
        ).exists()

class HorarioSelectorForm(forms.Form):
    """Formulario para seleccionar horarios laborables disponibles"""
    fecha = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    especialidad = forms.ModelChoiceField(
        queryset=Especialidad.objects.all(),
        empty_label="Seleccionar especialidad",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Agregar campo dinámico de horarios cuando se selecciona fecha y especialidad
        self.fields['horario_disponible'] = forms.ChoiceField(
            choices=[('', 'Selecciona fecha y especialidad primero')],
            widget=forms.Select(attrs={'class': 'form-select'}),
            required=False
        )
    
    def get_horarios_disponibles(self, fecha, especialidad):
        """Obtiene horarios disponibles para una fecha y especialidad"""
        if not fecha or not especialidad:
            return [('', 'Selecciona fecha y especialidad primero')]
        
        # Obtener médicos de esa especialidad con horarios configurados
        from usuarios.models import UserProfile
        medicos = User.objects.filter(
            userprofile__rol='medico',
            horarios__activo=True
        ).distinct()
        
        # Obtener día de la semana
        dias_semana = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
        dia_semana = dias_semana[fecha.weekday()]
        
        # Obtener todos los horarios disponibles para ese día
        horarios_disponibles = []
        for medico in medicos:
            horarios = HorarioMedico.objects.filter(
                medico=medico,
                dia_semana=dia_semana,
                activo=True
            )
            
            for horario in horarios:
                hora_actual = horario.hora_inicio
                while hora_actual < horario.hora_fin:
                    # Verificar disponibilidad
                    if not self._esta_ocupada_general(medico, fecha, hora_actual):
                        horarios_disponibles.append((
                            f"{medico.id}_{hora_actual.strftime('%H:%M')}",
                            f"{medico.username} - {hora_actual.strftime('%H:%M')}"
                        ))
                    
                    # Avanzar 30 minutos
                    from datetime import datetime, timedelta
                    hora_actual = (datetime.combine(datetime.today(), hora_actual) + timedelta(minutes=30)).time()
        
        if not horarios_disponibles:
            return [('', 'No hay horarios disponibles')]
        
        return [('', 'Seleccionar horario')] + sorted(horarios_disponibles, key=lambda x: x[1])
    
    def _esta_ocupada_general(self, medico, fecha, hora):
        """Verifica si el médico ya tiene una cita a esa hora"""
        return Cita.objects.filter(
            medico=medico,
            fecha=fecha,
            hora_confirmada=hora,
            estado__in=['asignada', 'aprobada', 'completada']
        ).exists()
