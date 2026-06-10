#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Translate hardcoded Spanish strings in receptionist templates."""
import os

BASE = r'C:\Users\user\Desktop\healty-life-2'

def ensure_load_i18n(content):
    if '{% load i18n %}' in content:
        return content
    if '{% load static %}' in content:
        content = content.replace('{% load static %}', '{% load static %}\n{% load i18n %}', 1)
    else:
        content = '{% load i18n %}\n' + content
    return content

# Helper to wrap text in {% trans %}
def t(s):
    return '{% trans "' + s + '" %}'

# ---------------------------------------------------------------------------
# Template 1: dashboard_recepcionista.html
# ---------------------------------------------------------------------------
path1 = os.path.join(BASE, 'templates', 'usuarios', 'dashboard_recepcionista.html')
c1 = open(path1, 'r', encoding='utf-8').read()
c1 = ensure_load_i18n(c1)

c1 = c1.replace('Panel de Recepción - Healthy Life', t('Panel de Recepción') + ' - Healthy Life')
c1 = c1.replace('>Dashboard</a>', '>' + t('Dashboard') + '</a>')
c1 = c1.replace('>Citas</a>', '>' + t('Citas') + '</a>')
c1 = c1.replace('>Facturación</a>', '>' + t('Facturación') + '</a>')
c1 = c1.replace('>Pacientes</a>', '>' + t('Pacientes') + '</a>')
c1 = c1.replace('>Cerrar sesión</a>', '>' + t('Cerrar sesión') + '</a>')
c1 = c1.replace('"Citas hoy"', '"' + t('Citas hoy') + '"')
c1 = c1.replace('"Programadas"', '"' + t('Programadas') + '"')
c1 = c1.replace('>Citas pendientes</p>', '>' + t('Citas pendientes') + '</p>')
c1 = c1.replace('>Por confirmar</p>', '>' + t('Por confirmar') + '</p>')
c1 = c1.replace('>Pacientes nuevos hoy</p>', '>' + t('Pacientes nuevos hoy') + '</p>')
c1 = c1.replace('>Registrados</p>', '>' + t('Registrados') + '</p>')
c1 = c1.replace('>Médicos activos</p>', '>' + t('Médicos activos') + '</p>')
c1 = c1.replace('>En turno</p>', '>' + t('En turno') + '</p>')
c1 = c1.replace('placeholder="Buscar paciente, médico o especialidad..."', 'placeholder="' + t('Buscar paciente, médico o especialidad...') + '"')
c1 = c1.replace('>Registrar paciente</a>', '>' + t('Registrar paciente') + '</a>')

open(path1, 'w', encoding='utf-8').write(c1)
print('Translated:', path1)

# ---------------------------------------------------------------------------
# Template 2: gestionar_citas.html
# ---------------------------------------------------------------------------
path2 = os.path.join(BASE, 'templates', 'citas', 'gestionar_citas.html')
c2 = open(path2, 'r', encoding='utf-8').read()

c2 = c2.replace('Gestión de Citas - Healthy Life', t('Gestión de Citas') + ' - Healthy Life')
c2 = c2.replace('>Dashboard</a>', '>' + t('Dashboard') + '</a>')
c2 = c2.replace('>Citas</a>', '>' + t('Citas') + '</a>')
c2 = c2.replace('>Facturación</a>', '>' + t('Facturación') + '</a>')
c2 = c2.replace('>Pacientes</a>', '>' + t('Pacientes') + '</a>')
c2 = c2.replace('>Cerrar sesión</a>', '>' + t('Cerrar sesión') + '</a>')

c2 = c2.replace('>Inicio</a>', '>' + t('Inicio') + '</a>')
c2 = c2.replace('>Dashboard</a>', '>' + t('Dashboard') + '</a>')
c2 = c2.replace('>Gestionar</span>', '>' + t('Gestionar') + '</span>')
c2 = c2.replace('Gestión de Citas</h1>', t('Gestión de Citas') + '</h1>')
c2 = c2.replace('Administra todas las citas del sistema</p>', t('Administra todas las citas del sistema') + '</p>')

c2 = c2.replace('"Total citas"', '"' + t('Total citas') + '"')
c2 = c2.replace('"Solicitudes"', '"' + t('Solicitudes') + '"')
c2 = c2.replace('"Pagos por confirmar"', '"' + t('Pagos por confirmar') + '"')
c2 = c2.replace('"Aceptadas"', '"' + t('Aceptadas') + '"')

