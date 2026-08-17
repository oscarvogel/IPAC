from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from core.contexts.importacion.application.import_ipac_workbook import IPACWorkbookImporter


class Command(BaseCommand):
    help = "Importa carreras/cursos y alumnos desde un archivo XLSX o CSV de IPAC."

    def add_arguments(self, parser):
        parser.add_argument("archivo", type=Path)
        parser.add_argument("--sucursal", default="POS", help="Código de sucursal por defecto: POS o ELD.")
        parser.add_argument("--carrera", default="", help="Carrera/curso por defecto para filas de alumnos sin carrera.")

    def handle(self, *args, **options):
        path = options["archivo"]
        if not path.exists():
            raise CommandError(f"No existe el archivo: {path}")
        if path.suffix.lower() not in {".xlsx", ".csv"}:
            raise CommandError("El archivo debe tener extensión .xlsx o .csv.")
        try:
            result = IPACWorkbookImporter().import_file(
                path.open("rb"),
                path.name,
                default_branch_code=options["sucursal"],
                default_career_name=options["carrera"],
            )
        except Exception as exc:
            raise CommandError(f"No se pudo importar el archivo: {exc}") from exc
        self.stdout.write(self.style.SUCCESS(f"Importación completada: {result.filename}"))
        self.stdout.write(f"Carreras: {result.careers.created} creadas, {result.careers.updated} actualizadas, {result.careers.skipped} omitidas")
        self.stdout.write(f"Alumnos: {result.students.created} creados, {result.students.updated} actualizados, {result.students.skipped} omitidos")
        for warning in result.warnings:
            self.stdout.write(self.style.WARNING(f"Advertencia: {warning}"))
