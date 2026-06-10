#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Add extra receptionist translations to django.po files."""
import os, polib

BASE = r'C:\Users\user\Desktop\healty-life-2'

extra_strings = {
    "¿Cancelar esta cita?": {
        "en": "¿Cancelar esta cita?",
        "pt": "Cancelar esta consulta?",
    },
    "Cancelada por recepcionista/gerente": {
        "en": "Cancelada por recepcionista/gerente",
        "pt": "Cancelada por recepcionista/gerente",
    },
    "No hay citas aceptadas.": {
        "en": "No hay citas aceptadas.",
        "pt": "Nenhuma consulta aceita.",
    },
    "Gestiona citas, pacientes y horarios del día": {
        "en": "Manage appointments, patients and daily schedules",
        "pt": "Gerencie consultas, pacientes e horários do dia",
    },
}

for lang in ['en', 'pt']:
    po_path = os.path.join(BASE, 'locale', lang, 'LC_MESSAGES', 'django.po')
    mo_path = os.path.join(BASE, 'locale', lang, 'LC_MESSAGES', 'django.mo')
    po = polib.pofile(po_path)
    for msgid, translations in extra_strings.items():
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
