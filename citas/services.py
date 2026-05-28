from decimal import Decimal

from django.db import transaction
from django.utils import timezone


class CitaService:

    @staticmethod
    @transaction.atomic
    def cancelar_cita(cita, *, cancelada_por, motivo):
        from citas.models import Cita, PagoCita
        if getattr(cita, 'estado', None) == 'atendida':
            raise ValueError("No se puede cancelar una cita ya atendida.")

        cita.estado = Cita.ESTADO_CANCELADA
        cita.status = False
        cita.cancelada_por = str(cancelada_por)
        cita.motivo_cancelacion = motivo
        cita.fecha_cancelacion = timezone.now()
        cita.save(update_fields=[
            'estado', 'status', 'cancelada_por',
            'motivo_cancelacion', 'fecha_cancelacion',
        ])

        pago = getattr(cita, 'id_pago_cita', None)
        if pago and pago.status:
            pago.estado_pago = PagoCita.ESTADO_ANULACION_PENDIENTE
            pago.save(update_fields=['estado_pago'])

        return cita

    @staticmethod
    @transaction.atomic
    def aprobar_pago(cita):
        from citas.models import Cita, PagoCita
        pago = getattr(cita, 'id_pago_cita', None)
        if not pago:
            raise ValueError("La cita no tiene pago asociado.")

        pago.status = True
        pago.estado_pago = PagoCita.ESTADO_APROBADO
        pago.save(update_fields=['status', 'estado_pago'])

        cita.estado = Cita.ESTADO_CONFIRMADA
        cita.save(update_fields=['estado'])

        return cita


class FacturacionService:

    @staticmethod
    @transaction.atomic
    def generar_factura_cita(cita):
        from citas.models import Factura

        pago = getattr(cita, 'id_pago_cita', None)
        if not pago or not pago.status:
            raise ValueError("No se puede facturar una cita sin pago aprobado.")

        subtotal = getattr(pago, 'monto_pagar', None) or Decimal("0.00")
        subtotal = Decimal(str(subtotal))
        impuesto = Decimal("0.00")
        total = subtotal + impuesto

        numero = f"FAC-{timezone.now().strftime('%Y%m%d')}-{cita.pk}"

        factura, _ = Factura.objects.get_or_create(
            id_cita=cita,
            defaults={
                "numero": numero,
                "id_pago_cita": pago,
                "descripcion": (
                    str(cita.id_servicio_especialidad)
                    if cita.id_servicio_especialidad else "Consulta médica"
                ),
                "subtotal": subtotal,
                "impuesto": impuesto,
                "total": total,
                "estado": Factura.ESTADO_PAGADA,
            }
        )
        return factura