c2 = c2.replace('placeholder="Buscar paciente, medico o especialidad..."', 'placeholder="' + t('Buscar paciente, médico o especialidad...') + '"')
c2 = c2.replace('>Limpiar filtros</button>', '>' + t('Limpiar filtros') + '</button>')
c2 = c2.replace('>Todos los estados</option>', '>' + t('Todos los estados') + '</option>')
c2 = c2.replace('>Solicitada</option>', '>' + t('Solicitada') + '</option>')
c2 = c2.replace('>Aprobada</option>', '>' + t('Aprobada') + '</option>')
c2 = c2.replace('>Pago Pendiente</option>', '>' + t('Pago Pendiente') + '</option>')
c2 = c2.replace('>Pagada (Adelanto)</option>', '>' + t('Pagada (Adelanto)') + '</option>')
c2 = c2.replace('>Confirmada</option>', '>' + t('Confirmada') + '</option>')
c2 = c2.replace('>En Consulta</option>', '>' + t('En Consulta') + '</option>')
c2 = c2.replace('>Atendida</option>', '>' + t('Atendida') + '</option>')
c2 = c2.replace('>Cancelada</option>', '>' + t('Cancelada') + '</option>')
c2 = c2.replace('>Rechazada</option>', '>' + t('Rechazada') + '</option>')
c2 = c2.replace('>No Asistió</option>', '>' + t('No Asistió') + '</option>')

c2 = c2.replace('>Todas las citas</button>', '>' + t('Todas las citas') + '</button>')
c2 = c2.replace('>Solicitudes nuevas</button>', '>' + t('Solicitudes nuevas') + '</button>')
c2 = c2.replace('>Pagos por confirmar</button>', '>' + t('Pagos por confirmar') + '</button>')
c2 = c2.replace('>Citas aceptadas</button>', '>' + t('Citas aceptadas') + '</button>')

c2 = c2.replace('>Todas las citas</h2>', '>' + t('Todas las citas') + '</h2>')
c2 = c2.replace(' citas en total</p>', ' ' + t('citas en total') + '</p>')
c2 = c2.replace('>Solicitudes nuevas</h2>', '>' + t('Solicitudes nuevas') + '</h2>')
c2 = c2.replace(' solicitudes pendientes</p>', ' ' + t('solicitudes pendientes') + '</p>')
c2 = c2.replace('>Pagos por confirmar</h2>', '>' + t('Pagos por confirmar') + '</h2>')
c2 = c2.replace(' en revision</p>', ' ' + t('en revisión') + '</p>')
c2 = c2.replace('>Citas aceptadas</h2>', '>' + t('Citas aceptadas') + '</h2>')
c2 = c2.replace(' aceptadas</p>', ' ' + t('aceptadas') + '</p>')

c2 = c2.replace('>Sede</th>', '>' + t('Sede') + '</th>')
c2 = c2.replace('>Medico</th>', '>' + t('Médico') + '</th>')
c2 = c2.replace('>Acciones</th>', '>' + t('Acciones') + '</th>')
c2 = c2.replace('>Metodo Pago</th>', '>' + t('Método Pago') + '</th>')
c2 = c2.replace('>Referencia</th>', '>' + t('Referencia') + '</th>')
c2 = c2.replace('>Monto</th>', '>' + t('Monto') + '</th>')
c2 = c2.replace('>Fecha Cita</th>', '>' + t('Fecha Cita') + '</th>')

c2 = c2.replace('>Ver pago</button>', '>' + t('Ver pago') + '</button>')
c2 = c2.replace('>Confirmar</button>', '>' + t('Confirmar') + '</button>')
c2 = c2.replace('>Rechazar</button>', '>' + t('Rechazar') + '</button>')
c2 = c2.replace('>Confirmar Pago</button>', '>' + t('Confirmar Pago') + '</button>')
c2 = c2.replace('>Cancelar</button>', '>' + t('Cancelar') + '</button>')
c2 = c2.replace('>Sin acciones</span>', '>' + t('Sin acciones') + '</span>')

c2 = c2.replace('>No hay citas registradas.</p>', '>' + t('No hay citas registradas.') + '</p>')
c2 = c2.replace('>No hay solicitudes nuevas.</p>', '>' + t('No hay solicitudes nuevas.') + '</p>')
c2 = c2.replace('>No hay pagos pendientes de confirmacion.</p>', '>' + t('No hay pagos pendientes de confirmación.') + '</p>')

