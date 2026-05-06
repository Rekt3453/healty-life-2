from django.contrib import admin
from .models import (
    Servicio, DisponibilidadMedica, Cita, Factura, 
    HistoriaClinica, Reporte
)

@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'especialidad', 'precio_base', 'duracion_minutos', 'activo')
    list_filter = ('especialidad', 'activo')
    search_fields = ('nombre', 'descripcion')
    readonly_fields = ('id',)

@admin.register(DisponibilidadMedica)
class DisponibilidadMedicaAdmin(admin.ModelAdmin):
    list_display = ('medico', 'get_dia_semana_display', 'hora_inicio', 'hora_fin', 'activo')
    list_filter = ('dia_semana', 'activo')
    search_fields = ('medico__nombre_1', 'medico__apellido_1')

@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    list_display = ('id', 'paciente', 'medico', 'sede', 'servicio', 'fecha_hora', 'estado', 'precio_total')
    list_filter = ('estado', 'sede', 'servicio__especialidad', 'fecha_creacion')
    search_fields = ('paciente__first_name', 'paciente__last_name', 'medico__user_profile__user__first_name')
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion', 'precio_total')
    date_hierarchy = 'fecha_hora'

@admin.register(Factura)
class FacturaAdmin(admin.ModelAdmin):
    list_display = ('numero_factura', 'cita', 'monto_total', 'monto_pagado', 'saldo_pendiente', 'estado', 'fecha_emision')
    list_filter = ('estado', 'fecha_emision')
    search_fields = ('numero_factura', 'cita__paciente__first_name', 'cita__paciente__last_name')
    readonly_fields = ('numero_factura', 'fecha_emision', 'saldo_pendiente')

@admin.register(HistoriaClinica)
class HistoriaClinicaAdmin(admin.ModelAdmin):
    list_display = ('paciente', 'medico', 'fecha_consulta', 'diagnostico', 'dias_reposo')
    list_filter = ('fecha_consulta', 'dias_reposo')
    search_fields = ('paciente__nombre_1', 'paciente__apellido_1', 'medico__nombre_1', 'diagnostico')
    readonly_fields = ('fecha_consulta',)

@admin.register(Reporte)
class ReporteAdmin(admin.ModelAdmin):
    list_display = ('tipo', 'fecha_generacion', 'fecha_inicio', 'fecha_fin', 'sede', 'generado_por', 'archivo_pdf')
    list_filter = ('tipo', 'fecha_generacion', 'sede')
    search_fields = ('generado_por__username', 'tipo')
    readonly_fields = ('fecha_generacion', 'datos_json')
