# Healthy Life

Aplicación web para la gestión de citas médicas, historiales clínicos, facturación y administración de clínicas.

## Requisitos

- Python 3.12+
- pip
- Entorno virtual recomendado (venv)

## Instalación

1. **Clonar o ubicarse en el proyecto**

```bash
cd healty-life-2
```

2. **Crear entorno virtual**

```bash
python -m venv venv
```

3. **Activar entorno virtual**

- Windows:
```bash
venv\Scripts\activate
```

- Linux/macOS:
```bash
source venv/bin/activate
```

4. **Instalar dependencias**

```bash
pip install -r requirements.txt
```

5. **Configurar variables de entorno**

Crear un archivo `.env` en la raíz del proyecto basado en el siguiente ejemplo:

```env
SECRET_KEY=tu-clave-secreta-aqui
DEBUG=True
DB_NAME=healthy_life
DB_USER=usuario
DB_PASSWORD=contraseña
DB_HOST=localhost
DB_PORT=3306
```

6. **Aplicar migraciones**

```bash
python manage.py migrate
```

7. **Cargar datos iniciales (opcional)**

```bash
python manage.py loaddata data_inicial.json
```

8. **Ejecutar servidor de desarrollo**

```bash
python manage.py runserver
```

La aplicación estará disponible en `http://127.0.0.1:8000/`

## Internacionalización (i18n)

El proyecto soporta múltiples idiomas (Español, Inglés y Portugués).

### Agregar nuevas traducciones

1. Extraer strings nuevos de templates y código:

```bash
python manage.py makemessages -l en
python manage.py makemessages -l pt
```

2. Editar los archivos `.po` en `locale/<lang>/LC_MESSAGES/django.po`

3. Compilar traducciones:

```bash
python manage.py compilemessages
```

### Archivos de traducción

- `locale/en/LC_MESSAGES/django.po` — Inglés
- `locale/pt/LC_MESSAGES/django.po` — Portugués

### Template tag personalizado

Para traducir strings provenientes de la base de datos (vacunas, alergias, enfermedades), se usa el filtro `trans_str`:

```django
{% load user_tags %}
{{ valor_db|trans_str }}
```

## Estructura del proyecto

```
healty-life-2/
├── citas/                 # Gestión de citas, pagos y facturación
├── usuarios/              # Autenticación, perfiles y roles
├── templates/             # Templates HTML
│   ├── citas/
│   ├── usuarios/
│   └── partials/
├── locale/                # Archivos de traducción (.po/.mo)
├── static/                # CSS, JS, imágenes
├── manage.py
└── requirements.txt
```

## Roles del sistema

- **Paciente**: solicita citas, consulta historial médico, ve facturas
- **Doctor**: gestiona consultas, genera recetas
- **Recepcionista**: agenda citas, gestiona pagos
- **Gerente**: reportes, estadísticas, administración

## Notas

- La configuración de correo SMTP usa contraseña de aplicación de Gmail (requiere 2FA activado).
- Verificar que los puertos 587/465 no estén bloqueados por firewall si hay problemas de envío de correo.
