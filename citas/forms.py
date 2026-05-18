from django import forms
<<<<<<< Updated upstream

# Los formularios de citas son manejados directamente via POST en views.py.
# Este archivo se mantiene para compatibilidad con imports existentes.
=======
from .models import Cita, ServicioEspecialidad, Consultorio, Especialidad, Doctor, PagoCita
from usuarios.models import PacienteDatosPersonales, Sede

class SolicitudCitaForm(forms.Form):
    """Formulario para solicitar cita con flujo: especialidad → servicio → doctor → consultorio → fecha/hora → motivo"""
    
    # Paso 1: Especialidad
    especialidad = forms.ModelChoiceField(
        queryset=Especialidad.objects.filter(status=True),
        empty_label="Seleccionar especialidad",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_especialidad'}),
        required=True
    )
    
    # Paso 2: Servicio (se llena dinámicamente según especialidad y sede)
    servicio = forms.ModelChoiceField(
        queryset=ServicioEspecialidad.objects.filter(status=True),
        empty_label="Seleccionar especialidad primero",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_servicio'}),
        required=True
    )
    
    # Paso 3: Doctor (se llena dinámicamente según servicio)
    doctor = forms.ModelChoiceField(
        queryset=Doctor.objects.filter(status=True),
        empty_label="Seleccionar servicio primero",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_doctor'}),
        required=True
    )
    
    # Paso 4: Consultorio (se llena dinámicamente según sede)
    consultorio = forms.ModelChoiceField(
        queryset=Consultorio.objects.filter(status=True),
        empty_label="Seleccionar sede primero",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_consultorio'}),
        required=True
    )
    
    # Paso 5: Fecha y hora
    fecha_consulta = forms.DateTimeField(
        label="Fecha y hora de la consulta",
        widget=forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        required=True
    )
    
    # Paso 6: Motivo
    motivo = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control', 
            'rows': 4, 
            'placeholder': 'Describe el motivo de tu consulta...'
        }),
        required=True
    )
    
    def __init__(self, *args, **kwargs):
        self.id_sede = kwargs.pop('id_sede', None)
        self.id_paciente = kwargs.pop('id_paciente', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar especialidades por sede si está disponible
        if self.id_sede:
            self.fields['especialidad'].queryset = Especialidad.objects.filter(
                id_sede=self.id_sede,
                status=True
            )
        
        # Filtrar servicios por sede si está disponible
        if self.id_sede:
            self.fields['servicio'].queryset = ServicioEspecialidad.objects.filter(
                id_sede=self.id_sede,
                status=True
            )
        
        # Filtrar consultorios por sede si está disponible
        if self.id_sede:
            self.fields['consultorio'].queryset = Consultorio.objects.filter(
                id_sede=self.id_sede,
                status=True
            )

class AsignarMedicoForm(forms.Form):
    """Formulario para asignar médico a una cita (para recepcionista)"""
    doctor = forms.ModelChoiceField(
        queryset=Doctor.objects.filter(status=True),
        empty_label="Seleccionar médico",
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True
    )
    
    consultorio = forms.ModelChoiceField(
        queryset=Consultorio.objects.filter(status=True),
        empty_label="Seleccionar consultorio",
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False
    )

class CrearPagoForm(forms.ModelForm):
    """Formulario para crear pago de cita"""
    class Meta:
        model = PagoCita
        fields = ['monto_pagar', 'metodo_pago', 'referencia_pago']
        widgets = {
            'monto_pagar': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'metodo_pago': forms.Select(attrs={'class': 'form-select'}),
            'referencia_pago': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.id_paciente = kwargs.pop('id_paciente', None)
        self.id_sede = kwargs.pop('id_sede', None)
        self.fecha_consulta = kwargs.pop('fecha_consulta', None)
        super().__init__(*args, **kwargs)
        
        # Establecer valores por defecto si están disponibles
        if self.id_paciente:
            self.instance.id_paciente_id = self.id_paciente
        if self.id_sede:
            self.instance.id_sede_id = self.id_sede
        if self.fecha_consulta:
            self.instance.fecha_consulta = self.fecha_consulta

class CancelarCitaForm(forms.Form):
    """Formulario para cancelar cita"""
    motivo_cancelacion = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Motivo de la cancelación...'
        }),
        required=True
    )
>>>>>>> Stashed changes
