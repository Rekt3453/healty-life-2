from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile

class RegistroPacienteForm(UserCreationForm):
    email = forms.EmailField(required=True)
    cedula = forms.CharField(max_length=20, required=True)
    telefono = forms.CharField(max_length=20, required=True)
    fecha_nacimiento = forms.DateField(required=True, widget=forms.DateInput(attrs={'type': 'date'}))
    direccion = forms.CharField(widget=forms.Textarea, required=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'cedula', 'telefono', 'fecha_nacimiento', 'direccion')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            UserProfile.objects.create(
                user=user,
                rol='paciente',
                cedula=self.cleaned_data['cedula'],
                telefono=self.cleaned_data['telefono'],
                fecha_nacimiento=self.cleaned_data['fecha_nacimiento'],
                direccion=self.cleaned_data['direccion']
            )
        return user

class RegistroStaffForm(UserCreationForm):
    email = forms.EmailField(required=True)
    cedula = forms.CharField(max_length=20, required=True, widget=forms.TextInput(attrs={'class': 'form-input w-full px-3 py-2 rounded-lg'}))
    telefono = forms.CharField(max_length=20, required=True, widget=forms.TextInput(attrs={'class': 'form-input w-full px-3 py-2 rounded-lg'}))
    fecha_nacimiento = forms.DateField(required=True, widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-input w-full px-3 py-2 rounded-lg'}))
    direccion = forms.CharField(widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-input w-full px-3 py-2 rounded-lg'}), required=True)
    rol = forms.ChoiceField(choices=[
        ('medico', 'Médico'),
        ('recepcionista', 'Secretaria/Recepcionista'),
    ], required=True, widget=forms.Select(attrs={'class': 'form-input w-full px-3 py-2 rounded-lg'}))
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'cedula', 'telefono', 'fecha_nacimiento', 'direccion', 'rol')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-input w-full px-3 py-2 rounded-lg'})
        self.fields['email'].widget.attrs.update({'class': 'form-input w-full px-3 py-2 rounded-lg'})
        self.fields['password1'].widget.attrs.update({'class': 'form-input w-full px-3 py-2 rounded-lg'})
        self.fields['password2'].widget.attrs.update({'class': 'form-input w-full px-3 py-2 rounded-lg'})
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            UserProfile.objects.create(
                user=user,
                rol=self.cleaned_data['rol'],
                cedula=self.cleaned_data['cedula'],
                telefono=self.cleaned_data['telefono'],
                fecha_nacimiento=self.cleaned_data['fecha_nacimiento'],
                direccion=self.cleaned_data['direccion']
            )
        return user
