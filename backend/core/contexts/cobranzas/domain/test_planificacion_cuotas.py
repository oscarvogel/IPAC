import unittest
from datetime import date

from .planificacion_cuotas import (
    CANTIDAD_MAXIMA,
    DIA_VENCIMIENTO_MAXIMO,
    ErrorPlanificacionCuotas,
    PeriodoCuota,
    PlanificacionCuotas,
    exigir_vencimientos,
    planificar_periodo_unico,
    planificar_secuencia,
)


class PlanificarSecuenciaTests(unittest.TestCase):
    def test_genera_meses_consecutivos_del_mismo_anio(self):
        plan = planificar_secuencia(
            cantidad=4, mes_inicial=3, anio_inicial=2026, dia_vencimiento=10
        )

        self.assertEqual(plan.nombres, ["2026-03", "2026-04", "2026-05", "2026-06"])
        self.assertEqual(plan.cantidad, 4)
        self.assertEqual(plan.primero.periodo, "2026-03")
        self.assertEqual(plan.ultimo.periodo, "2026-06")

    def test_aplica_el_dia_de_vencimiento_a_cada_mes(self):
        plan = planificar_secuencia(
            cantidad=3, mes_inicial=1, anio_inicial=2026, dia_vencimiento=10
        )

        self.assertEqual(
            [p.fecha_vencimiento for p in plan.periodos],
            [date(2026, 1, 10), date(2026, 2, 10), date(2026, 3, 10)],
        )

    def test_atraviesa_el_cambio_de_anio(self):
        plan = planificar_secuencia(
            cantidad=3, mes_inicial=11, anio_inicial=2026, dia_vencimiento=10
        )

        self.assertEqual(plan.nombres, ["2026-11", "2026-12", "2027-01"])
        self.assertEqual(plan.ultimo.fecha_vencimiento, date(2027, 1, 10))

    def test_un_solo_periodo_tambien_es_un_lote_valido(self):
        plan = planificar_secuencia(
            cantidad=1, mes_inicial=8, anio_inicial=2026, dia_vencimiento=10
        )

        self.assertEqual(plan.nombres, ["2026-08"])
        self.assertEqual(plan.total_para(30), 30)

    def test_total_para_cuenta_filas_por_alumno(self):
        plan = planification_de_prueba()

        self.assertEqual(plan.total_para(0), 0)
        self.assertEqual(plan.total_para(12), plan.cantidad * 12)

    def test_etiquetas_muestran_mes_legible_y_dia_de_vencimiento(self):
        plan = planificar_periodo_unico(
            periodo="2026-08", fecha_vencimiento=date(2026, 8, 10)
        )

        self.assertEqual(plan.etiquetas, ["agosto 2026 (vence el 10)"])

    def test_rechaza_cantidades_fuera_de_rango(self):
        for cantidad in (0, -3, CANTIDAD_MAXIMA + 1):
            with self.subTest(cantidad=cantidad):
                with self.assertRaises(ErrorPlanificacionCuotas):
                    planificar_secuencia(
                        cantidad=cantidad,
                        mes_inicial=3,
                        anio_inicial=2026,
                        dia_vencimiento=10,
                    )

    def test_rechaza_meses_y_anios_fuera_de_rango(self):
        for mes in (0, 13, "marzo"):
            with self.subTest(mes=mes):
                with self.assertRaises(ErrorPlanificacionCuotas):
                    planificar_secuencia(
                        cantidad=2, mes_inicial=mes, anio_inicial=2026, dia_vencimiento=10
                    )
        with self.assertRaises(ErrorPlanificacionCuotas):
            planificar_secuencia(
                cantidad=2, mes_inicial=3, anio_inicial=1990, dia_vencimiento=10
            )

    def test_rechaza_dias_que_invalidan_febrero_en_vez_de_ajustarlos(self):
        """El día 30 no puede aceptarse: en febrero esa fecha no existe.

        Ajustarlo en silencio al 28 haría que el vencimiento no sea el que el
        operador eligió, y no lo vería nadie hasta un reclamo.
        """
        for dia in (DIA_VENCIMIENTO_MAXIMO + 1, 30, 31):
            with self.subTest(dia=dia):
                with self.assertRaises(ErrorPlanificacionCuotas):
                    planificar_secuencia(
                        cantidad=2, mes_inicial=1, anio_inicial=2026, dia_vencimiento=dia
                    )

    def test_el_dia_28_si_es_valido_para_febrero(self):
        plan = planificar_secuencia(
            cantidad=2, mes_inicial=2, anio_inicial=2026, dia_vencimiento=28
        )

        self.assertEqual(plan.nombres, ["2026-02", "2026-03"])
        self.assertEqual(plan.primero.fecha_vencimiento, date(2026, 2, 28))


