from django.test import TestCase

from core.contexts.importacion.application.import_ipac_workbook import IPACWorkbookImporter
from core.models import Alumno, CarreraCurso, ConceptoCobrable, Sucursal


class ImportacionRegresionesTests(TestCase):
    def setUp(self):
        self.posadas = Sucursal.objects.create(codigo="POS", nombre="Posadas")
        self.eldorado = Sucursal.objects.create(codigo="ELD", nombre="Eldorado")

    def test_existing_student_found_by_dni_keeps_current_branch(self):
        alumno = Alumno.objects.create(
            legajo="POS-001",
            nombre="Ana",
            apellido="PEREZ",
            dni="30111222",
            sucursal=self.posadas,
        )

        class FakeReader:
            def read(self, source, filename):
                return {
                    "Alumnos": [
                        ["sucursal_codigo", "legajo", "apellido", "nombre", "dni", "email"],
                        ["ELD", "ELD-999", "PEREZ", "Ana", "30111222", "ana@nueva.test"],
                    ]
                }

        result = IPACWorkbookImporter(reader=FakeReader()).import_file(
            b"", "alumnos.csv", default_branch_code="ELD"
        )

        alumno.refresh_from_db()
        self.assertEqual(alumno.sucursal, self.posadas)
        self.assertEqual(alumno.legajo, "POS-001")
        self.assertEqual(alumno.email, "ana@nueva.test")
        self.assertTrue(any("traslados deben realizarse explícitamente" in warning for warning in result.warnings))

    def test_catalog_import_creates_year_agnostic_concepts(self):
        class FakeReader:
            def read(self, source, filename):
                return {
                    "Carreras": [
                        ["sucursal_codigo", "nombre", "tipo", "duracion", "plan_cuotas", "importe_matricula", "cuota_total"],
                        ["POS", "Tecnicatura de prueba", "carrera", "3 años", "10", "41400", "82000"],
                    ]
                }

        IPACWorkbookImporter(reader=FakeReader()).import_file(
            b"", "carreras.csv", default_branch_code="POS"
        )

        carrera = CarreraCurso.objects.get(nombre="Tecnicatura de prueba", sucursal=self.posadas)
        self.assertEqual(
            ConceptoCobrable.objects.get(nombre="Matrícula", carrera=carrera).importe,
            41400,
        )
        self.assertEqual(
            ConceptoCobrable.objects.get(nombre="Cuota mensual", carrera=carrera).importe,
            82000,
        )
        self.assertFalse(ConceptoCobrable.objects.filter(nombre__contains="2026", carrera=carrera).exists())
