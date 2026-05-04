#!/usr/bin/env python
"""
AUDITORÍA COMPLETA DEL SISTEMA - Healthy Life
Por: Desarrollador Senior (10 años de experiencia)
Fecha: Abril 2026
"""

import os
import sys

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clinica_root.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import django
django.setup()

# Importar modelos
from django.contrib.auth.models import User
from usuarios.models import Sede, UserProfile, MedicoProfile, PacienteProfile, Especialidad
from citas.models import Servicio, DisponibilidadMedica, Cita, Factura, HistoriaClinica, Reporte
from django.urls import reverse, resolve
from django.test import Client

print("="*80)
print("AUDITORÍA COMPLETA - SISTEMA MÉDICO HEALTHY LIFE")
print("="*80)
print()

# ============================================
# SECCIÓN 1: ESTADO DE DATOS
# ============================================
print("[1] SECCION 1: ESTADO DE DATOS EN BASE DE DATOS")
print("-"*80)

datos = {
    'Sedes': Sede.objects.count(),
    'Perfiles de Usuario': UserProfile.objects.count(),
    'Médicos': MedicoProfile.objects.count(),
    'Pacientes': PacienteProfile.objects.count(),
    'Especialidades': Especialidad.objects.count(),
    'Servicios': Servicio.objects.count(),
    'Disponibilidades': DisponibilidadMedica.objects.count(),
    'Citas': Cita.objects.count(),
    'Facturas': Factura.objects.count(),
    'Historias Clínicas': HistoriaClinica.objects.count(),
    'Reportes': Reporte.objects.count(),
}

for key, value in datos.items():
    estado = "[OK]" if value > 0 else "[WARN]"
    print(f"{estado} {key}: {value} registros")

print()

# ============================================
# SECCIÓN 2: USUARIOS DE PRUEBA
# ============================================
print("[2] SECCION 2: USUARIOS DE PRUEBA CONFIGURADOS")
print("-"*80)

usuarios_test = [
    'admin', 'gerente_general', 'gerente_caracas', 
    'dr_perez', 'dra_martinez', 'recepcionista_caracas', 'paciente_prueba'
]

usuarios_faltantes = []
for username in usuarios_test:
    try:
        user = User.objects.get(username=username)
        profile = getattr(user, 'userprofile', None)
        rol = profile.rol if profile else 'Sin perfil'
        print(f"[OK] {username}: {user.email} | Rol: {rol} | Activo: {user.is_active}")
    except User.DoesNotExist:
        print(f"[FAIL] {username}: NO EXISTE")
        usuarios_faltantes.append(username)

print()

# ============================================
# SECCIÓN 3: INTEGRIDAD DE MODELOS
# ============================================
print("[3] SECCION 3: INTEGRIDAD DE RELACIONES ENTRE MODELOS")
print("-"*80)

# Verificar médicos sin perfil
medicos_sin_user = MedicoProfile.objects.filter(user_profile__isnull=True)
if medicos_sin_user.exists():
    print(f"[WARN] Medicos sin UserProfile: {medicos_sin_user.count()}")
else:
    print("[OK] Todos los medicos tienen UserProfile")

# Verificar pacientes sin perfil  
pacientes_sin_user = PacienteProfile.objects.filter(user_profile__isnull=True)
if pacientes_sin_user.exists():
    print(f"[WARN] Pacientes sin UserProfile: {pacientes_sin_user.count()}")
else:
    print("[OK] Todos los pacientes tienen UserProfile")

# Verificar citas huérfanas
citas_sin_paciente = Cita.objects.filter(paciente__isnull=True)
if citas_sin_paciente.exists():
    print(f"[WARN] Citas sin paciente: {citas_sin_paciente.count()}")
else:
    print("[OK] Todas las citas tienen paciente")

# Verificar facturas sin citas
facturas_sin_cita = Factura.objects.filter(cita__isnull=True)
if facturas_sin_cita.exists():
    print(f"[WARN] Facturas sin cita: {facturas_sin_cita.count()}")
else:
    print("[OK] Todas las facturas tienen cita asociada")

print()

# ============================================
# SECCIÓN 4: VERIFICACIÓN DE URLs
# ============================================
print("[4] SECCION 4: VERIFICACION DE URLS PRINCIPALES")
print("-"*80)