class PlanificarPeriodoUnicoTests(unittest.TestCase):
    def test_acepta_una_fecha_iso_en_texto(self):
        plan = planificar_periodo_unico(
            periodo="2026-08", fecha_vencimiento="2026-08-10"
        )

        self.assertEqual(plan.primero.fecha_vencimiento, date(2026, 8, 10))

    def test_rechaza_periodos_con_formato_incorrecto(self):
        for periodo in ("08/2026", "2026", "2026-13", "2026-8", "aaaa-mm", None, ""):
            with self.subTest(periodo=periodo):
                with self.assertRaises(ErrorPlanificacionCuotas):
                    planificar_periodo_unico(
                        periodo=periodo, fecha_vencimiento=date(2026, 8, 10)
                    )

    def test_rechaza_fechas_que_no_se_pueden_parsear(self):
        with self.assertRaises(ErrorPlanificacionCuotas):
            planificar_periodo_unico(periodo="2026-08", fecha_vencimiento="10/08/2026")
        with self.assertRaises(ErrorPlanificacionCuotas):
            planificar_periodo_unico(periodo="2026-08", fecha_vencimiento=12345)

    def test_acepta_un_periodo_sin_fecha_para_poder_previsualizar(self):
        """La vista previa necesita los períodos, no las fechas de vencimiento."""
        plan = planificar_periodo_unico(periodo="2026-08", fecha_vencimiento=None)

        self.assertEqual(plan.nombres, ["2026-08"])
        self.assertIsNone(plan.primero.fecha_vencimiento)
        self.assertEqual(plan.etiquetas, ["agosto 2026"])

    def test_una_cadena_vacia_tambien_significa_sin_fecha(self):
        plan = planificar_periodo_unico(periodo="2026-08", fecha_vencimiento="  ")

        self.assertIsNone(plan.primero.fecha_vencimiento)

    def test_exigir_vencimientos_rechaza_el_lote_que_va_a_escribirse(self):
        plan = planificar_periodo_unico(periodo="2026-08", fecha_vencimiento=None)

        with self.assertRaises(ErrorPlanificacionCuotas):
            exigir_vencimientos(plan)

    def test_exigir_vencimientos_acepta_un_lote_completo(self):
        plan = planificar_secuencia(
            cantidad=2, mes_inicial=3, anio_inicial=2026, dia_vencimiento=10
        )

        self.assertIs(exigir_vencimientos(plan), plan)


class PlanificacionCuotasTests(unittest.TestCase):
    def test_rechaza_lotes_vacios(self):
        with self.assertRaises(ErrorPlanificacionCuotas):
            PlanificacionCuotas(periodos=())

    def test_rechaza_periodos_repetidos(self):
        repetido = PeriodoCuota(periodo="2026-08", fecha_vencimiento=date(2026, 8, 10))
        otro = PeriodoCuota(periodo="2026-08", fecha_vencimiento=date(2026, 8, 20))

        with self.assertRaises(ErrorPlanificacionCuotas):
            PlanificacionCuotas(periodos=(repetido, otro))


def planification_de_prueba():
    return planificar_secuencia(
        cantidad=6, mes_inicial=3, anio_inicial=2026, dia_vencimiento=10
    )
