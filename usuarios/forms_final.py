from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from datetime import date
from .models import UserPaciente, PacienteDatosPersonales, Estado, Municipio, Ciudad, Parroquia, DireccionPaciente, Sede

class RegistroPacienteForm(forms.Form):
    # Campos básicos de cuenta
    email = forms.EmailField(
        required=True, 
        label="Correo Electrónico",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'ejemplo@correo.com'})
    )
    
    # Campos personales
    nombre_1 = forms.CharField(
        max_length=50, 
        required=True, 
        label="Primer Nombre",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Primer nombre'})
    )
    nombre_2 = forms.CharField(
        max_length=50, 
        required=False, 
        label="Segundo Nombre",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Segundo nombre (opcional)'})
    )
    apellido_1 = forms.CharField(
        max_length=50, 
        required=True, 
        label="Primer Apellido",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Primer apellido'})
    )
    apellido_2 = forms.CharField(
        max_length=50, 
        required=False, 
        label="Segundo Apellido",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Segundo apellido (opcional)'})
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
        label="Tipo de Cédula",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    cedula = forms.CharField(
        max_length=20, 
        required=True, 
        label="Cédula de Identidad",
        validators=[RegexValidator(r'^\d+$', 'Solo números')],
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '12345678'})
    )
    
    sexo = forms.ChoiceField(
        choices=[
            ('M', 'Masculino'),
            ('F', 'Femenino'),
        ],
        required=True, 
        label="Sexo",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    fecha_nacimiento = forms.DateField(
        required=True, 
        label="Fecha de Nacimiento",
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'max': date.today().isoformat()
        })
    )
    
    telefono = forms.CharField(
        max_length=20, 
        required=True, 
        label="Teléfono",
        validators=[RegexValidator(r'^\d+$', 'Solo números')],
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '04121234567'})
    )
    
    # Campos de ubicación como texto libre
    estado = forms.CharField(
        max_length=100,
        required=False,
        label="Estado",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Distrito Capital'})
    )
    
    municipio = forms.CharField(
        max_length=100,
        required=False,
        label="Municipio",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Libertador'})
    )
    
    ciudad = forms.CharField(
        max_length=100,
        required=False,
        label="Ciudad",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Caracas'})
    )
    
    parroquia = forms.CharField(
        max_length=100,
        required=False,
        label="Parroquia",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Altagracia'})
    )
    
    direccion = forms.CharField(
        required=False, 
        label="Dirección",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Dirección de domicilio'
        })
    )
    
    username = forms.CharField(
    max_length=150,
    required=True,
    label="Nombre de usuario",
    widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de usuario'})
)
    
    password1 = forms.CharField(
        required=True,
        label="Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Contraseña'})
    )
    
    password2 = forms.CharField(
        required=True,
        label="Confirmar Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirmar contraseña'})
    )
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if UserPaciente.objects.filter(username=username).exists():
            raise forms.ValidationError("Este nombre de usuario ya está en uso")
        return username
    
    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Las contraseñas no coinciden")
        return password2
    
    def clean_cedula(self):
        cedula = self.cleaned_data.get('cedula')
        if PacienteDatosPersonales.objects.filter(cedula=cedula).exists():
            raise forms.ValidationError("Esta cédula ya está registrada")
        return cedula
    
    def clean_fecha_nacimiento(self):
        fecha = self.cleaned_data.get('fecha_nacimiento')
        if fecha and fecha > date.today():
            raise forms.ValidationError("La fecha no puede ser futura")
        return fecha
    
    def save(self, commit=True):
        # Obtener primera sede disponible
        try:
            sede = Sede.objects.first()
        except:
            sede = None
        
        # Crear UserPaciente directamente
        user_paciente = UserPaciente.objects.create(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            password='',  # Se agregará después
            id_sede=sede,
            status=True
        )
        user_paciente.set_password(self.cleaned_data['password1'])
        user_paciente.save()
        
        # Crear DireccionPaciente con los datos de ubicación
        direccion_paciente = DireccionPaciente.objects.create(
            id_estado=None,  # No usar FK, solo guardar texto
            id_municipio=None,
            id_ciudad=None,
            id_parroquia=None,
            direccion=self.cleaned_data.get('direccion', ''),
            referencia=f"{self.cleaned_data.get('estado', '')}, {self.cleaned_data.get('municipio', '')}, {self.cleaned_data.get('ciudad', '')}, {self.cleaned_data.get('parroquia', '')}"
        )
        
        # Crear PacienteDatosPersonales con campos REALES de Supabase
        paciente_datos = PacienteDatosPersonales.objects.create(
            nombre_1=self.cleaned_data['nombre_1'],
            nombre_2=self.cleaned_data.get('nombre_2', ''),
            apellido_1=self.cleaned_data['apellido_1'],
            apellido_2=self.cleaned_data.get('apellido_2', ''),
            cedula=self.cleaned_data['cedula'],
            tipo_cedula=self.cleaned_data['tipo_cedula'],
            sexo=self.cleaned_data['sexo'],
            telefono=self.cleaned_data['telefono'],
            fecha_nacimiento=self.cleaned_data['fecha_nacimiento'],
            id_user_paciente=user_paciente,
            id_sede=sede,
            id_direccion_paciente=direccion_paciente,
            status=True
        )
        
        return user_paciente
