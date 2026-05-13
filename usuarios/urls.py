from django.urls import path
from . import views
from . import views_final

urlpatterns = [
    # Homepage
    path('', views.home, name='home'),
    
    # Registro público (solo pacientes) - usando formulario final
    path('registro/', views_final.registro_paciente, name='registro'),
    
    # Logins por rol
    path('login/paciente/', views.login_paciente, name='login_paciente'),
    path('login/medico/', views.login_medico, name='login_medico'),
    path('login/recepcionista/', views.login_recepcionista, name='login_recepcionista'),
    path('login/gerente/', views.login_gerente, name='login_gerente'),
    
    # Logout
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboards
    path('dashboard/paciente/', views.dashboard_paciente, name='dashboard_paciente'),
    path('dashboard/medico/', views.dashboard_medico, name='dashboard_medico'),
    path('dashboard/recepcionista/', views.dashboard_recepcionista, name='dashboard_recepcionista'),
    path('dashboard/gerente/', views.dashboard_gerente, name='dashboard_gerente'),
    
    # Registro de staff (gerente)
    path('dashboard/gerente/registrar-staff/', views.registro_staff, name='registro_staff'),
    
    # API endpoints para selectores dependientes
    path('ajax/municipios/', views.cargar_municipios, name='cargar_municipios'),
    path('ajax/ciudades/', views.cargar_ciudades, name='cargar_ciudades'),
    path('ajax/parroquias/', views.cargar_parroquias, name='cargar_parroquias'),
]
