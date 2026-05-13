from django import forms
from django.core.exceptions import ValidationError
from .models import (
    UserPaciente, PacienteDatosPersonales, 
    Estado, Municipio, Ciudad, Parroquia
)

class RegistroPacienteForm(forms.Form):
    """Formulario de registro para pacientes usando los modelos de Supabase"""
    
    # Datos de autenticación
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-input w-full px-3 py-2 rounded-lg'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-input w-full px-3 py-2 rounded-lg'})
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-input w-full px-3 py-2 rounded-lg'}),
        label="Contraseña",
        required=True
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-input w-full px-3 py-2 rounded-lg'}),
        label="Confirmar Contraseña",
        required=True
    )
    
    # Datos personales obligatorios según Supabase
    nombre_1 = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-input w-full px-3 py-2 rounded-lg'})
    )
    apellido_1 = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-input w-full px-3 py-2 rounded-lg'})
    )
    cedula = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-input w-full px-3 py-2 rounded-lg'})
    )
    tipo_cedula = forms.ChoiceField(
        choices=[
            ('V', 'V - Venezolano'),
            ('E', 'E - Extranjero'),
            ('J', 'J - Jurídico'),
            ('C', 'C - Consejo Comunal'),
            ('G', 'G - Gobierno'),
            ('P', 'P - Pasaporte'),
        ],
        required=True,
        widget=forms.Select(attrs={'class': 'form-input w-full px-3 py-2 rounded-lg'})
    )
    sexo = forms.ChoiceField(
        choices=[
            ('M', 'Masculino'),
            ('F', 'Femenino'),
        ],
        required=True,
        widget=forms.Select(attrs={'class': 'form-input w-full px-3 py-2 rounded-lg'})
    )
    telefono = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-input w-full px-3 py-2 rounded-lg'})
    )
    fecha_nacimiento = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-input w-full px-3 py-2 rounded-lg'})
    )
    
    # Datos de ubicación (obligatorios según Supabase)
    id_estado = forms.ModelChoiceField(
        queryset=Estado.objects.all(),
        required=True,
        empty_label="Seleccione un estado",
        widget=forms.Select(attrs={'class': 'form-input w-full px-3 py-2 rounded-lg'})
    )
    id_municipio = forms.ModelChoiceField(
        queryset=Municipio.objects.none(),
        required=True,
        empty_label="Seleccione un municipio",
        widget=forms.Select(attrs={'class': 'form-input w-full px-3 py-2 rounded-lg'})
    )
    id_ciudad = forms.ModelChoiceField(
        queryset=Ciudad.objects.none(),
        required=True,
        empty_label="Seleccione una ciudad",
        widget=forms.Select(attrs={'class': 'form-input w-full px-3 py-2 rounded-lg'})
    )
    id_parroquia = forms.ModelChoiceField(
        queryset=Parroquia.objects.none(),
        required=True,
        empty_label="Seleccione una parroquia",
        widget=forms.Select(attrs={'class': 'form-input w-full px-3 py-2 rounded-lg'})
    )
    direccion = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-input w-full px-3 py-2 rounded-lg'}),
        required=True
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurar dinámicamente los campos de ubicación
        if 'id_estado' in self.data:
            try:
                estado_id = int(self.data.get('id_estado'))
                self.fields['id_municipio'].queryset = Municipio.objects.filter(id_estado=estado_id).order_by('municipio')
                self.fields['id_ciudad'].queryset = Ciudad.objects.filter(id_estado=estado_id).order_by('ciudad')
            except (ValueError, TypeError):
                pass
        
        if 'id_municipio' in self.data:
            try:
                municipio_id = int(self.data.get('id_municipio'))
                self.fields['id_parroquia'].queryset = Parroquia.objects.filter(id_municipio=municipio_id).order_by('parroquia')
            except (ValueError, TypeError):
                pass
    
    def clean_fecha_nacimiento(self):
        fecha = self.cleaned_data.get('fecha_nacimiento')
        from datetime import date
        if fecha and fecha > date.today():
            raise forms.ValidationError("La fecha de nacimiento no puede ser futura")
        return fecha
    
    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono')
        if telefono and not telefono.isdigit():
            raise forms.ValidationError("El teléfono solo debe contener números")
        return telefono
    
    def clean_cedula(self):
        cedula = self.cleaned_data.get('cedula')
        tipo = self.cleaned_data.get('tipo_cedula')
        
        # Verificar duplicados en PacienteDatosPersonales
        if PacienteDatosPersonales.objects.filter(cedula=cedula).exists():
            raise forms.ValidationError("Esta cédula ya está registrada")
        return cedula
    
    def save(self, commit=True):
        # Crear usuario paciente
        from django.contrib.auth.models import User
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password1']
        )
        
        # Crear datos personales del paciente
        paciente_datos = PacienteDatosPersonales.objects.create(
            nombre_1=self.cleaned_data['nombre_1'],
            apellido_1=self.cleaned_data['apellido_1'],
            cedula=self.cleaned_data['cedula'],
            tipo_cedula=self.cleaned_data['tipo_cedula'],
            sexo=self.cleaned_data['sexo'],
            telefono=self.cleaned_data['telefono'],
            fecha_nacimiento=self.cleaned_data['fecha_nacimiento'],
            direccion=self.cleaned_data['direccion'],
            id_estado=self.cleaned_data['id_estado'],
            id_municipio=self.cleaned_data['id_municipio'],
            id_ciudad=self.cleaned_data['id_ciudad'],
            id_parroquia=self.cleaned_data['id_parroquia'],
        )
        
        # Asociar usuario con datos personales (simulado)
        # En un sistema real, esto sería una relación foreign key
        
        return user
