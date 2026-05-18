from django.urls import path
from . import views

urlpatterns = [
<<<<<<< Updated upstream
    # Solicitar / agendar cita (paciente)
    path('solicitar/', views.solicitar_cita, name='solicitar_cita'),
    path('agendar/', views.solicitar_cita, name='agendar_cita'),
    # Citas del paciente
    path('mis-citas/', views.mis_citas, name='mis_citas'),
    path('mis-facturas/', views.mis_facturas, name='mis_facturas'),
    path('<int:cita_id>/detalle/', views.detalle_cita, name='detalle_cita'),
    path('<int:cita_id>/cancelar/', views.cancelar_cita_paciente, name='cancelar_cita'),
    # Gestión (recepcionista/gerente)
    path('gestionar/', views.gestionar_citas, name='gestionar_citas'),
    path('<int:cita_id>/aprobar/', views.aprobar_cita, name='aprobar_cita'),
    path('rechazar/<int:cita_id>/', views.rechazar_cita, name='rechazar_cita'),
    # Endpoints AJAX para formulario encadenado
    path('ajax/especialidades/', views.ajax_especialidades, name='ajax_especialidades'),
    path('ajax/doctores/', views.ajax_doctores, name='ajax_doctores'),
    path('ajax/horas/', views.ajax_horas_disponibles, name='ajax_horas'),
    path('ajax/servicios/', views.ajax_servicios, name='ajax_servicios'),
=======
    # Vistas para pacientes
    path('solicitar/', views.solicitar_cita, name='solicitar_cita'),
    path('mis-citas/', views.mis_citas, name='mis_citas'),
    path('detalle/<int:cita_id>/', views.detalle_cita, name='detalle_cita'),
    path('cancelar/<int:cita_id>/', views.cancelar_cita, name='cancelar_cita'),
    
    # Vistas para recepcionista
    path('gestionar/', views.gestionar_citas, name='gestionar_citas'),
    path('asignar-medico/<int:cita_id>/', views.asignar_medico_cita, name='asignar_medico_cita'),
    
    # Vistas para doctores
    path('doctor/citas/', views.citas_doctor, name='citas_doctor'),
    
    # API endpoints para selectores dependientes
    path('api/servicios-por-especialidad/', views.api_servicios_por_especialidad, name='api_servicios_por_especialidad'),
    path('api/doctores-por-servicio/', views.api_doctores_por_servicio, name='api_doctores_por_servicio'),
    path('api/consultorios-por-sede/', views.api_consultorios_por_sede, name='api_consultorios_por_sede'),
>>>>>>> Stashed changes
]
