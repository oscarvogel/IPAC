import unittest
from datetime import date

from ..domain.planificacion_cuotas import planificar_periodo_unico, planificar_secuencia
from .evaluar_generacion_cuotas import EvaluarGeneracionCuotas


class LectorFalso:
    def __init__(self, candidatos):
        self.candidatos = candidatos
        self.kwargs = None

    def obtener_candidatos(self, **kwargs):
        self.kwargs = kwargs
        return self.candidatos


def candidato(alumno_id, existentes=()):
    return {
        "id": alumno_id,
        "legajo": f"P-{alumno_id:03d}",
        "nombre_completo": f"Alumno {alumno_id}",
        "carrera_nombre": "Enfermeria",
        "estado": "activo",
        "periodos_existentes": list(existentes),
    }


class EvaluarGeneracionCuotasTests(unittest.TestCase):
    def test_arma_resumen_y_motivos_sin_pedir_datos_personales(self):
        reader = LectorFalso([
            candidato(2),
            candidato(3, existentes=["2026-10"]),
        ])
        actor = object()

        result = EvaluarGeneracionCuotas(reader).execute(
            actor=actor,
            sucursal_id=1,
            carrera_id=None,
            concepto_id=8,
            planificacion=planificar_periodo_unico(
                periodo="2026-10", fecha_vencimiento=date(2026, 10, 10)
            ),
        )

        self.assertIs(reader.kwargs["actor"], actor)
        self.assertEqual(reader.kwargs["periodos"], ["2026-10"])
        self.assertEqual(result["alumnos_encontrados"], 2)
        self.assertEqual(result["omitidas"], 1)
        self.assertEqual(result["alumnos_elegibles"], [2])
        self.assertEqual(result["cantidad_periodos"], 1)
        self.assertEqual(result["cuotas_a_generar"], 1)
        self.assertEqual(result["detalle_alumnos"][0]["motivo"], "")
        self.assertIn("Ya tiene todas", result["detalle_alumnos"][1]["motivo"])
        self.assertNotIn("dni", result["detalle_alumnos"][0])
        self.assertNotIn("email", result["detalle_alumnos"][0])

    def test_un_alumno_con_parte_del_lote_hecho_sigue_siendo_elegible(self):
        """El caso central: tiene 7 de 10, le faltan 3 y hay que generarlas."""
        periodos = [f"2026-{mes:02d}" for mes in range(1, 11)]
        reader = LectorFalso([candidato(2, existentes=periodos[:7])])

        result = EvaluarGeneracionCuotas(reader).execute(
            actor=None,
            sucursal_id=1,
            carrera_id=None,
            concepto_id=8,
            planificacion=planificar_secuencia(
                cantidad=10, mes_inicial=1, anio_inicial=2026, dia_vencimiento=10
            ),
        )

        detalle = result["detalle_alumnos"][0]
        self.assertEqual(detalle["existentes"], periodos[:7])
        self.assertEqual(detalle["faltantes"], periodos[7:])
        self.assertEqual(detalle["motivo"], "")
        self.assertEqual(result["alumnos_elegibles"], [2])
        self.assertEqual(result["omitidas"], 0)
        self.assertEqual(result["cuotas_a_generar"], 3)

    def test_excluye_a_quien_ya_completo_el_lote_entero(self):
        periodos = [f"2026-{mes:02d}" for mes in range(1, 4)]
        reader = LectorFalso([
            candidato(2, existentes=periodos),
            candidato(3),
        ])

        result = EvaluarGeneracionCuotas(reader).execute(
            actor=None,
            sucursal_id=1,
            carrera_id=None,
            concepto_id=8,
            planificacion=planificar_secuencia(
                cantidad=3, mes_inicial=1, anio_inicial=2026, dia_vencimiento=10
            ),
        )

        self.assertEqual(result["alumnos_elegibles"], [3])
        self.assertEqual(result["omitidas"], 1)
        self.assertEqual(result["cuotas_a_generar"], 3)
        self.assertEqual(result["detalle_alumnos"][0]["faltantes"], [])

    def test_expone_los_periodos_del_lote_para_que_el_operador_los_revise(self):
        result = EvaluarGeneracionCuotas(LectorFalso([])).execute(
            actor=None,
            sucursal_id=1,
            carrera_id=None,
            concepto_id=8,
            planificacion=planificar_secuencia(
                cantidad=2, mes_inicial=11, anio_inicial=2026, dia_vencimiento=10
            ),
        )

        self.assertEqual(result["periodos"], ["2026-11", "2026-12"])
        self.assertEqual(
            result["etiquetas_periodo"],
            ["noviembre 2026 (vence el 10)", "diciembre 2026 (vence el 10)"],
        )

    def test_devuelve_lista_vacia_y_campos_compatibles_cuando_no_hay_candidatos(self):
        result = EvaluarGeneracionCuotas(LectorFalso([])).execute(
            actor=None,
            sucursal_id=1,
            carrera_id=None,
            concepto_id=8,
            planificacion=planificar_periodo_unico(
                periodo="2026-10", fecha_vencimiento=date(2026, 10, 10)
            ),
        )

        self.assertEqual(result, {
            "cantidad_periodos": 1,
            "periodos": ["2026-10"],
            "etiquetas_periodo": ["octubre 2026 (vence el 10)"],
            "alumnos_encontrados": 0,
            "omitidas": 0,
            "alumnos_elegibles": [],
            "cuotas_a_generar": 0,
            "detalle_alumnos": [],
        })
