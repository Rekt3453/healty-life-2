from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator, EmailValidator, MinLengthValidator
from datetime import date, timedelta
from .models import (
    UserPaciente, UserDoctor, UserRecepcionista, UserAdmin, UserSuperAdmin,
    PacienteDatosPersonales, Doctor, Recepcionista, Administrador, Superadmin,
    DireccionPaciente, DireccionDoctor, DireccionRecepcionista, DireccionAdmin,
    Sede, Estado, Municipio, Ciudad, Parroquia, PacienteEspecial, CentroMedico
)
from citas.models import EspecialidadDoctor, Consultorio, Horario

class DireccionForm(forms.Form):
    """Formulario base para direcciones"""
    id_estado = forms.ModelChoiceField(
        queryset=Estado.objects.all(),
        empty_label="Seleccione un estado",
        required=True,
        widget=forms.Select(attrs={'class': 'form-input w-full px-3 py-2 rounded-lg'})
    )
    id_municipio = forms.ModelChoiceField(
        queryset=Municipio.objects.none(),
        empty_label="Seleccione un municipio",
        required=True,
        widget=forms.Select(attrs={'class': 'form-input w-full px-3 py-2 rounded-lg'})
    )
    id_ciudad = forms.ModelChoiceField(
        queryset=Ciudad.objects.none(),
        empty_label="Seleccione una ciudad",
        required=True,
        widget=forms.Select(attrs={'class': 'form-input w-full px-3 py-2 rounded-lg'})
    )
    id_parroquia = forms.ModelChoiceField(
        queryset=Parroquia.objects.none(),
        empty_label="Seleccione una parroquia",
        required=True,
        widget=forms.Select(attrs={'class': 'form-input w-full px-3 py-2 rounded-lg'})
    )
    direccion = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-input w-full px-3 py-2 rounded-lg'}),
        required=True
    )
    referencia = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2, 'class': 'form-input w-full px-3 py-2 rounded-lg'}),
        required=False
    )
    latitud = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-input w-full px-3 py-2 rounded-lg'})
    )
    longitud = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-input w-full px-3 py-2 rounded-lg'})
    )

