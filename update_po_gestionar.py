#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, polib

BASE = r'C:\Users\user\Desktop\healty-life-2'

strings = {
    "Total citas": {"en": "Total appointments", "pt": "Total de consultas"},
    "Solicitudes": {"en": "Requests", "pt": "Solicitações"},
    "Pagos por confirmar": {"en": "Payments to confirm", "pt": "Pagamentos a confirmar"},
    "Aceptadas": {"en": "Accepted", "pt": "Aceitas"},
    "Fecha": {"en": "Date", "pt": "Data"},
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