c2 = c2.replace('>Pago pendiente</span>', '>' + t('Pago pendiente') + '</span>')
c2 = c2.replace('"No asignado"', '"' + t('No asignado') + '"')
c2 = c2.replace('"No registrado"', '"' + t('No registrado') + '"')

c2 = c2.replace('data-titulo="Confirmar pago"', 'data-titulo="' + t('Confirmar pago') + '"')
c2 = c2.replace('data-titulo="Rechazar cita"', 'data-titulo="' + t('Rechazar cita') + '"')
c2 = c2.replace('data-mensaje="Esta seguro que desea confirmar el pago y aceptar esta cita?"', 'data-mensaje="' + t('¿Está seguro que desea confirmar el pago y aceptar esta cita?') + '"')
c2 = c2.replace('data-mensaje="Esta seguro que desea rechazar esta cita?"', 'data-mensaje="' + t('¿Está seguro que desea rechazar esta cita?') + '"')
c2 = c2.replace('data-mensaje="Esta seguro que desea confirmar el pago y activar esta cita?"', 'data-mensaje="' + t('¿Está seguro que desea confirmar el pago y activar esta cita?') + '"')
c2 = c2.replace('data-btn-text="Confirmar"', 'data-btn-text="' + t('Confirmar') + '"')
c2 = c2.replace('data-btn-text="Rechazar"', 'data-btn-text="' + t('Rechazar') + '"')

open(path2, 'w', encoding='utf-8').write(c2)
print('Translated:', path2)

# ---------------------------------------------------------------------------
# Template 3: facturas_recepcionista.html
# ---------------------------------------------------------------------------
path3 = os.path.join(BASE, 'templates', 'citas', 'facturas_recepcionista.html')
c3 = open(path3, 'r', encoding='utf-8').read()
c3 = ensure_load_i18n(c3)

c3 = c3.replace('Gestión de Facturas - Healthy Life', t('Gestión de Facturas') + ' - Healthy Life')
c3 = c3.replace('>Dashboard</a>', '>' + t('Dashboard') + '</a>')
c3 = c3.replace('>Citas</a>', '>' + t('Citas') + '</a>')
c3 = c3.replace('>Facturacion</a>', '>' + t('Facturación') + '</a>')
c3 = c3.replace('>Pacientes</a>', '>' + t('Pacientes') + '</a>')
c3 = c3.replace('>Cerrar sesion</a>', '>' + t('Cerrar sesión') + '</a>')

c3 = c3.replace('aria-label="Menu"', 'aria-label="' + t('Menú') + '"')
c3 = c3.replace('>Inicio</a>', '>' + t('Inicio') + '</a>')
c3 = c3.replace('>Facturas</span>', '>' + t('Facturas') + '</span>')
c3 = c3.replace('Gestion de Facturas</h1>', t('Gestión de Facturas') + '</h1>')
c3 = c3.replace('Consulta y administra las facturas de los pacientes</p>', t('Consulta y administra las facturas de los pacientes') + '</p>')
c3 = c3.replace('>Gestionar citas</a>', '>' + t('Gestionar citas') + '</a>')

c3 = c3.replace('"Total facturas"', '"' + t('Total facturas') + '"')
c3 = c3.replace('"Monto total"', '"' + t('Monto total') + '"')
c3 = c3.replace('"Facturas pagadas"', '"' + t('Facturas pagadas') + '"')
c3 = c3.replace('"Adelantos"', '"' + t('Adelantos') + '"')

c3 = c3.replace('placeholder="Buscar paciente, medico o numero..."', 'placeholder="' + t('Buscar paciente, médico o número...') + '"')
c3 = c3.replace('>Todos los estados</option>', '>' + t('Todos los estados') + '</option>')
c3 = c3.replace('>Pagada</option>', '>' + t('Pagada') + '</option>')
c3 = c3.replace('>Pendiente</option>', '>' + t('Pendiente') + '</option>')
c3 = c3.replace('>Vencida</option>', '>' + t('Vencida') + '</option>')
c3 = c3.replace('>Reembolsada</option>', '>' + t('Reembolsada') + '</option>')
c3 = c3.replace('placeholder="Desde"', 'placeholder="' + t('Desde') + '"')
c3 = c3.replace('placeholder="Hasta"', 'placeholder="' + t('Hasta') + '"')
c3 = c3.replace('>Aplicar filtros</button>', '>' + t('Aplicar filtros') + '</button>')
c3 = c3.replace('>Limpiar</a>', '>' + t('Limpiar') + '</a>')

