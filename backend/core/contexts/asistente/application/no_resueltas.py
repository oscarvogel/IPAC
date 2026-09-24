from django.utils import timezone

from core.models import AsistenteConsultaNoResuelta


class RegistrarNoResuelta:
    def __init__(self, repository, notifier=None):
        self.repository = repository
        self.notifier = notifier

    def execute(
        self,
        *,
        user,
        question,
        category,
        response,
        conversation=None,
        user_message=None,
        intent="",
        tool="",
        metadata=None,
    ):
        event = self.repository.register_unresolved(
            user=user,
            question=question,
            category=category,
            response=response,
            conversation=conversation,
            user_message=user_message,
            intent=intent,
            tool=tool,
            metadata=metadata,
        )
        if self.notifier is not None:
            try:
                self.notifier.notify_immediate(event.id)
            except Exception:
                pass
        return event


def resolver_consulta(event, *, user, article=None, ignored=False):
    event.estado = (
        AsistenteConsultaNoResuelta.Estado.IGNORADA
        if ignored
        else AsistenteConsultaNoResuelta.Estado.RESUELTA
    )
    event.articulo = article
    event.resuelto_por = user
    event.resuelto_en = timezone.now()
    event.save(
        update_fields=[
            "estado",
            "articulo",
            "resuelto_por",
            "resuelto_en",
            "actualizado",
        ]
    )
    return event
