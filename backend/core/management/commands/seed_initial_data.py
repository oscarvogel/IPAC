import os

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError

from core.models import Alumno, CarreraCurso, ConceptoCobrable, Pago, PerfilUsuario, Sucursal


class Command(BaseCommand):
    help = "Carga los datos minimos iniciales para IPAC."

    def handle(self, *args, **options):
        sucursales = {}
        for codigo, nombre in (("POS", "Posadas"), ("ELD", "Eldorado")):
            sucursal, _ = Sucursal.objects.update_or_create(
                codigo=codigo,
                defaults={"nombre": nombre, "activa": True},
            )
            sucursales[codigo] = sucursal

        administracion, _ = CarreraCurso.objects.update_or_create(
            nombre="Administracion contable",
            sucursal=sucursales["POS"],
            defaults={"descripcion": "Trayecto administrativo inicial.", "activa": True},
        )
        auxiliar, _ = CarreraCurso.objects.update_or_create(
            nombre="Auxiliar administrativo",
            sucursal=sucursales["ELD"],
            defaults={"descripcion": "Curso orientado a gestion de oficina.", "activa": True},
        )

        matricula, _ = ConceptoCobrable.objects.update_or_create(
            nombre="Matricula 2026",
            sucursal=sucursales["POS"],
            carrera=administracion,
            defaults={"tipo": ConceptoCobrable.Tipo.MATRICULA, "importe": 50000, "activo": True},
        )
        cuota_posadas, _ = ConceptoCobrable.objects.update_or_create(
            nombre="Cuota mensual",
            sucursal=sucursales["POS"],
            carrera=administracion,
            defaults={"tipo": ConceptoCobrable.Tipo.CUOTA, "importe": 25000, "activo": True},
        )
        cuota_eldorado, _ = ConceptoCobrable.objects.update_or_create(
            nombre="Cuota mensual",
            sucursal=sucursales["ELD"],
            carrera=auxiliar,
            defaults={"tipo": ConceptoCobrable.Tipo.CUOTA, "importe": 22000, "activo": True},
        )

        demo_students = [
            {
                "legajo": "POS-001",
                "nombre": "Ana",
                "apellido": "Gomez",
                "dni": "30111222",
                "email": "ana.gomez@ipac.local",
                "telefono": "3764000001",
                "sucursal": sucursales["POS"],
                "carrera": administracion,
            },
            {
                "legajo": "POS-002",
                "nombre": "Marta",
                "apellido": "Rios",
                "dni": "32111222",
                "email": "marta.rios@ipac.local",
                "telefono": "3764000002",
                "sucursal": sucursales["POS"],
                "carrera": administracion,
            },
            {
                "legajo": "ELD-001",
                "nombre": "Pedro",
                "apellido": "Silva",
                "dni": "33111222",
                "email": "pedro.silva@ipac.local",
                "telefono": "3751000001",
                "sucursal": sucursales["ELD"],
                "carrera": auxiliar,
            },
        ]
        for student in demo_students:
            Alumno.objects.update_or_create(
                legajo=student["legajo"],
                defaults={**student, "estado": Alumno.Estado.ACTIVO},
            )

        ana = Alumno.objects.get(legajo="POS-001")
        pedro = Alumno.objects.get(legajo="ELD-001")
        Pago.objects.get_or_create(
            alumno=ana,
            concepto=matricula,
            sucursal=sucursales["POS"],
            importe=50000,
            medio=Pago.Medio.EFECTIVO,
            defaults={"observacion": "Pago demo de matricula"},
        )
        Pago.objects.get_or_create(
            alumno=pedro,
            concepto=cuota_eldorado,
            sucursal=sucursales["ELD"],
            importe=22000,
            medio=Pago.Medio.TRANSFERENCIA,
            defaults={"observacion": "Pago demo por transferencia"},
        )

        production = os.getenv("IPAC_ENVIRONMENT", "development").lower() == "production"
        username = os.getenv("IPAC_SEED_ADMIN_USERNAME", "" if production else "admin").strip()
        password = os.getenv("IPAC_SEED_ADMIN_PASSWORD", "" if production else "admin123")
        if not username or not password:
            raise CommandError(
                "En producción IPAC_SEED_ADMIN_USERNAME e IPAC_SEED_ADMIN_PASSWORD son obligatorios."
            )
        if production and (username == "admin" or password == "admin123"):
            raise CommandError("Las credenciales de demostración no están permitidas en producción.")
        admin, created = User.objects.get_or_create(
            username=username,
            defaults={
                "is_staff": True,
                "is_superuser": True,
                "email": "admin@ipac.local",
            },
        )
        if created:
            admin.set_password(password)
            admin.save(update_fields=["password"])
        elif not admin.is_staff or not admin.is_superuser:
            admin.is_staff = True
            admin.is_superuser = True
            admin.save(update_fields=["is_staff", "is_superuser"])

        PerfilUsuario.objects.update_or_create(
            user=admin,
            defaults={
                "rol": PerfilUsuario.Rol.ADMINISTRACION,
                "sucursal": sucursales["POS"],
                "puede_ver_todas_las_sucursales": True,
            },
        )

        self.stdout.write(self.style.SUCCESS("Datos iniciales cargados."))
