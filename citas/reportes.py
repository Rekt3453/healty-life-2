from django.db.models import Sum, Count, Q, F, DecimalField
from django.db.models.functions import TruncDate, Coalesce
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from citas.models import Cita, PagoCita, Factura, MovimientoCaja, HonorarioMedico
from usuarios.models import Doctor, Sede, PacienteDatosPersonales


class ReportesService:
    """Servicio para generar reportes operativos y financieros."""

    @staticmethod
    def reporte_diario_atencion(fecha_inicio, fecha_fin, id_sede=None):
        """
        Reporte diario de personas atendidas.
        
        Args:
            fecha_inicio: Fecha de inicio del período
            fecha_fin: Fecha de fin del período
            id_sede: ID de la sede (opcional, para filtrar por sede)
        
        Returns:
            dict con estadísticas de atención
        """
        queryset = Cita.objects.filter(
            fecha_consulta__date__gte=fecha_inicio,
            fecha_consulta__date__lte=fecha_fin,
            status=True
        )
        
        if id_sede:
            queryset = queryset.filter(id_sede_id=id_sede)
        
        # Contar por estado final
        stats = queryset.values('estado').annotate(
            cantidad=Count('id_citas')
        ).order_by('estado')
        
        # Convertir a diccionario
        estado_counts = {item['estado']: item['cantidad'] for item in stats}
        
        # Total de citas en el período
        total_citas = queryset.count()
        
        # Citas atendidas (cerradas)
        atendidas = estado_counts.get(Cita.ESTADO_ATENDIDA, 0)
        
        # Citas canceladas
        canceladas = estado_counts.get(Cita.ESTADO_CANCELADA, 0)
        
        # No asistió
        no_asistio = estado_counts.get(Cita.ESTADO_NO_ASISTIO, 0)
        
        # En proceso (otros estados)
        en_proceso = total_citas - atendidas - canceladas - no_asistio
        
        # Porcentaje de atención
        porcentaje_atencion = (atendidas / total_citas * 100) if total_citas > 0 else 0
        
        return {
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'total_citas': total_citas,
            'atendidas': atendidas,
            'canceladas': canceladas,
            'no_asistio': no_asistio,
            'en_proceso': en_proceso,
            'porcentaje_atencion': round(porcentaje_atencion, 2),
            'por_sede': id_sede is not None,
            'detalle_estados': estado_counts,
        }

    @staticmethod
    def reporte_caja(fecha_inicio, fecha_fin, id_sede=None):
        """
        Reporte de caja (ingresos por pagos del día o período).
        
        Args:
            fecha_inicio: Fecha de inicio del período
            fecha_fin: Fecha de fin del período
            id_sede: ID de la sede (opcional)
        
        Returns:
            dict con datos de caja
        """
        # Pagos de citas aprobados
        pagos_queryset = PagoCita.objects.filter(
            fecha_pago__date__gte=fecha_inicio,
            fecha_pago__date__lte=fecha_fin,
            estado_pago=PagoCita.ESTADO_APROBADO,
            status=True
        )
        
        if id_sede:
            pagos_queryset = pagos_queryset.filter(id_sede_id=id_sede)
        
        ingresos_citas = pagos_queryset.aggregate(
            total=Coalesce(Sum('monto_pagar'), Decimal('0.00')),
            cantidad=Count('id_pagos_cita')
        )
        
        # Movimientos de caja
        movimientos_queryset = MovimientoCaja.objects.filter(
            fecha_movimiento__date__gte=fecha_inicio,
            fecha_movimiento__date__lte=fecha_fin,
            status=True
        )
        
        if id_sede:
            movimientos_queryset = movimientos_queryset.filter(id_sede_id=id_sede)
        
        # Ingresos adicionales
        ingresos_adicionales = movimientos_queryset.filter(
            tipo_movimiento=MovimientoCaja.TIPO_INGRESO
        ).aggregate(
            total=Coalesce(Sum('monto'), Decimal('0.00')),
            cantidad=Count('id_movimiento')
        )
        
        # Egresos
        egresos = movimientos_queryset.filter(
            tipo_movimiento=MovimientoCaja.TIPO_EGRESO
        ).aggregate(
            total=Coalesce(Sum('monto'), Decimal('0.00')),
            cantidad=Count('id_movimiento')
        )
        
        # Totales
        total_ingresos = ingresos_citas['total'] + ingresos_adicionales['total']
        total_egresos = egresos['total']
        balance = total_ingresos - total_egresos
        
        # Detalle por método de pago
        pagos_por_metodo = pagos_queryset.values('metodo_pago').annotate(
            total=Coalesce(Sum('monto_pagar'), Decimal('0.00')),
            cantidad=Count('id_pagos_cita')
        ).order_by('-total')
        
        return {
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'ingresos_citas': ingresos_citas,
            'ingresos_adicionales': ingresos_adicionales,
            'egresos': egresos,
            'total_ingresos': total_ingresos,
            'total_egresos': total_egresos,
            'balance': balance,
            'pagos_por_metodo': list(pagos_por_metodo),
            'por_sede': id_sede is not None,
        }

    @staticmethod
    def reporte_balance(fecha_inicio, fecha_fin, id_sede=None):
        """
        Reporte de balance (sumatoria de costos generados).
        
        Args:
            fecha_inicio: Fecha de inicio del período
            fecha_fin: Fecha de fin del período
            id_sede: ID de la sede (opcional)
        
        Returns:
            dict con datos de balance
        """
        # Facturas emitidas
        facturas_queryset = Factura.objects.filter(
            fecha_emision__date__gte=fecha_inicio,
            fecha_emision__date__lte=fecha_fin,
            estado__in=[Factura.ESTADO_EMITIDA, Factura.ESTADO_PAGADA]
        )
        
        if id_sede:
            facturas_queryset = facturas_queryset.filter(id_cita__id_sede_id=id_sede)
        
        facturacion = facturas_queryset.aggregate(
            subtotal=Coalesce(Sum('subtotal'), Decimal('0.00')),
            impuesto=Coalesce(Sum('impuesto'), Decimal('0.00')),
            total=Coalesce(Sum('total'), Decimal('0.00')),
            cantidad=Count('id_factura')
        )
        
        # Facturas pagadas
        facturas_pagadas = facturas_queryset.filter(estado=Factura.ESTADO_PAGADA).aggregate(
            total=Coalesce(Sum('total'), Decimal('0.00')),
            cantidad=Count('id_factura')
        )
        
        # Facturas pendientes
        facturas_pendientes = facturas_queryset.filter(estado=Factura.ESTADO_EMITIDA).aggregate(
            total=Coalesce(Sum('total'), Decimal('0.00')),
            cantidad=Count('id_factura')
        )
        
        # Movimientos de caja (para egresos)
        movimientos_queryset = MovimientoCaja.objects.filter(
            fecha_movimiento__date__gte=fecha_inicio,
            fecha_movimiento__date__lte=fecha_fin,
            status=True
        )
        
        if id_sede:
            movimientos_queryset = movimientos_queryset.filter(id_sede_id=id_sede)
        
        egresos = movimientos_queryset.filter(
            tipo_movimiento=MovimientoCaja.TIPO_EGRESO
        ).aggregate(
            total=Coalesce(Sum('monto'), Decimal('0.00')),
            cantidad=Count('id_movimiento')
        )
        
        # Balance neto
        ingresos_netos = facturas_pagadas['total']
        egresos_netos = egresos['total']
        balance_neto = ingresos_netos - egresos_netos
        
        return {
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'facturacion': facturacion,
            'facturas_pagadas': facturas_pagadas,
            'facturas_pendientes': facturas_pendientes,
            'egresos': egresos,
            'ingresos_netos': ingresos_netos,
            'egresos_netos': egresos_netos,
            'balance_neto': balance_neto,
            'por_sede': id_sede is not None,
        }

    @staticmethod
    def reporte_pagos_medicos(fecha_inicio, fecha_fin, id_sede=None, id_doctor=None):
        """
        Reporte de cuánto se le debe pagar a cada médico por consultas atendidas.
        
        Args:
            fecha_inicio: Fecha de inicio del período
            fecha_fin: Fecha de fin del período
            id_sede: ID de la sede (opcional)
            id_doctor: ID del médico (opcional, para filtrar por médico específico)
        
        Returns:
            dict con datos de pagos a médicos
        """
        honorarios_queryset = HonorarioMedico.objects.filter(
            fecha_atencion__date__gte=fecha_inicio,
            fecha_atencion__date__lte=fecha_fin,
            status=True
        )
        
        if id_sede:
            honorarios_queryset = honorarios_queryset.filter(id_sede_id=id_sede)
        
        if id_doctor:
            honorarios_queryset = honorarios_queryset.filter(id_doctor_id=id_doctor)
        
        # Agrupar por médico
        por_medico = honorarios_queryset.values('id_doctor').annotate(
            nombre_doctor=F('id_doctor__nombre_1'),
            apellido_doctor=F('id_doctor__apellido_1'),
            total_honorarios=Coalesce(Sum('monto_honorario'), Decimal('0.00')),
            cantidad_consultas=Count('id_honorario'),
            cantidad_pendiente=Count('id_honorario', filter=Q(estado_pago=HonorarioMedico.ESTADO_PENDIENTE)),
            cantidad_pagada=Count('id_honorario', filter=Q(estado_pago=HonorarioMedico.ESTADO_PAGADO)),
            total_pendiente=Coalesce(
                Sum('monto_honorario', filter=Q(estado_pago=HonorarioMedico.ESTADO_PENDIENTE)),
                Decimal('0.00')
            ),
            total_pagado=Coalesce(
                Sum('monto_honorario', filter=Q(estado_pago=HonorarioMedico.ESTADO_PAGADO)),
                Decimal('0.00')
            ),
        ).order_by('-total_honorarios')
        
        # Totales generales
        totales = honorarios_queryset.aggregate(
            total_honorarios=Coalesce(Sum('monto_honorario'), Decimal('0.00')),
            cantidad_consultas=Count('id_honorario'),
            cantidad_pendiente=Count('id_honorario', filter=Q(estado_pago=HonorarioMedico.ESTADO_PENDIENTE)),
            cantidad_pagada=Count('id_honorario', filter=Q(estado_pago=HonorarioMedico.ESTADO_PAGADO)),
            total_pendiente=Coalesce(
                Sum('monto_honorario', filter=Q(estado_pago=HonorarioMedico.ESTADO_PENDIENTE)),
                Decimal('0.00')
            ),
            total_pagado=Coalesce(
                Sum('monto_honorario', filter=Q(estado_pago=HonorarioMedico.ESTADO_PAGADO)),
                Decimal('0.00')
            ),
        )
        
        return {
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'por_medico': list(por_medico),
            'totales': totales,
            'por_sede': id_sede is not None,
            'por_doctor': id_doctor is not None,
        }

    @staticmethod
    def obtener_sedes():
        """Obtener lista de sedes activas."""
        return Sede.objects.filter(status=True).values('id_sede', 'nombre_sede')

    @staticmethod
    def obtener_medicos(id_sede=None):
        """Obtener lista de médicos activos."""
        queryset = Doctor.objects.filter(status=True)
        if id_sede:
            queryset = queryset.filter(id_sede_id=id_sede)
        return queryset.values('id_doctor', 'nombre_1', 'apellido_1')

    @staticmethod
    def reporte_pacientes_nuevos(fecha_inicio, fecha_fin, id_sede=None):
        """
        Reporte de pacientes nuevos registrados en un período.

        Args:
            fecha_inicio: Fecha de inicio del período
            fecha_fin: Fecha de fin del período
            id_sede: ID de la sede (opcional)

        Returns:
            dict con total de pacientes nuevos
        """
        queryset = PacienteDatosPersonales.objects.filter(
            fecha_registro__date__gte=fecha_inicio,
            fecha_registro__date__lte=fecha_fin,
            status=True
        )
        if id_sede:
            queryset = queryset.filter(id_sede_id=id_sede)
        total = queryset.count()
        return {
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'total': total,
        }

    @staticmethod
    def reporte_doctores(id_sede=None):
        """
        Reporte de médicos activos.

        Args:
            id_sede: ID de la sede (opcional)

        Returns:
            dict con total de médicos activos
        """
        queryset = Doctor.objects.filter(status=True)
        if id_sede:
            queryset = queryset.filter(id_sede_id=id_sede)
        total = queryset.count()
        return {
            'total': total,
        }
