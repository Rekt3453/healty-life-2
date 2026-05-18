from django.urls import path
from . import views
from . import views_final

urlpatterns = [
    # Homepage
    path('', views.home, name='home'),
    
    # Registro público (solo pacientes)
    path('registro/', views.registro_paciente, name='registro'),
    
    # Logins por rol
    path('login/paciente/', views.login_paciente, name='login_paciente'),
    path('login/medico/', views.login_medico, name='login_medico'),
    path('login/recepcionista/', views.login_recepcionista, name='login_recepcionista'),
    path('login/gerente/', views.login_gerente, name='login_gerente'),
    path('login/admin/', views.login_admin, name='login_admin'),
    
    # Logout
    path('logout/', views.logout_view, name='logout'),
    
    # Perfil paciente
    path('perfil/paciente/', views.perfil_paciente, name='perfil_paciente'),
    path('perfil/', views.perfil_paciente, name='perfil'),
    # Dashboards
    path('dashboard/paciente/', views.dashboard_paciente, name='dashboard_paciente'),
    path('dashboard/medico/', views.dashboard_medico, name='dashboard_medico'),
    path('dashboard/recepcionista/', views.dashboard_recepcionista, name='dashboard_recepcionista'),
    path('dashboard/gerente/', views.dashboard_gerente, name='dashboard_gerente'),
    path('dashboard/root/', views.dashboard_root, name='dashboard_root'),
    
    # Registro de staff (gerente)
    path('dashboard/gerente/registrar-staff/', views.registro_staff, name='registro_staff'),
    path('dashboard/gerente/registrar-doctor/', views.registrar_doctor, name='registrar_doctor'),
    path('dashboard/gerente/registrar-recepcionista/', views.registrar_recepcionista, name='registrar_recepcionista'),
    
    # API endpoints para selectores dependientes
    path('ajax/municipios/', views.cargar_municipios, name='cargar_municipios'),
    path('ajax/ciudades/', views.cargar_ciudades, name='cargar_ciudades'),
    path('ajax/parroquias/', views.cargar_parroquias, name='cargar_parroquias'),
    
    # API endpoints para validación en tiempo real
    path('ajax/validar-username/', views.validar_username, name='validar_username'),
    path('ajax/validar-email/', views.validar_email, name='validar_email'),
    path('ajax/validar-cedula/', views.validar_cedula, name='validar_cedula'),
]
