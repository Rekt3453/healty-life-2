from decimal import Decimal

from django.db import transaction
from django.utils import timezone


class CitaService:

    @staticmethod
    def transicionar(cita, nuevo_estado, *, campos_extra=None):
        """
        Valida y aplica una transición de estado.
        Lanza ValueError si la transición no está permitida.
        campos_extra: dict de campos adicionales a guardar junto con estado.
        """
        from citas.models import Cita as CitaModel
        estado_actual = cita.estado or CitaModel.ESTADO_SOLICITADA
        permitidos = CitaModel.TRANSICIONES_VALIDAS.get(estado_actual, set())
        if nuevo_estado not in permitidos:
            raise ValueError(
                f"Transición inválida: '{estado_actual}' → '{nuevo_estado}'. "
                f"Permitidos: {sorted(permitidos) or ['ninguno (estado terminal)']}."
            )
        update_fields = ['estado']
        cita.estado = nuevo_estado
        if campos_extra:
            for campo, valor in campos_extra.items():
                setattr(cita, campo, valor)
                update_fields.append(campo)
        cita.save(update_fields=update_fields)
        return cita

    @staticmethod
    @transaction.atomic
    def cancelar_cita(cita, *, cancelada_por, motivo):
        from citas.models import Cita as CitaModel
        estado_actual = cita.estado or CitaModel.ESTADO_SOLICITADA
        permitidos = CitaModel.TRANSICIONES_VALIDAS.get(estado_actual, set())
        if CitaModel.ESTADO_CANCELADA not in permitidos:
            raise ValueError(
                f"No se puede cancelar una cita en estado '{cita.get_estado_display()}'."
            )
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
    def aprobar_cita(cita):
        """Recepcionista aprueba la solicitud (sin pago aún)."""
        from citas.models import Cita as CitaModel
        CitaService.transicionar(cita, CitaModel.ESTADO_APROBADA)
        cita.status = True
        cita.save(update_fields=['status'])
        return cita

    @staticmethod
    @transaction.atomic
    def confirmar_pago(cita):
        """Recepcionista verifica el pago → cita queda confirmada."""
        from citas.models import Cita as CitaModel, PagoCita
        pago = getattr(cita, 'id_pago_cita', None)
        if not pago:
            raise ValueError("La cita no tiene pago asociado.")
        pago.status = True
        pago.estado_pago = PagoCita.ESTADO_APROBADO
        pago.save(update_fields=['status', 'estado_pago'])
        CitaService.transicionar(cita, CitaModel.ESTADO_CONFIRMADA)
        cita.status = True
        cita.save(update_fields=['status'])
        return cita

    @staticmethod
    @transaction.atomic
    def aprobar_pago(cita):
        """Alias de confirmar_pago para compatibilidad con código existente."""
        return CitaService.confirmar_pago(cita)

    @staticmethod
    @transaction.atomic
    def iniciar_consulta(cita):
        """Médico abre la consulta: cita pasa a en_consulta."""
        from citas.models import Cita as CitaModel, ConsultaMedica
        estados_validos = {CitaModel.ESTADO_CONFIRMADA, CitaModel.ESTADO_EN_CONSULTA}
        if cita.estado not in estados_validos:
            raise ValueError(
                f"Solo se puede iniciar consulta en citas confirmadas. "
                f"Estado actual: '{cita.get_estado_display()}'."
            )
        consulta, created = ConsultaMedica.objects.get_or_create(
            id_cita=cita,
            defaults={'motivo_consulta': cita.motivo or ''},
        )
        if cita.estado != CitaModel.ESTADO_EN_CONSULTA:
            CitaService.transicionar(cita, CitaModel.ESTADO_EN_CONSULTA)
        return consulta, created

    @staticmethod
    @transaction.atomic
    def registrar_adelanto(cita, *, monto, metodo_pago, referencia=None):
        """Recepcionista registra un adelanto de pago sin generar factura inmediata."""
        from citas.models import Cita as CitaModel, PagoCita
        CitaService.transicionar(cita, CitaModel.ESTADO_PAGADA_ADELANTO)
        pago = PagoCita.objects.create(
            id_paciente=cita.id_paciente,
            monto_pagar=monto,
            metodo_pago=metodo_pago,
            referencia_pago=referencia,
            id_sede=cita.id_sede,
            fecha_consulta=cita.fecha_consulta,
            fecha_pago=timezone.now(),
            status=True,
            estado_pago=PagoCita.ESTADO_APROBADO,
            id_cita=cita.id_citas,
        )
        cita.id_pago_cita = pago
        cita.save(update_fields=['id_pago_cita'])
        return pago

    @staticmethod
    @transaction.atomic
    def cerrar_consulta(cita):
        """Médico cierra la consulta: cita pasa a atendida y genera factura si no existe."""
        from citas.models import Cita as CitaModel, ConsultaMedica, Factura
        if cita.estado != CitaModel.ESTADO_EN_CONSULTA:
            raise ValueError(
                f"Solo se puede cerrar una cita en estado 'en_consulta'. "
                f"Estado actual: '{cita.get_estado_display()}'."
            )
        consulta = ConsultaMedica.objects.filter(id_cita=cita).first()
        if not consulta:
            raise ValueError("No existe consulta médica asociada a esta cita.")
        if consulta.estado == ConsultaMedica.ESTADO_CERRADA:
            raise ValueError("Esta consulta ya está cerrada.")
        now = timezone.now()
        consulta.estado = ConsultaMedica.ESTADO_CERRADA
        consulta.fecha_cierre = now
        consulta.save(update_fields=['estado', 'fecha_cierre'])
        CitaService.transicionar(cita, CitaModel.ESTADO_ATENDIDA,
                                 campos_extra={'fecha_atencion': now})
        if not hasattr(cita, 'factura') or not cita.factura:
            FacturacionService.generar_factura_cita(cita)
        return consulta