class RegistroPacienteForm(forms.Form):
    """Formulario de registro para pacientes con soporte para menores de edad y condiciones especiales"""
    # ==================== DATOS DE AUTENTICACIÓN ====================
    username = forms.CharField(
        max_length=30,
        min_length=4,
        required=True,
        label="Nombre de Usuario",
        validators=[
            RegexValidator(r'^[a-zA-Z0-9_-]+$', 'Solo letras, números, guiones y guiones bajos'),
        ],
        error_messages={
            'required': 'El nombre de usuario es obligatorio',
            'min_length': 'Mínimo 4 caracteres',
        },
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'usuario_ejemplo',
            'data-validate': 'username',
            'maxlength': '30',
        })
    )
    
    email = forms.EmailField(
        max_length=30,
        required=True,
        label="Correo Electrónico",
        validators=[EmailValidator(message='Ingrese un correo electrónico válido')],
        error_messages={
            'required': 'El correo electrónico es obligatorio',
            'max_length': 'Máximo 30 caracteres',
        },
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'ejemplo@correo.com',
            'data-validate': 'email',
            'maxlength': '30',
        })
    )
    
    password1 = forms.CharField(
        required=True,
        label="Contraseña",
        min_length=8,
        max_length=30,
        validators=[
            RegexValidator(
                r'^(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};:\'",.<>/?\\|`~]).{8,30}$',
                'Debe contener al menos 1 mayúscula, 1 número, 1 carácter especial y tener entre 8 y 30 caracteres'
            ),
        ],
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mínimo 8 caracteres',
            'data-validate': 'password',
            'maxlength': '30',
        })
    )
    
    password2 = forms.CharField(
        required=True,
        label="Confirmar Contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Repita su contraseña',
            'data-validate': 'password2',
        })
    )
    
    # ==================== DATOS PERSONALES ====================
    nombre_1 = forms.CharField(
        max_length=30, min_length=2, required=True,
        label="Primer Nombre",
        validators=[RegexValidator(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', 'Solo letras')],
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Juan', 'data-validate': 'nombre', 'maxlength': '30'})
    )
    
    nombre_2 = forms.CharField(
        max_length=30, required=False,
        label="Segundo Nombre",
        validators=[RegexValidator(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]*$', 'Solo letras')],
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Carlos (opcional)', 'data-validate': 'nombre', 'maxlength': '30'})
    )
    
    apellido_1 = forms.CharField(
        max_length=30, min_length=2, required=True,
        label="Primer Apellido",
        validators=[RegexValidator(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', 'Solo letras')],
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Pérez', 'data-validate': 'apellido', 'maxlength': '30'})
    )
    
    apellido_2 = forms.CharField(
        max_length=30, required=False,
        label="Segundo Apellido",
        validators=[RegexValidator(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]*$', 'Solo letras')],
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: García (opcional)', 'data-validate': 'apellido', 'maxlength': '30'})
    )
    
    tipo_cedula = forms.ChoiceField(
        choices=[('V','V'), ('E','E'), ('J','J')],
        required=True, label="Tipo de Cédula",
        widget=forms.Select(attrs={'class': 'form-select', 'data-validate': 'select'})
    )
    
    cedula = forms.CharField(
        max_length=8, min_length=7, required=True,
        label="Cédula de Identidad",
        validators=[
            RegexValidator(r'^\d+$', 'Solo números'),
            MinLengthValidator(7, 'Mínimo 7 dígitos'),
        ],
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '12345678', 'data-validate': 'cedula', 'maxlength': '8'})
    )
    
    sexo = forms.ChoiceField(
        choices=[('M','Masculino'), ('F','Femenino'), ('NB','No Binario'), ('O','Otro'), ('PN','Prefiero no decirlo')],
        required=True, label="Sexo",
        widget=forms.Select(attrs={'class': 'form-select', 'data-validate': 'select'})
    )
    
    fecha_nacimiento = forms.DateField(
        required=True, label="Fecha de Nacimiento",
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'max': date.today().isoformat(),
            'min': (date.today() - timedelta(days=365*120)).isoformat(),
            'data-validate': 'fecha',
            'id': 'id_fecha_nacimiento'
        })
    )
    
    telefono = forms.CharField(
        max_length=15, min_length=10, required=True,
        label="Número de Teléfono",
        validators=[RegexValidator(r'^\d+$', 'Solo números'), MinLengthValidator(10, 'Mínimo 10 dígitos')],
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '04121234567', 'data-validate': 'telefono'})
    )
    
    # ==================== SEDE ====================
    sede = forms.ModelChoiceField(
        queryset=Sede.objects.filter(status=True).order_by('nombre_sede'),
        required=True,
        label="Sede de Atención",
        empty_label="Seleccione una sede",
        error_messages={'required': 'Debe seleccionar una sede'},
        widget=forms.Select(attrs={
            'class': 'form-select',
            'data-validate': 'select',
            'id': 'id_sede'
        })
    )
    
    # ==================== UBICACIÓN GEOGRÁFICA ====================
    id_estado = forms.ModelChoiceField(
        queryset=Estado.objects.all().order_by('estado'),
        required=True, label="Estado",
        empty_label="Seleccione un estado",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_estado', 'data-validate': 'select'})
    )
    
    id_municipio = forms.ModelChoiceField(
        queryset=Municipio.objects.none(),
        required=True, label="Municipio",
        empty_label="Seleccione un municipio",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_municipio'})
    )
    
    id_ciudad = forms.ModelChoiceField(
        queryset=Ciudad.objects.none(),
        required=True, label="Ciudad",
        empty_label="Seleccione una ciudad",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_ciudad'})
    )
    
    id_parroquia = forms.ModelChoiceField(
        queryset=Parroquia.objects.none(),
        required=True, label="Parroquia",
        empty_label="Seleccione una parroquia",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_parroquia'})
    )
    
    direccion = forms.CharField(
        max_length=100, required=False,
        label="Dirección",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Dirección de domicilio (opcional)', 'maxlength': '100'})
    )
    
    referencia = forms.CharField(
        max_length=100, required=False,
        label="Referencia",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Punto de referencia (opcional)', 'maxlength': '100'})
    )
    
    
    # ==================== CONDICIÓN ESPECIAL ====================
    tiene_condicion_especial = forms.BooleanField(
        required=False,
        label="Tengo una condición médica que requiere atención especial",
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'id_tiene_condicion_especial',
            'data-toggle': 'condicion-especial'
        })
    )
    
    descripcion_condicion = forms.CharField(
        required=False,
        label="Describa su condición médica",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Describa su condición médica, enfermedad, alergia o requerimiento especial...',
            'id': 'id_descripcion_condicion',
            'style': 'display:none;'
        })
    )
    
    # ==================== DATOS DEL TUTOR ====================
    tutor_nombre = forms.CharField(
        max_length=100, required=False,
        label="Nombre completo del tutor/responsable",
        validators=[RegexValidator(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', 'Solo letras')],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre completo del tutor',
            'id': 'id_tutor_nombre',
            'style': 'display:none;'
        })
    )
    
    tutor_cedula = forms.CharField(
        max_length=20, required=False,
        label="Cédula del tutor",
        validators=[RegexValidator(r'^\d+$', 'Solo números')],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Cédula del tutor',
            'id': 'id_tutor_cedula',
            'style': 'display:none;'
        })
    )
    
    tutor_telefono = forms.CharField(
        max_length=15, required=False,
        label="Teléfono del tutor",
        validators=[RegexValidator(r'^\d+$', 'Solo números')],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Teléfono del tutor',
            'id': 'id_tutor_telefono',
            'style': 'display:none;'
        })
    )
    
    tutor_parentesco = forms.ChoiceField(
        choices=[
            ('', 'Seleccione parentesco'),
            ('padre', 'Padre'),
            ('madre', 'Madre'),
            ('tutor_legal', 'Tutor legal'),
            ('abuelo', 'Abuelo/a'),
            ('otro', 'Otro'),
        ],
        required=False,
        label="Parentesco del tutor",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_tutor_parentesco',
            'style': 'display:none;'
        })
    )
    
    tutor_correo = forms.EmailField(
        required=False,
        label="Correo del tutor",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Correo del tutor',
            'id': 'id_tutor_correo',
            'style': 'display:none;'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        estado_id = None
        if self.data.get('id_estado'):
            try:
                estado_id = int(self.data['id_estado'])
            except (ValueError, TypeError):
                pass
        if estado_id:
            self.fields['id_municipio'].queryset = Municipio.objects.filter(id_estado=estado_id)
            self.fields['id_ciudad'].queryset = Ciudad.objects.filter(id_estado=estado_id)
        
        municipio_id = None
        if self.data.get('id_municipio'):
            try:
                municipio_id = int(self.data['id_municipio'])
            except (ValueError, TypeError):
                pass
        if municipio_id:
            self.fields['id_parroquia'].queryset = Parroquia.objects.filter(id_municipio=municipio_id)
    
    # ==================== VALIDACIONES ====================
    
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
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if UserPaciente.objects.filter(username=username).exists():
            raise forms.ValidationError("Este nombre de usuario ya está en uso")
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if UserPaciente.objects.filter(email=email).exists():
            raise forms.ValidationError("Este correo ya está en uso")
        return email
    
    def clean_cedula(self):
        cedula = self.cleaned_data.get('cedula', '').strip()
        if PacienteDatosPersonales.objects.filter(cedula=cedula).exists():
            raise forms.ValidationError("Esta cédula ya está registrada")
        return cedula
    
    def clean(self):
        cleaned_data = super().clean()
        fecha_nacimiento = cleaned_data.get('fecha_nacimiento')
        
        if fecha_nacimiento:
            hoy = date.today()
            edad = hoy.year - fecha_nacimiento.year - ((hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
            
            # Si es menor de edad, validar datos del tutor
            if edad < 18:
                tutor_nombre = cleaned_data.get('tutor_nombre', '').strip()
                tutor_cedula = cleaned_data.get('tutor_cedula', '').strip()
                tutor_telefono = cleaned_data.get('tutor_telefono', '').strip()
                tutor_parentesco = cleaned_data.get('tutor_parentesco', '')
                tutor_correo = cleaned_data.get('tutor_correo', '').strip()
                
                if not tutor_nombre:
                    self.add_error('tutor_nombre', "Obligatorio para menores de edad")
                if not tutor_cedula:
                    self.add_error('tutor_cedula', "Obligatorio para menores de edad")
                if not tutor_telefono:
                    self.add_error('tutor_telefono', "Obligatorio para menores de edad")
                if not tutor_parentesco:
                    self.add_error('tutor_parentesco', "Obligatorio para menores de edad")
                if not tutor_correo:
                    self.add_error('tutor_correo', "Obligatorio para menores de edad")
        
        return cleaned_data
    
    # ==================== GUARDADO ====================
    
    def save(self):
        sede = self.cleaned_data['sede']
        
        # Crear dirección del paciente con los FKs seleccionados
        direccion = DireccionPaciente.objects.create(
            id_estado=self.cleaned_data['id_estado'],
            id_municipio=self.cleaned_data['id_municipio'],
            id_ciudad=self.cleaned_data['id_ciudad'],
            id_parroquia=self.cleaned_data['id_parroquia'],
            direccion=self.cleaned_data.get('direccion', ''),
            referencia=self.cleaned_data.get('referencia', '') or '',
        )
        
        # Crear usuario paciente
        user_paciente = UserPaciente.objects.create_user(
            username=self.cleaned_data['username'],
            correo=self.cleaned_data['email'],
            password=self.cleaned_data['password1'],
            id_sede=sede
        )
        
        # Determinar si es menor de edad
        fecha_nacimiento = self.cleaned_data['fecha_nacimiento']
        hoy = date.today()
        edad = hoy.year - fecha_nacimiento.year - ((hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
        es_menor = edad < 18
        
        # Determinar si es paciente especial
        tiene_condicion = self.cleaned_data.get('tiene_condicion_especial', False)
        es_paciente_especial = es_menor or tiene_condicion
        
        # Crear datos personales del paciente
        paciente = PacienteDatosPersonales.objects.create(
            nombre_1=self.cleaned_data['nombre_1'].upper(),
            nombre_2=self.cleaned_data.get('nombre_2', '').upper() or None,
            apellido_1=self.cleaned_data['apellido_1'].upper(),
            apellido_2=self.cleaned_data.get('apellido_2', '').upper() or None,
            id_user_paciente=user_paciente,
            cedula=self.cleaned_data['cedula'],
            tipo_cedula=self.cleaned_data['tipo_cedula'],
            sexo=self.cleaned_data['sexo'],
            telefono=self.cleaned_data['telefono'],
            fecha_nacimiento=fecha_nacimiento,
            id_sede=sede,
            id_direccion_paciente=direccion,
            status=True
        )
        
        # Crear PacienteEspecial si es necesario
        if es_paciente_especial:
            paciente_especial = PacienteEspecial.objects.create(
                id_paciente_tutor=paciente,
                nombre_1=paciente.nombre_1,
                nombre_2=paciente.nombre_2,
                apellido_1=paciente.apellido_1,
                apellido_2=paciente.apellido_2,
                sexo=paciente.sexo,
                fecha_nacimiento=paciente.fecha_nacimiento,
                telefono=paciente.telefono,
                id_sede=sede,
                status=True
            )
            
            # Si tiene condición especial, guardar descripción en nombre_2 (workaround)
            if tiene_condicion:
                paciente_especial.nombre_2 = self.cleaned_data.get('descripcion_condicion', '')[:255]
                paciente_especial.save()
        
        # Si es menor de edad, crear registro del tutor
        if es_menor:
            tutor = PacienteEspecial.objects.create(
                id_paciente_tutor=paciente,
                nombre_1=self.cleaned_data.get('tutor_nombre', '').upper(),
                apellido_1='TUTOR',
                sexo=self.cleaned_data['sexo'],
                fecha_nacimiento=fecha_nacimiento,
                telefono=self.cleaned_data.get('tutor_telefono', ''),
                id_sede=sede,
                status=True
            )
            # Guardar información adicional en nombre_2 como workaround
            info_tutor = f"{self.cleaned_data.get('tutor_cedula', '')}|{self.cleaned_data.get('tutor_parentesco', '')}|{self.cleaned_data.get('tutor_correo', '')}"
            tutor.nombre_2 = info_tutor[:255]
            tutor.save()
        
        return user_paciente

class RegistroStaffForm(forms.Form):
    """Formulario de registro para staff (doctores y recepcionistas)"""
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
    
    # Datos personales
    nombre_1 = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-input w-full px-3 py-2 rounded-lg'})
    )
    nombre_2 = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-input w-full px-3 py-2 rounded-lg'})
    )
    apellido_1 = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-input w-full px-3 py-2 rounded-lg'})
    )
    apellido_2 = forms.CharField(
        max_length=100,
        required=False,
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

    # Rol del staff
    rol = forms.ChoiceField(
        choices=[
            ('medico', 'Médico'),
            ('recepcionista', 'Recepcionista'),
        ],
        required=True,
        widget=forms.Select(attrs={'class': 'form-input w-full px-3 py-2 rounded-lg'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Inicializar campos de dirección
        self.fields.update(DireccionForm().fields)
        
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

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Las contraseñas no coinciden")
        return password2

    def clean_username(self):
        username = self.cleaned_data.get('username')
        rol = self.cleaned_data.get('rol')
        
        if rol == 'medico' and UserDoctor.objects.filter(username=username).exists():
            raise forms.ValidationError("Este nombre de usuario ya está en uso")
        elif rol == 'recepcionista' and UserRecepcionista.objects.filter(username=username).exists():
            raise forms.ValidationError("Este nombre de usuario ya está en uso")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        rol = self.cleaned_data.get('rol')
        
        if rol == 'medico' and UserDoctor.objects.filter(correo=email).exists():
            raise forms.ValidationError("Este correo electrónico ya está en uso")
        elif rol == 'recepcionista' and UserRecepcionista.objects.filter(correo=email).exists():
            raise forms.ValidationError("Este correo electrónico ya está en uso")
        return email

    def clean_cedula(self):
        cedula = self.cleaned_data.get('cedula')
        rol = self.cleaned_data.get('rol')
        
        if rol == 'medico' and Doctor.objects.filter(cedula=cedula).exists():
            raise forms.ValidationError("Esta cédula ya está registrada")
        elif rol == 'recepcionista' and Recepcionista.objects.filter(cedula=cedula).exists():
            raise forms.ValidationError("Esta cédula ya está registrada")
        return cedula

    def save(self):
        # Obtener la sede por defecto (ID=1)
        try:
            sede = Sede.objects.get(id_sede=1)
        except Sede.DoesNotExist:
            raise ValidationError("No hay sedes configuradas en el sistema")

        rol = self.cleaned_data['rol']
        
        # Crear dirección según el rol
        if rol == 'medico':
            direccion = DireccionDoctor.objects.create(
                id_estado=self.cleaned_data['id_estado'],
                id_municipio=self.cleaned_data['id_municipio'],
                id_ciudad=self.cleaned_data['id_ciudad'],
                id_parroquia=self.cleaned_data['id_parroquia'],
                direccion=self.cleaned_data['direccion'],
                referencia=self.cleaned_data.get('referencia', ''),
                latitud=self.cleaned_data.get('latitud', ''),
                longitud=self.cleaned_data.get('longitud', '')
            )
            
            # Crear usuario doctor
            user_doctor = UserDoctor.objects.create_user(
                username=self.cleaned_data['username'],
                correo=self.cleaned_data['email'],
                password=self.cleaned_data['password1'],
                id_sede=sede
            )
            
            # Crear datos personales del doctor
            doctor = Doctor.objects.create(
                nombre_1=self.cleaned_data['nombre_1'],
                nombre_2=self.cleaned_data.get('nombre_2', ''),
                apellido_1=self.cleaned_data['apellido_1'],
                apellido_2=self.cleaned_data.get('apellido_2', ''),
                id_user_doctor=user_doctor,
                cedula=self.cleaned_data['cedula'],
                tipo_cedula=self.cleaned_data['tipo_cedula'],
                sexo=self.cleaned_data['sexo'],
                telefono=self.cleaned_data['telefono'],
                fecha_nacimiento=self.cleaned_data['fecha_nacimiento'],
                id_sede=sede,
                id_direccion_doctor=direccion
            )
            
            return user_doctor
            
        elif rol == 'recepcionista':
            direccion = DireccionRecepcionista.objects.create(
                id_estado=self.cleaned_data['id_estado'],
                id_municipio=self.cleaned_data['id_municipio'],
                id_ciudad=self.cleaned_data['id_ciudad'],
                id_parroquia=self.cleaned_data['id_parroquia'],
                direccion=self.cleaned_data['direccion'],
                referencia=self.cleaned_data.get('referencia', ''),
                latitud=self.cleaned_data.get('latitud', ''),
                longitud=self.cleaned_data.get('longitud', '')
            )
            
            # Crear usuario recepcionista
            user_recepcionista = UserRecepcionista.objects.create_user(
                username=self.cleaned_data['username'],
                correo=self.cleaned_data['email'],
                password=self.cleaned_data['password1'],
                id_sede=sede
            )
            
            # Crear datos personales del recepcionista
            recepcionista = Recepcionista.objects.create(
                nombre_1=self.cleaned_data['nombre_1'],
                nombre_2=self.cleaned_data.get('nombre_2', ''),
                apellido_1=self.cleaned_data['apellido_1'],
                apellido_2=self.cleaned_data.get('apellido_2', ''),
                id_user_recepcionista=user_recepcionista,
                cedula=self.cleaned_data['cedula'],
                tipo_cedula=self.cleaned_data['tipo_cedula'],
                sexo=self.cleaned_data['sexo'],
                telefono=self.cleaned_data['telefono'],
                fecha_nacimiento=self.cleaned_data['fecha_nacimiento'],
                id_sede=sede,
                id_direccion_recepcionista=direccion
            )
            
            return user_recepcionista


# ── Formularios separados para Doctor y Recepcionista ────────────────────────

_CSS = 'form-input w-full px-3 py-2 rounded-lg'

_TIPO_CEDULA_CHOICES = [
    ('V', 'V - Venezolano'), ('E', 'E - Extranjero'), ('J', 'J - Jurídico'),
    ('C', 'C - Consejo Comunal'), ('G', 'G - Gobierno'),
    ('P', 'P - Pasaporte'), ('F', 'F - Fallecido'),
]
_SEXO_CHOICES = [('M', 'Masculino'), ('F', 'Femenino')]


class EspecialidadDoctorChoiceField(forms.ModelChoiceField):
    """ModelChoiceField que muestra el nombre de la especialidad."""
    def label_from_instance(self, obj):
        if obj.id_especialidad and obj.id_especialidad.tipo_especialidad:
            return obj.id_especialidad.tipo_especialidad
        return f"Especialidad {obj.pk}"


class RegistrarDoctorForm(forms.Form):
    """Formulario dedicado para registrar un doctor con sus credenciales."""

    # ── Autenticación ──────────────────────────────────────────────────────
    username = forms.CharField(max_length=150, required=True,
        widget=forms.TextInput(attrs={'class': _CSS}))
    email = forms.EmailField(required=True,
        widget=forms.EmailInput(attrs={'class': _CSS}))
    password1 = forms.CharField(label="Contraseña", required=True,
        widget=forms.PasswordInput(attrs={'class': _CSS}))
    password2 = forms.CharField(label="Confirmar contraseña", required=True,
        widget=forms.PasswordInput(attrs={'class': _CSS}))

    # ── Datos personales ───────────────────────────────────────────────────
    nombre_1 = forms.CharField(max_length=100, required=True,
        widget=forms.TextInput(attrs={'class': _CSS}))
    nombre_2 = forms.CharField(max_length=100, required=False,
        widget=forms.TextInput(attrs={'class': _CSS}))
    apellido_1 = forms.CharField(max_length=100, required=True,
        widget=forms.TextInput(attrs={'class': _CSS}))
    apellido_2 = forms.CharField(max_length=100, required=False,
        widget=forms.TextInput(attrs={'class': _CSS}))
    cedula = forms.CharField(max_length=20, required=True,
        widget=forms.TextInput(attrs={'class': _CSS}))
    tipo_cedula = forms.ChoiceField(choices=_TIPO_CEDULA_CHOICES, required=True,
        widget=forms.Select(attrs={'class': _CSS}))
    sexo = forms.ChoiceField(choices=_SEXO_CHOICES, required=True,
        widget=forms.Select(attrs={'class': _CSS}))
    telefono = forms.CharField(max_length=50, required=True,
        widget=forms.TextInput(attrs={'class': _CSS}))
    fecha_nacimiento = forms.DateField(required=True,
        widget=forms.DateInput(attrs={'type': 'date', 'class': _CSS}))

    # ── Datos profesionales ────────────────────────────────────────────────
    id_especialidad_doctor = EspecialidadDoctorChoiceField(
        queryset=EspecialidadDoctor.objects.select_related('id_especialidad').all(),
        required=False, empty_label="Sin especialidad asignada",
        widget=forms.Select(attrs={'class': _CSS}))
    id_consultorio = forms.ModelChoiceField(
        queryset=Consultorio.objects.filter(status__in=[True, None]),
        required=False, empty_label="Sin consultorio asignado",
        widget=forms.Select(attrs={'class': _CSS}))
    id_horario = forms.ModelChoiceField(
        queryset=Horario.objects.all(),
        required=False, empty_label="Sin horario asignado",
        widget=forms.Select(attrs={'class': _CSS}))

    # ── Dirección ──────────────────────────────────────────────────────────
    id_estado = forms.ModelChoiceField(queryset=Estado.objects.all(),
        required=True, empty_label="Seleccione un estado",
        widget=forms.Select(attrs={'class': _CSS, 'id': 'id_estado_doc'}))
    id_municipio = forms.ModelChoiceField(queryset=Municipio.objects.none(),
        required=True, empty_label="Seleccione un municipio",
        widget=forms.Select(attrs={'class': _CSS, 'id': 'id_municipio_doc'}))
    id_ciudad = forms.ModelChoiceField(queryset=Ciudad.objects.none(),
        required=True, empty_label="Seleccione una ciudad",
        widget=forms.Select(attrs={'class': _CSS, 'id': 'id_ciudad_doc'}))
    id_parroquia = forms.ModelChoiceField(queryset=Parroquia.objects.none(),
        required=True, empty_label="Seleccione una parroquia",
        widget=forms.Select(attrs={'class': _CSS, 'id': 'id_parroquia_doc'}))
    direccion = forms.CharField(required=True,
        widget=forms.Textarea(attrs={'rows': 3, 'class': _CSS}))
    referencia = forms.CharField(required=False,
        widget=forms.Textarea(attrs={'rows': 2, 'class': _CSS}))
    latitud = forms.CharField(max_length=100, required=False,
        widget=forms.TextInput(attrs={'class': _CSS}))
    longitud = forms.CharField(max_length=100, required=False,
        widget=forms.TextInput(attrs={'class': _CSS}))

    def __init__(self, *args, sede_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        if sede_id:
            self.fields['id_consultorio'].queryset = Consultorio.objects.filter(
                id_sede_id=sede_id, status__in=[True, None])
            self.fields['id_horario'].queryset = Horario.objects.filter(id_sede_id=sede_id)
            # Filtra especialidades activas de esta sede
            self.fields['id_especialidad_doctor'].queryset = (
                EspecialidadDoctor.objects
                .filter(id_especialidad__id_sede=sede_id, id_especialidad__status=True)
                .select_related('id_especialidad')
            )
        if 'id_estado' in self.data:
            try:
                estado_id = int(self.data['id_estado'])
                self.fields['id_municipio'].queryset = Municipio.objects.filter(id_estado=estado_id)
                self.fields['id_ciudad'].queryset = Ciudad.objects.filter(id_estado=estado_id)
            except (ValueError, TypeError):
                pass
        if 'id_municipio' in self.data:
            try:
                municipio_id = int(self.data['id_municipio'])
                self.fields['id_parroquia'].queryset = Parroquia.objects.filter(id_municipio=municipio_id)
            except (ValueError, TypeError):
                pass

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        return p2

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if UserDoctor.objects.filter(username=username).exists():
            raise forms.ValidationError("Este nombre de usuario ya está en uso.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if UserDoctor.objects.filter(email=email).exists():
            raise forms.ValidationError("Este correo ya está registrado para un doctor.")
        return email

    def clean_cedula(self):
        cedula = self.cleaned_data.get('cedula')
        if Doctor.objects.filter(cedula=cedula).exists():
            raise forms.ValidationError("Esta cédula ya está registrada.")
        return cedula

    def clean_fecha_nacimiento(self):
        fecha = self.cleaned_data.get('fecha_nacimiento')
        if fecha:
            hoy = date.today()
            edad = hoy.year - fecha.year - ((hoy.month, hoy.day) < (fecha.month, fecha.day))
            if edad < 18:
                raise forms.ValidationError(
                    "El doctor debe tener al menos 18 años de edad."
                )
        return fecha

    def save(self, sede):
        from django.utils import timezone
        direccion = DireccionDoctor.objects.create(
            id_estado=self.cleaned_data['id_estado'],
            id_municipio=self.cleaned_data['id_municipio'],
            id_ciudad=self.cleaned_data['id_ciudad'],
            id_parroquia=self.cleaned_data['id_parroquia'],
            direccion=self.cleaned_data['direccion'],
            referencia=self.cleaned_data.get('referencia') or '',
            latitud=self.cleaned_data.get('latitud') or '',
            longitud=self.cleaned_data.get('longitud') or '',
        )
        user_doctor = UserDoctor.objects.create_user(
            username=self.cleaned_data['username'],
            correo=self.cleaned_data['email'],
            password=self.cleaned_data['password1'],
            id_sede=sede,
        )
        espec_obj   = self.cleaned_data.get('id_especialidad_doctor')
        consul_obj  = self.cleaned_data.get('id_consultorio')
        horario_obj = self.cleaned_data.get('id_horario')
        Doctor.objects.create(
            nombre_1=self.cleaned_data['nombre_1'],
            nombre_2=self.cleaned_data.get('nombre_2') or '',
            apellido_1=self.cleaned_data['apellido_1'],
            apellido_2=self.cleaned_data.get('apellido_2') or '',
            id_user_doctor=user_doctor,
            cedula=self.cleaned_data['cedula'],
            tipo_cedula=self.cleaned_data['tipo_cedula'],
            sexo=self.cleaned_data['sexo'],
            telefono=self.cleaned_data['telefono'],
            fecha_nacimiento=self.cleaned_data['fecha_nacimiento'],
            id_sede=sede,
            id_direccion_doctor=direccion,
            fecha_registro=timezone.now(),
            status=True,
            id_especialidad_doctor=espec_obj.pk if espec_obj else None,
            id_consultorio=consul_obj.pk if consul_obj else None,
            id_horario=horario_obj.pk if horario_obj else None,
        )
        return user_doctor


class RegistrarRecepcionistaForm(forms.Form):
    """Formulario dedicado para registrar una recepcionista."""

    # ── Autenticación ──────────────────────────────────────────────────────
    username = forms.CharField(max_length=150, required=True,
        widget=forms.TextInput(attrs={'class': _CSS}))
    email = forms.EmailField(required=True,
        widget=forms.EmailInput(attrs={'class': _CSS}))
    password1 = forms.CharField(label="Contraseña", required=True,
        widget=forms.PasswordInput(attrs={'class': _CSS}))
    password2 = forms.CharField(label="Confirmar contraseña", required=True,
        widget=forms.PasswordInput(attrs={'class': _CSS}))

    # ── Datos personales ───────────────────────────────────────────────────
    nombre_1 = forms.CharField(max_length=100, required=True,
        widget=forms.TextInput(attrs={'class': _CSS}))
    nombre_2 = forms.CharField(max_length=100, required=False,
        widget=forms.TextInput(attrs={'class': _CSS}))
    apellido_1 = forms.CharField(max_length=100, required=True,
        widget=forms.TextInput(attrs={'class': _CSS}))
    apellido_2 = forms.CharField(max_length=100, required=False,
        widget=forms.TextInput(attrs={'class': _CSS}))
    cedula = forms.CharField(max_length=20, required=True,
        widget=forms.TextInput(attrs={'class': _CSS}))
    tipo_cedula = forms.ChoiceField(choices=_TIPO_CEDULA_CHOICES, required=True,
        widget=forms.Select(attrs={'class': _CSS}))
    sexo = forms.ChoiceField(choices=_SEXO_CHOICES, required=True,
        widget=forms.Select(attrs={'class': _CSS}))
    telefono = forms.CharField(max_length=50, required=True,
        widget=forms.TextInput(attrs={'class': _CSS}))
    fecha_nacimiento = forms.DateField(required=True,
        widget=forms.DateInput(attrs={'type': 'date', 'class': _CSS}))

    # ── Datos profesionales ────────────────────────────────────────────────
    id_horario = forms.ModelChoiceField(
        queryset=Horario.objects.none(),
        required=False, empty_label="Sin horario asignado",
        widget=forms.Select(attrs={'class': _CSS}))

    # ── Dirección ──────────────────────────────────────────────────────────
    id_estado = forms.ModelChoiceField(queryset=Estado.objects.all(),
        required=True, empty_label="Seleccione un estado",
        widget=forms.Select(attrs={'class': _CSS, 'id': 'id_estado_rec'}))
    id_municipio = forms.ModelChoiceField(queryset=Municipio.objects.none(),
        required=True, empty_label="Seleccione un municipio",
        widget=forms.Select(attrs={'class': _CSS, 'id': 'id_municipio_rec'}))
    id_ciudad = forms.ModelChoiceField(queryset=Ciudad.objects.none(),
        required=True, empty_label="Seleccione una ciudad",
        widget=forms.Select(attrs={'class': _CSS, 'id': 'id_ciudad_rec'}))
    id_parroquia = forms.ModelChoiceField(queryset=Parroquia.objects.none(),
        required=True, empty_label="Seleccione una parroquia",
        widget=forms.Select(attrs={'class': _CSS, 'id': 'id_parroquia_rec'}))
    direccion = forms.CharField(required=True,
        widget=forms.Textarea(attrs={'rows': 3, 'class': _CSS}))
    referencia = forms.CharField(required=False,
        widget=forms.Textarea(attrs={'rows': 2, 'class': _CSS}))
    latitud = forms.CharField(max_length=100, required=False,
        widget=forms.TextInput(attrs={'class': _CSS}))
    longitud = forms.CharField(max_length=100, required=False,
        widget=forms.TextInput(attrs={'class': _CSS}))

    def __init__(self, *args, sede_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtra horarios de la sede del administrador
        if sede_id:
            self.fields['id_horario'].queryset = Horario.objects.filter(id_sede_id=sede_id)
        if 'id_estado' in self.data:
            try:
                estado_id = int(self.data['id_estado'])
                self.fields['id_municipio'].queryset = Municipio.objects.filter(id_estado=estado_id)
                self.fields['id_ciudad'].queryset = Ciudad.objects.filter(id_estado=estado_id)
            except (ValueError, TypeError):
                pass
        if 'id_municipio' in self.data:
            try:
                municipio_id = int(self.data['id_municipio'])
                self.fields['id_parroquia'].queryset = Parroquia.objects.filter(id_municipio=municipio_id)
            except (ValueError, TypeError):
                pass

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        return p2

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if UserRecepcionista.objects.filter(username=username).exists():
            raise forms.ValidationError("Este nombre de usuario ya está en uso.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if UserRecepcionista.objects.filter(email=email).exists():
            raise forms.ValidationError("Este correo ya está registrado para una recepcionista.")
        return email

    def clean_cedula(self):
        cedula = self.cleaned_data.get('cedula')
        if Recepcionista.objects.filter(cedula=cedula).exists():
            raise forms.ValidationError("Esta cédula ya está registrada.")
        return cedula

    def clean_fecha_nacimiento(self):
        fecha = self.cleaned_data.get('fecha_nacimiento')
        if fecha:
            hoy = date.today()
            edad = hoy.year - fecha.year - ((hoy.month, hoy.day) < (fecha.month, fecha.day))
            if edad < 18:
                raise forms.ValidationError(
                    "La recepcionista debe tener al menos 18 años de edad."
                )
        return fecha

    def save(self, sede):
        from django.utils import timezone
        direccion = DireccionRecepcionista.objects.create(
            id_estado=self.cleaned_data['id_estado'],
            id_municipio=self.cleaned_data['id_municipio'],
            id_ciudad=self.cleaned_data['id_ciudad'],
            id_parroquia=self.cleaned_data['id_parroquia'],
            direccion=self.cleaned_data['direccion'],
            referencia=self.cleaned_data.get('referencia') or '',
            latitud=self.cleaned_data.get('latitud') or '',
            longitud=self.cleaned_data.get('longitud') or '',
        )
        user_recepcionista = UserRecepcionista.objects.create_user(
            username=self.cleaned_data['username'],
            correo=self.cleaned_data['email'],
            password=self.cleaned_data['password1'],
            id_sede=sede,
        )
        horario_obj = self.cleaned_data.get('id_horario')
        Recepcionista.objects.create(
            nombre_1=self.cleaned_data['nombre_1'],
            nombre_2=self.cleaned_data.get('nombre_2') or '',
            apellido_1=self.cleaned_data['apellido_1'],
            apellido_2=self.cleaned_data.get('apellido_2') or '',
            id_user_recepcionista=user_recepcionista,
            cedula=self.cleaned_data['cedula'],
            tipo_cedula=self.cleaned_data['tipo_cedula'],
            sexo=self.cleaned_data['sexo'],
            telefono=self.cleaned_data['telefono'],
            fecha_nacimiento=self.cleaned_data['fecha_nacimiento'],
            id_sede=sede,
            id_direccion_recepcionista=direccion,
            fecha_registro=timezone.now(),
            status=True,
            id_horario=horario_obj.pk if horario_obj else None,
        )
        return user_recepcionista


# ── Formularios de edición de Doctor y Recepcionista ─────────────────────────

class EditarDoctorForm(forms.Form):
    """Editar datos de un doctor existente (no crea registros nuevos)."""

    # ── Cuenta de acceso ───────────────────────────────────────────────────
    username = forms.CharField(max_length=150, required=True,
        widget=forms.TextInput(attrs={'class': _CSS}))
    email = forms.EmailField(required=True,
        widget=forms.EmailInput(attrs={'class': _CSS}))
    status = forms.BooleanField(required=False, label="Usuario activo",
        widget=forms.CheckboxInput(attrs={'class': 'h-5 w-5 text-green-600 rounded border-gray-300'}))
    password1 = forms.CharField(label="Nueva contraseña", required=False,
        widget=forms.PasswordInput(attrs={
            'class': _CSS,
            'placeholder': 'Dejar vacío para no cambiar',
        }))
    password2 = forms.CharField(label="Confirmar contraseña", required=False,
        widget=forms.PasswordInput(attrs={'class': _CSS}))

    # ── Datos personales ───────────────────────────────────────────────────
    nombre_1   = forms.CharField(max_length=100, required=True,  widget=forms.TextInput(attrs={'class': _CSS}))
    nombre_2   = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': _CSS}))
    apellido_1 = forms.CharField(max_length=100, required=True,  widget=forms.TextInput(attrs={'class': _CSS}))
    apellido_2 = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': _CSS}))
    cedula     = forms.CharField(max_length=20,  required=True,  widget=forms.TextInput(attrs={'class': _CSS}))
    tipo_cedula = forms.ChoiceField(choices=_TIPO_CEDULA_CHOICES, required=True,
        widget=forms.Select(attrs={'class': _CSS}))
    sexo = forms.ChoiceField(choices=_SEXO_CHOICES, required=True,
        widget=forms.Select(attrs={'class': _CSS}))
    telefono = forms.CharField(max_length=50, required=True,
        widget=forms.TextInput(attrs={'class': _CSS}))
    fecha_nacimiento = forms.DateField(required=True,
        widget=forms.DateInput(attrs={'type': 'date', 'class': _CSS}))

    # ── Profesionales ──────────────────────────────────────────────────────
    id_especialidad_doctor = EspecialidadDoctorChoiceField(
        queryset=EspecialidadDoctor.objects.select_related('id_especialidad').all(),
        required=False, empty_label="Sin especialidad asignada",
        widget=forms.Select(attrs={'class': _CSS}))
    id_consultorio = forms.ModelChoiceField(
        queryset=Consultorio.objects.filter(status__in=[True, None]),
        required=False, empty_label="Sin consultorio asignado",
        widget=forms.Select(attrs={'class': _CSS}))
    id_horario = forms.ModelChoiceField(
        queryset=Horario.objects.all(),
        required=False, empty_label="Sin horario asignado",
        widget=forms.Select(attrs={'class': _CSS}))

    # ── Dirección ──────────────────────────────────────────────────────────
    id_estado    = forms.ModelChoiceField(queryset=Estado.objects.all(), required=True,
        empty_label="Seleccione un estado",    widget=forms.Select(attrs={'class': _CSS}))
    id_municipio = forms.ModelChoiceField(queryset=Municipio.objects.none(), required=True,
        empty_label="Seleccione un municipio", widget=forms.Select(attrs={'class': _CSS}))
    id_ciudad    = forms.ModelChoiceField(queryset=Ciudad.objects.none(), required=True,
        empty_label="Seleccione una ciudad",   widget=forms.Select(attrs={'class': _CSS}))
    id_parroquia = forms.ModelChoiceField(queryset=Parroquia.objects.none(), required=True,
        empty_label="Seleccione una parroquia", widget=forms.Select(attrs={'class': _CSS}))
    direccion  = forms.CharField(required=True,  widget=forms.Textarea(attrs={'rows': 3, 'class': _CSS}))
    referencia = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2, 'class': _CSS}))
    latitud    = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': _CSS}))
    longitud   = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': _CSS}))

    def __init__(self, *args, doctor_pk=None, user_doctor_pk=None, sede_id=None, **kwargs):
        self._doctor_pk = doctor_pk
        self._user_doctor_pk = user_doctor_pk
        initial = kwargs.get('initial', {})
        super().__init__(*args, **kwargs)

        if sede_id:
            self.fields['id_consultorio'].queryset = Consultorio.objects.filter(
                id_sede_id=sede_id, status__in=[True, None])
            self.fields['id_horario'].queryset = Horario.objects.filter(id_sede_id=sede_id)
            # Filtra especialidades activas de esta sede
            self.fields['id_especialidad_doctor'].queryset = (
                EspecialidadDoctor.objects
                .filter(id_especialidad__id_sede=sede_id, id_especialidad__status=True)
                .select_related('id_especialidad')
            )

        estado_id = None
        if self.data.get('id_estado'):
            try:
                estado_id = int(self.data['id_estado'])
            except (ValueError, TypeError):
                pass
        elif initial.get('id_estado'):
            est = initial['id_estado']
            estado_id = est.pk if hasattr(est, 'pk') else int(est)
        if estado_id:
            self.fields['id_municipio'].queryset = Municipio.objects.filter(id_estado=estado_id)
            self.fields['id_ciudad'].queryset    = Ciudad.objects.filter(id_estado=estado_id)

        municipio_id = None
        if self.data.get('id_municipio'):
            try:
                municipio_id = int(self.data['id_municipio'])
            except (ValueError, TypeError):
                pass
        elif initial.get('id_municipio'):
            mun = initial['id_municipio']
            municipio_id = mun.pk if hasattr(mun, 'pk') else int(mun)
        if municipio_id:
            self.fields['id_parroquia'].queryset = Parroquia.objects.filter(id_municipio=municipio_id)

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 and not p2:
            raise forms.ValidationError("Por favor confirma la nueva contraseña.")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        return p2

    def clean_username(self):
        username = self.cleaned_data.get('username')
        qs = UserDoctor.objects.filter(username=username)
        if self._user_doctor_pk:
            qs = qs.exclude(pk=self._user_doctor_pk)
        if qs.exists():
            raise forms.ValidationError("Este nombre de usuario ya está en uso.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        qs = UserDoctor.objects.filter(email=email)
        if self._user_doctor_pk:
            qs = qs.exclude(pk=self._user_doctor_pk)
        if qs.exists():
            raise forms.ValidationError("Este correo ya está registrado para un doctor.")
        return email

    def clean_cedula(self):
        cedula = self.cleaned_data.get('cedula')
        qs = Doctor.objects.filter(cedula=cedula)
        if self._doctor_pk:
            qs = qs.exclude(pk=self._doctor_pk)
        if qs.exists():
            raise forms.ValidationError("Esta cédula ya está registrada.")
        return cedula

    def clean_fecha_nacimiento(self):
        fecha = self.cleaned_data.get('fecha_nacimiento')
        if fecha:
            hoy = date.today()
            edad = hoy.year - fecha.year - ((hoy.month, hoy.day) < (fecha.month, fecha.day))
            if edad < 18:
                raise forms.ValidationError(
                    "El doctor debe tener al menos 18 años de edad."
                )
        return fecha

    def save(self, doctor, user_doctor, direccion=None):
        cd = self.cleaned_data
        address_data = {
            'id_estado':    cd['id_estado'],
            'id_municipio': cd['id_municipio'],
            'id_ciudad':    cd['id_ciudad'],
            'id_parroquia': cd['id_parroquia'],
            'direccion':    cd['direccion'],
            'referencia':   cd.get('referencia') or '',
            'latitud':      cd.get('latitud') or '',
            'longitud':     cd.get('longitud') or '',
        }
        if direccion:
            for k, v in address_data.items():
                setattr(direccion, k, v)
            direccion.save()
        else:
            direccion = DireccionDoctor.objects.create(**address_data)

        user_doctor.username = cd['username']
        user_doctor.email    = cd['email']
        user_doctor.status   = cd['status']
        if cd.get('password1'):
            user_doctor.set_password(cd['password1'])
        user_doctor.save()

        espec_obj   = cd.get('id_especialidad_doctor')
        consul_obj  = cd.get('id_consultorio')
        horario_obj = cd.get('id_horario')
        doctor.nombre_1   = cd['nombre_1']
        doctor.nombre_2   = cd.get('nombre_2') or ''
        doctor.apellido_1 = cd['apellido_1']
        doctor.apellido_2 = cd.get('apellido_2') or ''
        doctor.cedula          = cd['cedula']
        doctor.tipo_cedula     = cd['tipo_cedula']
        doctor.sexo            = cd['sexo']
        doctor.telefono        = cd['telefono']
        doctor.fecha_nacimiento = cd['fecha_nacimiento']
        doctor.id_especialidad_doctor = espec_obj.pk if espec_obj else None
        doctor.id_consultorio         = consul_obj.pk if consul_obj else None
        doctor.id_horario             = horario_obj.pk if horario_obj else None
        doctor.id_direccion_doctor    = direccion
        doctor.save()
        return doctor


class EditarRecepcionistaForm(forms.Form):
    """Editar datos de una recepcionista existente (no crea registros nuevos)."""

    # ── Cuenta de acceso ───────────────────────────────────────────────────
    username = forms.CharField(max_length=150, required=True,
        widget=forms.TextInput(attrs={'class': _CSS}))
    email = forms.EmailField(required=True,
        widget=forms.EmailInput(attrs={'class': _CSS}))
    status = forms.BooleanField(required=False, label="Usuario activo",
        widget=forms.CheckboxInput(attrs={'class': 'h-5 w-5 text-blue-600 rounded border-gray-300'}))
    password1 = forms.CharField(label="Nueva contraseña", required=False,
        widget=forms.PasswordInput(attrs={
            'class': _CSS,
            'placeholder': 'Dejar vacío para no cambiar',
        }))
    password2 = forms.CharField(label="Confirmar contraseña", required=False,
        widget=forms.PasswordInput(attrs={'class': _CSS}))

    # ── Datos personales ───────────────────────────────────────────────────
    nombre_1   = forms.CharField(max_length=100, required=True,  widget=forms.TextInput(attrs={'class': _CSS}))
    nombre_2   = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': _CSS}))
    apellido_1 = forms.CharField(max_length=100, required=True,  widget=forms.TextInput(attrs={'class': _CSS}))
    apellido_2 = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': _CSS}))
    cedula     = forms.CharField(max_length=20,  required=True,  widget=forms.TextInput(attrs={'class': _CSS}))
    tipo_cedula = forms.ChoiceField(choices=_TIPO_CEDULA_CHOICES, required=True,
        widget=forms.Select(attrs={'class': _CSS}))
    sexo = forms.ChoiceField(choices=_SEXO_CHOICES, required=True,
        widget=forms.Select(attrs={'class': _CSS}))
    telefono = forms.CharField(max_length=50, required=True,
        widget=forms.TextInput(attrs={'class': _CSS}))
    fecha_nacimiento = forms.DateField(required=True,
        widget=forms.DateInput(attrs={'type': 'date', 'class': _CSS}))

    # ── Datos profesionales ────────────────────────────────────────────────
    id_horario = forms.ModelChoiceField(
        queryset=Horario.objects.none(),
        required=False, empty_label="Sin horario asignado",
        widget=forms.Select(attrs={'class': _CSS}))

    # ── Dirección ──────────────────────────────────────────────────────────
    id_estado    = forms.ModelChoiceField(queryset=Estado.objects.all(), required=True,
        empty_label="Seleccione un estado",    widget=forms.Select(attrs={'class': _CSS}))
    id_municipio = forms.ModelChoiceField(queryset=Municipio.objects.none(), required=True,
        empty_label="Seleccione un municipio", widget=forms.Select(attrs={'class': _CSS}))
    id_ciudad    = forms.ModelChoiceField(queryset=Ciudad.objects.none(), required=True,
        empty_label="Seleccione una ciudad",   widget=forms.Select(attrs={'class': _CSS}))
    id_parroquia = forms.ModelChoiceField(queryset=Parroquia.objects.none(), required=True,
        empty_label="Seleccione una parroquia", widget=forms.Select(attrs={'class': _CSS}))
    direccion  = forms.CharField(required=True,  widget=forms.Textarea(attrs={'rows': 3, 'class': _CSS}))
    referencia = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2, 'class': _CSS}))
    latitud    = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': _CSS}))
    longitud   = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': _CSS}))

    def __init__(self, *args, recepcionista_pk=None, user_recepcionista_pk=None, sede_id=None, **kwargs):
        self._recepcionista_pk      = recepcionista_pk
        self._user_recepcionista_pk = user_recepcionista_pk
        initial = kwargs.get('initial', {})
        super().__init__(*args, **kwargs)

        # Filtra horarios de la sede del administrador
        if sede_id:
            self.fields['id_horario'].queryset = Horario.objects.filter(id_sede_id=sede_id)

        estado_id = None
        if self.data.get('id_estado'):
            try:
                estado_id = int(self.data['id_estado'])
            except (ValueError, TypeError):
                pass
        elif initial.get('id_estado'):
            est = initial['id_estado']
            estado_id = est.pk if hasattr(est, 'pk') else int(est)
        if estado_id:
            self.fields['id_municipio'].queryset = Municipio.objects.filter(id_estado=estado_id)
            self.fields['id_ciudad'].queryset    = Ciudad.objects.filter(id_estado=estado_id)

        municipio_id = None
        if self.data.get('id_municipio'):
            try:
                municipio_id = int(self.data['id_municipio'])
            except (ValueError, TypeError):
                pass
        elif initial.get('id_municipio'):
            mun = initial['id_municipio']
            municipio_id = mun.pk if hasattr(mun, 'pk') else int(mun)
        if municipio_id:
            self.fields['id_parroquia'].queryset = Parroquia.objects.filter(id_municipio=municipio_id)

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 and not p2:
            raise forms.ValidationError("Por favor confirma la nueva contraseña.")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        return p2

    def clean_username(self):
        username = self.cleaned_data.get('username')
        qs = UserRecepcionista.objects.filter(username=username)
        if self._user_recepcionista_pk:
            qs = qs.exclude(pk=self._user_recepcionista_pk)
        if qs.exists():
            raise forms.ValidationError("Este nombre de usuario ya está en uso.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        qs = UserRecepcionista.objects.filter(email=email)
        if self._user_recepcionista_pk:
            qs = qs.exclude(pk=self._user_recepcionista_pk)
        if qs.exists():
            raise forms.ValidationError("Este correo ya está registrado para una recepcionista.")
        return email

    def clean_cedula(self):
        cedula = self.cleaned_data.get('cedula')
        qs = Recepcionista.objects.filter(cedula=cedula)
        if self._recepcionista_pk:
            qs = qs.exclude(pk=self._recepcionista_pk)
        if qs.exists():
            raise forms.ValidationError("Esta cédula ya está registrada.")
        return cedula

    def clean_fecha_nacimiento(self):
        fecha = self.cleaned_data.get('fecha_nacimiento')
        if fecha:
            hoy = date.today()
            edad = hoy.year - fecha.year - ((hoy.month, hoy.day) < (fecha.month, fecha.day))
            if edad < 18:
                raise forms.ValidationError(
                    "La recepcionista debe tener al menos 18 años de edad."
                )
        return fecha

    def save(self, recepcionista, user_recepcionista, direccion=None):
        cd = self.cleaned_data
        address_data = {
            'id_estado':    cd['id_estado'],
            'id_municipio': cd['id_municipio'],
            'id_ciudad':    cd['id_ciudad'],
            'id_parroquia': cd['id_parroquia'],
            'direccion':    cd['direccion'],
            'referencia':   cd.get('referencia') or '',
            'latitud':      cd.get('latitud') or '',
            'longitud':     cd.get('longitud') or '',
        }
        if direccion:
            for k, v in address_data.items():
                setattr(direccion, k, v)
            direccion.save()
        else:
            direccion = DireccionRecepcionista.objects.create(**address_data)

        user_recepcionista.username = cd['username']
        user_recepcionista.email    = cd['email']
        user_recepcionista.status   = cd['status']
        if cd.get('password1'):
            user_recepcionista.set_password(cd['password1'])
        user_recepcionista.save()

        recepcionista.nombre_1   = cd['nombre_1']
        recepcionista.nombre_2   = cd.get('nombre_2') or ''
        recepcionista.apellido_1 = cd['apellido_1']
        recepcionista.apellido_2 = cd.get('apellido_2') or ''
        recepcionista.cedula          = cd['cedula']
        recepcionista.tipo_cedula     = cd['tipo_cedula']
        recepcionista.sexo            = cd['sexo']
        recepcionista.telefono        = cd['telefono']
        recepcionista.fecha_nacimiento = cd['fecha_nacimiento']
        recepcionista.id_direccion_recepcionista = direccion
        horario_obj = cd.get('id_horario')
        recepcionista.id_horario = horario_obj.pk if horario_obj else None
        recepcionista.save()
        return recepcionista


# ── Utilidad compartida: validar que una fecha de nacimiento corresponda a menor de edad ──

def _validar_menor_de_edad(fecha):
    """
    Lanza forms.ValidationError si 'fecha' correspond a una persona de 18 años o más.
    También rechaza fechas futuras.
    Reutilizada por RegistrarPacienteEspecialForm y EditarPacienteEspecialForm.
    """
    if not fecha:
        return fecha
    hoy = date.today()
    if fecha > hoy:
        raise forms.ValidationError("La fecha de nacimiento no puede ser en el futuro.")
    edad = hoy.year - fecha.year - ((hoy.month, hoy.day) < (fecha.month, fecha.day))
    if edad >= 18:
        raise forms.ValidationError(
            f"El paciente especial debe ser menor de 18 años "
            f"(edad ingresada: {edad} años)."
        )
    return fecha


# ── Formulario de registro de paciente especial (menor de edad) ──────────────

class RegistrarPacienteEspecialForm(forms.Form):
    """
    Formulario para que el tutor-paciente registre a un menor de edad.
    No incluye credenciales de acceso; el menor es gestionado por el tutor.
    Los campos id_paciente_tutor, id_sede, fecha_registro y status se
    asignan automáticamente en la vista.

    Validación de edad: bloqueante — se rechaza si la persona tiene 18 años o más.
    """
    _CSS = (
        'form-input w-full px-3 py-2 rounded-lg border border-gray-300 '
        'focus:outline-none focus:ring-2 focus:ring-green-500'
    )
    SEXO_CHOICES = [
        ('',  'Seleccionar...'),
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('O', 'Otro'),
    ]
    TIPO_CEDULA_CHOICES_REGISTRO = [
        ('',  'Seleccionar... (opcional)'),
        ('V', 'V - Venezolano'),
        ('E', 'E - Extranjero'),
        ('J', 'J - Jurídico'),
        ('C', 'C - Consejo Comunal'),
        ('G', 'G - Gobierno'),
        ('P', 'P - Pasaporte'),
    ]

    _RE_NOMBRE = r"^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$"
    _RE_TELEFONO = r"^[\d\s\-\+\(\)]+$"
    _MSG_NOMBRE = "Solo se permiten letras, espacios y tildes."
    _MSG_TELEFONO = "Solo se permiten números, espacios, guiones, paréntesis y '+'"

    nombre_1 = forms.CharField(
        max_length=30, required=True, label="Primer nombre",
        widget=forms.TextInput(attrs={
            'class': _CSS,
            'placeholder': 'Primer nombre',
            'minlength': '2',
            'maxlength': '30',
            'pattern': r'[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+',
            'title': 'Solo letras, espacios y tildes. Mínimo 2, máximo 30 caracteres.',
        }),
        validators=[
            RegexValidator(_RE_NOMBRE, _MSG_NOMBRE),
            MinLengthValidator(2, "Debe tener al menos 2 caracteres."),
        ]
    )
    nombre_2 = forms.CharField(
        max_length=30, required=False, label="Segundo nombre",
        widget=forms.TextInput(attrs={
            'class': _CSS,
            'placeholder': 'Segundo nombre (opcional)',
            'minlength': '2',
            'maxlength': '30',
            'pattern': r'[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+',
            'title': 'Solo letras, espacios y tildes. Máximo 30 caracteres.',
        }),
        validators=[
            RegexValidator(_RE_NOMBRE, _MSG_NOMBRE),
            MinLengthValidator(2, "Debe tener al menos 2 caracteres."),
        ]
    )
    apellido_1 = forms.CharField(
        max_length=30, required=True, label="Primer apellido",
        widget=forms.TextInput(attrs={
            'class': _CSS,
            'placeholder': 'Primer apellido',
            'minlength': '2',
            'maxlength': '30',
            'pattern': r'[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+',
            'title': 'Solo letras, espacios y tildes. Mínimo 2, máximo 30 caracteres.',
        }),
        validators=[
            RegexValidator(_RE_NOMBRE, _MSG_NOMBRE),
            MinLengthValidator(2, "Debe tener al menos 2 caracteres."),
        ]
    )
    apellido_2 = forms.CharField(
        max_length=30, required=False, label="Segundo apellido",
        widget=forms.TextInput(attrs={
            'class': _CSS,
            'placeholder': 'Segundo apellido (opcional)',
            'minlength': '2',
            'maxlength': '30',
            'pattern': r'[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+',
            'title': 'Solo letras, espacios y tildes. Máximo 30 caracteres.',
        }),
        validators=[
            RegexValidator(_RE_NOMBRE, _MSG_NOMBRE),
            MinLengthValidator(2, "Debe tener al menos 2 caracteres."),
        ]
    )
    sexo = forms.ChoiceField(
        choices=SEXO_CHOICES, required=True, label="Sexo",
        widget=forms.Select(attrs={'class': _CSS, 'required': 'required'})
    )
    fecha_nacimiento = forms.DateField(
        required=True, label="Fecha de nacimiento",
        widget=forms.DateInput(
            format='%Y-%m-%d',
            attrs={
                'type': 'date',
                'class': _CSS,
                'max': date.today().isoformat(),
                'required': 'required',
            }
        )
    )
    telefono = forms.CharField(
        max_length=20, required=False, label="Teléfono de contacto",
        widget=forms.TextInput(attrs={
            'class': _CSS,
            'placeholder': 'Teléfono (opcional)',
            'minlength': '7',
            'maxlength': '20',
            'pattern': r'[\d\s\-\+\(\)]+',
            'title': 'Solo números, espacios, guiones, paréntesis y +. Mínimo 7 caracteres.',
        }),
        validators=[
            RegexValidator(_RE_TELEFONO, _MSG_TELEFONO),
            MinLengthValidator(7, "Debe tener al menos 7 caracteres."),
        ]
    )
    tipo_cedula = forms.ChoiceField(
        choices=TIPO_CEDULA_CHOICES_REGISTRO, required=False, label="Tipo de cédula",
        widget=forms.Select(attrs={'class': _CSS})
    )
    cedula = forms.CharField(
        max_length=20, required=False, label="Número de cédula",
        widget=forms.TextInput(attrs={
            'class': _CSS,
            'placeholder': 'Número de cédula (opcional)',
            'minlength': '5',
            'maxlength': '20',
            'pattern': r'[\d\-]+',
            'title': 'Solo números y guiones. Mínimo 5, máximo 20 caracteres.',
        }),
    )

    def clean_nombre_1(self):
        val = self.cleaned_data['nombre_1'].strip()
        if not val:
            raise forms.ValidationError("El primer nombre es obligatorio.")
        if len(val) < 2:
            raise forms.ValidationError("Debe tener al menos 2 caracteres.")
        if len(val) > 30:
            raise forms.ValidationError("No puede exceder 30 caracteres.")
        return val.upper()

    def clean_nombre_2(self):
        val = (self.cleaned_data.get('nombre_2') or '').strip()
        if val and len(val) < 2:
            raise forms.ValidationError("Debe tener al menos 2 caracteres.")
        if val and len(val) > 30:
            raise forms.ValidationError("No puede exceder 30 caracteres.")
        return val.upper()

    def clean_apellido_1(self):
        val = self.cleaned_data['apellido_1'].strip()
        if not val:
            raise forms.ValidationError("El primer apellido es obligatorio.")
        if len(val) < 2:
            raise forms.ValidationError("Debe tener al menos 2 caracteres.")
        if len(val) > 30:
            raise forms.ValidationError("No puede exceder 30 caracteres.")
        return val.upper()

    def clean_apellido_2(self):
        val = (self.cleaned_data.get('apellido_2') or '').strip()
        if val and len(val) < 2:
            raise forms.ValidationError("Debe tener al menos 2 caracteres.")
        if val and len(val) > 30:
            raise forms.ValidationError("No puede exceder 30 caracteres.")
        return val.upper()

    def clean_telefono(self):
        val = (self.cleaned_data.get('telefono') or '').strip()
        if val:
            if len(val) < 7:
                raise forms.ValidationError("El teléfono debe tener al menos 7 caracteres.")
            if len(val) > 20:
                raise forms.ValidationError("El teléfono no puede exceder 20 caracteres.")
        return val

    def clean_cedula(self):
        val = (self.cleaned_data.get('cedula') or '').strip()
        if val and len(val) > 20:
            raise forms.ValidationError("La cédula no puede exceder 20 caracteres.")
        return val

    def clean(self):
        cleaned_data = super().clean()
        tipo_cedula = cleaned_data.get('tipo_cedula')
        cedula = cleaned_data.get('cedula')
        if tipo_cedula and not cedula:
            self.add_error('cedula', "Debe indicar el número de cédula si seleccionó un tipo.")
        if cedula and not tipo_cedula:
            self.add_error('tipo_cedula', "Debe seleccionar un tipo de cédula si indicó un número.")
        return cleaned_data

    def clean_fecha_nacimiento(self):
        """Bloquea si la fecha es futura o si la edad es >= 18 años."""
        return _validar_menor_de_edad(self.cleaned_data.get('fecha_nacimiento'))


# ── Formulario de edición de paciente especial ───────────────────────────────

class EditarPacienteEspecialForm(forms.Form):
    """
    Formulario para que el tutor-paciente edite los datos de un menor ya
    registrado. Solo expone los campos modificables; id_paciente_tutor,
    id_sede, fecha_registro y status se gestionan exclusivamente en la vista.

    Reutiliza _validar_menor_de_edad para la validación de edad.
    """
    _CSS = (
        'form-input w-full px-3 py-2 rounded-lg border border-gray-300 '
        'focus:outline-none focus:ring-2 focus:ring-green-500'
    )
    SEXO_CHOICES = [
        ('',  'Seleccionar...'),
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('O', 'Otro'),
    ]
    TIPO_CEDULA_CHOICES_REGISTRO = [
        ('',  'Seleccionar... (opcional)'),
        ('V', 'V - Venezolano'),
        ('E', 'E - Extranjero'),
        ('J', 'J - Jurídico'),
        ('C', 'C - Consejo Comunal'),
        ('G', 'G - Gobierno'),
        ('P', 'P - Pasaporte'),
    ]

    _RE_NOMBRE = r"^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$"
    _RE_TELEFONO = r"^[\d\s\-\+\(\)]+$"
    _MSG_NOMBRE = "Solo se permiten letras, espacios y tildes."
    _MSG_TELEFONO = "Solo se permiten números, espacios, guiones, paréntesis y '+'"

    nombre_1 = forms.CharField(
        max_length=30, required=True, label="Primer nombre",
        widget=forms.TextInput(attrs={
            'class': _CSS,
            'minlength': '2',
            'maxlength': '30',
            'pattern': r'[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+',
            'title': 'Solo letras, espacios y tildes. Mínimo 2, máximo 30 caracteres.',
        }),
        validators=[
            RegexValidator(_RE_NOMBRE, _MSG_NOMBRE),
            MinLengthValidator(2, "Debe tener al menos 2 caracteres."),
        ]
    )
    nombre_2 = forms.CharField(
        max_length=30, required=False, label="Segundo nombre",
        widget=forms.TextInput(attrs={
            'class': _CSS,
            'minlength': '2',
            'maxlength': '30',
            'pattern': r'[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+',
            'title': 'Solo letras, espacios y tildes. Máximo 30 caracteres.',
        }),
        validators=[
            RegexValidator(_RE_NOMBRE, _MSG_NOMBRE),
            MinLengthValidator(2, "Debe tener al menos 2 caracteres."),
        ]
    )
    apellido_1 = forms.CharField(
        max_length=30, required=True, label="Primer apellido",
        widget=forms.TextInput(attrs={
            'class': _CSS,
            'minlength': '2',
            'maxlength': '30',
            'pattern': r'[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+',
            'title': 'Solo letras, espacios y tildes. Mínimo 2, máximo 30 caracteres.',
        }),
        validators=[
            RegexValidator(_RE_NOMBRE, _MSG_NOMBRE),
            MinLengthValidator(2, "Debe tener al menos 2 caracteres."),
        ]
    )
    apellido_2 = forms.CharField(
        max_length=30, required=False, label="Segundo apellido",
        widget=forms.TextInput(attrs={
            'class': _CSS,
            'minlength': '2',
            'maxlength': '30',
            'pattern': r'[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+',
            'title': 'Solo letras, espacios y tildes. Máximo 30 caracteres.',
        }),
        validators=[
            RegexValidator(_RE_NOMBRE, _MSG_NOMBRE),
            MinLengthValidator(2, "Debe tener al menos 2 caracteres."),
        ]
    )
    sexo = forms.ChoiceField(
        choices=SEXO_CHOICES, required=True, label="Sexo",
        widget=forms.Select(attrs={'class': _CSS, 'required': 'required'})
    )
    fecha_nacimiento = forms.DateField(
        required=True, label="Fecha de nacimiento",
        widget=forms.DateInput(
            format='%Y-%m-%d',
            attrs={
                'type': 'date',
                'class': _CSS,
                'max': date.today().isoformat(),
                'required': 'required',
            }
        )
    )
    telefono = forms.CharField(
        max_length=50, required=False, label="Teléfono de contacto",
        widget=forms.TextInput(attrs={
            'class': _CSS,
            'minlength': '7',
            'maxlength': '20',
            'pattern': r'[\d\s\-\+\(\)]+',
            'title': 'Solo números, espacios, guiones, paréntesis y +. Mínimo 7 caracteres.',
        }),
        validators=[
            RegexValidator(_RE_TELEFONO, _MSG_TELEFONO),
            MinLengthValidator(7, "Debe tener al menos 7 caracteres."),
        ]
    )
    tipo_cedula = forms.ChoiceField(
        choices=TIPO_CEDULA_CHOICES_REGISTRO, required=False, label="Tipo de cédula",
        widget=forms.Select(attrs={'class': _CSS})
    )
    cedula = forms.CharField(
        max_length=20, required=False, label="Número de cédula",
        widget=forms.TextInput(attrs={
            'class': _CSS,
            'placeholder': 'Número de cédula (opcional)',
            'minlength': '5',
            'maxlength': '20',
            'pattern': r'[\d\-]+',
            'title': 'Solo números y guiones. Mínimo 5, máximo 20 caracteres.',
        }),
    )

    def clean_nombre_1(self):
        val = self.cleaned_data['nombre_1'].strip()
        if not val:
            raise forms.ValidationError("El primer nombre es obligatorio.")
        if len(val) < 2:
            raise forms.ValidationError("Debe tener al menos 2 caracteres.")
        if len(val) > 30:
            raise forms.ValidationError("No puede exceder 30 caracteres.")
        return val.upper()

    def clean_nombre_2(self):
        val = (self.cleaned_data.get('nombre_2') or '').strip()
        if val and len(val) < 2:
            raise forms.ValidationError("Debe tener al menos 2 caracteres.")
        if val and len(val) > 30:
            raise forms.ValidationError("No puede exceder 30 caracteres.")
        return val.upper()

    def clean_apellido_1(self):
        val = self.cleaned_data['apellido_1'].strip()
        if not val:
            raise forms.ValidationError("El primer apellido es obligatorio.")
        if len(val) < 2:
            raise forms.ValidationError("Debe tener al menos 2 caracteres.")
        if len(val) > 30:
            raise forms.ValidationError("No puede exceder 30 caracteres.")
        return val.upper()

    def clean_apellido_2(self):
        val = (self.cleaned_data.get('apellido_2') or '').strip()
        if val and len(val) < 2:
            raise forms.ValidationError("Debe tener al menos 2 caracteres.")
        if val and len(val) > 30:
            raise forms.ValidationError("No puede exceder 30 caracteres.")
        return val.upper()

    def clean_telefono(self):
        val = (self.cleaned_data.get('telefono') or '').strip()
        if val:
            if len(val) < 7:
                raise forms.ValidationError("El teléfono debe tener al menos 7 caracteres.")
            if len(val) > 20:
                raise forms.ValidationError("El teléfono no puede exceder 20 caracteres.")
        return val

    def clean_cedula(self):
        val = (self.cleaned_data.get('cedula') or '').strip()
        if val and len(val) > 20:
            raise forms.ValidationError("La cédula no puede exceder 20 caracteres.")
        return val

    def clean(self):
        cleaned_data = super().clean()
        tipo_cedula = cleaned_data.get('tipo_cedula')
        cedula = cleaned_data.get('cedula')
        if tipo_cedula and not cedula:
            self.add_error('cedula', "Debe indicar el número de cédula si seleccionó un tipo.")
        if cedula and not tipo_cedula:
            self.add_error('tipo_cedula', "Debe seleccionar un tipo de cédula si indicó un número.")
        return cleaned_data

    def clean_fecha_nacimiento(self):
        """Bloquea si la fecha es futura o si la edad es >= 18 años."""
        return _validar_menor_de_edad(self.cleaned_data.get('fecha_nacimiento'))


# ── Formulario de historial médico ───────────────────────────────────────────
# Los catálogos viven en citas.models; se importan aquí para no duplicar modelos.
from citas.models import Alergias, TipoSangre, Vacunas, Enfermedades

class HistorialMedicoForm(forms.Form):
    """
    Formulario de historial médico del paciente (adulto o menor).

    - alergias, vacunas, enfermedades: selección múltiple (M2M vía tablas intermedias).
    - id_tipo_sangre: selección única (FK directa en historial_medico_paciente).
    Todos los campos son opcionales (required=False).
    """
    _CSS_SELECT = (
        'form-input w-full px-3 py-2 rounded-lg border border-gray-300 '
        'focus:outline-none focus:ring-2 focus:ring-green-500'
    )

    # Tipo de sangre: desplegable de selección única
    id_tipo_sangre = forms.ModelChoiceField(
        queryset=TipoSangre.objects.all(),
        required=False,
        label='Tipo de sangre',
        empty_label='Desconocido',
        widget=forms.Select(attrs={'class': _CSS_SELECT}),
    )
    # Alergias, vacunas, enfermedades: checkboxes de selección múltiple
    alergias = forms.ModelMultipleChoiceField(
        queryset=Alergias.objects.all(),
        required=False,
        label='Alergias',
        widget=forms.CheckboxSelectMultiple(),
    )
    vacunas = forms.ModelMultipleChoiceField(
        queryset=Vacunas.objects.all(),
        required=False,
        label='Vacunas',
        widget=forms.CheckboxSelectMultiple(),
    )
    enfermedades = forms.ModelMultipleChoiceField(
        queryset=Enfermedades.objects.all(),
        required=False,
        label='Enfermedades',
        widget=forms.CheckboxSelectMultiple(),
    )


class RegistroSuperAdminForm(forms.Form):
    """Formulario de registro de Super Admin con validaciones estrictas."""

    # ── CREDENCIALES ──
    username = forms.CharField(
        max_length=30,
        min_length=3,
        required=True,
        label="Nombre de Usuario",
        validators=[
            RegexValidator(r'^[a-zA-Z0-9_]+$', 'Solo letras, números y guiones bajos'),
        ],
        widget=forms.TextInput(attrs={
            'class': 'form-input w-full pl-10 pr-4 py-3 rounded-xl text-gray-900 text-sm',
            'placeholder': 'usuario_ejemplo',
            'maxlength': '30',
        })
    )

    correo = forms.EmailField(
        max_length=100,
        required=True,
        label="Correo Electrónico",
        validators=[EmailValidator(message='Ingrese un correo electrónico válido')],
        widget=forms.EmailInput(attrs={
            'class': 'form-input w-full pl-10 pr-4 py-3 rounded-xl text-gray-900 text-sm',
            'placeholder': 'ejemplo@gmail.com',
            'maxlength': '100',
        })
    )

    password = forms.CharField(
        required=True,
        label="Contraseña",
        min_length=8,
        max_length=30,
        validators=[
            RegexValidator(
                r'^(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};:''",.<>/?\\|`~]).{8,30}$',
                'Debe contener al menos 1 mayúscula, 1 número, 1 carácter especial y tener entre 8 y 30 caracteres'
            ),
        ],
        widget=forms.PasswordInput(attrs={
            'class': 'form-input w-full pl-10 pr-4 py-3 rounded-xl text-gray-900 text-sm',
            'placeholder': 'Mínimo 8 caracteres',
            'maxlength': '30',
        })
    )

    password_confirm = forms.CharField(
        required=True,
        label="Confirmar Contraseña",
        min_length=8,
        max_length=30,
        widget=forms.PasswordInput(attrs={
            'class': 'form-input w-full pl-10 pr-4 py-3 rounded-xl text-gray-900 text-sm',
            'placeholder': 'Repite la contraseña',
            'maxlength': '30',
        })
    )

    # ── DATOS PERSONALES ──
    nombre_1 = forms.CharField(
        max_length=30,
        required=True,
        label="Primer Nombre",
        validators=[RegexValidator(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', 'Solo letras permitidas')],
        widget=forms.TextInput(attrs={
            'class': 'form-input w-full pl-10 pr-4 py-3 rounded-xl text-gray-900 text-sm',
            'placeholder': 'Juan',
            'maxlength': '30',
        })
    )

    nombre_2 = forms.CharField(
        max_length=30,
        required=False,
        label="Segundo Nombre",
        validators=[RegexValidator(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', 'Solo letras permitidas')],
        widget=forms.TextInput(attrs={
            'class': 'form-input w-full pl-10 pr-4 py-3 rounded-xl text-gray-900 text-sm',
            'placeholder': 'José',
            'maxlength': '30',
        })
    )

    apellido_1 = forms.CharField(
        max_length=30,
        required=True,
        label="Primer Apellido",
        validators=[RegexValidator(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', 'Solo letras permitidas')],
        widget=forms.TextInput(attrs={
            'class': 'form-input w-full pl-10 pr-4 py-3 rounded-xl text-gray-900 text-sm',
            'placeholder': 'Pérez',
            'maxlength': '30',
        })
    )

    apellido_2 = forms.CharField(
        max_length=30,
        required=False,
        label="Segundo Apellido",
        validators=[RegexValidator(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', 'Solo letras permitidas')],
        widget=forms.TextInput(attrs={
            'class': 'form-input w-full pl-10 pr-4 py-3 rounded-xl text-gray-900 text-sm',
            'placeholder': 'Gómez',
            'maxlength': '30',
        })
    )

    tipo_cedula = forms.ChoiceField(
        choices=[('V', 'V'), ('E', 'E'), ('J', 'J')],
        required=True,
        label="Tipo de Cédula",
        widget=forms.Select(attrs={
            'class': 'form-input w-full pl-10 pr-4 py-3 rounded-xl text-gray-900 text-sm bg-white',
        })
    )

    cedula = forms.CharField(
        max_length=8,
        min_length=7,
        required=True,
        label="Cédula",
        validators=[
            RegexValidator(r'^\d+$', 'Solo números'),
            MinLengthValidator(7, 'Mínimo 7 dígitos'),
        ],
        widget=forms.TextInput(attrs={
            'class': 'form-input w-full pl-10 pr-4 py-3 rounded-xl text-gray-900 text-sm',
            'placeholder': '12345678',
            'maxlength': '8',
        })
    )

    sexo = forms.ChoiceField(
        choices=[
            ('', '--- Seleccione ---'),
            ('M', 'Masculino'),
            ('F', 'Femenino'),
            ('NB', 'No Binario'),
            ('O', 'Otro'),
            ('PN', 'Prefiero no decir'),
        ],
        required=False,
        label="Sexo",
        widget=forms.Select(attrs={
            'class': 'form-input w-full pl-10 pr-4 py-3 rounded-xl text-gray-900 text-sm bg-white',
        })
    )

    fecha_nacimiento = forms.DateField(
        required=False,
        label="Fecha de Nacimiento",
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-input w-full pl-10 pr-4 py-3 rounded-xl text-gray-900 text-sm',
        })
    )

    telefono = forms.CharField(
        max_length=11,
        min_length=11,
        required=False,
        label="Teléfono",
        validators=[
            RegexValidator(r'^0\d{10}$', 'Debe comenzar con 0 y tener 11 dígitos (ej: 04241234567)'),
            MinLengthValidator(11, 'Debe tener 11 dígitos'),
        ],
        widget=forms.TextInput(attrs={
            'class': 'form-input w-full pl-10 pr-4 py-3 rounded-xl text-gray-900 text-sm',
            'placeholder': '04241234567',
            'maxlength': '11',
        })
    )

    id_cm = forms.ModelChoiceField(
        queryset=CentroMedico.objects.filter(status=True).order_by('nombre_cm'),
        required=True,
        label="Centro Médico",
        empty_label="--- Seleccionar ---",
        widget=forms.Select(attrs={
            'class': 'form-input w-full pl-10 pr-4 py-3 rounded-xl text-gray-900 text-sm bg-white',
        })
    )

    def clean_password_confirm(self):
        pwd1 = self.cleaned_data.get('password')
        pwd2 = self.cleaned_data.get('password_confirm')
        if pwd1 and pwd2 and pwd1 != pwd2:
            raise ValidationError('Las contraseñas no coinciden.')
        return pwd2

    def clean_fecha_nacimiento(self):
        fecha = self.cleaned_data.get('fecha_nacimiento')
        if fecha:
            hoy = date.today()
            edad = hoy.year - fecha.year - ((hoy.month, hoy.day) < (fecha.month, fecha.day))
            if edad < 18:
                raise ValidationError('Debes tener al menos 18 años.')
        return fecha

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if UserSuperAdmin.objects.filter(username__iexact=username).exists():
            raise ValidationError('Este nombre de usuario ya está en uso.')
        return username

    def clean_cedula(self):
        cedula = self.cleaned_data.get('cedula')
        if Superadmin.objects.filter(cedula=cedula).exists():
            raise ValidationError('Esta cédula ya está registrada.')
        return cedula
