#!/usr/bin/env python3
"""
Envía correos personalizados a partir de yacambukrae1.csv
CC visible  : kracademyofeucation@gmail.com
BCC (oculta): informacion@kraeducation.com
"""

import csv, ssl, smtplib, time, pathlib, sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ── CONFIGURACIÓN SMTP ───────────────────────────────────────────────
SMTP_HOST_IP   = "204.13.23"            # fuerza IPv4
SMTP_HOST_NAME = "mail.kraeducation.com"     # nombre del certificado
SMTP_PORT      = 587                         # STARTTLS
SMTP_USER      = "informacion@krtion.com"
SMTP_PASS      = "Kra"

# ── RUTA AL CSV ──────────────────────────────────────────────────────
BASE_DIR = pathlib.Path(__file__).parent
CSV_PATH = BASE_DIR / "OAV14_ISBET.csv"

# ── DESTINATARIOS EN COPIA ───────────────────────────────────────────
CC_ADDR  = "tu correo@gmail.com"
BCC_ADDR = "rapanuti@gmail.com"

# ── MENSAJE ──────────────────────────────────────────────────────────
# ── MENSAJE ──────────────────────────────────────────────────────────
SUBJECT  = "Curso Operaciones Aduaneras desde Venezuela XIV"

TEMPLATE = """\
Estimado(a) {firstname} {lastname},

¡Bienvenido(a) al curso Operaciones Aduaneras desde Venezuela XIV!

Nos complace contar con su participación en esta experiencia formativa diseñada para quienes desean comprender y dominar el mundo del comercio exterior y las operaciones aduaneras en Venezuela.

Este curso ha sido desarrollado para brindarle conocimientos prácticos y actuales que le permitirán entender cómo funcionan realmente los procesos de importación y exportación, la normativa vigente y los elementos clave para operar con seguridad y eficiencia en el entorno aduanero.

Aquí no solo verá teoría: aprenderá cómo se mueve la mercancía, qué documentos se exigen, cómo evitar errores costosos y cómo tomar decisiones estratégicas en operaciones reales. ()

El comercio internacional no espera… y usted está a punto de entender cómo jugar en ese terreno con ventaja. 🚀

Ya puede acceder a la plataforma a través del siguiente enlace:

https://kraeducation.com/aula/course/view.php?id=55

Sus credenciales son:

Usuario: {username}
Contraseña: {password}
Correo electrónico: {email}

Le recomendamos comenzar con lo siguiente:

• Explorar los fundamentos de las operaciones aduaneras
• Familiarizarse con los procesos de importación y exportación
• Avanzar de forma progresiva, aplicando cada concepto

Durante este recorrido descubrirá cómo funcionan realmente las aduanas, los requisitos documentales, los actores involucrados y las oportunidades que existen en el comercio internacional cuando se sabe lo que se está haciendo.

Este espacio ha sido diseñado para que desarrolle criterio, visión estratégica y habilidades aplicables desde el primer momento.

Estamos seguros de que este curso marcará un antes y un después en su comprensión del área aduanera.

¡Mucho éxito en esta nueva etapa de aprendizaje!"""
# ── LECTURA DEL CSV (detección encoding y delimitador) ───────────────
encodings = ["utf-8", "utf-8-sig", "latin1", "cp1252"]
rows = None
for enc in encodings:
    try:
        with CSV_PATH.open("r", encoding=enc, newline='') as f:
            sample = f.read(2048)
            delim = ";" if sample.count(";") > sample.count(",") else ","
            f.seek(0)
            rows = list(csv.DictReader(f, delimiter=delim))
            break
    except UnicodeDecodeError:
        continue

if not rows:
    sys.exit("❌ No pude leer el CSV. Guarda en UTF-8 o Latin-1.")

print("ℹ️ CSV leído correctamente – enviando correos…")

# ── ENVÍO ────────────────────────────────────────────────────────────
context = ssl.create_default_context()
with smtplib.SMTP(SMTP_HOST_IP, SMTP_PORT, timeout=60) as server:
    # Ajusta _host para que la verificación TLS use el nombre del certificado
    server._host = SMTP_HOST_NAME
    server.starttls(context=context)
    server.login(SMTP_USER, SMTP_PASS)

    for row in rows:
        msg = MIMEMultipart()
        msg["From"]    = SMTP_USER
        msg["To"]      = row["email"]
        msg["Cc"]      = CC_ADDR
        msg["Bcc"]     = BCC_ADDR
        msg["Subject"] = SUBJECT
        msg.attach(MIMEText(TEMPLATE.format(**row), "plain"))

        server.send_message(msg)
        print("✔ Enviado a", row["email"])
        time.sleep(2)  # ajusta si tu hosting limita envíos/hora
