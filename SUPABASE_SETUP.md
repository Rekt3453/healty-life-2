# Configuración de Django con Supabase

## Estado Actual

✅ **Completado:**
- Configuración de settings.py con credenciales de Supabase
- Instalación de dependencias (psycopg2-binary, Django, reportlab)
- Actualización de modelos con `managed = False`
- Implementación de filtrado automático por sede
- Creación de Managers personalizados para consultas
- Configuración de middleware para contexto de sede
- Verificación de configuración con `manage.py check`

❌ **Pendiente:**
- Corregir credenciales de conexión a Supabase

## Problema Detectado

Las credenciales proporcionadas para Supabase no están funcionando:
```
USER: postgres.xpzrljaykpanthomlegn
PASSWORD: licuadora33
HOST: aws-0-us-west-2.pooler.supabase.com
PORT: 6543
```

Error: `tenant/user postgres.xpzrljaykpanthomlegn not found`

## Pasos para Solucionar

1. **Verificar credenciales en Supabase:**
   - Inicia sesión en tu panel de Supabase
   - Ve a Settings > Database
   - Revisa las credenciales de conexión
   - El formato de usuario suele ser: `postgres.[project-ref]`

2. **Actualizar credenciales en settings.py:**
   Reemplaza las credenciales actuales en `clinica_root/settings.py` con las correctas.

3. **Ejecutar inspectdb (opcional):**
   Una vez conectado, puedes ejecutar:
   ```bash
   python manage.py inspectdb > models_generated.py
   ```
   Para verificar que los nombres de tabla coinciden.

## Modelos Configurados

Todos los modelos ahora tienen:
- `managed = False` (Django no modificará las tablas)
- `db_table` especificando el nombre exacto de la tabla
- Lógica de negocio preservada
- Filtrado automático por sede

### Nombres de tabla configurados:
- `usuarios_sede`
- `usuarios_userprofile`
- `usuarios_especialidad`
- `usuarios_medicoprofile`
- `usuarios_pacienteprofile`
- `citas_servicio`
- `citas_disponibilidadmedica`
- `citas_cita`
- `citas_factura`
- `citas_historiaclinica`
- `citas_reporte`

## Filtrado por Sede

Se ha implementado un sistema completo de filtrado por sede:

1. **Middleware:** `SedeMiddleware` establece automáticamente la sede del usuario
2. **Manager:** `CitaManager` con métodos específicos para filtrar por sede
3. **Uso en vistas:**
   ```python
   # Filtrado automático
   citas = Cita.objects.all()
   
   # Filtrado explícito
   citas = Cita.objects.for_sede(sede_usuario)
   
   # Métodos específicos
   citas_pendientes = Cita.objects.pendientes(sede_usuario)
   ```

## Pruebas

Una vez corregidas las credenciales:
```bash
# Verificar conexión
python manage.py check

# Iniciar servidor
python manage.py runserver
```

## Restricciones Importantes

- ❌ **NO EJECUTAR:** `makemigrations`, `migrate`, `flush`, `loaddata`
- ✅ **PERMITIDO:** `check`, `runserver`, `shell`, `inspectdb`
- 📋 Las tablas existentes no serán modificadas
- 🔒 Solo lectura del esquema de la base de datos
