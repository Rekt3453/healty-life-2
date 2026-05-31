from django.urls import path
from . import views
from . import views_root
from . import views_superadmin

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
    path('login/root/', views_root.login_root, name='login_root'),
    path('login/super-admin/', views_superadmin.login_superadmin, name='login_superadmin'),

    # Logout
    path('logout/', views.logout_view, name='logout'),
    path('logout/root/', views_root.logout_root, name='logout_root'),
    path('logout/super-admin/', views_superadmin.logout_superadmin, name='logout_superadmin'),

    # Perfil paciente
    path('perfil/paciente/', views.perfil_paciente, name='perfil_paciente'),
    path('perfil/', views.perfil_paciente, name='perfil'),

    # Pacientes especiales (menores de edad gestionados por el tutor)
    path('dashboard/paciente/registrar-menor/', views.registrar_paciente_especial, name='registrar_paciente_especial'),
    path('dashboard/paciente/mis-menores/', views.lista_pacientes_especiales, name='lista_pacientes_especiales'),
    path('dashboard/paciente/mis-menores/editar/<int:id_paciente_especial>/', views.editar_paciente_especial, name='editar_paciente_especial'),
    path('dashboard/paciente/mis-menores/<int:id_paciente_especial>/historial/', views.historial_medico_menor, name='historial_medico_menor'),
    path('dashboard/paciente/historial-medico/', views.historial_medico, name='historial_medico'),

    # Dashboards
    path('dashboard/paciente/', views.dashboard_paciente, name='dashboard_paciente'),
    path('dashboard/medico/', views.dashboard_medico, name='dashboard_medico'),
    path('perfil/doctor/', views.perfil_doctor, name='perfil_doctor'),
    path('dashboard/recepcionista/', views.dashboard_recepcionista, name='dashboard_recepcionista'),
    path('dashboard/gerente/', views.dashboard_gerente, name='dashboard_gerente'),
    path('dashboard/root/', views_root.dashboard_root, name='dashboard_root'),
    path('dashboard/super-admin/', views_superadmin.dashboard_superadmin, name='dashboard_superadmin'),

    # Root
    path('root/registrar-centro-medico/', views_root.registrar_centro_medico, name='registrar_centro_medico'),
    path('root/registrar-superadmin/', views_root.registrar_superadmin, name='registrar_superadmin'),

    # Super Admin
    path('super-admin/registrar-sede/', views_superadmin.registrar_sede, name='registrar_sede'),
    path('super-admin/registrar-gerente/', views_superadmin.registrar_gerente, name='registrar_gerente'),
    path('super-admin/auditoria/', views_superadmin.audit_log_list, name='audit_log_list'),
    
    # Registro de staff (gerente)
    path('dashboard/gerente/registrar-staff/', views.registro_staff, name='registro_staff'),
    path('dashboard/gerente/registrar-doctor/', views.registrar_doctor, name='registrar_doctor'),
    path('dashboard/gerente/registrar-recepcionista/', views.registrar_recepcionista, name='registrar_recepcionista'),
    path('dashboard/gerente/personal/', views.lista_personal, name='lista_personal'),
    path('dashboard/gerente/personal/editar-doctor/<int:id_doctor>/', views.editar_doctor_view, name='editar_doctor'),
    path('dashboard/gerente/personal/editar-recepcionista/<int:id_recepcionista>/', views.editar_recepcionista_view, name='editar_recepcionista'),

    # Especialidades
    path('dashboard/gerente/especialidades/', views.lista_especialidades, name='lista_especialidades'),
    path('dashboard/gerente/especialidades/crear/', views.crear_especialidad, name='crear_especialidad'),
    path('dashboard/gerente/especialidades/<int:id_especialidad>/toggle/', views.toggle_especialidad_status, name='toggle_especialidad_status'),
    path('dashboard/gerente/especialidades/<int:id_especialidad>/editar/', views.editar_especialidad, name='editar_especialidad'),

    # Horarios
    path('dashboard/gerente/horarios/', views.lista_horarios, name='lista_horarios'),
    path('dashboard/gerente/horarios/crear/', views.crear_horario, name='crear_horario'),
    
    # API endpoints para selectores dependientes
    path('ajax/municipios/', views.cargar_municipios, name='cargar_municipios'),
    path('ajax/ciudades/', views.cargar_ciudades, name='cargar_ciudades'),
    path('ajax/parroquias/', views.cargar_parroquias, name='cargar_parroquias'),
    
    # Recuperación de contraseña
    path('recuperar-password/', views.recuperar_password, name='recuperar_password'),
    path('verificar-preguntas/', views.verificar_preguntas, name='verificar_preguntas'),
    path('cambiar-password/', views.cambiar_password, name='cambiar_password'),
    path('configurar-preguntas/<int:user_id>/<str:token>/', views.configurar_preguntas_paciente, name='configurar_preguntas_token'),
    path('perfil/preguntas-seguridad/', views.configurar_preguntas_paciente, name='configurar_preguntas_perfil'),

    # API endpoints para validación en tiempo real
    path('ajax/validar-username/', views.validar_username, name='validar_username'),
    path('ajax/validar-email/', views.validar_email, name='validar_email'),
    path('ajax/validar-cedula/', views.validar_cedula, name='validar_cedula'),
]
