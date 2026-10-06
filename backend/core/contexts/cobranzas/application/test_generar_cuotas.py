import unittest
from datetime import date
from decimal import Decimal

from .generar_cuotas import (
    GeneracionCuotasError,
    GenerarCuotas,
    ResultadoGeneracionCuotas,
)


class GeneratorFake:
    def __init__(self, resultado=None):
        self.actor = None
        self.solicitud = None
        self._resultado = resultado or ResultadoGeneracionCuotas(creadas=["cuota"])

    def generar(self, *, actor, solicitud):
        self.actor = actor
        self.solicitud = solicitud
        return self._resultado


class GenerarCuotasTests(unittest.TestCase):
    def test_normaliza_solicitud_y_delega_al_puerto(self):
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

        self.assertIs(result, generator._resultado)
        self.assertIs(generator.actor, actor)
        self.assertEqual(generator.solicitud.alumno_ids, (4, 5))
        self.assertEqual(generator.solicitud.fecha_emision, date(2026, 10, 1))
        self.assertEqual(generator.solicitud.importe, Decimal("1200.00"))
        self.assertEqual(generator.solicitud.tipo_descuento_id, 3)

    def test_un_periodo_unico_se_convierte_en_un_lote_de_uno(self):
        generator = GeneratorFake()
        GenerarCuotas(generator).execute(actor=None, payload={
            "alumnos": [4],
            "concepto": 8,
            "periodo": "2026-10",
            "fecha_emision": "2026-10-01",
            "fecha_vencimiento": "2026-10-15",
        })

        plan = generator.solicitud.planificacion
        self.assertEqual(plan.cantidad, 1)
        self.assertEqual(plan.primero.periodo, "2026-10")
        self.assertEqual(plan.primero.fecha_vencimiento, date(2026, 10, 15))

    def test_cantidad_mes_anio_dia_arman_un_lote_de_meses_consecutivos(self):
        generator = GeneratorFake()
        GenerarCuotas(generator).execute(actor=None, payload={
            "alumnos": [4, 5],
            "concepto": 8,
            "fecha_emision": "2026-03-01",
            "cantidad": "4",
            "mes_inicial": "3",
            "anio_inicial": "2026",
            "dia_vencimiento": "10",
        })

        plan = generator.solicitud.planificacion
        self.assertEqual(plan.nombres, ["2026-03", "2026-04", "2026-05", "2026-06"])
        self.assertEqual(
            [p.fecha_vencimiento for p in plan.periodos],
            [
                date(2026, 3, 10),
                date(2026, 4, 10),
                date(2026, 5, 10),
                date(2026, 6, 10),
            ],
        )

    def test_el_lote_acepta_mes_y_anio_como_alias(self):
        generator = GeneratorFake()
        GenerarCuotas(generator).execute(actor=None, payload={
            "alumnos": [4],
            "concepto": 8,
            "fecha_emision": "2026-03-01",
            "cantidad": 2,
            "mes": 8,
            "anio": 2026,
        })

        self.assertEqual(
            generator.solicitud.planificacion.nombres, ["2026-08", "2026-09"]
        )

    def test_el_dia_de_vencimiento_por_defecto_es_el_10(self):
        """El 10 es el día que IPAC declaró en la reunión del 24/09/2026."""
        generator = GeneratorFake()
        GenerarCuotas(generator).execute(actor=None, payload={
            "alumnos": [4],
            "concepto": 8,
            "fecha_emision": "2026-03-01",
            "cantidad": 1,
            "mes_inicial": 3,
            "anio_inicial": 2026,
        })

        self.assertEqual(
            generator.solicitud.planificacion.primero.fecha_vencimiento, date(2026, 3, 10)
        )

    def test_cantidad_gana_cuando_viene_con_un_periodo_suelto(self):
        """Si el formulario manda los dos, manda el lote: es el camino nuevo."""
        generator = GeneratorFake()
        GenerarCuotas(generator).execute(actor=None, payload={
            "alumnos": [4],
            "concepto": 8,
            "fecha_emision": "2026-03-01",
            "periodo": "2026-08",
            "fecha_vencimiento": "2026-08-10",
            "cantidad": 2,
            "mes_inicial": 3,
            "anio_inicial": 2026,
        })

        self.assertEqual(
            generator.solicitud.planificacion.nombres, ["2026-03", "2026-04"]
        )

    def test_rechaza_solicitudes_incompletas_o_importes_invalidos_sin_invocar_puerto(self):
        class GeneratorEstricto(GeneratorFake):
            def generar(self, **kwargs):
                raise AssertionError("No debe invocarse con datos inválidos")

        use_case = GenerarCuotas(GeneratorEstricto())
        with self.assertRaises(GeneracionCuotasError):
            use_case.execute(actor=None, payload={"alumnos": []})
        with self.assertRaises(GeneracionCuotasError):
            use_case.execute(actor=None, payload={
                "alumnos": [1], "concepto": 2, "periodo": "2026-10",
                "fecha_emision": "2026-10-01", "fecha_vencimiento": "2026-10-10",
                "importe": "NaN",
            })

    def test_rechaza_un_lote_invalido_traduciendo_el_error_de_dominio(self):
        generator = GeneratorFake()
        use_case = GenerarCuotas(generator)

        with self.assertRaises(GeneracionCuotasError) as caso:
            use_case.execute(actor=None, payload={
                "alumnos": [1], "concepto": 2, "fecha_emision": "2026-10-01",
                "cantidad": 0, "mes_inicial": 3, "anio_inicial": 2026,
            })
        self.assertIn("cantidad", caso.exception.detail.lower())

        # Un lote de 100 es un error de tipeo, no una solicitud válida.
        with self.assertRaises(GeneracionCuotasError):
            use_case.execute(actor=None, payload={
                "alumnos": [1], "concepto": 2, "fecha_emision": "2026-10-01",
                "cantidad": 100, "mes_inicial": 3, "anio_inicial": 2026,
            })

    def test_sin_periodo_ni_cantidad_no_hay_lote_que_generar(self):
        generator = GeneratorFake()
        with self.assertRaises(GeneracionCuotasError):
            GenerarCuotas(generator).execute(actor=None, payload={
                "alumnos": [1], "concepto": 2, "fecha_emision": "2026-10-01",
            })

    def test_generar_exige_vencimiento_pero_la_previsualizacion_no(self):
        """Sin fecha no se puede escribir, pero sí se puede previsualizar."""
        generator = GeneratorFake()

        with self.assertRaises(GeneracionCuotasError) as caso:
            GenerarCuotas(generator).execute(actor=None, payload={
                "alumnos": [4], "concepto": 8, "fecha_emision": "2026-10-01",
                "periodo": "2026-10",
            })
        self.assertIn("vencimiento", caso.exception.detail.lower())
        self.assertIsNone(generator.solicitud)


class ResultadoGeneracionCuotasTests(unittest.TestCase):
    def test_cuenta_creadas_y_omitidas(self):
        resultado = ResultadoGeneracionCuotas(
            creadas=[1, 2, 3],
            omitidas=[{"alumno_id": 4, "periodo": "2026-03"}],
        )

        self.assertEqual(resultado.total_creadas, 3)
        self.assertEqual(resultado.total_omitidas, 1)

    def test_una_generacion_sin_omitidas_arranca_en_ceros(self):
        resultado = ResultadoGeneracionCuotas()

        self.assertEqual(resultado.total_creadas, 0)
        self.assertEqual(resultado.total_omitidas, 0)
