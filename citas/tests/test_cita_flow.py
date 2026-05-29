import pytest
from django.utils import timezone
from datetime import timedelta
from citas.models import Cita, ConsultaMedica, Factura
from citas.services import CitaService


@pytest.mark.django_db
def test_flujo_completo_cita(cita_solicitada, medico_test, recepcionista_test):
    """Simula el flujo completo de una cita: solicitud → aprobación → pago → atención → cierre → factura."""
    from usuarios.models.usuarios import UserRecepcionista, UserDoctor

    # Estado inicial: solicitada
    assert cita_solicitada.estado == Cita.ESTADO_SOLICITADA

    # Paso 1: Recepcionista aprueba la cita
    user_recepcionista = recepcionista_test.id_user_recepcionista
    cita_aprobada = CitaService.aprobar_cita(user_recepcionista, cita_solicitada)
    assert cita_aprobada.estado == Cita.ESTADO_APROBADA
    assert cita_aprobada.status == True

    # Paso 2: Recepcionista confirma el pago
    cita_confirmada = CitaService.confirmar_pago(user_recepcionista, cita_aprobada)
    assert cita_confirmada.estado == Cita.ESTADO_CONFIRMADA
    assert cita_confirmada.id_pago_cita.status == True
    assert cita_confirmada.id_pago_cita.estado_pago == 'aprobado'

    # Paso 3: Médico inicia la consulta
    user_doctor = medico_test.id_user_doctor
    consulta, created = CitaService.iniciar_consulta(user_doctor, cita_confirmada)
    assert cita_confirmada.estado == Cita.ESTADO_EN_CONSULTA
    assert created == True  # Primera vez que se crea la consulta
    assert consulta.estado == ConsultaMedica.ESTADO_ABIERTA

    # Paso 4: Médico cierra la consulta
    consulta_cerrada = CitaService.cerrar_consulta(user_doctor, cita_confirmada)
    assert cita_confirmada.estado == Cita.ESTADO_ATENDIDA
    assert consulta_cerrada.estado == ConsultaMedica.ESTADO_CERRADA
    assert consulta_cerrada.fecha_cierre is not None

    # Paso 5: Verificar que se generó factura
    cita_actualizada = Cita.objects.get(pk=cita_solicitada.pk)
    assert hasattr(cita_actualizada, 'factura') or Factura.objects.filter(id_cita=cita_actualizada).exists()


@pytest.mark.django_db
def test_transicion_invalida_estado(cita_solicitada):
    """Verifica que no se pueden realizar transiciones de estado inválidas."""
    from usuarios.models.usuarios import UserRecepcionista

    user_recepcionista = UserRecepcionista.objects.create(
        email='recepcionista@test2.com',
        password='hashed_password_123',
        status=True
    )

    # Intentar pasar de solicitada directamente a atendida (debería fallar)
    with pytest.raises(ValueError, match="Transición inválida"):
        CitaService.transicionar(cita_solicitada, Cita.ESTADO_ATENDIDA)


@pytest.mark.django_db
def test_permiso_incorrecto_aprobar_cita(cita_solicitada, paciente_test):
    """Verifica que un paciente no puede aprobar una cita (solo recepcionista/gerente)."""
    user_paciente = paciente_test.id_user_paciente

    with pytest.raises(PermissionError, match="Se requiere uno de estos roles"):
        CitaService.aprobar_cita(user_paciente, cita_solicitada)


@pytest.mark.django_db
def test_permiso_incorrecto_iniciar_consulta(cita_solicitada, recepcionista_test):
    """Verifica que un recepcionista no puede iniciar una consulta (solo médico)."""
    from citas.services import CitaService
    from usuarios.models.usuarios import UserRecepcionista

    # Primero aprobar y confirmar pago para dejar la cita en estado confirmada
    user_recepcionista = recepcionista_test.id_user_recepcionista
    cita_aprobada = CitaService.aprobar_cita(user_recepcionista, cita_solicitada)
    cita_confirmada = CitaService.confirmar_pago(user_recepcionista, cita_aprobada)

    # Intentar iniciar consulta como recepcionista (debería fallar)
    with pytest.raises(PermissionError, match="Se requiere uno de estos roles"):
        CitaService.iniciar_consulta(user_recepcionista, cita_confirmada)


@pytest.mark.django_db
def test_cancelar_cita(cita_solicitada, paciente_test):
    """Verifica que se puede cancelar una cita correctamente."""
    from usuarios.models.usuarios import UserPaciente

    user_paciente = paciente_test.id_user_paciente
    cita_cancelada = CitaService.cancelar_cita(
        cita_solicitada,
        cancelada_por=user_paciente,
        motivo='Cancelación por prueba'
    )

    assert cita_cancelada.estado == Cita.ESTADO_CANCELADA
    assert cita_cancelada.status == False
    assert cita_cancelada.motivo_cancelacion == 'Cancelación por prueba'
    assert cita_cancelada.cancelada_por == str(user_paciente)
