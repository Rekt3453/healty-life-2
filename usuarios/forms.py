from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator, EmailValidator, MinLengthValidator
from datetime import date, timedelta
from .models import (
    UserPaciente, UserDoctor, UserRecepcionista, UserAdmin,
    PacienteDatosPersonales, Doctor, Recepcionista, Administrador,
    DireccionPaciente, DireccionDoctor, DireccionRecepcionista, DireccionAdmin,
    Sede, Estado, Municipio, Ciudad, Parroquia, PacienteEspecial
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
        max_length=150,
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
        })
    )
    
    email = forms.EmailField(
        required=True,
        label="Correo Electrónico",
        validators=[EmailValidator(message='Ingrese un correo electrónico válido')],
        error_messages={'required': 'El correo electrónico es obligatorio'},
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'ejemplo@correo.com',
            'data-validate': 'email',
        })
    )
    
    password1 = forms.CharField(
        required=True,
        label="Contraseña",
        min_length=8,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mínimo 8 caracteres',
            'data-validate': 'password',
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
        max_length=100, min_length=2, required=True,
        label="Primer Nombre",
        validators=[RegexValidator(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', 'Solo letras')],
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Juan', 'data-validate': 'nombre'})
    )
    
    nombre_2 = forms.CharField(
        max_length=100, required=False,
        label="Segundo Nombre",
        validators=[RegexValidator(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]*$', 'Solo letras')],
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Carlos (opcional)', 'data-validate': 'nombre'})
    )
    
    apellido_1 = forms.CharField(
        max_length=100, min_length=2, required=True,
        label="Primer Apellido",
        validators=[RegexValidator(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', 'Solo letras')],
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Pérez', 'data-validate': 'apellido'})
    )
    
    apellido_2 = forms.CharField(
        max_length=100, required=False,
        label="Segundo Apellido",
        validators=[RegexValidator(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]*$', 'Solo letras')],
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: García (opcional)', 'data-validate': 'apellido'})
    )
    
    tipo_cedula = forms.ChoiceField(
        choices=[('V','V'), ('E','E'), ('J','J'), ('C','C'), ('G','G'), ('P','P'), ('F','F')],
        required=True, label="Tipo de Cédula",
        widget=forms.Select(attrs={'class': 'form-select', 'data-validate': 'select'})
    )
    
    cedula = forms.CharField(
        max_length=20, min_length=6, required=True,
        label="Cédula de Identidad",
        validators=[RegexValidator(r'^\d+$', 'Solo números'), MinLengthValidator(6, 'Mínimo 6 dígitos')],
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '12345678', 'data-validate': 'cedula'})
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
    
    ciudad = forms.CharField(
        max_length=100, required=True,
        label="Ciudad",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Caracas', 'id': 'id_ciudad'})
    )
    
    municipio = forms.CharField(
        max_length=100, required=False,
        label="Municipio",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Libertador', 'id': 'id_municipio'})
    )
    
    parroquia = forms.CharField(
        max_length=100, required=False,
        label="Parroquia",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Sucre', 'id': 'id_parroquia'})
    )
    
    direccion = forms.CharField(
        max_length=500, required=False,
        label="Dirección",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Dirección de domicilio (opcional)'})
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
        # Obtener la sede seleccionada
        sede = self.cleaned_data['sede']
        
        # Buscar o crear ciudad, municipio y parroquia
        estado = self.cleaned_data['id_estado']
        ciudad_nombre = self.cleaned_data['ciudad'].upper()
        municipio_nombre = self.cleaned_data.get('municipio', '').upper()
        parroquia_nombre = self.cleaned_data.get('parroquia', '').upper()
        
        # Buscar o crear ciudad
        ciudad, _ = Ciudad.objects.get_or_create(
            ciudad=ciudad_nombre,
            id_estado=estado,
            defaults={'status': True}
        )
        
        # Buscar o crear municipio si se proporcionó
        municipio = None
        if municipio_nombre:
            municipio, _ = Municipio.objects.get_or_create(
                municipio=municipio_nombre,
                id_estado=estado,
                defaults={'status': True}
            )
        
        # Buscar o crear parroquia si se proporcionó
        parroquia = None
        if parroquia_nombre and municipio:
            parroquia, _ = Parroquia.objects.get_or_create(
                parroquia=parroquia_nombre,
                id_municipio=municipio,
                defaults={'status': True}
            )
        
        # Crear dirección del paciente
        direccion = DireccionPaciente.objects.create(
            id_estado=estado,
            id_municipio=municipio,
            id_ciudad=ciudad,
            id_parroquia=parroquia,
            direccion=self.cleaned_data.get('direccion', ''),
            referencia='',
            latitud='',
            longitud=''
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
            ('C', 'C - Consejo Comunal'),
            ('G', 'G - Gobierno'),
            ('P', 'P - Pasaporte'),
            ('F', 'F - Fallecido'),
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
        )
        return user_recepcionista
