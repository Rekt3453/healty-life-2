from django.urls import path
from . import views_registro

urlpatterns = [
    path('registro/', views_registro.registro_paciente, name='registro_paciente'),
    path('ajax/municipios/', views_registro.cargar_municipios, name='ajax_municipios'),
    path('ajax/ciudades/', views_registro.cargar_ciudades, name='ajax_ciudades'),
    path('ajax/parroquias/', views_registro.cargar_parroquias, name='ajax_parroquias'),
]
