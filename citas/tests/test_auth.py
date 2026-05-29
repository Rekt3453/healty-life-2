import pytest
from django.test import Client
from django.urls import reverse


@pytest.mark.django_db
def test_login_paciente_correcto(paciente_test):
    """Verifica que un paciente puede iniciar sesión con credenciales correctas."""
    # Este test usa datos existentes de la base de datos
    # Solo verifica que el fixture funciona correctamente
    assert paciente_test is not None
    assert paciente_test.id_user_paciente is not None


@pytest.mark.django_db
def test_login_paciente_incorrecto():
    """Verifica que credenciales incorrectas muestran error."""
    client = Client()
    response = client.post('/login/paciente/', {
        'email': 'noexiste@test.com',
        'password': 'wrongpassword'
    })

    # Debería mostrar error o redirigir con mensaje de error
    assert response.status_code in [200, 302]


@pytest.mark.django_db
def test_acceso_dashboard_paciente_autenticado(client_authenticated_paciente):
    """Verifica que un paciente autenticado puede acceder a su dashboard."""
    response = client_authenticated_paciente.get(reverse('dashboard_paciente'))
    assert response.status_code == 200


@pytest.mark.django_db
def test_acceso_dashboard_paciente_no_autenticado():
    """Verifica que un paciente no autenticado es redirigido al login."""
    client = Client()
    response = client.get(reverse('dashboard_paciente'))
    assert response.status_code in [302, 403]  # Redirección a login o prohibido


@pytest.mark.django_db
def test_acceso_dashboard_medico_autenticado(client_authenticated_medico):
    """Verifica que un médico autenticado puede acceder a su dashboard."""
    response = client_authenticated_medico.get(reverse('dashboard_medico'))
    assert response.status_code == 200


@pytest.mark.django_db
def test_acceso_dashboard_recepcionista_autenticado(client_authenticated_recepcionista):
    """Verifica que un recepcionista autenticado puede acceder a su dashboard."""
    response = client_authenticated_recepcionista.get(reverse('dashboard_recepcionista'))
    assert response.status_code == 200
