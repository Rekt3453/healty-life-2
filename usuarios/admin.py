from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import UserProfile

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Perfil de Usuario'

class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_rol')
    
    def get_rol(self, obj):
        try:
            return obj.userprofile.get_rol_display()
        except UserProfile.DoesNotExist:
            return 'Sin perfil'
    get_rol.short_description = 'Rol'

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'rol', 'cedula', 'telefono')
    list_filter = ('rol',)
    search_fields = ('user__username', 'cedula', 'telefono')

# Re-registrar el User admin con nuestro custom
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
