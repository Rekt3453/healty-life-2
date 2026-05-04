from django.urls import path
from . import views

urlpatterns = [
    # URLs para pacientes
    path('agendar/', views.agendar_cita, name='agendar_cita'),
    path('mis-citas/', views.mis_citas, name='mis_citas'),
    path('cita/<int:pk>/', views.detalle_cita, name='detalle_cita'),
    path('cita/<int:pk>/cancelar/', views.cancelar_cita, name='cancelar_cita'),
    path('mis-facturas/', views.mis_facturas, name='mis_facturas'),
    path('factura/<int:pk>/pdf/', views.descargar_factura_pdf, name='descargar_factura_pdf'),
    
    # URLs para médicos
    path('calendario-medico/', views.calendario_medico, name='calendario_medico'),
    path('cita/<int:cita_id>/historia/crear/', views.crear_historia_clinica, name='crear_historia_clinica'),
    path('historia/<int:pk>/', views.ver_historia_clinica, name='ver_historia_clinica'),
    
    # URLs para recepcionistas y gerentes
    path('calendario-general/', views.calendario_general, name='calendario_general'),
    
    # URLs AJAX
    path('ajax/obtener-medicos/', views.obtener_medicos_por_especialidad, name='obtener_medicos_por_especialidad'),
    path('ajax/obtener-servicios/', views.obtener_servicios_por_especialidad, name='obtener_servicios_por_especialidad'),
    path('ajax/verificar-disponibilidad/', views.verificar_disponibilidad, name='verificar_disponibilidad'),
]
