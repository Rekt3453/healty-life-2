from django.urls import path
from . import views

urlpatterns = [
    path('solicitar/', views.solicitar_cita, name='solicitar_cita'),
    path('solicitar-con-horario/', views.solicitar_cita_con_horario, name='solicitar_cita_con_horario'),
    path('gestionar/', views.gestionar_citas, name='gestionar_citas'),
    path('rechazar/<int:cita_id>/', views.rechazar_cita, name='rechazar_cita'),
    path('asignar-medico/<int:cita_id>/', views.asignar_medico, name='asignar_medico'),
    path('confirmar-cita/<int:cita_id>/', views.confirmar_cita, name='confirmar_cita'),
    path('gestionar-horarios/', views.gestionar_horarios, name='gestionar_horarios'),
    path('eliminar-horario/<int:horario_id>/', views.eliminar_horario, name='eliminar_horario'),
    path('calendario/', views.calendario_citas, name='calendario_citas'),
    path('citas-pendientes/', views.citas_pendientes_medico, name='citas_pendientes_medico'),
    path('api/horarios-disponibles/', views.api_horarios_disponibles, name='api_horarios_disponibles'),
]
