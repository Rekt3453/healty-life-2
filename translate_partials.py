#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

BASE = r'C:\Users\user\Desktop\healty-life-2'

def t(s):
    return '{% trans "' + s + '" %}'

# ---------------------------------------------------------------------------
# _recep_acciones.html
# ---------------------------------------------------------------------------
p1 = os.path.join(BASE, 'templates', 'partials', '_recep_acciones.html')
c1 = open(p1, 'r', encoding='utf-8').read()

c1 = c1.replace('Próximas citas', t('Próximas citas'))
c1 = c1.replace('Próximos 3 días', t('Próximos 3 días'))
c1 = c1.replace('Sin paciente', t('Sin paciente'))
c1 = c1.replace('Sin especialidad', t('Sin especialidad'))
c1 = c1.replace('Sin médico', t('Sin médico'))
c1 = c1.replace('>Confirmada</span>', '>' + t('Confirmada') + '</span>')
c1 = c1.replace('>Aprobada</span>', '>' + t('Aprobada') + '</span>')
c1 = c1.replace('>Pago Pendiente</span>', '>' + t('Pago Pendiente') + '</span>')
c1 = c1.replace('>Pagada</span>', '>' + t('Pagada') + '</span>')
c1 = c1.replace('>En Consulta</span>', '>' + t('En Consulta') + '</span>')
c1 = c1.replace('>Ver detalles</a>', '>' + t('Ver detalles') + '</a>')
c1 = c1.replace('No hay citas programadas próximamente', t('No hay citas programadas próximamente'))

open(p1, 'w', encoding='utf-8').write(c1)
print('Translated:', p1)

# ---------------------------------------------------------------------------
# _recep_solicitudes.html
# ---------------------------------------------------------------------------
p2 = os.path.join(BASE, 'templates', 'partials', '_recep_solicitudes.html')
c2 = open(p2, 'r', encoding='utf-8').read()

c2 = c2.replace('Solicitudes pendientes', t('Solicitudes pendientes'))
c2 = c2.replace('Citas por confirmar o rechazar', t('Citas por confirmar o rechazar'))
c2 = c2.replace('|default:"Paciente"', '|default:"' + t('Paciente') + '"')
c2 = c2.replace('>Pendiente</span>', '>' + t('Pendiente') + '</span>')
c2 = c2.replace('>Confirmada</span>', '>' + t('Confirmada') + '</span>')
c2 = c2.replace('>En consulta</span>', '>' + t('En consulta') + '</span>')
c2 = c2.replace('>Completada</span>', '>' + t('Completada') + '</span>')
c2 = c2.replace('>Cancelada</span>', '>' + t('Cancelada') + '</span>')
c2 = c2.replace('No hay solicitudes pendientes', t('No hay solicitudes pendientes'))

open(p2, 'w', encoding='utf-8').write(c2)
print('Translated:', p2)

# ---------------------------------------------------------------------------
# _recep_citas_dia.html
# ---------------------------------------------------------------------------
p3 = os.path.join(BASE, 'templates', 'partials', '_recep_citas_dia.html')
c3 = open(p3, 'r', encoding='utf-8').read()

c3 = c3.replace('Citas del día', t('Citas del día'))
c3 = c3.replace(' citas programadas · ', ' ' + t('citas programadas') + ' · ')
c3 = c3.replace(' en consulta</p>', ' ' + t('en consulta') + '</p>')
c3 = c3.replace('>Ver todas</a>', '>' + t('Ver todas') + '</a>')
c3 = c3.replace('>Hora</th>', '>' + t('Hora') + '</th>')
c3 = c3.replace('>Paciente</th>', '>' + t('Paciente') + '</th>')
c3 = c3.replace('>Médico</th>', '>' + t('Médico') + '</th>')
c3 = c3.replace('>Especialidad</th>', '>' + t('Especialidad') + '</th>')
c3 = c3.replace('>Consultorio</th>', '>' + t('Consultorio') + '</th>')
c3 = c3.replace('>Estado</th>', '>' + t('Estado') + '</th>')
c3 = c3.replace('>Acciones</th>', '>' + t('Acciones') + '</th>')
c3 = c3.replace('>Pendiente</span>', '>' + t('Pendiente') + '</span>')
c3 = c3.replace('>Confirmada</span>', '>' + t('Confirmada') + '</span>')
c3 = c3.replace('>En consulta</span>', '>' + t('En consulta') + '</span>')
c3 = c3.replace('>Completada</span>', '>' + t('Completada') + '</span>')
c3 = c3.replace('>Cancelada</span>', '>' + t('Cancelada') + '</span>')
c3 = c3.replace('>Llegó</button>', '>' + t('Llegó') + '</button>')
c3 = c3.replace('>Cancelar</button>', '>' + t('Cancelar') + '</button>')
c3 = c3.replace('No hay citas programadas para hoy', t('No hay citas programadas para hoy'))

open(p3, 'w', encoding='utf-8').write(c3)
print('Translated:', p3)

# ---------------------------------------------------------------------------
# facturas_recepcionista.html extra strings
# ---------------------------------------------------------------------------
p4 = os.path.join(BASE, 'templates', 'citas', 'facturas_recepcionista.html')
c4 = open(p4, 'r', encoding='utf-8').read()

c4 = c4.replace('registros</p>', t('registros') + '</p>')

open(p4, 'w', encoding='utf-8').write(c4)
print('Translated:', p4)

print('\nAll partials translated!')
