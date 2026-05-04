"""
URL configuration for clinica_root project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # URLs de la app usuarios (login, registro, dashboard, etc.)
    path('', include('usuarios.urls')),
    
    # URLs de la app citas (agendamiento, facturas, etc.)
    path('citas/', include('citas.urls')),
    
    # URLs específicas por sede - las sedes son: caracas, valencia
    # Estas deben ir AL FINAL y Django probará los slugs específicos
    path('<slug:sede_slug>/', include('usuarios.urls')),
    path('<slug:sede_slug>/citas/', include('citas.urls')),
]

# Servir archivos estáticos y media en desarrollo
if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()