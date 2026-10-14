"""Crea cuotas vencidas de prueba para revisar el interés de mora.

El seed inicial arma conceptos y pagos pero no cuotas, así que sin esto la
proyección de intereses arranca siempre vacía y no hay forma de ver la pantalla
con algo dentro.

Es un comando de **datos de prueba**, no de producción: crea alumnos y cuotas
con nombres ficticios y es idempotente, así que se puede correr varias veces.
"""

from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import Alumno, CarreraCurso, ConceptoCobrable, Cuota, Sucursal


class Command(BaseCommand):
    help = "Carga cuotas vencidas de prueba para revisar el cálculo de interés."

    def add_arguments(self, parser):
        parser.add_argument(
            "--periodo",
            default="2026-03",
            help="Período de las cuotas (AAAA-MM). Por defecto 2026-03.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        periodo = options["periodo"]
        anio, mes = int(periodo[:4]), int(periodo[5:7])

        posadas, _ = Sucursal.objects.get_or_create(codigo="POS", defaults={"nombre": "Posadas"})
        eldorado, _ = Sucursal.objects.get_or_create(codigo="ELD", defaults={"nombre": "Eldorado"})

        created = 0
        created += self._cuotas(
            sucursal=posadas,
            legajos=["PRUEBA-001", "PRUEBA-002"],
            nombre="Alumno",
            apellido="De Prueba",
            periodo=periodo,
            anio=anio,
            mes=mes,
            importe=Decimal("10000.00"),
        )
        # Una sucursal sin tasa cargada, para ver el aviso de "cuotas sin tasa"
        # en la pantalla en lugar de un total que engaña.
        created += self._cuotas(
            sucursal=eldorado,
            legajos=["PRUEBA-ELD-001"],
            nombre="Alumno",
            apellido="De Prueba Eldorado",
            periodo=periodo,
            anio=anio,
            mes=mes,
            importe=Decimal("8000.00"),
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"{created} cuotas de prueba en período {periodo}. "
                "Cargá una tasa y usá 'Proyectar interés'."
            )
        )

    def _cuotas(self, *, sucursal, legajos, nombre, apellido, periodo, anio, mes, importe):
        concepto, _ = ConceptoCobrable.objects.get_or_create(
            nombre="Cuota mensual",
            sucursal=sucursal,
            carrera=None,
            defaults={"tipo": ConceptoCobrable.Tipo.CUOTA, "importe": importe},
        )
        carrera, _ = CarreraCurso.objects.get_or_create(
            nombre="Carrera de prueba",
            sucursal=sucursal,
            defaults={"tipo": CarreraCurso.Tipo.CARRERA, "plan_cuotas": 10, "cuota_total": importe},
        )
        vencimiento = date(anio, mes, 10)
        creados = 0
        for legajo in legajos:
            alumno, _ = Alumno.objects.get_or_create(
                legajo=legajo,
                defaults={
                    "nombre": nombre,
                    "apellido": apellido,
                    "sucursal": sucursal,
                    "carrera": carrera,
                },
            )
            _, se_creo = Cuota.objects.get_or_create(
                alumno=alumno,
                concepto=concepto,
                periodo=periodo,
                defaults={
                    "sucursal": sucursal,
                    "fecha_emision": date(anio, mes, 1),
                    "fecha_vencimiento": vencimiento,
                    "importe": importe,
                },
            )
            creados += int(se_creo)
        return creados