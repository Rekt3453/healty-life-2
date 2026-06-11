#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, polib

BASE = r'C:\Users\user\Desktop\healty-life-2'

strings = {
    "Llegó": {"en": "Arrived", "pt": "Chegou"},
    "Confirmar cita": {"en": "Confirm Appointment", "pt": "Confirmar Consulta"},
    "¿Deseas confirmar esta cita? El paciente recibirá una notificación.": {"en": "Do you want to confirm this appointment? The patient will receive a notification.", "pt": "Deseja confirmar esta consulta? O paciente receberá uma notificação."},
    "Sí, confirmar": {"en": "Yes, confirm", "pt": "Sim, confirmar"},
    "Rechazar cita": {"en": "Reject Appointment", "pt": "Rejeitar Consulta"},
    "¿Deseas rechazar esta cita? Esta acción no se puede deshacer.": {"en": "Do you want to reject this appointment? This action cannot be undone.", "pt": "Deseja rejeitar esta consulta? Esta ação não pode ser desfeita."},
    "Motivo (opcional)": {"en": "Reason (optional)", "pt": "Motivo (opcional)"},
    "Indica el motivo del rechazo...": {"en": "Indicate the reason for rejection...", "pt": "Indique o motivo da rejeição..."},
    "Sí, rechazar": {"en": "Yes, reject", "pt": "Sim, rejeitar"},
    "Cancelar cita": {"en": "Cancel Appointment", "pt": "Cancelar Consulta"},
    "¿Deseas cancelar esta cita confirmada? El paciente será notificado.": {"en": "Do you want to cancel this confirmed appointment? The patient will be notified.", "pt": "Deseja cancelar esta consulta confirmada? O paciente será notificado."},
    "No, mantener": {"en": "No, keep it", "pt": "Não, manter"},
    "Sí, cancelar": {"en": "Yes, cancel", "pt": "Sim, cancelar"},
    "Marcar como atendida": {"en": "Mark as attended", "pt": "Marcar como atendida"},
    "¿Confirmas que el paciente llegó a su consulta?": {"en": "Do you confirm that the patient arrived for their appointment?", "pt": "Confirma que o paciente chegou para a consulta?"},
    "Sí, marcar llegada": {"en": "Yes, mark arrival", "pt": "Sim, marcar chegada"},
    "Cita confirmada correctamente": {"en": "Appointment confirmed successfully", "pt": "Consulta confirmada com sucesso"},
    "Cita rechazada correctamente": {"en": "Appointment rejected successfully", "pt": "Consulta rejeitada com sucesso"},
    "Cita cancelada correctamente": {"en": "Appointment cancelled successfully", "pt": "Consulta cancelada com sucesso"},
    "Paciente marcado como atendido": {"en": "Patient marked as attended", "pt": "Paciente marcado como atendido"},
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
