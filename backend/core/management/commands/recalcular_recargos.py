from django.core.management.base import BaseCommand

from core.contexts.cobranzas.application.recalcular_recargos import RecalcularRecargos
from core.contexts.cobranzas.infrastructure.django_recargo_repository import DjangoRecargoRepository


class Command(BaseCommand):
    help = "Recalcula recargos vencidos según las reglas activas. Apto para ejecución diaria programada."

    def handle(self, *args, **options):
        result = RecalcularRecargos(DjangoRecargoRepository()).execute()
        self.stdout.write(self.style.SUCCESS(f"Cuotas evaluadas: {result['evaluadas']}; actualizadas: {result['actualizadas']}"))
