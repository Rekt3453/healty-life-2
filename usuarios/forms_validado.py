from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.validators import RegexValidator, EmailValidator, MinLengthValidator
from django.contrib.auth.password_validation import validate_password
from datetime import date, timedelta
import re
from .models import UserPaciente, PacienteDatosPersonales, Estado, Municipio, Ciudad, Parroquia, DireccionPaciente, Sede


class RegistroPacienteForm(forms.Form):
    
    # ==================== CAMPOS DE CUENTA ====================
    
    username = forms.CharField(
        max_length=30,
        min_length=4,
        required=True,
        label="Nombre de Usuario",
        validators=[
            RegexValidator(
                r'^[a-zA-Z0-9_-]+$',
                'Solo letras, números, guiones y guiones bajos'
            ),
        ],
        error_messages={
            'required': 'El nombre de usuario es obligatorio',
            'min_length': 'Mínimo 4 caracteres',
            'max_length': 'Máximo 30 caracteres',
        },
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'usuario_ejemplo',
            'autocomplete': 'username',
            'data-validate': 'username',
        })
    )
    
    email = forms.EmailField(
        required=True,
        label="Correo Electrónico",
        validators=[EmailValidator(message='Ingrese un correo electrónico válido')],
        error_messages={
            'required': 'El correo electrónico es obligatorio',
            'invalid': 'Ingrese un correo electrónico válido',
        },
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'ejemplo@correo.com',
            'autocomplete': 'email',
            'data-validate': 'email',
        })
    )
    
    password1 = forms.CharField(
        required=True,
        label="Contraseña",
        min_length=8,
        validators=[validate_password],
        error_messages={
            'required': 'La contraseña es obligatoria',
            'min_length': 'La contraseña debe tener al menos 8 caracteres',
        },
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mínimo 8 caracteres',
            'autocomplete': 'new-password',
            'data-validate': 'password',
        })
    )
    
    password2 = forms.CharField(
        required=True,
        label="Confirmar Contraseña",
        error_messages={
            'required': 'Confirme su contraseña',
        },
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Repita su contraseña',
            'autocomplete': 'new-password',
            'data-validate': 'password2',
        })
    )
    
    # ==================== CAMPOS PERSONALES ====================
    
    primer_nombre = forms.CharField(
        max_length=50,
        min_length=2,
        required=True,
        label="Primer Nombre",
        validators=[
            RegexValidator(
                r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$',
                'El nombre solo debe contener letras'
            ),
        ],
        error_messages={
            'required': 'El primer nombre es obligatorio',
            'min_length': 'Mínimo 2 letras',
        },
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Juan',
            'data-validate': 'nombre',
        })
    )
    
    segundo_nombre = forms.CharField(
        max_length=50,
        required=False,
        label="Segundo Nombre",
        validators=[
            RegexValidator(
                r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]*$',
                'El nombre solo debe contener letras'
            ),
        ],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Carlos (opcional)',
            'data-validate': 'nombre',
        })
    )
    
    primer_apellido = forms.CharField(
        max_length=50,
        min_length=2,
        required=True,
        label="Primer Apellido",
        validators=[
            RegexValidator(
                r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$',
                'El apellido solo debe contener letras'
            ),
        ],
        error_messages={
            'required': 'El primer apellido es obligatorio',
            'min_length': 'Mínimo 2 letras',
        },
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Pérez',
            'data-validate': 'apellido',
        })
    )
    
    segundo_apellido = forms.CharField(
        max_length=50,
        required=False,
        label="Segundo Apellido",
        validators=[
            RegexValidator(
                r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]*$',
                'El apellido solo debe contener letras'
            ),
        ],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: García (opcional)',
            'data-validate': 'apellido',
        })
    )
    
    tipo_cedula = forms.ChoiceField(
        choices=[
            ('V', 'V - Venezolano'),
            ('E', 'E - Extranjero'),
            ('J', 'J - Jurídico'),
            ('C', 'C - Consejo Comunal'),
            ('G', 'G - Gobierno'),
            ('P', 'P - Pasaporte'),
            ('F', 'F - Fallecido'),
        ],
        required=True,
        label="Tipo de Cédula",
        error_messages={'required': 'Seleccione el tipo de cédula'},
        widget=forms.Select(attrs={
            'class': 'form-select',
            'data-validate': 'select',
        })
    )
    
    cedula = forms.CharField(
        max_length=20,
        min_length=6,
        required=True,
        label="Cédula de Identidad",
        validators=[
            RegexValidator(r'^\d+$', 'La cédula solo debe contener números'),
            MinLengthValidator(6, 'La cédula debe tener al menos 6 dígitos'),
        ],
        error_messages={
            'required': 'La cédula es obligatoria',
            'min_length': 'Mínimo 6 dígitos',
        },
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '12345678',
            'inputmode': 'numeric',
            'maxlength': '20',
            'data-validate': 'cedula',
        })
    )
    
    sexo = forms.ChoiceField(
        choices=[
            ('M', 'Masculino'),
            ('F', 'Femenino'),
            ('NB', 'No Binario'),
            ('O', 'Otro'),
            ('PN', 'Prefiero no decirlo'),
        ],
        required=True,
        label="Sexo",
        error_messages={'required': 'Seleccione una opción'},
        widget=forms.Select(attrs={
            'class': 'form-select',
            'data-validate': 'select',
        })
    )
    
    fecha_nacimiento = forms.DateField(
        required=True,
        label="Fecha de Nacimiento",
        error_messages={
            'required': 'La fecha de nacimiento es obligatoria',
            'invalid': 'Ingrese una fecha válida',
        },
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'max': date.today().isoformat(),
            'min': (date.today() - timedelta(days=365*120)).isoformat(),
            'data-validate': 'fecha',
        })
    )
    
    telefono = forms.CharField(
        max_length=15,
        min_length=10,
        required=True,
        label="Número de Teléfono",
        validators=[
            RegexValidator(r'^\d+$', 'El teléfono solo debe contener números'),
            MinLengthValidator(10, 'El teléfono debe tener al menos 10 dígitos'),
        ],
        error_messages={
            'required': 'El teléfono es obligatorio',
            'min_length': 'Mínimo 10 dígitos',
        },
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '04121234567',
            'inputmode': 'numeric',
            'maxlength': '15',
            'data-validate': 'telefono',
        })
    )
    
    direccion = forms.CharField(
        max_length=500,
        required=False,
        label="Dirección",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Dirección de domicilio (opcional)',
            'maxlength': '500',
        })
    )
    
    # ==================== CAMPOS DE UBICACIÓN (TEXTO LIBRE) ====================
    
    estado = forms.CharField(
        max_length=100,
        required=False,
        label="Estado",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Distrito Capital',
            'data-validate': 'texto',
        })
    )
    
    municipio = forms.CharField(
        max_length=100,
        required=False,
        label="Municipio",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Libertador',
            'data-validate': 'texto',
        })
    )
    
    ciudad = forms.CharField(
        max_length=100,
        required=False,
        label="Ciudad",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Caracas',
            'data-validate': 'texto',
        })
    )
    
    parroquia = forms.CharField(
        max_length=100,
        required=False,
        label="Parroquia",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Altagracia',
            'data-validate': 'texto',
        })
    )
    
    # ==================== VALIDACIONES PERSONALIZADAS ====================
    
    def clean_primer_nombre(self):
        nombre = self.cleaned_data.get('primer_nombre', '').strip()
        if nombre and len(nombre) < 2:
            raise forms.ValidationError("El nombre debe tener al menos 2 letras")
        if nombre and re.search(r'[0-9]', nombre):
            raise forms.ValidationError("El nombre no puede contener números")
        return nombre.upper()
    
    def clean_segundo_nombre(self):
        nombre = self.cleaned_data.get('segundo_nombre', '').strip()
        if nombre and re.search(r'[0-9]', nombre):
            raise forms.ValidationError("El nombre no puede contener números")
        return nombre.upper() if nombre else ''
    
    def clean_primer_apellido(self):
        apellido = self.cleaned_data.get('primer_apellido', '').strip()
        if apellido and len(apellido) < 2:
            raise forms.ValidationError("El apellido debe tener al menos 2 letras")
        if apellido and re.search(r'[0-9]', apellido):
            raise forms.ValidationError("El apellido no puede contener números")
        return apellido.upper()
    
    def clean_segundo_apellido(self):
        apellido = self.cleaned_data.get('segundo_apellido', '').strip()
        if apellido and re.search(r'[0-9]', apellido):
            raise forms.ValidationError("El apellido no puede contener números")
        return apellido.upper() if apellido else ''
    
    def clean_cedula(self):
        cedula = self.cleaned_data.get('cedula', '').strip()
        tipo = self.cleaned_data.get('tipo_cedula')
        
        if not cedula.isdigit():
            raise forms.ValidationError("La cédula solo debe contener números")
        if len(cedula) < 6:
            raise forms.ValidationError("La cédula debe tener al menos 6 dígitos")
        if len(cedula) > 20:
            raise forms.ValidationError("La cédula no puede tener más de 20 dígitos")
        
        # Verificar unicidad
        if PacienteDatosPersonales.objects.filter(cedula=cedula).exists():
            raise forms.ValidationError(f"La cédula {tipo}-{cedula} ya está registrada")
        
        return cedula
    
    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if UserPaciente.objects.filter(email=email).exists():
            raise forms.ValidationError("Este correo electrónico ya está en uso")
        return email
    
    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip().lower()
        if UserPaciente.objects.filter(username=username).exists():
            raise forms.ValidationError("Este nombre de usuario ya existe")
        if len(username) < 4:
            raise forms.ValidationError("El usuario debe tener al menos 4 caracteres")
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            raise forms.ValidationError("Solo letras, números, guiones y guiones bajos")
        return username
    
    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        validate_password(password)
        return password
    
    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Las contraseñas no coinciden")
        return password2
    
    def clean_fecha_nacimiento(self):
        fecha = self.cleaned_data.get('fecha_nacimiento')
        if fecha:
            hoy = date.today()
            edad = hoy.year - fecha.year - ((hoy.month, hoy.day) < (fecha.month, fecha.day))
            if fecha > hoy:
                raise forms.ValidationError("La fecha no puede ser futura")
            if edad < 0:
                raise forms.ValidationError("Fecha de nacimiento inválida")
            if edad > 120:
                raise forms.ValidationError("Fecha de nacimiento improbable")
        return fecha
    
    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono', '').strip()
        if not telefono.isdigit():
            raise forms.ValidationError("El teléfono solo debe contener números")
        if len(telefono) < 10:
            raise forms.ValidationError("El teléfono debe tener al menos 10 dígitos")
        if len(telefono) > 15:
            raise forms.ValidationError("El teléfono no puede tener más de 15 dígitos")
        return telefono
    
    # ==================== GUARDADO ====================
    
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
            nombre_1=self.cleaned_data['primer_nombre'],
            nombre_2=self.cleaned_data.get('segundo_nombre', ''),
            apellido_1=self.cleaned_data['primer_apellido'],
            apellido_2=self.cleaned_data.get('segundo_apellido', ''),
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
