from decimal import Decimal

from django.db import transaction
from django.utils import timezone


class CitaService:

    @staticmethod
    def verificar_rol(user, *roles_permitidos):
        """Verifica que el usuario tenga uno de los roles permitidos. Lanza PermissionError si no."""
        from usuarios.authentication import CustomAuthBackend
        auth_backend = CustomAuthBackend()
        user_rol = auth_backend.get_rol(user)
        rol_mapping = {
            'paciente': 'paciente',
            'medico': 'medico',
            'recepcionista': 'recepcionista',
            'gerente': 'gerente',
            'administrador': 'gerente',
        }
        mapped_roles = [rol_mapping.get(r, r) for r in roles_permitidos]
        if user_rol not in mapped_roles:
            raise PermissionError(
                f"Se requiere uno de estos roles: {', '.join(roles_permitidos)}. "
                f"Rol actual: {user_rol or 'sin rol'}."
            )
        return user_rol

    @staticmethod
    @transaction.atomic
    def crear_cita(user, *, sede_id, especialidad_id, doctor_id, servicio_id,
                    fecha, hora, motivo_raw, paciente_objetivo='self'):
        """
        Crea una cita con su pago asociado. Valida roles, especialidades por tipo de paciente,
        y genera el motivo con prefijo si es para un menor.
        """
        from citas.models import Cita as CitaModel, PagoCita, ServicioEspecialidad, Especialidad
        from usuarios.models import PacienteDatosPersonales, PacienteEspecial, Sede, Doctor
        from datetime import datetime, date, timedelta
        from django.utils.timezone import make_aware, localtime

        CitaService.verificar_rol(user, 'paciente')

        paciente = PacienteDatosPersonales.objects.filter(id_user_paciente=user).first()
        if not paciente:
            raise ValueError("No se encontró el perfil de paciente para el usuario.")

        _CLASIFICACIONES_POR_TIPO = {
            'adulto': ['Adultos', 'General'],
            'menor':  ['Pediatría', 'General'],
        }

        fecha_hora_naive = datetime.strptime(f"{fecha} {hora}", "%Y-%m-%d %H:%M")
        fecha_hora = make_aware(fecha_hora_naive)

        # Debe ser al menos mañana
        manana = make_aware(datetime.combine(date.today(), datetime.min.time())) + timedelta(days=1)
        if fecha_hora < manana:
            raise ValueError("Las citas deben solicitarse con al menos un día de anticipación.")

        # Validar disponibilidad del doctor para esa fecha/hora
        from citas.models import DisponibilidadDoctor as DispDoctor
        doctor = Doctor.objects.get(id_doctor=doctor_id)
        try:
            disp = DispDoctor.objects.get(doctor=doctor, fecha=fecha)
        except DispDoctor.DoesNotExist:
            raise ValueError("El médico no tiene disponibilidad configurada para esta fecha.")
        if not disp.turno_mañana and not disp.turno_tarde:
            raise ValueError("El médico no tiene disponibilidad configurada para esta fecha.")

        hora_int = fecha_hora_naive.hour
        if disp.turno_mañana and 8 <= hora_int < 13:
            pass
        elif disp.turno_tarde and 13 <= hora_int < 18:
            pass
        else:
            raise ValueError("La hora seleccionada no está dentro de los turnos disponibles del médico.")

        # Verificar conflicto de horario con el mismo doctor (bloques de 1 hora)
        if CitaModel.objects.filter(
            id_doctor_id=doctor_id,
            fecha_consulta__gte=fecha_hora,
            fecha_consulta__lt=fecha_hora + timedelta(hours=1),
            status=True,
        ).exists():
            raise ValueError("El médico ya tiene una cita agendada en ese bloque horario. Por favor selecciona otro horario.")

        sede = Sede.objects.get(id_sede=sede_id)
        especialidad = Especialidad.objects.get(id_especialidad=especialidad_id)
        doctor = Doctor.objects.get(id_doctor=doctor_id)

        menor_obj = None
        if paciente_objetivo.startswith('especial_'):
            menor_id = int(paciente_objetivo.split('_', 1)[1])
            menor_obj = PacienteEspecial.objects.get(
                id_paciente_especial=menor_id,
                id_paciente_tutor=paciente,
                status=True,
            )
            clasificacion = especialidad.clasificacion_especialidad or ''
            permitidas_menor = _CLASIFICACIONES_POR_TIPO['menor']
            if clasificacion not in permitidas_menor:
                raise ValueError(
                    f"Para un menor de edad debes seleccionar una especialidad de "
                    f"Pediatría o General. La especialidad '{especialidad.tipo_especialidad}' "
                    f"está clasificada como '{clasificacion or 'Sin clasificar'}'."
                )
            nombre_menor = f"{menor_obj.nombre_1} {menor_obj.apellido_1}"
            motivo = f"[Cita para {nombre_menor}] {motivo_raw}"
        else:
            clasificacion = especialidad.clasificacion_especialidad or ''
            permitidas_adulto = _CLASIFICACIONES_POR_TIPO['adulto']
            if clasificacion and clasificacion not in permitidas_adulto:
                raise ValueError(
                    f"Para un paciente adulto debes seleccionar una especialidad de "
                    f"Adultos o General. La especialidad '{especialidad.tipo_especialidad}' "
                    f"está clasificada como '{clasificacion}'."
                )
            motivo = motivo_raw

        servicio_obj = None
        if servicio_id:
            servicio_obj = ServicioEspecialidad.objects.filter(
                id_servicios_especialidad=servicio_id
            ).first()

        pago = PagoCita.objects.create(
            id_paciente=paciente,
            id_sede=sede,
            fecha_consulta=fecha_hora,
            status=False,
            estado_pago=PagoCita.ESTADO_PENDIENTE,
        )

        cita = CitaModel.objects.create(
            id_paciente=paciente,
            id_doctor=doctor,
            id_sede=sede,
            id_especialidades=especialidad,
            id_servicio_especialidad=servicio_obj,
            id_pago_cita=pago,
            fecha_consulta=fecha_hora,
            fecha_emision=timezone.now(),
            motivo=motivo,
            status=True,
            estado=CitaModel.ESTADO_SOLICITADA,
        )

        nombre_destino = nombre_menor if menor_obj else "ti"
        return cita, f"✅ Cita solicitada para {nombre_destino} el {fecha} a las {hora}. Espera confirmación."

    @staticmethod
    def listar_citas_medico(user):
        """
        Retorna (citas_pendientes, citas_asignadas) para el médico autenticado.
        Pendientes → confirmadas, listas para consulta.
        Asignadas → en consulta actualmente.
        """
        from citas.models import Cita as CitaModel
        from usuarios.authentication import CustomAuthBackend
        from django.db.models import Q

        CitaService.verificar_rol(user, 'medico')
        datos_medico = CustomAuthBackend().get_datos_personales(user)

        citas_pendientes = CitaModel.objects.none()
        citas_asignadas = CitaModel.objects.none()

        if datos_medico:
            base_qs = CitaModel.objects.filter(
                id_doctor=datos_medico,
                status=True,
            ).select_related(
                'id_paciente', 'id_especialidades', 'id_sede', 'id_pago_cita'
            ).order_by('fecha_consulta')

            citas_pendientes = base_qs.filter(
                Q(estado=CitaModel.ESTADO_CONFIRMADA) |
                Q(estado__isnull=True, id_pago_cita__status=True)
            ).exclude(estado=CitaModel.ESTADO_EN_CONSULTA)

            citas_asignadas = base_qs.filter(estado=CitaModel.ESTADO_EN_CONSULTA)

        return citas_pendientes, citas_asignadas, datos_medico

    @staticmethod
    def obtener_doctores_disponibles(especialidad_id, sede_id):
        """
        Retorna lista de doctores disponibles para una especialidad y sede.
        Usa ServicioEspecialidad como fuente principal, con fallback a EspecialidadDoctor.
        """
        from citas.models import Doctor, ServicioEspecialidad, EspecialidadDoctor

        def _serializar(qs):
            return [
                {
                    'id': d.id_doctor,
                    'nombre': f"Dr/a. {(d.nombre_1 or '')} {(d.apellido_1 or '')}".strip(),
                }
                for d in qs
            ]

        doctor_ids = list(
            ServicioEspecialidad.objects.filter(
                id_especialidad_id=especialidad_id,
                id_sede_id=sede_id,
                status__in=[True, None],
            ).values_list('id_doctor_id', flat=True).distinct()
        )

        if doctor_ids:
            doctores = Doctor.objects.filter(
                id_doctor__in=doctor_ids,
                status__in=[True, None],
            )
            return _serializar(doctores)

        espec_doctor_ids = list(
            EspecialidadDoctor.objects.filter(
                id_especialidad_id=especialidad_id
            ).values_list('id_especialidad_doctor', flat=True)
        )

        if espec_doctor_ids:
            doctores = Doctor.objects.filter(
                id_sede_id=sede_id,
                id_especialidad_doctor__in=espec_doctor_ids,
                status__in=[True, None],
            )
        else:
            doctores = Doctor.objects.filter(
                id_sede_id=sede_id,
                status__in=[True, None],
            )

        return _serializar(doctores)

    @staticmethod
    def obtener_horas_disponibles(doctor_id, fecha):
        """
        Retorna slots de 1 hora disponibles para un doctor en una fecha específica,
        respetando su disponibilidad configurada para esa fecha.
        """
        from citas.models import Cita as CitaModel, Doctor, DisponibilidadDoctor
        from datetime import datetime, date, time, timedelta

        doctor = Doctor.objects.get(id_doctor=doctor_id)

        if isinstance(fecha, str):
            fecha = datetime.strptime(fecha, '%Y-%m-%d').date()

        try:
            disp = DisponibilidadDoctor.objects.get(doctor=doctor, fecha=fecha)
        except DisponibilidadDoctor.DoesNotExist:
            return [], 'Doctor no disponible este día'

        if not disp.turno_mañana and not disp.turno_tarde:
            return [], 'Doctor no disponible este día'

        slots = []
        if disp.turno_mañana:
            h = time(8, 0)
            while h < time(13, 0):
                slots.append(h.strftime('%H:%M'))
                h = (datetime.combine(date.today(), h) + timedelta(hours=1)).time()
        if disp.turno_tarde:
            h = time(13, 0)
            while h < time(18, 0):
                slots.append(h.strftime('%H:%M'))
                h = (datetime.combine(date.today(), h) + timedelta(hours=1)).time()

        from django.utils.timezone import is_naive, localtime
        from datetime import timezone as dt_tz
        ocupadas = set()
        for c in CitaModel.objects.filter(id_doctor_id=doctor_id, fecha_consulta__date=fecha, status=True):
            if c.fecha_consulta:
                if is_naive(c.fecha_consulta):
                    # PostgreSQL timestamp without time zone stores UTC
                    aware_utc = c.fecha_consulta.replace(tzinfo=dt_tz.utc)
                    hora_local = localtime(aware_utc)
                    ocupadas.add(f"{hora_local.hour:02d}:00")
                else:
                    hora_local = localtime(c.fecha_consulta)
                    ocupadas.add(f"{hora_local.hour:02d}:00")

        horas = [s for s in slots if s not in ocupadas]
        return horas, None

    @staticmethod
    def transicionar(cita, nuevo_estado, *, campos_extra=None):
        """
        Valida y aplica una transición de estado.
        Lanza ValueError si la transición no está permitida.
        campos_extra: dict de campos adicionales a guardar junto con estado.
        """
        from citas.models import Cita as CitaModel
        estado_actual = cita.estado or CitaModel.ESTADO_SOLICITADA
        permitidos = CitaModel.TRANSICIONES_VALIDAS.get(estado_actual, set())
        if nuevo_estado not in permitidos:
            raise ValueError(
                f"Transición inválida: '{estado_actual}' → '{nuevo_estado}'. "
                f"Permitidos: {sorted(permitidos) or ['ninguno (estado terminal)']}."
            )
        update_fields = ['estado']
        cita.estado = nuevo_estado
        if campos_extra:
            for campo, valor in campos_extra.items():
                setattr(cita, campo, valor)
                update_fields.append(campo)
        cita.save(update_fields=update_fields)
        return cita

    @staticmethod
    @transaction.atomic
    def cancelar_cita(cita, *, cancelada_por, motivo):
        from citas.models import Cita as CitaModel
        estado_actual = cita.estado or CitaModel.ESTADO_SOLICITADA
        permitidos = CitaModel.TRANSICIONES_VALIDAS.get(estado_actual, set())
        if CitaModel.ESTADO_CANCELADA not in permitidos:
            raise ValueError(
                f"No se puede cancelar una cita en estado '{cita.get_estado_display()}'."
            )
        cita.status = False
        cita.estado = CitaModel.ESTADO_CANCELADA
        cita.motivo_cancelacion = motivo
        cita.fecha_cancelacion = timezone.now()
        cita.cancelada_por = str(cancelada_por)
        cita.save(update_fields=[
            'status', 'estado', 'motivo_cancelacion',
            'fecha_cancelacion', 'cancelada_por',
        ])
        return cita

    @staticmethod
    @transaction.atomic
    def aprobar_cita(user, cita):
        """Recepcionista aprueba la solicitud (sin pago aún)."""
        CitaService.verificar_rol(user, 'recepcionista', 'gerente')
        from citas.models import Cita as CitaModel
        CitaService.transicionar(cita, CitaModel.ESTADO_APROBADA)
        cita.status = True
        cita.save(update_fields=['status'])
        return cita

    @staticmethod
    @transaction.atomic
    def confirmar_pago(user, cita):
        """Recepcionista verifica el pago → cita queda confirmada."""
        CitaService.verificar_rol(user, 'recepcionista', 'gerente')
        from citas.models import Cita as CitaModel, PagoCita
        pago = getattr(cita, 'id_pago_cita', None)
        if not pago:
            raise ValueError("La cita no tiene pago asociado.")
        pago.status = True
        pago.estado_pago = PagoCita.ESTADO_APROBADO
        pago.save(update_fields=['status', 'estado_pago'])
        CitaService.transicionar(cita, CitaModel.ESTADO_CONFIRMADA)
        cita.status = True
        cita.save(update_fields=['status'])
        return cita

    @staticmethod
    @transaction.atomic
    def aprobar_pago(user, cita):
        """Alias de confirmar_pago para compatibilidad con código existente."""
        return CitaService.confirmar_pago(user, cita)

    @staticmethod
    @transaction.atomic
    def iniciar_consulta(user, cita):
        """Médico abre la consulta: cita pasa a en_consulta."""
        CitaService.verificar_rol(user, 'medico')
        from citas.models import Cita as CitaModel, ConsultaMedica
        estados_validos = {CitaModel.ESTADO_CONFIRMADA, CitaModel.ESTADO_EN_CONSULTA}
        if cita.estado not in estados_validos:
            raise ValueError(
                f"Solo se puede iniciar consulta en citas confirmadas. "
                f"Estado actual: '{cita.get_estado_display()}'."
            )
        consulta, created = ConsultaMedica.objects.get_or_create(
            id_cita=cita,
            defaults={'motivo_consulta': cita.motivo or ''},
        )
        if cita.estado != CitaModel.ESTADO_EN_CONSULTA:
            CitaService.transicionar(cita, CitaModel.ESTADO_EN_CONSULTA)
        return consulta, created

    @staticmethod
    @transaction.atomic
    def registrar_adelanto(user, cita, *, monto, metodo_pago, referencia=None):
        """Recepcionista registra un adelanto de pago sin generar factura inmediata."""
        CitaService.verificar_rol(user, 'recepcionista', 'gerente')
        from citas.models import Cita as CitaModel, PagoCita
        CitaService.transicionar(cita, CitaModel.ESTADO_PAGADA_ADELANTO)
        pago = PagoCita.objects.create(
            id_paciente=cita.id_paciente,
            monto_pagar=monto,
            metodo_pago=metodo_pago,
            referencia_pago=referencia,
            id_sede=cita.id_sede,
            fecha_consulta=cita.fecha_consulta,
            fecha_pago=timezone.now(),
            status=True,
            estado_pago=PagoCita.ESTADO_APROBADO,
            id_cita=cita.id_citas,
        )
        cita.id_pago_cita = pago
        cita.save(update_fields=['id_pago_cita'])
        return pago

    @staticmethod
    @transaction.atomic
    def cerrar_consulta(user, cita):
        """Médico cierra la consulta: cita pasa a atendida y genera factura si no existe."""
        CitaService.verificar_rol(user, 'medico')
        from citas.models import Cita as CitaModel, ConsultaMedica, Factura
        if cita.estado != CitaModel.ESTADO_EN_CONSULTA:
            raise ValueError(
                f"Solo se puede cerrar una cita en estado 'en_consulta'. "
                f"Estado actual: '{cita.get_estado_display()}'."
            )
        consulta = ConsultaMedica.objects.filter(id_cita=cita).first()
        if not consulta:
            raise ValueError("No existe consulta médica asociada a esta cita.")
        if consulta.estado == ConsultaMedica.ESTADO_CERRADA:
            raise ValueError("Esta consulta ya está cerrada.")
        now = timezone.now()
        consulta.estado = ConsultaMedica.ESTADO_CERRADA
        consulta.fecha_cierre = now
        consulta.save(update_fields=['estado', 'fecha_cierre'])
        CitaService.transicionar(cita, CitaModel.ESTADO_ATENDIDA,
                                 campos_extra={'fecha_atencion': now})
        if not hasattr(cita, 'factura') or not cita.factura:
            FacturacionService.generar_factura_cita(cita)
        return consulta


