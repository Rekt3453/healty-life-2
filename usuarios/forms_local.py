from django import forms
from django.core.exceptions import ValidationError
from .models import (
    UserPaciente, PacienteDatosPersonales, 
    Estado, Municipio, Ciudad, Parroquia
)

class RegistroPacienteFormLocal(forms.Form):
    """Formulario de registro para pacientes con datos locales de prueba"""
    
    # Datos de autenticación
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Contraseña",
        required=True
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Confirmar Contraseña",
        required=True
    )
    
    # Datos personales obligatorios según Supabase
    nombre_1 = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    apellido_1 = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    cedula = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
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
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    sexo = forms.ChoiceField(
        choices=[
            ('M', 'Masculino'),
            ('F', 'Femenino'),
        ],
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    telefono = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    fecha_nacimiento = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    # Datos de ubicación con datos locales
    ESTADOS_CHOICES = [
        ('1', 'Distrito Capital'),
        ('2', 'Carabobo'),
        ('3', 'Zulia'),
        ('4', 'Miranda'),
        ('5', 'Anzoátegui'),
    ]
    
    MUNICIPIOS_CHOICES = [
        ('', 'Seleccione un municipio'),
        # Distrito Capital
        ('1', 'Libertador'),
        ('2', 'Baruta'),
        # Carabobo
        ('3', 'Valencia'),
        ('4', 'Guacara'),
        # Zulia
        ('5', 'Maracaibo'),
        ('6', 'San Francisco'),
        # Miranda
        ('7', 'Sucre'),
        ('8', 'Baruta'),
        # Anzoátegui
        ('9', 'Anaco'),
        ('10', 'Barcelona'),
    ]
    
    CIUDADES_CHOICES = [
        ('', 'Seleccione una ciudad'),
        # Distrito Capital
        ('1', 'Caracas'),
        ('2', 'Los Teques'),
        # Carabobo
        ('3', 'Valencia'),
        ('4', 'Naguanagua'),
        # Zulia
        ('5', 'Maracaibo'),
        ('6', 'San Francisco'),
        # Miranda
        ('7', 'Los Teques'),
        ('8', 'Baruta'),
        # Anzoátegui
        ('9', 'Barcelona'),
        ('10', 'Puerto La Cruz'),
    ]
    
    PARROQUIAS_CHOICES = [
        ('', 'Seleccione una parroquia'),
        # Libertador
        ('1', 'Altagracia'),
        ('2', 'Catedral'),
        ('3', 'San Juan'),
        ('4', 'Santa Rosalía'),
        # Baruta
        ('5', 'Baruta'),
        ('6', 'El Cafetal'),
        # Valencia
        ('7', 'San José'),
        ('8', 'Catedral'),
        # Maracaibo
        ('9', 'San Francisco'),
        ('10', 'Maracaibo'),
        # Sucre
        ('11', 'Petare'),
        ('12', 'La Dolorita'),
        # Anaco
        ('13', 'Anaco'),
        ('14', 'Santa Rosa'),
        # Barcelona
        ('15', 'Barcelona'),
        ('16', 'Guanta'),
    ]
    
    id_estado = forms.ChoiceField(
        choices=ESTADOS_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    id_municipio = forms.ChoiceField(
        choices=MUNICIPIOS_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    id_ciudad = forms.ChoiceField(
        choices=CIUDADES_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    id_parroquia = forms.ChoiceField(
        choices=PARROQUIAS_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    direccion = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        required=True
    )
    
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
            id_estado_id=self.cleaned_data['id_estado'],
            id_municipio_id=self.cleaned_data['id_municipio'],
            id_ciudad_id=self.cleaned_data['id_ciudad'],
            id_parroquia_id=self.cleaned_data['id_parroquia'],
        )
        
        return user
