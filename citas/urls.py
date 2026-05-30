from django.urls import path
from . import views

urlpatterns = [
    # Solicitar / agendar cita (paciente)
    path('solicitar/', views.solicitar_cita, name='solicitar_cita'),
    path('agendar/', views.solicitar_cita, name='agendar_cita'),
    path('checkout-reserva/', views.checkout_reserva, name='checkout_reserva'),
    # Citas del paciente
    path('mis-citas/', views.mis_citas, name='mis_citas'),
    path('mis-facturas/', views.mis_facturas, name='mis_facturas'),
    path('historial-consultas/', views.historial_consultas, name='historial_consultas'),
    path('<int:cita_id>/detalle/', views.detalle_cita, name='detalle_cita'),
    path('<int:cita_id>/cancelar/', views.cancelar_cita_paciente, name='cancelar_cita'),
    path('<int:cita_id>/pagar/', views.pagar_cita, name='pagar_cita'),
    # Vistas del médico
    path('calendario/', views.calendario_citas, name='calendario_citas'),
    path('medico/pendientes/', views.citas_pendientes_medico, name='citas_pendientes_medico'),
    path('medico/horarios/', views.gestionar_horarios, name='gestionar_horarios'),
    path('medico/<int:cita_id>/confirmar/', views.confirmar_cita, name='confirmar_cita'),
    path('medico/<int:cita_id>/receta/', views.realizar_receta, name='realizar_receta'),
    # Gestión (recepcionista/gerente)
    path('gestionar/', views.gestionar_citas, name='gestionar_citas'),
    path('<int:cita_id>/aprobar/', views.aprobar_cita, name='aprobar_cita'),
    path('rechazar/<int:cita_id>/', views.rechazar_cita, name='rechazar_cita'),
    path('<int:cita_id>/adelanto/', views.registrar_adelanto, name='registrar_adelanto'),
    path('<int:cita_id>/confirmar-pago/', views.confirmar_pago, name='confirmar_pago'),
    path('<int:cita_id>/cancelar-secretaria/', views.cancelar_cita_secretaria, name='cancelar_cita_secretaria'),
    # Endpoints AJAX para formulario encadenado
    path('ajax/especialidades/', views.ajax_especialidades, name='ajax_especialidades'),
    path('ajax/doctores/', views.ajax_doctores, name='ajax_doctores'),
    path('ajax/fechas/', views.ajax_fechas_disponibles, name='ajax_fechas'),
    path('ajax/horas/', views.ajax_horas_disponibles, name='ajax_horas'),
    path('ajax/servicios/', views.ajax_servicios, name='ajax_servicios'),
    path('ajax/servicios-medico/', views.ajax_servicios_medico, name='ajax_servicios_medico'),
    # Consulta médica
    path('consulta/<int:cita_id>/', views.iniciar_consulta, name='iniciar_consulta'),
    path('consulta/<int:cita_id>/cerrar/', views.cerrar_consulta, name='cerrar_consulta'),
    # Facturación
    path('factura/<int:cita_id>/', views.detalle_factura, name='detalle_factura'),
    path('factura/pdf/<int:factura_id>/', views.factura_pdf, name='factura_pdf'),
    path('facturas/', views.gestionar_facturas, name='gestionar_facturas'),
    path('facturas-recepcionista/', views.facturas_recepcionista, name='facturas_recepcionista'),
    path('pagar-saldo/<int:cita_id>/', views.pagar_saldo, name='pagar_saldo'),
    # Catálogo de servicios médicos (médico)
    path('servicios/', views.servicios_doctor, name='servicios_doctor'),
    path('servicios/crear/', views.servicio_crear, name='servicio_crear'),
    path('servicios/editar/<int:servicio_id>/', views.servicio_editar, name='servicio_editar'),
    path('servicios/toggle/<int:servicio_id>/', views.servicio_toggle, name='servicio_toggle'),
    # Reportes (gerente/admin)
    path('reportes/atencion-diaria/', views.reporte_atencion_diaria, name='reporte_atencion_diaria'),
    path('reportes/caja/', views.reporte_caja, name='reporte_caja'),
    path('reportes/balance/', views.reporte_balance, name='reporte_balance'),
    path('reportes/pagos-medicos/', views.reporte_pagos_medicos, name='reporte_pagos_medicos'),
]
