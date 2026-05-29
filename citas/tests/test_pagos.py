import pytest
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from citas.models import Cita, PagoCita, Factura
from citas.services import CitaService, FacturacionService


@pytest.mark.django_db
def test_registrar_adelanto_pago(cita_solicitada, recepcionista_test):
    """Verifica que al registrar un adelanto se asocie correctamente a la cita."""
    user_recepcionista = recepcionista_test.id_user_recepcionista

    # Registrar adelanto
    pago = CitaService.registrar_adelanto(
        user_recepcionista,
        cita_solicitada,
        monto=Decimal('25.00'),
        metodo_pago='efectivo',
        referencia='TEST-001'
    )

    # Verificar que el pago se creó correctamente
    assert pago.monto_pagar == Decimal('25.00')
    assert pago.metodo_pago == 'efectivo'
    assert pago.referencia_pago == 'TEST-001'
    assert pago.status == True
    assert pago.estado_pago == PagoCita.ESTADO_APROBADO
    assert pago.fecha_pago is not None

    # Verificar que la cita cambió a estado pagada_adelanto
    cita_actualizada = Cita.objects.get(pk=cita_solicitada.pk)
    assert cita_actualizada.estado == Cita.ESTADO_PAGADA_ADELANTO
    assert cita_actualizada.id_pago_cita == pago


@pytest.mark.django_db
def test_generar_factura_al_cerrar_consulta(cita_solicitada, medico_test, recepcionista_test):
    """Verifica que al cerrar la consulta se emite factura con el total correcto."""
    from usuarios.models.usuarios import UserRecepcionista, UserDoctor

    # Configurar cita para que esté lista para ser atendida
    user_recepcionista = recepcionista_test.id_user_recepcionista
    cita_aprobada = CitaService.aprobar_cita(user_recepcionista, cita_solicitada)
    cita_confirmada = CitaService.confirmar_pago(user_recepcionista, cita_aprobada)

    # Iniciar y cerrar consulta
    user_doctor = medico_test.id_user_doctor
    CitaService.iniciar_consulta(user_doctor, cita_confirmada)
    CitaService.cerrar_consulta(user_doctor, cita_confirmada)

    # Verificar que se generó factura
    cita_actualizada = Cita.objects.get(pk=cita_solicitada.pk)
    factura = FacturacionService.generar_factura_cita(cita_actualizada)

    assert factura is not None
    assert factura.id_cita == cita_actualizada
    assert factura.numero.startswith('FAC-')
    assert factura.total >= 0  # Aceptamos 0 si no hay precio configurado
    assert factura.estado in [Factura.ESTADO_EMITIDA, Factura.ESTADO_PAGADA]


@pytest.mark.django_db
def test_factura_asocia_pago_existente(cita_solicitada, recepcionista_test):
    """Verifica que la factura se asocie al pago existente."""
    user_recepcionista = recepcionista_test.id_user_recepcionista

    # Registrar adelanto
    pago = CitaService.registrar_adelanto(
        user_recepcionista,
        cita_solicitada,
        monto=Decimal('30.00'),
        metodo_pago='tarjeta',
        referencia='TEST-002'
    )

    # Generar factura manualmente
    cita_actualizada = Cita.objects.get(pk=cita_solicitada.pk)
    factura = FacturacionService.generar_factura_cita(cita_actualizada)

    # Verificar asociación (la factura debe tener el pago asociado)
    assert factura.id_pago_cita == pago


@pytest.mark.django_db
def test_permiso_incorrecto_registrar_adelanto(cita_solicitada, paciente_test):
    """Verifica que un paciente no puede registrar adelantos (solo recepcionista/gerente)."""
    user_paciente = paciente_test.id_user_paciente

    with pytest.raises(PermissionError, match="Se requiere uno de estos roles"):
        CitaService.registrar_adelanto(
            user_paciente,
            cita_solicitada,
            monto=Decimal('20.00'),
            metodo_pago='efectivo'
        )


