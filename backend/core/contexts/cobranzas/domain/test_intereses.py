import ast
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

from . import intereses
from .intereses import (
    BASE_DESDE_DIA_1,
    BASE_DESDE_VENCIMIENTO,
    BASE_MSG,
    TASA_NEGATIVA_MSG,
    TASA_VIGENTE_MSG,
    UNIDAD_DIAS,
    UNIDAD_MESES,
    UNIDAD_MSG,
    VIGENCIA_INVERTIDA_MSG,
    ErrorInteres,
    PoliticaInteres,
    TasaInteres,
    calcular_interes,
    dias_interesables,
    evaluar_interes_cuota,
    fecha_base_interes,
    fecha_inicio_interes,
    periodos_interesables,
    seleccionar_tasa,
)

#: Cuota de marzo de 2026. Es el caso que usó IPAC para describir la regla:
#: vence el día 10 pero el interés se cuenta desde el día 1.
PERIODO = "2026-03"
VENCIMIENTO = date(2026, 3, 10)


def tasa(pct="5.5", desde=date(2026, 1, 1), hasta=None):
    return TasaInteres(
        porcentaje_mensual=Decimal(pct), vigencia_desde=desde, vigencia_hasta=hasta
    )


class BaseDeCalculoTests(unittest.TestCase):
    def test_la_base_por_defecto_es_el_dia_1_del_mes_del_periodo(self):
        base = fecha_base_interes(periodo=PERIODO, fecha_vencimiento=VENCIMIENTO)

        self.assertEqual(base, date(2026, 3, 1))

    def test_la_base_no_es_la_fecha_de_vencimiento(self):
        """Es la diferencia exacta que describió IPAC: vencía el 10 y cuenta
        desde el 1. Si alguna vez se rompe, el interés se corre nueve días."""
        base = fecha_base_interes(periodo=PERIODO, fecha_vencimiento=VENCIMIENTO)

        self.assertNotEqual(base, VENCIMIENTO)

    def test_la_base_alternativa_es_el_vencimiento(self):
        politica = PoliticaInteres(base_calculo=BASE_DESDE_VENCIMIENTO)

        base = fecha_base_interes(
            periodo=PERIODO, fecha_vencimiento=VENCIMIENTO, politica=politica
        )

        self.assertEqual(base, VENCIMIENTO)

    def test_el_interes_arranca_al_pasar_el_mes_del_periodo(self):
        inicio = fecha_inicio_interes(periodo=PERIODO, fecha_vencimiento=VENCIMIENTO)

        self.assertEqual(inicio, date(2026, 4, 1))

    def test_el_cambio_de_anio_no_arma_un_dicembre_imposible(self):
        inicio = fecha_inicio_interes(
            periodo="2026-12", fecha_vencimiento=date(2026, 12, 10)
        )

        self.assertEqual(inicio, date(2027, 1, 1))


class DiasInteresablesTests(unittest.TestCase):
    def test_dentro_del_mes_de_la_cuota_no_hay_interes(self):
        """Vencía el 10 y se paga el 25: el alumno llegó tarde pero dentro del
        mes, y la regla que describió IPAC empieza a contar recién
        al mes siguiente."""
        dias = dias_interesables(
            periodo=PERIODO,
            fecha_vencimiento=VENCIMIENTO,
            fecha_evaluacion=date(2026, 3, 25),
        )

        self.assertEqual(dias, 0)

    def test_el_dia_uno_del_mes_siguiente_cuenta_un_mes_entero(self):
        dias = dias_interesables(
            periodo=PERIODO,
            fecha_vencimiento=VENCIMIENTO,
            fecha_evaluacion=date(2026, 4, 1),
        )

        self.assertEqual(dias, 31)

    def test_los_dias_se_cuentan_desde_el_dia_1_no_desde_el_vencimiento(self):
        dias = dias_interesables(
            periodo=PERIODO,
            fecha_vencimiento=VENCIMIENTO,
            fecha_evaluacion=date(2026, 4, 5),
        )

        self.assertEqual(dias, 35)

    def test_cuota_pagada_dos_meses_despues(self):
        dias = dias_interesables(
            periodo=PERIODO,
            fecha_vencimiento=VENCIMIENTO,
            fecha_evaluacion=date(2026, 5, 15),
        )

        self.assertEqual(dias, 75)

    def test_la_base_por_vencimiento_cuenta_desde_el_dia_del_vencimiento(self):
        politica = PoliticaInteres(base_calculo=BASE_DESDE_VENCIMIENTO)

        dias = dias_interesables(
            periodo=PERIODO,
            fecha_vencimiento=VENCIMIENTO,
            fecha_evaluacion=date(2026, 3, 25),
            politica=politica,
        )

        self.assertEqual(dias, 15)


