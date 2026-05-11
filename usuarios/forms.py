from django import forms
from django.core.exceptions import ValidationError
from .models import (
    UserPaciente, UserDoctor, UserRecepcionista, UserAdmin,
    PacienteDatosPersonales, Doctor, Recepcionista, Administrador,
    DireccionPaciente, DireccionDoctor, DireccionRecepcionista, DireccionAdmin,
    Sede, Estado, Municipio, Ciudad, Parroquia
)

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
    """Formulario de registro para pacientes usando los nuevos modelos de Supabase"""
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
            ('V', 'Venezolano'),
            ('E', 'Extranjero'),
            ('P', 'Pasaporte'),
        ],
        required=True,
        widget=forms.Select(attrs={'class': 'form-input w-full px-3 py-2 rounded-lg'})
    )
    sexo = forms.ChoiceField(
        choices=[
            ('M', 'Masculino'),
            ('F', 'Femenino'),
            ('O', 'Otro'),
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
        if UserPaciente.objects.filter(username=username).exists():
            raise forms.ValidationError("Este nombre de usuario ya está en uso")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if UserPaciente.objects.filter(email=email).exists():
            raise forms.ValidationError("Este correo electrónico ya está en uso")
        return email

    def clean_cedula(self):
        cedula = self.cleaned_data.get('cedula')
        if PacienteDatosPersonales.objects.filter(cedula=cedula).exists():
            raise forms.ValidationError("Esta cédula ya está registrada")
        return cedula

    def save(self):
        # Obtener la sede por defecto (ID=1)
        try:
            sede = Sede.objects.get(id_sede=1)
        except Sede.DoesNotExist:
            raise ValidationError("No hay sedes configuradas en el sistema")

        # Crear dirección del paciente
        direccion = DireccionPaciente.objects.create(
            id_estado=self.cleaned_data['id_estado'],
            id_municipio=self.cleaned_data['id_municipio'],
            id_ciudad=self.cleaned_data['id_ciudad'],
            id_parroquia=self.cleaned_data['id_parroquia'],
            direccion=self.cleaned_data['direccion'],
            referencia=self.cleaned_data.get('referencia', ''),
            latitud=self.cleaned_data.get('latitud', ''),
            longitud=self.cleaned_data.get('longitud', '')
        )

        # Crear usuario paciente
        user_paciente = UserPaciente.objects.create_user(
            username=self.cleaned_data['username'],
            correo=self.cleaned_data['email'],
            password=self.cleaned_data['password1'],
            id_sede=sede
        )

        # Crear datos personales del paciente
        paciente = PacienteDatosPersonales.objects.create(
            nombre_1=self.cleaned_data['nombre_1'],
            nombre_2=self.cleaned_data.get('nombre_2', ''),
            apellido_1=self.cleaned_data['apellido_1'],
            apellido_2=self.cleaned_data.get('apellido_2', ''),
            id_user_paciente=user_paciente,
            cedula=self.cleaned_data['cedula'],
            tipo_cedula=self.cleaned_data['tipo_cedula'],
            sexo=self.cleaned_data['sexo'],
            telefono=self.cleaned_data['telefono'],
            fecha_nacimiento=self.cleaned_data['fecha_nacimiento'],
            id_sede=sede,
            id_direccion_paciente=direccion
        )

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
            ('V', 'Venezolano'),
            ('E', 'Extranjero'),
            ('P', 'Pasaporte'),
        ],
        required=True,
        widget=forms.Select(attrs={'class': 'form-input w-full px-3 py-2 rounded-lg'})
    )
    sexo = forms.ChoiceField(
        choices=[
            ('M', 'Masculino'),
            ('F', 'Femenino'),
            ('O', 'Otro'),
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
