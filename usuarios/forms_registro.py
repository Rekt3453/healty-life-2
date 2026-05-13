from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from datetime import date
from .models import UserPaciente, PacienteDatosPersonales, Estado, Municipio, Ciudad, Parroquia, Sede


class RegistroPacienteForm(UserCreationForm):
    # ============ CAMPOS DE CUENTA ============
    email = forms.EmailField(
        required=True,
        label="Correo Electrónico",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'ejemplo@correo.com'})
    )
    
    # ============ CAMPOS PERSONALES ============
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
        validators=[RegexValidator(r'^\d+$', 'La cédula solo debe contener números')],
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
        label="Número de Teléfono",
        validators=[RegexValidator(r'^\d+$', 'El teléfono solo debe contener números')],
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '04121234567'})
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
    
    # ============ CAMPOS DE UBICACIÓN ============
    id_estado = forms.ModelChoiceField(
        queryset=Estado.objects.all().order_by('estado'),
        required=True,
        label="Estado",
        empty_label="Seleccione un estado",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_estado'})
    )
    
    id_municipio = forms.ModelChoiceField(
        queryset=Municipio.objects.none(),
        required=True,
        label="Municipio",
        empty_label="Seleccione un municipio",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_municipio'})
    )
    
    id_ciudad = forms.ModelChoiceField(
        queryset=Ciudad.objects.none(),
        required=True,
        label="Ciudad",
        empty_label="Seleccione una ciudad",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_ciudad'})
    )
    
    id_parroquia = forms.ModelChoiceField(
        queryset=Parroquia.objects.none(),
        required=True,
        label="Parroquia",
        empty_label="Seleccione una parroquia",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_parroquia'})
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de usuario'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Estilizar campos de password
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Contraseña'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirmar contraseña'})
        
        # Si hay datos POST, habilitar selectores dependientes
        if 'id_estado' in self.data:
            try:
                estado_id = int(self.data.get('id_estado'))
                self.fields['id_municipio'].queryset = Municipio.objects.filter(
                    id_estado=estado_id
                ).order_by('municipio')
            except (ValueError, TypeError):
                pass
        
        if 'id_municipio' in self.data:
            try:
                municipio_id = int(self.data.get('id_municipio'))
                self.fields['id_ciudad'].queryset = Ciudad.objects.filter(
                    id_municipio=municipio_id
                ).order_by('ciudad')
            except (ValueError, TypeError):
                pass
        
        if 'id_ciudad' in self.data:
            try:
                ciudad_id = int(self.data.get('id_ciudad'))
                self.fields['id_parroquia'].queryset = Parroquia.objects.filter(
                    id_municipio=ciudad_id
                ).order_by('parroquia')
            except (ValueError, TypeError):
                pass
    
    # ============ VALIDACIONES ============
    
    def clean_cedula(self):
        cedula = self.cleaned_data.get('cedula')
        tipo = self.cleaned_data.get('tipo_cedula')
        
        if PacienteDatosPersonales.objects.filter(cedula=cedula).exists():
            raise forms.ValidationError("Esta cédula ya está registrada en el sistema")
        return cedula
    
    def clean_fecha_nacimiento(self):
        fecha = self.cleaned_data.get('fecha_nacimiento')
        if fecha and fecha > date.today():
            raise forms.ValidationError("La fecha de nacimiento no puede ser futura")
        return fecha
    
    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono')
        if telefono and not telefono.isdigit():
            raise forms.ValidationError("El teléfono solo debe contener números")
        if telefono and len(telefono) < 10:
            raise forms.ValidationError("Ingrese un número de teléfono válido")
        return telefono
    
    # ============ GUARDADO ============
    
    def save(self, commit=True):
        # Crear User de Django
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        
        # Obtener primera sede disponible
        try:
            sede = Sede.objects.first()
        except:
            sede = None
        
        # Crear UserPaciente
        user_paciente = UserPaciente.objects.create(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            password='',  # Se agregará después
            id_sede=sede,
            status=True
        )
        user_paciente.set_password(self.cleaned_data['password1'])
        user_paciente.save()
        
        # Crear PacienteDatosPersonales con todos los campos
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
            status=True
        )
        
        return user