class PeriodosTests(unittest.TestCase):
    def test_meses_completos_descarta_el_resto(self):
        """59 días son dos meses menos uno: se cobran uno, no dos."""
        periodos = periodos_interesables(59, PoliticaInteres(unidad_calculo=UNIDAD_MESES))

        self.assertEqual(periodos, Decimal("1"))

    def test_meses_completos_llegando_a_suavisa_el_dia_30(self):
        periodos = periodos_interesables(60, PoliticaInteres(unidad_calculo=UNIDAD_MESES))

        self.assertEqual(periodos, Decimal("2"))

    def test_por_dias_prorratea_de_a_treinta(self):
        periodos = periodos_interesables(35, PoliticaInteres(unidad_calculo=UNIDAD_DIAS))

        self.assertEqual(periodos, Decimal(35) / Decimal(30))

    def test_sin_dias_no_hay_periodos(self):
        self.assertEqual(periodos_interesables(0), Decimal("0"))


class CalcularInteresTests(unittest.TestCase):
    def test_un_mes_de_interes(self):
        importe = calcular_interes(
            importe_base=Decimal("10000"),
            tasa=tasa(),
            dias=dias_interesables(
                periodo=PERIODO,
                fecha_vencimiento=VENCIMIENTO,
                fecha_evaluacion=date(2026, 4, 1),
            ),
        )

        self.assertEqual(importe, Decimal("550.00"))

    def test_prorrateo_por_dias_no_redondea_dos_veces(self):
        """Si el cálculo se hiciera en dos pasos redondeando los períodos a
        1,17 el resultado subiría a 643,50. Con un solo redondeo da 641,67."""
        politica = PoliticaInteres(unidad_calculo=UNIDAD_DIAS)

        importe = calcular_interes(
            importe_base=Decimal("10000"),
            tasa=tasa(),
            dias=35,
            politica=politica,
        )

        self.assertEqual(importe, Decimal("641.67"))

    def test_redondea_a_mitad_hacia_arriba(self):
        """0,045 con mitad-al-arriba es 0,05. Con mitad-al-par sería 0,04, y
        un redondeo al banco descuenta plata del alumno o se la paga al
        instituto según el signo."""
        importe = calcular_interes(
            importe_base=Decimal("1"),
            tasa=tasa("4.5"),
            dias=30,
            politica=PoliticaInteres(unidad_calculo=UNIDAD_MESES),
        )

        self.assertEqual(importe, Decimal("0.05"))

    def test_el_interes_es_simple_no_se_capitaliza(self):
        """Dos meses sobre el mismo importe base dan el doble exacto de un
        mes, no el interés sobre el interés."""
        un_mes = calcular_interes(importe_base=Decimal("10000"), tasa=tasa(), dias=30)
        dos_meses = calcular_interes(importe_base=Decimal("10000"), tasa=tasa(), dias=60)

        self.assertEqual(dos_meses, un_mes * 2)

    def test_sin_saldo_pendiente_no_hay_interes(self):
        self.assertEqual(
            calcular_interes(importe_base=Decimal("0"), tasa=tasa(), dias=60), Decimal("0.00")
        )

    def test_una_tasa_de_cero_no_cobra_nada(self):
        self.assertEqual(
            calcular_interes(importe_base=Decimal("10000"), tasa=tasa("0"), dias=60),
            Decimal("0.00"),
        )


class SeleccionarTasaTests(unittest.TestCase):
    def test_ignora_las_tasas_que_aun_no_rigen(self):
        elegida = seleccionar_tasa(
            [tasa("5.5", desde=date(2026, 1, 1)), tasa("9", desde=date(2026, 7, 1))],
            date(2026, 6, 30),
        )

        self.assertEqual(elegida.porcentaje_mensual, Decimal("5.5"))

    def test_toma_la_tasa_mas_reciente_entre_las_vigentes(self):
        elegida = seleccionar_tasa(
            [tasa("5.5", desde=date(2026, 1, 1)), tasa("9", desde=date(2026, 7, 1))],
            date(2026, 8, 15),
        )

        self.assertEqual(elegida.porcentaje_mensual, Decimal("9"))

    def test_una_tasa_vencida_ya_no_rige(self):
        elegida = seleccionar_tasa(
            [
                tasa("5.5", desde=date(2026, 1, 1), hasta=date(2026, 6, 30)),
                tasa("9", desde=date(2026, 7, 1)),
            ],
            date(2026, 8, 15),
        )

        self.assertEqual(elegida.porcentaje_mensual, Decimal("9"))

    def test_a_igual_inicio_gana_la_vigencia_mas_acotada(self):
        """Una tasa de emergencia para un mes puntual pisa a la general abierta."""
        elegida = seleccionar_tasa(
            [
                tasa("5.5", desde=date(2026, 7, 1)),
                tasa("12", desde=date(2026, 7, 1), hasta=date(2026, 7, 31)),
            ],
            date(2026, 7, 15),
        )

        self.assertEqual(elegida.porcentaje_mensual, Decimal("12"))

    def test_sin_tasa_vigente_falla_con_un_mensaje_que_diga_que_cargar(self):
        with self.assertRaises(ErrorInteres) as ctx:
            seleccionar_tasa([tasa("5.5", desde=date(2026, 1, 1))], date(2025, 12, 31))

        self.assertEqual(ctx.exception.detail, TASA_VIGENTE_MSG)