client = Client()

urls_a_verificar = [
    ('/', 'Página principal'),
    ('/login/', 'Login'),
    ('/registro/paciente/', 'Registro paciente'),
    ('/caracas/', 'Sede Caracas'),
    ('/valencia/', 'Sede Valencia'),
]

urls_fallidas = []
for url, nombre in urls_a_verificar:
    try:
        response = client.get(url)
        if response.status_code == 200:
            print(f"[OK] {nombre}: {url} (200 OK)")
        elif response.status_code == 302:
            print(f"[REDIR] {nombre}: {url} (Redirect - normal para login)")
        else:
            print(f"[WARN] {nombre}: {url} ({response.status_code})")
            urls_fallidas.append((url, nombre, response.status_code))
    except Exception as e:
        print(f"[FAIL] {nombre}: {url} (ERROR: {str(e)[:50]})")
        urls_fallidas.append((url, nombre, str(e)))

print()

# ============================================
# SECCIÓN 5: VERIFICACIÓN DE TEMPLATES
# ============================================
print("[5] SECCION 5: VERIFICACION DE TEMPLATES CRITICOS")
print("-"*80)

from django.template.loader import get_template, TemplateDoesNotExist

templates_criticos = [
    'base.html',
    'selector.html',
    'usuarios/login.html',
    'usuarios/registro_paciente.html',
    'dashboard/paciente.html',
    'dashboard/medico.html',
    'dashboard/recepcionista.html',
    'citas/agendar_cita.html',
    'citas/mis_citas.html',
    'citas/mis_facturas.html',
    'citas/calendario_medico.html',
    'citas/detalle_cita.html',
    'citas/cancelar_cita.html',
    'home_sede.html',
]

templates_faltantes = []
for template in templates_criticos:
    try:
        get_template(template)
        print(f"[OK] {template}")
    except TemplateDoesNotExist:
        print(f"[FAIL] {template} - NO EXISTE")
        templates_faltantes.append(template)

print()

# ============================================
#print("[6] SECCION 6: RESUMEN DE BUGS ENCONTRADOS")
# ============================================
print("[BUG] SECCIÓN 6: RESUMEN DE BUGS Y PROBLEMAS ENCONTRADOS")
print("-"*80)

bugs = []

# Bug 1: Usuarios faltantes
if usuarios_faltantes:
    bugs.append({
        'nivel': 'CRÍTICO',
        'problema': f'Usuarios de prueba faltantes: {", ".join(usuarios_faltantes)}',
        'solucion': 'Ejecutar script crear_datos_iniciales.py'
    })

# Bug 2: URLs fallidas
for url, nombre, status in urls_fallidas:
    if status != 302:  # Los redirects son normales
        bugs.append({
            'nivel': 'ALTO',
            'problema': f'URL fallida: {nombre} ({url}) - Status: {status}',
            'solucion': 'Verificar configuración de URLs y vistas'
        })

# Bug 3: Templates faltantes
if templates_faltantes:
    bugs.append({
        'nivel': 'ALTO',
        'problema': f'Templates faltantes: {len(templates_faltantes)}',
        'solucion': 'Crear templates: ' + ', '.join(templates_faltantes[:3]) + '...'
    })

# Bug 4: Datos mínimos
if datos['Sedes'] == 0:
    bugs.append({
        'nivel': 'CRÍTICO',
        'problema': 'No hay sedes configuradas',
        'solucion': 'Crear sedes Caracas y Valencia en admin'
    })

if datos['Servicios'] == 0:
    bugs.append({
        'nivel': 'MEDIO',
        'problema': 'No hay servicios médicos configurados',
        'solucion': 'Ejecutar script crear_datos_citas.py'
    })

if not bugs:
    print("[SUCCESS] NO SE ENCONTRARON BUGS CRITICOS")
else:
    print(f"[WARN] SE ENCONTRARON {len(bugs)} PROBLEMAS:")
    print()
    for i, bug in enumerate(bugs, 1):
        print(f"{i}. [{bug['nivel']}] {bug['problema']}")
        print(f"   Solución: {bug['solucion']}")
        print()

print()

