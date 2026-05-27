from django import forms
from django.utils import timezone
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

    def clean_fecha_consulta(self):
        """Valida que la fecha/hora de la cita no sea en el pasado."""
        fecha_consulta = self.cleaned_data.get('fecha_consulta')
        if fecha_consulta:
            ahora = timezone.now()
            # Normaliza a naive si fecha_consulta es naive (la BD usa timestamp sin zona)
            if timezone.is_naive(fecha_consulta):
                ahora = timezone.make_naive(ahora)
            if fecha_consulta < ahora:
                raise forms.ValidationError(
                    "No puedes solicitar una cita en una fecha/hora que ya ha pasado. "
                    "Elige una fecha y hora futura."
                )
        return fecha_consulta


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


class RecetaForm(forms.Form):
    """
    Formulario para generar una receta médica completa.
    Contiene seis apartados independientes, todos opcionales.
    El doctor puede dejar en blanco los que no apliquen.
    """
    # Apartado 1: Órdenes médicas (radiografías, tomografías, etc.)
    ordenes_medicas = forms.CharField(
        label="Órdenes Médicas",
        widget=forms.Textarea(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 resize-none',
            'rows': 4,
            'placeholder': 'Ej: Radiografía de tórax AP y lateral, Eco abdominal...',
        }),
        required=False,
    )
    # Apartado 2: Tratamiento (medicamentos y posología)
    tratamiento = forms.CharField(
        label="Tratamiento",
        widget=forms.Textarea(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 resize-none',
            'rows': 4,
            'placeholder': 'Ej: Paracetamol 500 mg cada 8 h por 5 días...',
        }),
        required=False,
    )
    # Apartado 3: Reposo
    reposo = forms.CharField(
        label="Reposo",
        widget=forms.Textarea(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 resize-none',
            'rows': 3,
            'placeholder': 'Ej: Reposo relativo por 3 días a partir de hoy...',
        }),
        required=False,
    )
    # Apartado 4: Medicamentos especiales (prescripción médica controlada)
    medicamentos_especiales = forms.CharField(
        label="Medicamentos Especiales",
        widget=forms.Textarea(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 resize-none',
            'rows': 4,
            'placeholder': 'Ej: Tramadol 50 mg (controlado) 1 cápsula cada 8 h...',
        }),
        required=False,
    )
    # Apartado 5: Estudios a realizar (análisis clínicos)
    estudios = forms.CharField(
        label="Estudios a Realizar",
        widget=forms.Textarea(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 resize-none',
            'rows': 4,
            'placeholder': 'Ej: Hemograma completo, glucosa en ayunas, perfil lipídico...',
        }),
        required=False,
    )
    # Apartado 6: Diagnóstico general
    diagnostico = forms.CharField(
        label="Diagnóstico General",
        widget=forms.Textarea(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 resize-none',
            'rows': 4,
            'placeholder': 'Diagnóstico del médico...',
        }),
        required=False,
    )
