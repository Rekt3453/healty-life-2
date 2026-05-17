from django.urls import path
from . import views

urlpatterns = [
    # Vistas principales
    path('solicitar/', views.solicitar_cita, name='solicitar_cita'),
    path('gestionar/', views.gestionar_citas, name='gestionar_citas'),
    path('<int:cita_id>/aprobar/', views.aprobar_cita, name='aprobar_cita'),
    path('rechazar/<int:cita_id>/', views.rechazar_cita, name='rechazar_cita'),
    # Endpoints AJAX para formulario encadenado
    path('ajax/especialidades/', views.ajax_especialidades, name='ajax_especialidades'),
    path('ajax/doctores/', views.ajax_doctores, name='ajax_doctores'),
    path('ajax/horas/', views.ajax_horas_disponibles, name='ajax_horas'),
    path('ajax/servicios/', views.ajax_servicios, name='ajax_servicios'),
]