c3 = c3.replace('>N Factura</th>', '>' + t('N° Factura') + '</th>')
c3 = c3.replace('>Paciente</th>', '>' + t('Paciente') + '</th>')
c3 = c3.replace('>Medico</th>', '>' + t('Médico') + '</th>')
c3 = c3.replace('>Fecha consulta</th>', '>' + t('Fecha consulta') + '</th>')
c3 = c3.replace('>Monto</th>', '>' + t('Monto') + '</th>')
c3 = c3.replace('>Estado</th>', '>' + t('Estado') + '</th>')
c3 = c3.replace('>Acciones</th>', '>' + t('Acciones') + '</th>')

c3 = c3.replace('Sin paciente', t('Sin paciente'))
c3 = c3.replace('Sin medico', t('Sin médico'))
c3 = c3.replace('Adel.', t('Adel.'))

c3 = c3.replace('>Pagada</span>', '>' + t('Pagada') + '</span>')
c3 = c3.replace('>Emitida</span>', '>' + t('Emitida') + '</span>')
c3 = c3.replace('>Borrador</span>', '>' + t('Borrador') + '</span>')
c3 = c3.replace('>Anulada</span>', '>' + t('Anulada') + '</span>')
c3 = c3.replace('>Atendida</span>', '>' + t('Atendida') + '</span>')
c3 = c3.replace('>Pagada adelanto</span>', '>' + t('Pagada adelanto') + '</span>')

c3 = c3.replace('>Ver detalle</button>', '>' + t('Ver detalle') + '</button>')
c3 = c3.replace('>PDF</a>', '>' + t('PDF') + '</a>')

c3 = c3.replace('No se encontraron facturas en el periodo seleccionado.', t('No se encontraron facturas en el período seleccionado.'))

c3 = c3.replace('>Pagina', '>' + t('Página'))
c3 = c3.replace(' de ', ' ' + t('de') + ' ')
c3 = c3.replace('>Anterior</', '>' + t('Anterior') + '</')
c3 = c3.replace('>Siguiente</', '>' + t('Siguiente') + '</')

c3 = c3.replace('Paciente: ', t('Paciente:') + ' ')
c3 = c3.replace('Medico: ', t('Médico:') + ' ')
c3 = c3.replace('Fecha: ', t('Fecha:') + ' ')
c3 = c3.replace('Total: ', t('Total:') + ' ')
c3 = c3.replace('(Adel.', '(' + t('Adel.'))
c3 = c3.replace('Monto no disponible', t('Monto no disponible'))

c3 = c3.replace('Detalle de factura</h3>', t('Detalle de factura') + '</h3>')
c3 = c3.replace('Healthy Life Clinica', 'Healthy Life ' + t('Clínica'))
c3 = c3.replace('RIF: J-XXXXXXXX-X</p>', t('RIF:') + ' J-XXXXXXXX-X</p>')
c3 = c3.replace('Direccion de la sede principal</p>', t('Dirección de la sede principal') + '</p>')
c3 = c3.replace('Paciente', t('Paciente'))
c3 = c3.replace('Medico', t('Médico'))
c3 = c3.replace('Fecha consulta', t('Fecha consulta'))
c3 = c3.replace('Estado', t('Estado'))
c3 = c3.replace('Concepto', t('Concepto'))
c3 = c3.replace('Cant.', t('Cant.'))
c3 = c3.replace('Precio', t('Precio'))
c3 = c3.replace('Total', t('Total'))
c3 = c3.replace('Cargando conceptos...', t('Cargando conceptos...'))
c3 = c3.replace('>Cerrar</button>', '>' + t('Cerrar') + '</button>')
c3 = c3.replace('>Descargar PDF</button>', '>' + t('Descargar PDF') + '</button>')

