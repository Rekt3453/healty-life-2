#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, polib

BASE = r'C:\Users\user\Desktop\healty-life-2'

strings = {
    "Nombre de Usuario": {"en": "Username", "pt": "Nome de Usuário"},
    "Correo Electrónico": {"en": "Email", "pt": "E-mail"},
    "Contraseña": {"en": "Password", "pt": "Senha"},
    "Confirmar Contraseña": {"en": "Confirm Password", "pt": "Confirmar Senha"},
    "Primer Nombre": {"en": "First Name", "pt": "Primeiro Nome"},
    "Segundo Nombre": {"en": "Second Name", "pt": "Segundo Nome"},
    "Primer Apellido": {"en": "First Last Name", "pt": "Primeiro Sobrenome"},
    "Segundo Apellido": {"en": "Second Last Name", "pt": "Segundo Sobrenome"},
    "Tipo de Cédula": {"en": "ID Type", "pt": "Tipo de Cédula"},
    "Cédula de Identidad": {"en": "ID Card", "pt": "Bilhete de Identidade"},
    "Sexo": {"en": "Sex", "pt": "Sexo"},
    "Fecha de Nacimiento": {"en": "Date of Birth", "pt": "Data de Nascimento"},
    "Número de Teléfono": {"en": "Phone Number", "pt": "Número de Telefone"},
    "Sede de Atención": {"en": "Attention Center", "pt": "Centro de Atendimento"},
    "Seleccione una sede": {"en": "Select a center", "pt": "Selecione uma sede"},
    "Estado": {"en": "State", "pt": "Estado"},
    "Seleccione un estado": {"en": "Select a state", "pt": "Selecione um estado"},
    "Municipio": {"en": "Municipality", "pt": "Município"},
    "Seleccione un municipio": {"en": "Select a municipality", "pt": "Selecione um município"},
    "Ciudad": {"en": "City", "pt": "Cidade"},
    "Seleccione una ciudad": {"en": "Select a city", "pt": "Selecione uma cidade"},
    "Parroquia": {"en": "Parish", "pt": "Paróquia"},
    "Seleccione una parroquia": {"en": "Select a parish", "pt": "Selecione uma paróquia"},
    "Dirección": {"en": "Address", "pt": "Endereço"},
    "Referencia": {"en": "Reference", "pt": "Referência"},
    "Tengo una condición médica que requiere atención especial": {"en": "I have a medical condition that requires special attention", "pt": "Tenho uma condição médica que requer atenção especial"},
    "Describa su condición médica": {"en": "Describe your medical condition", "pt": "Descreva sua condição médica"},
    "Nombre completo del tutor/responsable": {"en": "Full name of tutor/guardian", "pt": "Nome completo do tutor/responsável"},
    "Cédula del tutor": {"en": "Tutor's ID", "pt": "Cédula do tutor"},
    "Teléfono del tutor": {"en": "Tutor's Phone", "pt": "Telefone do tutor"},
    "Parentesco del tutor": {"en": "Tutor's Relationship", "pt": "Parentesco do tutor"},
    "Seleccione parentesco": {"en": "Select relationship", "pt": "Selecione parentesco"},
    "Padre": {"en": "Father", "pt": "Pai"},
    "Madre": {"en": "Mother", "pt": "Mãe"},
    "Tutor legal": {"en": "Legal guardian", "pt": "Tutor legal"},
    "Abuelo/a": {"en": "Grandparent", "pt": "Avô/Avó"},
    "Otro": {"en": "Other", "pt": "Outro"},
    "Correo del tutor": {"en": "Tutor's Email", "pt": "E-mail do tutor"},
    "Primero seleccione un centro médico": {"en": "First select a medical center", "pt": "Primeiro selecione um centro médico"},
    "Cargando...": {"en": "Loading...", "pt": "Carregando..."},
    "Error al cargar sedes": {"en": "Error loading centers", "pt": "Erro ao carregar sedes"},
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