class FacturacionService:

    @staticmethod
    @transaction.atomic
    def generar_factura_cita(cita, precio_fijo=None):
        """
        Genera factura para una cita atendida.
        - Si existe pago previo, lo asocia y calcula estado según saldo.
        - Si no existe pago, usa precio_fijo (o monto del servicio) y deja factura pendiente.
        """
        from citas.models import Factura

        pago = getattr(cita, 'id_pago_cita', None)
        if pago and pago.status:
            subtotal = Decimal(str(pago.monto_pagar or 0))
        else:
            subtotal = Decimal(str(precio_fijo or 0))
            if not subtotal and cita.id_servicio_especialidad:
                try:
                    subtotal = Decimal(str(getattr(cita.id_servicio_especialidad, 'precio', 0) or 0))
                except (AttributeError, TypeError):
                    subtotal = Decimal("0.00")

        impuesto = Decimal("0.00")
        total = subtotal + impuesto

        numero = f"FAC-{timezone.now().strftime('%Y%m%d')}-{cita.pk}"

        estado_factura = Factura.ESTADO_EMITIDA
        if pago and pago.status and pago.monto_pagar is not None and pago.monto_pagar >= total:
            estado_factura = Factura.ESTADO_PAGADA
        elif pago and pago.status and pago.monto_pagar is not None and pago.monto_pagar < total:
            estado_factura = Factura.ESTADO_EMITIDA
        elif not pago or not pago.status:
            estado_factura = Factura.ESTADO_EMITIDA

        factura, created = Factura.objects.get_or_create(
            id_cita=cita,
            defaults={
                "numero": numero,
                "id_pago_cita": pago,
                "descripcion": (
                    str(cita.id_servicio_especialidad)
                    if cita.id_servicio_especialidad else "Consulta médica"
                ),
                "subtotal": subtotal,
                "impuesto": impuesto,
                "total": total,
                "estado": estado_factura,
            }
        )

        if not created and pago and not factura.id_pago_cita:
            factura.id_pago_cita = pago
            factura.estado = estado_factura
            factura.save(update_fields=['id_pago_cita', 'estado'])

        if pago and not pago.id_factura:
            pago.id_factura = factura
            pago.save(update_fields=['id_factura'])

        return factura