c3 = c3.replace('Registrar pago</h3>', t('Registrar pago') + '</h3>')
c3 = c3.replace('Factura <span id="pagoFacturaNum">', t('Factura') + ' <span id="pagoFacturaNum">')
c3 = c3.replace('Monto a pagar', t('Monto a pagar'))
c3 = c3.replace('Metodo de pago', t('Método de pago'))
c3 = c3.replace('Referencia / N operacion', t('Referencia / N° operación'))
c3 = c3.replace('Fecha de pago', t('Fecha de pago'))
c3 = c3.replace('>Cancelar</button>', '>' + t('Cancelar') + '</button>')
c3 = c3.replace('>Registrar pago</button>', '>' + t('Registrar pago') + '</button>')
c3 = c3.replace('<option value="efectivo">Efectivo</option>', '<option value="efectivo">' + t('Efectivo') + '</option>')
c3 = c3.replace('<option value="tarjeta">Tarjeta</option>', '<option value="tarjeta">' + t('Tarjeta') + '</option>')
c3 = c3.replace('<option value="transferencia">Transferencia</option>', '<option value="transferencia">' + t('Transferencia') + '</option>')
c3 = c3.replace('placeholder="0.00"', 'placeholder="' + t('0.00') + '"')
c3 = c3.replace('placeholder="Opcional"', 'placeholder="' + t('Opcional') + '"')

c3 = c3.replace('"Sin paciente"', '"' + t('Sin paciente') + '"')
c3 = c3.replace('"Sin medico"', '"' + t('Sin médico') + '"')
c3 = c3.replace('Consulta medica', t('Consulta médica'))

open(path3, 'w', encoding='utf-8').write(c3)
print('Translated:', path3)

# ---------------------------------------------------------------------------
# Template 4: lista_pacientes.html
# ---------------------------------------------------------------------------
path4 = os.path.join(BASE, 'templates', 'usuarios', 'lista_pacientes.html')
c4 = open(path4, 'r', encoding='utf-8').read()

c4 = c4.replace('Pacientes - Healthy Life', t('Pacientes') + ' - Healthy Life')
c4 = c4.replace('>Dashboard</a>', '>' + t('Dashboard') + '</a>')
c4 = c4.replace('>Citas</a>', '>' + t('Citas') + '</a>')
c4 = c4.replace('>Facturación</a>', '>' + t('Facturación') + '</a>')
c4 = c4.replace('>Pacientes</a>', '>' + t('Pacientes') + '</a>')
c4 = c4.replace('>Cerrar sesión</a>', '>' + t('Cerrar sesión') + '</a>')

c4 = c4.replace('aria-label="Menú"', 'aria-label="' + t('Menú') + '"')
c4 = c4.replace('>Inicio</a>', '>' + t('Inicio') + '</a>')
c4 = c4.replace('>Dashboard</a>', '>' + t('Dashboard') + '</a>')
c4 = c4.replace('>Pacientes</span>', '>' + t('Pacientes') + '</span>')
c4 = c4.replace('Lista de Pacientes</h1>', t('Lista de Pacientes') + '</h1>')
c4 = c4.replace('Pacientes registrados en el sistema</p>', t('Pacientes registrados en el sistema') + '</p>')
c4 = c4.replace('Recepcionista</p>', t('Recepcionista') + '</p>')

c4 = c4.replace('placeholder="Buscar por nombre, apellido, cédula o teléfono..."', 'placeholder="' + t('Buscar por nombre, apellido, cédula o teléfono...') + '"')
c4 = c4.replace('>Buscar</button>', '>' + t('Buscar') + '</button>')
c4 = c4.replace('>Limpiar</a>', '>' + t('Limpiar') + '</a>')

c4 = c4.replace('>Nombre</th>', '>' + t('Nombre') + '</th>')
c4 = c4.replace('>Apellido</th>', '>' + t('Apellido') + '</th>')
c4 = c4.replace('>Cédula</th>', '>' + t('Cédula') + '</th>')
c4 = c4.replace('>Teléfono</th>', '>' + t('Teléfono') + '</th>')
c4 = c4.replace('>Sede</th>', '>' + t('Sede') + '</th>')
c4 = c4.replace('>Menores a cargo</th>', '>' + t('Menores a cargo') + '</th>')

c4 = c4.replace('No se encontraron pacientes con', t('No se encontraron pacientes con'))
c4 = c4.replace('No hay pacientes registrados en el sistema.', t('No hay pacientes registrados en el sistema.'))
c4 = c4.replace(' menores a cargo', ' ' + t('menores a cargo'))

open(path4, 'w', encoding='utf-8').write(c4)
print('Translated:', path4)

print('\nAll receptionist templates translated!')
