import unittest

from .exportar_cajas import ExportarCajas, FiltrosExportacionCajas


class ExportarCajasTests(unittest.TestCase):
    def test_entrega_filtros_de_actor_y_columnas_al_adaptador(self):
        class ReaderFake:
            def leer_cajas(self, *, actor, filtros):
                self.actor = actor
                self.filtros = filtros
                return [["2026-09-01", "Posadas"]]

        reader = ReaderFake()
        actor = object()
        filtros = FiltrosExportacionCajas(desde="2026-09-01", usuario_id="8")

        result = ExportarCajas(reader).execute(actor=actor, filtros=filtros)

        self.assertIs(reader.actor, actor)
        self.assertIs(reader.filtros, filtros)
        self.assertEqual(result["headers"][0], "Fecha")
        self.assertEqual(result["rows"], [["2026-09-01", "Posadas"]])