# ============================================
# SECCIÓN 7: RECOMENDACIONES SENIOR
# ============================================
print("[7] SECCION 7: RECOMENDACIONES DE DESARROLLADOR SENIOR")
print("-"*80)

recomendaciones = [
    {
        'categoria': 'SEGURIDAD',
        'items': [
            'Cambiar SECRET_KEY antes de producción',
            'Configurar HTTPS para todas las comunicaciones',
            'Implementar rate limiting en login (fallos de autenticación)',
            'Agregar 2FA para usuarios administrativos',
            'Auditar permisos de archivos estáticos y media'
        ]
    },
    {
        'categoria': 'BASE DE DATOS',
        'items': [
            'Migrar de SQLite a PostgreSQL para producción',
            'Configurar backups automáticos diarios',
            'Implementar sistema de archivado para historias clínicas antiguas',
            'Agregar índices en campos de búsqueda frecuente (fechas, cédulas)'
        ]
    },
    {
        'categoria': 'FUNCIONALIDAD FALTANTE',
        'items': [
            'Sistema de notificaciones por email/SMS para citas',
            'Recordatorios automáticos 24h antes de citas',
            'Integración con pasarelas de pago (Stripe, PayPal)',
            'Portal de resultados de laboratorio para pacientes',
            'Sistema de encuestas de satisfacción post-consulta',
            'Chat interno entre médicos y recepción',
            'Importación/exportación de datos en Excel/CSV',
            'Dashboard analítico con gráficos (Chart.js)'
        ]
    },
    {
        'categoria': 'UX/UI',
        'items': [
            'Implementar modo oscuro',
            'Mejorar accesibilidad (ARIA labels, contraste)',
            'Agregar loading states en operaciones async',
            'Implementar PWA para uso offline',
            'Optimizar imágenes y recursos estáticos'
        ]
    },
    {
        'categoria': 'TESTING',
        'items': [
            'Crear suite de tests unitarios (pytest)',
            'Implementar tests de integración para flujos críticos',
            'Configurar CI/CD con GitHub Actions',
            'Agregar cobertura de código > 80%',
            'Tests end-to-end con Selenium/Playwright'
        ]
    },
    {
        'categoria': 'DEVOPS',
        'items': [
            'Dockerizar la aplicación',
            'Configurar nginx como reverse proxy',
            'Implementar sistema de logs centralizado',
            'Monitoreo con Sentry para errores',
            'Configurar certificados SSL automáticos (Let\'s Encrypt)'
        ]
    }
]

for rec in recomendaciones:
    print(f"[REC] {rec['categoria']}:")
    for item in rec['items']:
        print(f"   • {item}")
    print()

# ============================================
# SECCIÓN 8: PRIORIDADES DE IMPLEMENTACIÓN
# ============================================
print("[8] SECCION 8: PRIORIDADES DE IMPLEMENTACION (MVP -> PRODUCCION)")
print("-"*80)

prioridades = """
FASE 1 - URGENTE (1-2 semanas):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. ✅ Corregir bugs críticos identificados
2. ✅ Completar datos de prueba faltantes
3. ✅ Verificar todos los flujos de usuario
4. ✅ Pruebas de regresión completas

FASE 2 - IMPORTANTE (1 mes):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Sistema de notificaciones por email
2. Integración de pasarela de pagos
3. Panel de administración mejorado
4. Exportación de reportes en Excel

FASE 3 - MEJORAS (2-3 meses):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Aplicación móvil (React Native/Flutter)
2. Portal de resultados de laboratorio
3. Sistema de chat interno
4. Analíticas avanzadas con dashboards

FASE 4 - OPTIMIZACIÓN (3+ meses):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Migración a microservicios
2. Inteligencia artificial para diagnósticos asistidos
3. Telemedicina (videollamadas integradas)
4. Integración con dispositivos IoT (wearables)
"""

print(prioridades)

print("="*80)
print("AUDITORÍA COMPLETADA")
print("="*80)
print(f"Total de problemas encontrados: {len(bugs)}")
print(f"Total de recomendaciones: {sum(len(r['items']) for r in recomendaciones)}")
print()
print("💼 Recomendación final: El sistema está en estado BETA.")
print("   Necesita corregir bugs críticos antes de lanzamiento.")
print("   Tiempo estimado para producción: 2-4 semanas.")
print("="*80)
