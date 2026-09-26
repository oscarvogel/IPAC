import unittest

from .evaluar_generacion_cuotas import EvaluarGeneracionCuotas


class EvaluarGeneracionCuotasTests(unittest.TestCase):
    def test_construye_resumen_compatible_y_motivos_sin_pedir_datos_personales(self):
        class ReaderFalso:
            def obtener_candidatos(self, **kwargs):
                self.kwargs = kwargs
                return [
                    {
                        "id": 2,
                        "legajo": "P-002",
                        "nombre_completo": "Gomez, Ana",
                        "carrera_nombre": "Enfermeria",
                        "estado": "activo",
                        "cuota_existente": False,
                    },
                    {
                        "id": 3,
                        "legajo": "P-003",
                        "nombre_completo": "Perez, Luis",
                        "carrera_nombre": "",
                        "estado": "activo",
                        "cuota_existente": True,
                    },
                ]

        reader = ReaderFalso()
        actor = object()
        result = EvaluarGeneracionCuotas(reader).execute(
            actor=actor,
            sucursal_id=1,
            carrera_id=None,
            concepto_id=8,
            periodo="2026-10",
        )

        self.assertIs(reader.kwargs["actor"], actor)
        self.assertEqual(result["alumnos_encontrados"], 2)
        self.assertEqual(result["omitidas"], 1)
        self.assertEqual(result["alumnos_elegibles"], [2])
        self.assertEqual(result["detalle_alumnos"][0]["motivo"], "")
        self.assertIn("Ya existe una cuota", result["detalle_alumnos"][1]["motivo"])
        self.assertNotIn("dni", result["detalle_alumnos"][0])
        self.assertNotIn("email", result["detalle_alumnos"][0])

    def test_devuelve_lista_vacia_y_campos_compatibles_cuando_no_hay_candidatos(self):
        class ReaderVacio:
            def obtener_candidatos(self, **kwargs):
                return []

        result = EvaluarGeneracionCuotas(ReaderVacio()).execute(
            actor=None,
            sucursal_id=1,
            carrera_id=None,
            concepto_id=8,
            periodo="2026-10",
        )

        self.assertEqual(result, {
            "alumnos_encontrados": 0,
            "omitidas": 0,
            "alumnos_elegibles": [],
            "detalle_alumnos": [],
        })
