from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Sede, UserProfile, Especialidad, MedicoProfile, PacienteProfile

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Perfil de Usuario'

class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_rol', 'get_sede')
    
    def get_rol(self, obj):
        try:
            return obj.userprofile.get_rol_display()
        except UserProfile.DoesNotExist:
            return 'Sin perfil'
    get_rol.short_description = 'Rol'
    
    def get_sede(self, obj):
        try:
            return obj.userprofile.sede
        except (UserProfile.DoesNotExist, AttributeError):
            return 'Sin sede'
    get_sede.short_description = 'Sede'

class MedicoProfileInline(admin.StackedInline):
    model = MedicoProfile
    can_delete = False
    verbose_name_plural = 'Perfil Médico'

class PacienteProfileInline(admin.StackedInline):
    model = PacienteProfile
    can_delete = False
    verbose_name_plural = 'Perfil Paciente'

@admin.register(Sede)
class SedeAdmin(admin.ModelAdmin):
    list_display = ('id_sede', 'rif_sede', 'telefono', 'Status')
    list_filter = ('Status',)
    search_fields = ('rif_sede', 'telefono')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('id_administrador', 'nombre_1', 'apellido_1', 'cedula', 'telefono', 'status')
    list_filter = ('status', 'sexo')
    search_fields = ('nombre_1', 'apellido_1', 'cedula')

@admin.register(Especialidad)
class EspecialidadAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activa')
    list_filter = ('activa',)
    search_fields = ('nombre',)

@admin.register(MedicoProfile)
class MedicoProfileAdmin(admin.ModelAdmin):
    list_display = ('id_doctor', 'nombre_1', 'apellido_1', 'cedula', 'telefono')
    list_filter = ('sexo', 'status')
    search_fields = ('nombre_1', 'apellido_1', 'cedula')

@admin.register(PacienteProfile)
class PacienteProfileAdmin(admin.ModelAdmin):
    list_display = ('id_datos_paciente', 'nombre_1', 'apellido_1', 'cedula', 'tipo_cedula', 'sexo')
    search_fields = ('nombre_1', 'apellido_1', 'cedula')

# Re-registrar el User admin con nuestro custom
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
