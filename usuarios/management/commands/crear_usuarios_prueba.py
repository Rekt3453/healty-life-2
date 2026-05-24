import hashlib
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Crea usuarios de prueba para los 6 tipos de login'

    def handle(self, *args, **options):
        from usuarios.models import (
            UserRoot, Root, UserSuperAdmin, Superadmin, CentroMedico,
            Sede, DireccionSede,
            UserPaciente, PacienteDatosPersonales,
            UserDoctor, Doctor,
            UserRecepcionista, Recepcionista,
            UserAdmin, Administrador,
        )

        def md5(pw):
            return hashlib.md5(pw.encode()).hexdigest()

        def upsert_user(Model, pk_field, username_field, username, correo, password_field, password):
            obj = Model.objects.filter(**{username_field: username}).first()
            if obj:
                setattr(obj, password_field, md5(password))
                obj.save()
                self.stdout.write(self.style.WARNING(f'  {Model.__name__} "{username}" ya existia -> contrasena actualizada'))
            else:
                kwargs = {
                    username_field: username,
                    password_field: md5(password),
                    'status': True,
                }
                if 'correo' in [f.name for f in Model._meta.get_fields()]:
                    kwargs['correo'] = correo
                if 'email' in [f.name for f in Model._meta.get_fields()]:
                    kwargs['email'] = correo
                obj = Model.objects.create(**kwargs)
                self.stdout.write(self.style.SUCCESS(f'  {Model.__name__} "{username}" creado'))
            return obj

        # ── ROOT ──────────────────────────────────────────────────────────────
        ROOT_USER = 'root_test'
        ROOT_PASS = 'root1234'

        root_user, created = UserRoot.objects.get_or_create(
            username=ROOT_USER,
            defaults={'correo': 'root@healthylife.com', 'contrasena': md5(ROOT_PASS)},
        )
        if not created:
            root_user.contrasena = md5(ROOT_PASS)
            root_user.save()
            self.stdout.write(self.style.WARNING(f'  UserRoot "{ROOT_USER}" ya existia -> contrasena actualizada'))
        else:
            self.stdout.write(self.style.SUCCESS(f'  UserRoot "{ROOT_USER}" creado'))

        if not Root.objects.filter(id_user_root=root_user).exists():
            Root.objects.create(nombre='Root', apellido='Test', id_user_root=root_user, status=True)
            self.stdout.write(self.style.SUCCESS('  Registro Root creado'))

        # ── CENTRO MEDICO ─────────────────────────────────────────────────────
        cm = CentroMedico.objects.filter(status=True).first()
        if not cm:
            cm = CentroMedico.objects.create(nombre_cm='Centro Medico de Prueba', rif_cm='J-00000000-0', status=True)
            self.stdout.write(self.style.SUCCESS(f'  CentroMedico "{cm.nombre_cm}" creado'))
        else:
            self.stdout.write(self.style.WARNING(f'  Usando CentroMedico: "{cm.nombre_cm}"'))

        # ── SUPERADMIN ────────────────────────────────────────────────────────
        SA_USER = 'superadmin_test'
        SA_PASS = 'super1234'

        sa_user, created = UserSuperAdmin.objects.get_or_create(
            username=SA_USER,
            defaults={'correo': 'superadmin@healthylife.com', 'contrasena': md5(SA_PASS), 'status': True},
        )
        if not created:
            sa_user.contrasena = md5(SA_PASS)
            sa_user.save()
            self.stdout.write(self.style.WARNING(f'  UserSuperAdmin "{SA_USER}" ya existia -> contrasena actualizada'))
        else:
            self.stdout.write(self.style.SUCCESS(f'  UserSuperAdmin "{SA_USER}" creado'))

        if not Superadmin.objects.filter(id_user_superadmin=sa_user).exists():
            Superadmin.objects.create(id_user_superadmin=sa_user, nombre_1='Super', apellido_1='Admin', status=True)
            self.stdout.write(self.style.SUCCESS('  Registro Superadmin creado'))

        # ── SEDE DE PRUEBA ────────────────────────────────────────────────────
        sede = Sede.objects.filter(status=True).first()
        if not sede:
            dir_sede = DireccionSede.objects.create(direccion='Direccion de prueba')
            sede = Sede.objects.create(
                nombre_sede='Sede de Prueba',
                id_direccion=dir_sede,
                id_cm=cm,
                status=True,
            )
            self.stdout.write(self.style.SUCCESS(f'  Sede "{sede.nombre_sede}" creada'))
        else:
            self.stdout.write(self.style.WARNING(f'  Usando Sede: "{sede.nombre_sede}"'))

        # ── PACIENTE ──────────────────────────────────────────────────────────
        PAC_USER = 'paciente_test'
        PAC_PASS = 'pac1234'

        pac_user = UserPaciente.objects.filter(username=PAC_USER).first()
        if pac_user:
            pac_user.password = md5(PAC_PASS)
            pac_user.save()
            self.stdout.write(self.style.WARNING(f'  UserPaciente "{PAC_USER}" ya existia -> contrasena actualizada'))
        else:
            pac_user = UserPaciente.objects.create(
                username=PAC_USER, email='paciente@healthylife.com',
                password=md5(PAC_PASS), id_sede=sede, status=True,
            )
            self.stdout.write(self.style.SUCCESS(f'  UserPaciente "{PAC_USER}" creado'))

        if not PacienteDatosPersonales.objects.filter(id_user_paciente=pac_user).exists():
            PacienteDatosPersonales.objects.create(
                id_user_paciente=pac_user, nombre_1='Paciente', apellido_1='Test',
                cedula='V-11111111', id_sede=sede, status=True,
            )
            self.stdout.write(self.style.SUCCESS('  Datos personales paciente creados'))

        # ── MEDICO ────────────────────────────────────────────────────────────
        MED_USER = 'medico_test'
        MED_PASS = 'med1234'

        med_user = UserDoctor.objects.filter(username=MED_USER).first()
        if med_user:
            med_user.password = md5(MED_PASS)
            med_user.save()
            self.stdout.write(self.style.WARNING(f'  UserDoctor "{MED_USER}" ya existia -> contrasena actualizada'))
        else:
            med_user = UserDoctor.objects.create(
                username=MED_USER, email='medico@healthylife.com',
                password=md5(MED_PASS), id_sede=sede, status=True,
            )
            self.stdout.write(self.style.SUCCESS(f'  UserDoctor "{MED_USER}" creado'))

        if not Doctor.objects.filter(id_user_doctor=med_user).exists():
            Doctor.objects.create(
                id_user_doctor=med_user, nombre_1='Medico', apellido_1='Test',
                cedula='V-22222222', id_sede=sede, status=True,
            )
            self.stdout.write(self.style.SUCCESS('  Datos doctor creados'))

        # ── RECEPCIONISTA ─────────────────────────────────────────────────────
        REC_USER = 'recepcionista_test'
        REC_PASS = 'rec1234'

        rec_user = UserRecepcionista.objects.filter(username=REC_USER).first()
        if rec_user:
            rec_user.password = md5(REC_PASS)
            rec_user.save()
            self.stdout.write(self.style.WARNING(f'  UserRecepcionista "{REC_USER}" ya existia -> contrasena actualizada'))
        else:
            rec_user = UserRecepcionista.objects.create(
                username=REC_USER, email='recepcionista@healthylife.com',
                password=md5(REC_PASS), id_sede=sede, status=True,
            )
            self.stdout.write(self.style.SUCCESS(f'  UserRecepcionista "{REC_USER}" creado'))

        if not Recepcionista.objects.filter(id_user_recepcionista=rec_user).exists():
            Recepcionista.objects.create(
                id_user_recepcionista=rec_user, nombre_1='Recepcionista', apellido_1='Test',
                cedula='V-33333333', id_sede=sede, status=True,
            )
            self.stdout.write(self.style.SUCCESS('  Datos recepcionista creados'))

        # ── GERENTE ───────────────────────────────────────────────────────────
        GER_USER = 'gerente_test'
        GER_PASS = 'ger1234'

        ger_user = UserAdmin.objects.filter(username=GER_USER).first()
        if ger_user:
            ger_user.password = md5(GER_PASS)
            ger_user.save()
            self.stdout.write(self.style.WARNING(f'  UserAdmin "{GER_USER}" ya existia -> contrasena actualizada'))
        else:
            ger_user = UserAdmin.objects.create(
                username=GER_USER, email='gerente@healthylife.com',
                password=md5(GER_PASS), id_sede=sede, status=True,
            )
            self.stdout.write(self.style.SUCCESS(f'  UserAdmin "{GER_USER}" creado'))

        if not Administrador.objects.filter(id_user_admin=ger_user).exists():
            Administrador.objects.create(
                id_user_admin=ger_user, nombre_1='Gerente', apellido_1='Test',
                cedula='V-44444444', id_sede=sede, status=True,
            )
            self.stdout.write(self.style.SUCCESS('  Datos gerente creados'))

        # ── RESUMEN ───────────────────────────────────────────────────────────
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('========================================='))
        self.stdout.write(self.style.SUCCESS('  Usuarios de prueba listos'))
        self.stdout.write(self.style.SUCCESS('========================================='))
        rows = [
            ('ROOT',          '/login/root/',          ROOT_USER, ROOT_PASS),
            ('SUPERADMIN',    '/login/super-admin/',   SA_USER,   SA_PASS),
            ('PACIENTE',      '/login/paciente/',      PAC_USER,  PAC_PASS),
            ('MEDICO',        '/login/medico/',        MED_USER,  MED_PASS),
            ('RECEPCIONISTA', '/login/recepcionista/', REC_USER,  REC_PASS),
            ('GERENTE',       '/login/gerente/',       GER_USER,  GER_PASS),
        ]
        for rol, url, user, pwd in rows:
            self.stdout.write(f'  {rol:<14} {url}')
            self.stdout.write(f'    usuario   : {user}')
            self.stdout.write(f'    contrasena: {pwd}')
            self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('========================================='))
