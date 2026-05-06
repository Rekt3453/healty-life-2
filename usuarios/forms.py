from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Submit, Field, HTML
from .models import UserProfile, Sede, Especialidad, MedicoProfile, PacienteProfile

class CustomLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Field('username', placeholder='Email o nombre de usuario'),
                Field('password', placeholder='Contraseña'),
                Submit('submit', 'Iniciar Sesión', css_class='w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700'),
                css_class='space-y-4'
            )
        )
        self.fields['username'].label = 'Email o Usuario'
        self.fields['password'].label = 'Contraseña'

class PacienteRegistroForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Correo electrónico')
    first_name = forms.CharField(max_length=30, required=True, label='Nombre')
    last_name = forms.CharField(max_length=30, required=True, label='Apellido')
    cedula = forms.CharField(max_length=15, required=True, label='Cédula de identidad')
    telefono = forms.CharField(max_length=20, required=True, label='Teléfono')
    fecha_nacimiento = forms.DateField(
        required=True, 
        label='Fecha de nacimiento',
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    tipo_cedula = forms.ChoiceField(
        choices=[('V', 'V'), ('E', 'E')],
        initial='V',
        required=True,
        label='Tipo de cédula'
    )
    sexo = forms.ChoiceField(
        choices=[('M', 'Masculino'), ('F', 'Femenino')],
        required=True,
        label='Sexo'
    )
    sede = forms.ModelChoiceField(
        queryset=Sede.objects.all(),  # No hay campo activa en la tabla real
        required=True,
        label='Sede preferida'
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Field('username', placeholder='Nombre de usuario'),
                Field('email', placeholder='correo@ejemplo.com'),
                Field('first_name', placeholder='Nombre'),
                Field('last_name', placeholder='Apellido'),
                Field('cedula', placeholder='12345678'),
                Field('tipo_cedula'),
                Field('telefono', placeholder='04141234567'),
                Field('fecha_nacimiento'),
                Field('sexo'),
                Field('sede'),
                Field('password1'),
                Field('password2'),
                Submit('submit', 'Registrarse', css_class='w-full bg-green-600 text-white py-2 rounded-lg hover:bg-green-700'),
                css_class='space-y-4'
            )
        )
        
        # Labels personalizados
        self.fields['username'].label = 'Nombre de usuario'
        self.fields['password1'].label = 'Contraseña'
        self.fields['password2'].label = 'Confirmar contraseña'
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
            # Crear PacienteProfile directamente (sin UserProfile)
            paciente_profile = PacienteProfile.objects.create(
                nombre_1=self.cleaned_data['first_name'],
                nombre_2='',
                apellido_1=self.cleaned_data['last_name'],
                apellido_2='',
                id_historial_medico_paciente=1,  # Valor temporal, debe ajustarse
                id_user_paciente=user,
                cedula=self.cleaned_data['cedula'],
                tipo_cedula=self.cleaned_data['tipo_cedula'],
                sexo=self.cleaned_data['sexo']
            )
        
        return user

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['telefono']  # Solo usar campos existentes
        widgets = {
            'telefono': forms.TextInput(attrs={'placeholder': 'Teléfono'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Field('telefono'),
                Submit('submit', 'Actualizar Perfil', css_class='bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700'),
                css_class='space-y-4'
            )
        )

class MedicoRegistroForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Correo electrónico')
    first_name = forms.CharField(max_length=30, required=True, label='Nombre')
    last_name = forms.CharField(max_length=30, required=True, label='Apellido')
    cedula = forms.CharField(max_length=15, required=True, label='Cédula de identidad')
    telefono = forms.CharField(max_length=20, required=True, label='Teléfono')
    especialidad = forms.ModelChoiceField(
        queryset=Especialidad.objects.filter(activa=True),
        required=True,
        label='Especialidad'
    )
    numero_matricula = forms.CharField(max_length=50, required=True, label='Número de matrícula')
    experiencia_anios = forms.IntegerField(min_value=0, required=True, label='Años de experiencia')
    biografia = forms.CharField(widget=forms.Textarea, required=False, label='Biografía')
    consulta_precio_base = forms.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        required=True, 
        label='Precio base de consulta'
    )
    sede = forms.ModelChoiceField(
        queryset=Sede.objects.filter(Status=True),
        required=True,
        label='Sede asignada'
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Field('username'),
                Field('email'),
                Field('first_name'),
                Field('last_name'),
                Field('cedula'),
                Field('telefono'),
                Field('especialidad'),
                Field('numero_matricula'),
                Field('experiencia_anios'),
                Field('biografia', rows=4),
                Field('consulta_precio_base'),
                Field('sede'),
                Field('password1'),
                Field('password2'),
                Submit('submit', 'Registrar Médico', css_class='w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700'),
                css_class='space-y-4'
            )
        )
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
            # Crear UserProfile
            user_profile = UserProfile.objects.create(
                user=user,
                rol='medico',
                cedula=self.cleaned_data['cedula'],
                telefono=self.cleaned_data['telefono'],
                sede=self.cleaned_data['sede']
            )
            # Crear MedicoProfile
            MedicoProfile.objects.create(
                user_profile=user_profile,
                especialidad=self.cleaned_data['especialidad'],
                numero_matricula=self.cleaned_data['numero_matricula'],
                experiencia_anios=self.cleaned_data['experiencia_anios'],
                biografia=self.cleaned_data['biografia'],
                consulta_precio_base=self.cleaned_data['consulta_precio_base']
            )
        
        return user

class RecepcionistaRegistroForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Correo electrónico')
    first_name = forms.CharField(max_length=30, required=True, label='Nombre')
    last_name = forms.CharField(max_length=30, required=True, label='Apellido')
    cedula = forms.CharField(max_length=15, required=True, label='Cédula de identidad')
    telefono = forms.CharField(max_length=20, required=True, label='Teléfono')
    sede = forms.ModelChoiceField(
        queryset=Sede.objects.filter(Status=True),
        required=True,
        label='Sede asignada'
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Field('username'),
                Field('email'),
                Field('first_name'),
                Field('last_name'),
                Field('cedula'),
                Field('telefono'),
                Field('sede'),
                Field('password1'),
                Field('password2'),
                Submit('submit', 'Registrar Recepcionista', css_class='w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700'),
                css_class='space-y-4'
            )
        )
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
            # Crear UserProfile
            UserProfile.objects.create(
                user=user,
                rol='recepcionista',
                cedula=self.cleaned_data['cedula'],
                telefono=self.cleaned_data['telefono'],
                sede=self.cleaned_data['sede']
            )
        
        return user
