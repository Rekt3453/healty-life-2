from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Homepage principal - DEBE IR PRIMERO
    path('', views.homepage, name='homepage'),
    
    # URLs específicas primero (deben ir antes de los patrones de sede genéricos)
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('registro/paciente/', views.registro_paciente, name='registro_paciente'),
    
    # URLs de recuperación de contraseña
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='usuarios/password_reset.html',
        email_template_name='usuarios/password_reset_email.html',
        subject_template_name='usuarios/password_reset_subject.txt'
    ), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='usuarios/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='usuarios/password_reset_confirm.html'
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='usuarios/password_reset_complete.html'
    ), name='password_reset_complete'),
    
    # URLs protegidas (requieren login)
    path('dashboard/', views.dashboard_paciente, name='dashboard_paciente'),
    path('dashboard/paciente/', views.dashboard_paciente, name='dashboard_paciente'),
    path('dashboard/medico/', views.dashboard_medico, name='dashboard_medico'),
    path('dashboard/recepcion/', views.dashboard_recepcion, name='dashboard_recepcion'),
    path('dashboard/gerente/', views.dashboard_gerente, name='dashboard_gerente'),
    path('dashboard/general/', views.dashboard_general, name='dashboard_general'),
    
    # Gestión de usuarios
    path('perfil/', views.perfil, name='perfil'),
    path('registrar/medico/', views.registrar_medico, name='registrar_medico'),
    path('registrar/recepcionista/', views.registrar_recepcionista, name='registrar_recepcionista'),
    
    # URLs específicas por sede (con slug) - DEBEN IR ANTES del patrón genérico de sede
    path('<slug:sede_slug>/login/', views.CustomLoginView.as_view(), name='login_sede'),
    path('<slug:sede_slug>/registro/paciente/', views.registro_paciente, name='registro_paciente_sede'),
    
    # URL genérica de sede - VA AL FINAL
    path('<slug:sede_slug>/', views.selector_sede, name='selector_sede_especifica'),
    path('', views.selector_sede, name='selector_sede'),
]