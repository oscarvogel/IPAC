from django.forms.models import model_to_dict

from ..application.registrar_evento import RegistrarEventoAuditoria
from ..infrastructure.django_auditoria_repository import DjangoAuditoriaRepository


SENSITIVE_FIELDS = {"password", "last_login"}


def snapshot(instance):
    return {
        key: value
        for key, value in model_to_dict(instance).items()
        if key not in SENSITIVE_FIELDS
    }


class AuditableViewSetMixin:
    audit_module = "administracion"

    def _audit(self, *, action, instance, before=None, after=None, description=""):
        sucursal = getattr(instance, "sucursal", None)
        RegistrarEventoAuditoria(DjangoAuditoriaRepository()).execute(
            usuario=self.request.user,
            sucursal=sucursal,
            modulo=self.audit_module,
            accion=action,
            entidad=instance._meta.label,
            entidad_id=instance.pk,
            descripcion=description,
            valores_anteriores=before,
            valores_nuevos=after,
        )

    def perform_create(self, serializer):
        instance = serializer.save()
        self._audit(action="alta", instance=instance, after=snapshot(instance))

    def perform_update(self, serializer):
        before = snapshot(serializer.instance)
        instance = serializer.save()
        self._audit(action="edicion", instance=instance, before=before, after=snapshot(instance))

    def perform_destroy(self, instance):
        before = snapshot(instance)
        super().perform_destroy(instance)
        self._audit(action="baja", instance=instance, before=before)
