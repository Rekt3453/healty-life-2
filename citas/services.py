from decimal import Decimal

from django.db import transaction
from django.utils import timezone


class CitaService:

    @staticmethod
    @transaction.atomic
    def cancelar_cita(cita, *, cancelada_por, motivo):
        from citas.models import Cita as CitaModel
        if cita.estado == CitaModel.ESTADO_CANCELADA:
            raise ValueError("La cita ya está cancelada.")

        cita.status = False
        cita.estado = CitaModel.ESTADO_CANCELADA
        cita.motivo_cancelacion = motivo
        cita.fecha_cancelacion = timezone.now()
        cita.cancelada_por = str(cancelada_por)
        cita.save(update_fields=[
            'status', 'estado', 'motivo_cancelacion',
            'fecha_cancelacion', 'cancelada_por',
        ])
        return cita

    @staticmethod
    @transaction.atomic
    def aprobar_pago(cita):
        from citas.models import Cita as CitaModel, PagoCita
        pago = getattr(cita, 'id_pago_cita', None)
        if not pago:
            raise ValueError("La cita no tiene pago asociado.")

        pago.status = True
        pago.estado_pago = PagoCita.ESTADO_APROBADO
        pago.save(update_fields=['status', 'estado_pago'])

        cita.status = True
        cita.estado = CitaModel.ESTADO_APROBADA
        cita.save(update_fields=['status', 'estado'])

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
