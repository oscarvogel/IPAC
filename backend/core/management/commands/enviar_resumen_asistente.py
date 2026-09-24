from django.core.management.base import BaseCommand

from core.contexts.asistente.infrastructure.django_email_notifier import send_daily_digest


class Command(BaseCommand):
    help = "Envía el resumen diario configurable de consultas no resueltas del Asistente IPAC."

    def handle(self, *args, **options):
        result = send_daily_digest()
        self.stdout.write(
            f"assistant_digest sent={result['sent']} count={result['count']} reason={result['reason']}"
        )
