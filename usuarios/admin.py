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
    list_display = ('nombre', 'slug', 'telefono', 'email', 'activa', 'fecha_creacion')
    list_filter = ('activa', 'fecha_creacion')
    search_fields = ('nombre', 'slug')
    prepopulated_fields = {'slug': ('nombre',)}

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'rol', 'sede', 'cedula', 'telefono', 'activo', 'fecha_creacion')
    list_filter = ('rol', 'sede', 'activo', 'fecha_creacion')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'cedula')
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')

@admin.register(Especialidad)
class EspecialidadAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activa')
    list_filter = ('activa',)
    search_fields = ('nombre',)

@admin.register(MedicoProfile)
class MedicoProfileAdmin(admin.ModelAdmin):
    list_display = ('user_profile', 'especialidad', 'numero_matricula', 'experiencia_anios', 'consulta_precio_base')
    list_filter = ('especialidad', 'experiencia_anios')
    search_fields = ('user_profile__user__first_name', 'user_profile__user__last_name', 'numero_matricula')

@admin.register(PacienteProfile)
class PacienteProfileAdmin(admin.ModelAdmin):
    list_display = ('user_profile', 'historia_clinica_numero', 'contacto_emergencia_telefono')
    search_fields = ('user_profile__user__first_name', 'user_profile__user__last_name', 'historia_clinica_numero')

# Re-registrar el User admin con nuestro custom
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
