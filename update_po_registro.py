#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, polib

BASE = r'C:\Users\user\Desktop\healty-life-2'

strings = {
    "Registrar Paciente": {"en": "Register Patient", "pt": "Registrar Paciente"},
    "Información Básica": {"en": "Basic Information", "pt": "Informação Básica"},
    "Información Personal": {"en": "Personal Information", "pt": "Informação Pessoal"},
    "Centro Médico y Sede": {"en": "Medical Center and Branch", "pt": "Centro Médico e Sede"},
    "Centro Médico": {"en": "Medical Center", "pt": "Centro Médico"},
    "Seleccione un centro médico": {"en": "Select a medical center", "pt": "Selecione um centro médico"},
    "Ubicación": {"en": "Location", "pt": "Localização"},
    "Condición Especial": {"en": "Special Condition", "pt": "Condição Especial"},
    "Datos del Tutor o Representante Legal": {"en": "Tutor or Legal Representative Data", "pt": "Dados do Tutor ou Representante Legal"},
    "Cancelar": {"en": "Cancel", "pt": "Cancelar"},
    "Primero seleccione un centro médico": {"en": "First select a medical center", "pt": "Primeiro selecione um centro médico"},
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
