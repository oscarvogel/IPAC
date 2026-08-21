import json

from django.core.serializers.json import DjangoJSONEncoder

from ....models import EventoAuditoria


def serializable(value):
    return json.loads(json.dumps(value, cls=DjangoJSONEncoder))


class DjangoAuditoriaRepository:
    def guardar(self, **evento):
        for field in ("valores_anteriores", "valores_nuevos", "metadata"):
            evento[field] = serializable(evento.get(field, {}))
        return EventoAuditoria.objects.create(**evento)