class EvaluarInteresCuotaTests(unittest.TestCase):
    def test_una_cuota_al_dia_devuelve_el_tres_y_los_dias(self):
        resultado = evaluar_interes_cuota(
            periodo=PERIODO,
            fecha_vencimiento=VENCIMIENTO,
            importe_base=Decimal("10000"),
            fecha_evaluacion=date(2026, 4, 1),
            tasa=tasa(),
        )

        self.assertEqual(resultado.dias_interesables, 31)
        self.assertEqual(resultado.periodos, Decimal("1"))
        self.assertEqual(resultado.importe, Decimal("550.00"))

    def test_una_cuota_sin_interes_devuelve_cero_en_todo(self):
        resultado = evaluar_interes_cuota(
            periodo=PERIODO,
            fecha_vencimiento=VENCIMIENTO,
            importe_base=Decimal("10000"),
            fecha_evaluacion=date(2026, 3, 25),
            tasa=tasa(),
        )

        self.assertEqual(resultado.dias_interesables, 0)
        self.assertEqual(resultado.importe, Decimal("0.00"))

    def test_los_periodos_legibles_son_los_redondeados(self):
        resultado = evaluar_interes_cuota(
            periodo=PERIODO,
            fecha_vencimiento=VENCIMIENTO,
            importe_base=Decimal("10000"),
            fecha_evaluacion=date(2026, 4, 5),
            tasa=tasa(),
            politica=PoliticaInteres(unidad_calculo=UNIDAD_DIAS),
        )

        self.assertEqual(resultado.periodos_legibles, Decimal("1.17"))


class ValidacionTests(unittest.TestCase):
    def test_rechaza_una_tasa_negativa(self):
        with self.assertRaises(ErrorInteres) as ctx:
            tasa("-1")

        self.assertEqual(ctx.exception.detail, TASA_NEGATIVA_MSG)

    def test_rechaza_una_vigencia_invertida(self):
        with self.assertRaises(ErrorInteres) as ctx:
            tasa("5.5", desde=date(2026, 6, 1), hasta=date(2026, 1, 1))

        self.assertEqual(ctx.exception.detail, VIGENCIA_INVERTIDA_MSG)

    def test_rechaza_una_base_desconocida(self):
        with self.assertRaises(ErrorInteres) as ctx:
            PoliticaInteres(base_calculo="a_mano")

        self.assertEqual(ctx.exception.detail, BASE_MSG)

    def test_rechaza_una_unidad_desconocida(self):
        with self.assertRaises(ErrorInteres) as ctx:
            PoliticaInteres(unidad_calculo="semanas")

        self.assertEqual(ctx.exception.detail, UNIDAD_MSG)


class DominioPuroTests(unittest.TestCase):
    def test_el_dominio_no_importa_django_ni_drf(self):
        """AGENTS.md lo exige: el dominio no importa Django ni la base.

        Se mira el **archivo**, no `sys.modules`. Un guardián que chequea
        `sys.modules` pasa cuando se corre el archivo solo y falla en la suite
        completa, porque ahí Django ya está cargado por otros tests: mide el
        estado del intérprete, no la dependencia del módulo.
        """
        arbol = ast.parse(Path(intereses.__file__).read_text(encoding="utf-8"))
        raices = set()
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.Import):
                raices.update(alias.name.split(".")[0] for alias in nodo.names)
            elif isinstance(nodo, ast.ImportFrom) and nodo.module and nodo.level == 0:
                raices.add(nodo.module.split(".")[0])

        self.assertNotIn("django", raices)
        self.assertNotIn("rest_framework", raices)

    def test_el_dominio_no_importa_nada_del_adaptador(self):
        """El dominio no puede alcanzar la infraestructura de su contexto:
        si lo hace, la regla de cálculo queda atada al ORM."""
        arbol = ast.parse(Path(intereses.__file__).read_text(encoding="utf-8"))
        relativos = {
            nodo.module
            for nodo in ast.walk(arbol)
            if isinstance(nodo, ast.ImportFrom) and nodo.module and nodo.level > 0
        }

        self.assertNotIn("infrastructure", relativos)
        self.assertNotIn("application", relativos)


if __name__ == "__main__":
    unittest.main()