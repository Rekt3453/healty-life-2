#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, polib

BASE = r'C:\Users\user\Desktop\healty-life-2'

strings = {
    "Próximas citas": {"en": "Upcoming appointments", "pt": "Próximas consultas"},
    "Próximos 3 días": {"en": "Next 3 days", "pt": "Próximos 3 dias"},
    "Sin especialidad": {"en": "Sin especialidad", "pt": "Sem especialidade"},
    "En Consulta": {"en": "In Consultation", "pt": "Em Consulta"},
    "Ver detalles": {"en": "View details", "pt": "Ver detalhes"},
    "No hay citas programadas próximamente": {"en": "No upcoming appointments scheduled", "pt": "Nenhuma consulta programada próximamente"},
    "Solicitudes pendientes": {"en": "Pending requests", "pt": "Solicitações pendentes"},
    "Citas por confirmar o rechazar": {"en": "Appointments to confirm or reject", "pt": "Consultas para confirmar ou recusar"},
    "No hay solicitudes pendientes": {"en": "No pending requests", "pt": "Nenhuma solicitação pendente"},
    "Citas del día": {"en": "Today's appointments", "pt": "Consultas do dia"},
    "citas programadas": {"en": "appointments scheduled", "pt": "consultas programadas"},
    "en consulta": {"en": "in consultation", "pt": "em consulta"},
    "Ver todas": {"en": "View all", "pt": "Ver todas"},
    "Hora": {"en": "Time", "pt": "Hora"},
    "Especialidad": {"en": "Specialty", "pt": "Especialidade"},
    "Consultorio": {"en": "Office", "pt": "Consultório"},
    "Llegó": {"en": "Arrived", "pt": "Chegou"},
    "No hay citas programadas para hoy": {"en": "No appointments scheduled for today", "pt": "Nenhuma consulta programada para hoje"},
    "registros": {"en": "records", "pt": "registros"},
}

for lang in ['en', 'pt']:
    po_path = os.path.join(BASE, 'locale', lang, 'LC_MESSAGES', 'django.po')
    mo_path = os.path.join(BASE, 'locale', lang, 'LC_MESSAGES', 'django.mo')
    po = polib.pofile(po_path)
    for msgid, translations in strings.items():
        msgstr = translations.get(lang, msgid)
        entry = po.find(msgid)
        if entry:
            entry.msgstr = msgstr
        else:
            entry = polib.POEntry(msgid=msgid, msgstr=msgstr)
            po.append(entry)
    po.save()
    po.save_as_mofile(mo_path)
    print(f'Updated {lang} .po and .mo')

print('All done!')