class FacturacionService:

    @staticmethod
    @transaction.atomic
    def generar_factura_cita(cita, precio_fijo=None):
        """
        Genera factura para una cita atendida.
        - Si existe pago previo, lo asocia y calcula estado según saldo.
        - Si no existe pago, usa precio_fijo (o monto del servicio) y deja factura pendiente.
        """
        from citas.models import Factura

        pago = getattr(cita, 'id_pago_cita', None)
        if pago and pago.status:
            subtotal = Decimal(str(pago.monto_pagar or 0))
        else:
            subtotal = Decimal(str(precio_fijo or 0))
            if not subtotal and cita.id_servicio_especialidad:
                try:
                    subtotal = Decimal(str(getattr(cita.id_servicio_especialidad, 'precio', 0) or 0))
                except (AttributeError, TypeError):
                    subtotal = Decimal("0.00")

        impuesto = Decimal("0.00")
        total = subtotal + impuesto

        numero = f"FAC-{timezone.now().strftime('%Y%m%d')}-{cita.pk}"

        estado_factura = Factura.ESTADO_PAGADA
        if pago and pago.status and pago.monto_pagar >= total:
            estado_factura = Factura.ESTADO_PAGADA
        elif pago and pago.status and pago.monto_pagar < total:
            estado_factura = Factura.ESTADO_EMITIDA
        elif not pago or not pago.status:
            estado_factura = Factura.ESTADO_EMITIDA

        factura, created = Factura.objects.get_or_create(
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
                "estado": estado_factura,
            }
        )

        if not created and pago and not factura.id_pago_cita:
            factura.id_pago_cita = pago
            factura.estado = estado_factura
            factura.save(update_fields=['id_pago_cita', 'estado'])

        if pago and not pago.id_factura:
            pago.id_factura = factura
            pago.save(update_fields=['id_factura'])

        return factura
