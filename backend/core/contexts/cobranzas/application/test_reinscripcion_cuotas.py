import unittest
from datetime import date
from decimal import Decimal

from .generar_cuotas import GeneracionCuotasError, ResultadoGeneracionCuotas
from .reinscripcion_cuotas import (
    GenerarCuotasDeMatricula,
    MatriculaReinscribible,
    sugerir_plan,
)


class GeneratorFalso:
    def __init__(self):
        self.solicitud = None
        self.actor = None

    def generar(self, *, actor, solicitud):
        self.actor = actor
        self.solicitud = solicitud
        return ResultadoGeneracionCuotas(creadas=["cuota"])


def matricula(plan_cuotas=10, fecha_inicio=date(2026, 3, 1)):
    return MatriculaReinscribible(
        matricula_id=7,
        alumno_id=42,
        fecha_inicio=fecha_inicio,
        plan_cuotas=plan_cuotas,
    )


class SugerirPlanTests(unittest.TestCase):
    def test_delega_al_dominio_con_el_dia_por_defecto(self):
        plan = sugerir_plan(matricula=matricula())

        self.assertEqual(plan.cantidad, 10)
        self.assertEqual(plan.primero.fecha_vencimiento, date(2026, 3, 10))

    def test_devuelve_none_si_la_carrera_no_tiene_plan(self):
        self.assertIsNone(sugerir_plan(matricula=matricula(plan_cuotas=None)))

    def test_un_dia_cero_no_cae_al_dia_por_defecto(self):
        """Con `or`, el 0 se tomaba por "no informado" y vencia el 10.

        El operador escribio 0: eso es un dato invalido y tiene que rechazarlo
        el dominio, no caer al 10 en silencio.
        """
        from .generar_cuotas import GeneracionCuotasError

        with self.assertRaises(GeneracionCuotasError) as caso:
            GenerarCuotasDeMatricula(GeneratorFalso()).execute(
                actor=object(),
                matricula=matricula(),
                concepto_id=3,
                dia_vencimiento=0,
                fecha_emision=date(2026, 2, 20),
            )

        self.assertIn("1 y 28", str(caso.exception))

    def test_un_dia_29_tambien_se_rechaza(self):
        from .generar_cuotas import GeneracionCuotasError

        with self.assertRaises(GeneracionCuotasError):
            GenerarCuotasDeMatricula(GeneratorFalso()).execute(
                actor=object(),
                matricula=matricula(),
                concepto_id=3,
                dia_vencimiento=29,
                fecha_emision=date(2026, 2, 20),
            )


class GenerarCuotasDeMatriculaTests(unittest.TestCase):
    def test_genera_el_lote_del_plan_desde_el_mes_de_la_matricula(self):
        generator = GeneratorFalso()
        actor = object()

        resultado = GenerarCuotasDeMatricula(generator).execute(
            actor=actor,
            matricula=matricula(),
            concepto_id=3,
            fecha_emision=date(2026, 2, 20),
        )

        self.assertEqual(resultado.total_creadas, 1)
        self.assertIs(generator.actor, actor)
        self.assertEqual(generator.solicitud.alumno_ids, (42,))
        self.assertEqual(generator.solicitud.matricula_id, 7)
        self.assertEqual(generator.solicitud.concepto_id, 3)
        self.assertEqual(generator.solicitud.fecha_emision, date(2026, 2, 20))
        self.assertEqual(
            generator.solicitud.planificacion.nombres,
            [f"2026-{mes:02d}" for mes in range(3, 13)],
        )

    def test_la_cantidad_explicita_manda_sobre_el_plan(self):
        """Un alumno que entra a mitad de año no debe las 10 del plan."""
        generator = GeneratorFalso()

        GenerarCuotasDeMatricula(generator).execute(
            actor=None,
            matricula=matricula(),
            concepto_id=3,
            cantidad=4,
            fecha_emision=date(2026, 8, 1),
        )

        self.assertEqual(generator.solicitud.planificacion.nombres, [
            "2026-03", "2026-04", "2026-05", "2026-06",
        ])

    def test_el_importe_lo_resuelve_el_concepto_cuando_no_se_pasa(self):
        generator = GeneratorFalso()

        GenerarCuotasDeMatricula(generator).execute(
            actor=None,
            matricula=matricula(),
            concepto_id=3,
            fecha_emision=date(2026, 2, 20),
        )

        self.assertIsNone(generator.solicitud.importe)

    def test_propaga_el_importe_si_el_operador_lo_corrige(self):
        generator = GeneratorFalso()

        GenerarCuotasDeMatricula(generator).execute(
            actor=None,
            matricula=matricula(),
            concepto_id=3,
            fecha_emision=date(2026, 2, 20),
            importe=Decimal("50000.00"),
        )

        self.assertEqual(generator.solicitud.importe, Decimal("50000.00"))

    def test_sin_plan_ni_cantidad_explicita_no_adivina(self):
        generator = GeneratorFalso()

        with self.assertRaises(GeneracionCuotasError) as caso:
            GenerarCuotasDeMatricula(generator).execute(
                actor=None,
                matricula=matricula(plan_cuotas=None),
                concepto_id=3,
                fecha_emision=date(2026, 2, 20),
            )

        self.assertIn("plan", caso.exception.detail.lower())
        self.assertIsNone(generator.solicitud)

    def test_la_cantidad_invalida_no_llega_al_puerto(self):
        generator = GeneratorFalso()

        with self.assertRaises(GeneracionCuotasError):
            GenerarCuotasDeMatricula(generator).execute(
                actor=None,
                matricula=matricula(),
                concepto_id=3,
                cantidad=0,
                fecha_emision=date(2026, 2, 20),
            )

        self.assertIsNone(generator.solicitud)

    def test_el_alumno_no_se_puede_cambiar_por_el_llamador(self):
        """La invariante de que es un solo alumno no depende del payload."""
        generator = GeneratorFalso()

        GenerarCuotasDeMatricula(generator).execute(
            actor=None,
            matricula=matricula(),
            concepto_id=3,
            fecha_emision=date(2026, 2, 20),
        )

        self.assertEqual(generator.solicitud.alumno_ids, (42,))
        self.assertEqual(generator.solicitud.matricula_id, 7)
