from django import forms
from django.forms import inlineformset_factory
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Submit, Field, HTML, Row, Column
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Cita, Servicio, HistoriaClinica
from usuarios.models import MedicoProfile, Sede, Especialidad

class AgendarCitaForm(forms.ModelForm):
    """Formulario para agendar nuevas citas"""
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user and hasattr(user, 'userprofile'):
            sede_paciente = user.userprofile.sede
            # Filtrar por sede del paciente
            self.fields['sede'].queryset = Sede.objects.filter(activa=True)
            if sede_paciente:
                self.fields['sede'].initial = sede_paciente
        
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Row(
                    Column('sede', css_class='form-group col-md-6 mb-0'),
                    Column('especialidad', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                Row(
                    Column('medico', css_class='form-group col-md-6 mb-0'),
                    Column('servicio', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                Row(
                    Column('fecha', css_class='form-group col-md-6 mb-0'),
                    Column('hora', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                'notas_paciente',
                Submit('submit', 'Agendar Cita', css_class='btn btn-primary btn-lg w-100'),
                css_class='space-y-4'
            )
        )
    
    especialidad = forms.ModelChoiceField(
        queryset=Especialidad.objects.filter(activa=True),
        empty_label="Seleccione especialidad",
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    medico = forms.ModelChoiceField(
        queryset=MedicoProfile.objects.none(),
        empty_label="Primero seleccione especialidad y sede",
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    servicio = forms.ModelChoiceField(
        queryset=Servicio.objects.none(),
        empty_label="Primero seleccione especialidad",
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    fecha = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=True
    )
    
    hora = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        required=True
    )
    
    notas_paciente = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Describe tus síntomas o motivo de consulta...'}),
        required=False
    )
    
    class Meta:
        model = Cita
        fields = ['sede', 'notas_paciente']
    
    def clean_fecha(self):
        fecha = self.cleaned_data.get('fecha')
        if fecha and fecha < timezone.now().date():
            raise forms.ValidationError("No se pueden agendar citas en fechas pasadas.")
        return fecha
    
    def clean(self):
        cleaned_data = super().clean()
        sede = cleaned_data.get('sede')
        especialidad = cleaned_data.get('especialidad')
        medico = cleaned_data.get('medico')
        servicio = cleaned_data.get('servicio')
        fecha = cleaned_data.get('fecha')
        hora = cleaned_data.get('hora')
        
        # Validar que todos los campos estén presentes
        if not all([sede, especialidad, medico, servicio, fecha, hora]):
            return cleaned_data
        
        # Combinar fecha y hora
        fecha_hora = datetime.combine(fecha, hora)
        
        # Validar que no sea en el pasado
        if fecha_hora < timezone.now():
            raise forms.ValidationError("No se pueden agendar citas en el pasado.")
        
        # Validar disponibilidad del médico
        if medico:
            # Verificar que el médico trabaje ese día y hora
            dia_semana = fecha_hora.weekday() + 1  # Django: 0=Lunes, nuestro modelo: 1=Lunes
            if not DisponibilidadMedica.objects.filter(
                medico=medico,
                dia_semana=dia_semana,
                hora_inicio__lte=hora,
                hora_fin__gte=hora,
                activo=True
            ).exists():
                raise forms.ValidationError("El médico no está disponible en este horario.")
            
            # Verificar que no tenga otra cita a la misma hora
            if Cita.objects.filter(
                medico=medico,
                fecha_hora=fecha_hora,
                estado__in=['pendiente', 'confirmada']
            ).exists():
                raise forms.ValidationError("El médico ya tiene una cita agendada a esta hora.")
        
        return cleaned_data

class CancelarCitaForm(forms.ModelForm):
    """Formulario para cancelar citas"""
    
    class Meta:
        model = Cita
        fields = ['motivo_cancelacion']
        widgets = {
            'motivo_cancelacion': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control',
                'placeholder': 'Describe el motivo de la cancelación...'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'motivo_cancelacion',
            Submit('submit', 'Cancelar Cita', css_class='btn btn-danger'),
            HTML('<a href="javascript:history.back()" class="btn btn-secondary">Volver</a>')
        )

class HistoriaClinicaForm(forms.ModelForm):
    """Formulario para historias clínicas"""
    
    class Meta:
        model = HistoriaClinica
        fields = [
            'motivo_consulta', 'sintomas', 'diagnostico', 'tratamiento',
            'medicamentos_recetados', 'dosis_medicamentos', 'estudios_solicitados',
            'dias_reposo', 'indicaciones_reposo', 'ordenes_medicas',
            'proxima_cita_sugerida', 'observaciones'
        ]
        widgets = {
            'motivo_consulta': forms.TextInput(attrs={'class': 'form-control'}),
            'sintomas': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'diagnostico': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'tratamiento': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'medicamentos_recetados': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'dosis_medicamentos': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'estudios_solicitados': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'indicaciones_reposo': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'ordenes_medicas': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'proxima_cita_sugerida': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'observaciones': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                HTML('<h4 class="mb-3">Información de la Consulta</h4>'),
                Row(
                    Column('motivo_consulta', css_class='form-group col-md-12 mb-0'),
                    css_class='form-row'
                ),
                Row(
                    Column('sintomas', css_class='form-group col-md-6 mb-0'),
                    Column('diagnostico', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                HTML('<h4 class="mb-3 mt-4">Tratamiento y Medicamentos</h4>'),
                Row(
                    Column('tratamiento', css_class='form-group col-md-6 mb-0'),
                    Column('medicamentos_recetados', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                'dosis_medicamentos',
                HTML('<h4 class="mb-3 mt-4">Estudios y Reposo</h4>'),
                Row(
                    Column('estudios_solicitados', css_class='form-group col-md-6 mb-0'),
                    Column('dias_reposo', css_class='form-group col-md-3 mb-0'),
                    Column('proxima_cita_sugerida', css_class='form-group col-md-3 mb-0'),
                    css_class='form-row'
                ),
                'indicaciones_reposo',
                HTML('<h4 class="mb-3 mt-4">Órdenes Médicas</h4>'),
                'ordenes_medicas',
                'observaciones',
                Div(
                    Submit('submit', 'Guardar Historia Clínica', css_class='btn btn-primary'),
                    HTML('<a href="javascript:history.back()" class="btn btn-secondary ms-2">Volver</a>'),
                    css_class='mt-4'
                ),
                css_class='space-y-4'
            )
        )

class BusquedaCitasForm(forms.Form):
    """Formulario para búsqueda de citas"""
    
    fecha_inicio = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=False
    )
    
    fecha_fin = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=False
    )
    
    estado = forms.ChoiceField(
        choices=[('', 'Todos')] + Cita.ESTADOS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    especialidad = forms.ModelChoiceField(
        queryset=Especialidad.objects.filter(activa=True),
        empty_label="Todas",
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('fecha_inicio', css_class='form-group col-md-3 mb-0'),
                Column('fecha_fin', css_class='form-group col-md-3 mb-0'),
                Column('estado', css_class='form-group col-md-3 mb-0'),
                Column('especialidad', css_class='form-group col-md-3 mb-0'),
                css_class='form-row'
            ),
            Submit('submit', 'Buscar', css_class='btn btn-primary'),
            css_class='form-inline'
        )
