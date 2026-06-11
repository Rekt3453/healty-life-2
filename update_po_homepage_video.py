#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, polib

BASE = r'C:\Users\user\Desktop\healty-life-2'

strings = {
    "Ver nuestro tutorial en vídeo": {"en": "Watch our video tutorial", "pt": "Veja nosso tutorial em vídeo"},
    "Aprende a registrarte paso a paso": {"en": "Learn to register step by step", "pt": "Aprenda a se registrar passo a passo"},
    "Tutorial en vídeo – guía completa para usar la plataforma": {"en": "Video tutorial – complete guide to using the platform", "pt": "Tutorial em vídeo – guia completa para usar a plataforma"},
    "Aprende a solicitar una cita paso a paso": {"en": "Learn to request an appointment step by step", "pt": "Aprenda a solicitar uma consulta passo a passo"},
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
