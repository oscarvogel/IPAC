import unittest
from datetime import date
from decimal import Decimal

from .generar_cuotas import GeneracionCuotasError, GenerarCuotas


class GenerarCuotasTests(unittest.TestCase):
    def test_normaliza_solicitud_y_delega_al_puerto(self):
        class GeneratorFake:
            def generar(self, *, actor, solicitud):
                self.actor = actor
                self.solicitud = solicitud
                return ["cuota"]

        generator = GeneratorFake()
        actor = object()
        result = GenerarCuotas(generator).execute(actor=actor, payload={
            "alumnos": ["4", 4, 5],
            "concepto": "8",
            "periodo": "2026-10",
            "fecha_emision": "2026-10-01",
            "fecha_vencimiento": "2026-10-10",
            "importe": "1200.00",
            "descuento": "100",
            "recargo": "0",
            "tipo_descuento": "3",
        })

        self.assertEqual(result, ["cuota"])
        self.assertIs(generator.actor, actor)
        self.assertEqual(generator.solicitud.alumno_ids, (4, 5))
        self.assertEqual(generator.solicitud.fecha_emision, date(2026, 10, 1))
        self.assertEqual(generator.solicitud.importe, Decimal("1200.00"))
        self.assertEqual(generator.solicitud.tipo_descuento_id, 3)

    def test_rechaza_solicitudes_incompletas_o_importes_invalidos_sin_invocar_puerto(self):
        class GeneratorFake:
            def generar(self, **kwargs):
                raise AssertionError("No debe invocarse con datos inválidos")

        use_case = GenerarCuotas(GeneratorFake())
        with self.assertRaises(GeneracionCuotasError):
            use_case.execute(actor=None, payload={"alumnos": []})
        with self.assertRaises(GeneracionCuotasError):
            use_case.execute(actor=None, payload={
                "alumnos": [1], "concepto": 2, "periodo": "2026-10",
                "fecha_emision": "2026-10-01", "fecha_vencimiento": "2026-10-10",
                "importe": "NaN",
            })
