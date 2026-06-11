#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, polib

BASE = r'C:\Users\user\Desktop\healty-life-2'

strings = {
    "Agendadas": {"en": "Scheduled", "pt": "Agendadas"},
    "En planta": {"en": "On duty", "pt": "Em plantão"},
    "Consultas do dia": {"en": "Today's appointments", "pt": "Consultas do dia"},
    "consultas programadas": {"en": "scheduled appointments", "pt": "consultas programadas"},
    "em consulta": {"en": "in consultation", "pt": "em consulta"},
    "Nenhuma consulta programada para hoje": {"en": "No appointments scheduled for today", "pt": "Nenhuma consulta programada para hoje"},
    "Nenhuma solicitação pendente": {"en": "No pending requests", "pt": "Nenhuma solicitação pendente"},
    "Não há consultas agendadas nos próximos dias": {"en": "No appointments scheduled for the coming days", "pt": "Não há consultas agendadas nos próximos dias"},
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
