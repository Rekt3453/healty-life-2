import pytest
from django.utils import timezone
from datetime import datetime, timedelta


@pytest.fixture(scope='session')
def django_db_setup():
    """Configuración de base de datos para pruebas (SQLite en memoria)."""
    pass


@pytest.fixture
def ubicaciones_test(db):
    """Fixture para obtener ubicaciones existentes de la base de datos."""
    from usuarios.models.ubicacion import Estado, Municipio, Ciudad, Parroquia

    # Usar datos existentes (primer registro disponible)
    estado = Estado.objects.first()
    if not estado:
        raise ValueError("No hay estados en la base de datos. Ejecuta seed data primero.")

    municipio = Municipio.objects.filter(id_estado=estado).first()
    ciudad = Ciudad.objects.filter(id_estado=estado).first()
    parroquia = Parroquia.objects.filter(id_municipio=municipio).first() if municipio else None

    return {'estado': estado, 'municipio': municipio, 'ciudad': ciudad, 'parroquia': parroquia}


@pytest.fixture
def sede_test(db, ubicaciones_test):
    """Fixture para obtener una sede existente de la base de datos."""
    from usuarios.models.clinica import Sede

    sede = Sede.objects.filter(status=True).first()
    if not sede:
        raise ValueError("No hay sedes activas en la base de datos.")
    return sede


@pytest.fixture
def paciente_test(db, sede_test):
    """Fixture para obtener un paciente existente de la base de datos."""
    from usuarios.models.perfiles import PacienteDatosPersonales

    paciente = PacienteDatosPersonales.objects.filter(status=True).first()
    if not paciente:
        raise ValueError("No hay pacientes activos en la base de datos.")
    return paciente


@pytest.fixture
def medico_test(db, sede_test):
    """Fixture para obtener un médico existente de la base de datos."""
    from usuarios.models.perfiles import Doctor

    medico = Doctor.objects.filter(status=True).first()
    if not medico:
        raise ValueError("No hay médicos activos en la base de datos.")
    return medico


@pytest.fixture
def recepcionista_test(db, sede_test):
    """Fixture para obtener un recepcionista existente de la base de datos."""
    from usuarios.models.perfiles import Recepcionista

    recepcionista = Recepcionista.objects.filter(status=True).first()
    if not recepcionista:
        raise ValueError("No hay recepcionistas activos en la base de datos.")
    return recepcionista


@pytest.fixture
def cita_solicitada(db, paciente_test, medico_test, sede_test):
    """Fixture para obtener o crear una cita en estado 'solicitada'."""
    from citas.models import Cita, PagoCita, Especialidad, ServicioEspecialidad

    # Usar especialidad existente
    especialidad = Especialidad.objects.filter(status=True).first()
    if not especialidad:
        raise ValueError("No hay especialidades activas en la base de datos.")

    # Usar servicio existente o crear uno temporal
    servicio = ServicioEspecialidad.objects.filter(
        id_doctor=medico_test,
        id_especialidad=especialidad,
        status=True
    ).first()

    # Crear pago
    pago = PagoCita.objects.create(
        id_paciente=paciente_test,
        id_sede=sede_test,
        fecha_consulta=timezone.now() + timedelta(days=1),
        status=False,
        estado_pago=PagoCita.ESTADO_PENDIENTE
    )

    # Crear cita
    cita = Cita.objects.create(
        id_paciente=paciente_test,
        id_doctor=medico_test,
        id_sede=sede_test,
        id_especialidades=especialidad,
        id_servicio_especialidad=servicio,
        id_pago_cita=pago,
        fecha_consulta=timezone.now() + timedelta(days=1),
        fecha_emision=timezone.now(),
        motivo='Consulta de prueba',
        status=True,
        estado=Cita.ESTADO_SOLICITADA
    )

    return cita


@pytest.fixture
def client_authenticated_paciente(db, paciente_test):
    """Fixture para cliente autenticado como paciente."""
    from django.test import Client

    client = Client()
    user = paciente_test.id_user_paciente
    client.force_login(user)
    return client


@pytest.fixture
def client_authenticated_medico(db, medico_test):
    """Fixture para cliente autenticado como médico."""
    from django.test import Client

    client = Client()
    user = medico_test.id_user_doctor
    client.force_login(user)
    return client


@pytest.fixture
def client_authenticated_recepcionista(db, recepcionista_test):
    """Fixture para cliente autenticado como recepcionista."""
    from django.test import Client

    client = Client()
    user = recepcionista_test.id_user_recepcionista
    client.force_login(user)
    return client
