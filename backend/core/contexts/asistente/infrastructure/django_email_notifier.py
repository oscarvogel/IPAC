from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from core.models import AsistenteConfig, AsistenteConsultaNoResuelta


DEFAULT_NOTIFY_CATEGORIES = {
    AsistenteConsultaNoResuelta.Categoria.NO_DOCUMENTADA,
    AsistenteConsultaNoResuelta.Categoria.SIN_DATOS,
    AsistenteConsultaNoResuelta.Categoria.ERROR_IA,
    AsistenteConsultaNoResuelta.Categoria.ERROR_HERRAMIENTA,
}


def _category_allowed(config, category):
    if category in DEFAULT_NOTIFY_CATEGORIES:
        return True
    return (
        category == AsistenteConsultaNoResuelta.Categoria.FUERA_DE_ALCANCE
        and config.incluir_fuera_de_alcance
    )


def _event_body(event):
    return (
        f"Fecha: {timezone.localtime(event.creado):%d/%m/%Y %H:%M}\n"
        f"Usuario: {event.usuario.username}\n"
        f"Sucursal: {event.sucursal.nombre}\n"
        f"Categoría: {event.get_categoria_display()}\n\n"
        f"Pregunta:\n{event.pregunta}\n\n"
        "Revisar en Configuración → Asistente IA → Consultas no resueltas."
    )


class DjangoEmailNotifier:
    def notify_immediate(self, event_id):
        config = AsistenteConfig.get_solo()
        if (
            not config.email_habilitado
            or config.modo_email != AsistenteConfig.ModoEmail.INMEDIATO
            or not config.destinatarios
        ):
            return False

        event = (
            AsistenteConsultaNoResuelta.objects.select_related("usuario", "sucursal")
            .filter(pk=event_id, notificado_en__isnull=True)
            .first()
        )
        if not event or not _category_allowed(config, event.categoria):
            return False

        try:
            send_mail(
                subject=f"[IPAC] Consulta del asistente sin resolver — {event.get_categoria_display()}",
                message=_event_body(event),
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                recipient_list=config.destinatarios,
                fail_silently=False,
            )
        except Exception:
            return False

        event.notificado_en = timezone.now()
        event.save(update_fields=["notificado_en", "actualizado"])
        return True


def send_daily_digest(now=None):
    config = AsistenteConfig.get_solo()
    now = timezone.localtime(now or timezone.now())
    result = {"sent": False, "count": 0, "reason": ""}

    if (
        not config.email_habilitado
        or config.modo_email != AsistenteConfig.ModoEmail.DIARIO
        or not config.destinatarios
    ):
        result["reason"] = "disabled"
        return result

    target = config.hora_resumen_diario
    if now.hour != target.hour:
        result["reason"] = "outside_window"
        return result

    last = config.ultimo_resumen_exitoso_en
    if last:
        local_last = timezone.localtime(last)
        if local_last.date() == now.date() and local_last.hour == target.hour:
            result["reason"] = "already_sent"
            return result

    events = AsistenteConsultaNoResuelta.objects.filter(
        notificado_en__isnull=True,
        estado=AsistenteConsultaNoResuelta.Estado.PENDIENTE,
    ).select_related("usuario", "sucursal")
    allowed = list(DEFAULT_NOTIFY_CATEGORIES)
    if config.incluir_fuera_de_alcance:
        allowed.append(AsistenteConsultaNoResuelta.Categoria.FUERA_DE_ALCANCE)
    events = list(events.filter(categoria__in=allowed).order_by("creado", "id"))

    if events:
        body = [
            f"Resumen de consultas no resueltas del Asistente IPAC — {now:%d/%m/%Y}",
            "",
        ]
        for event in events:
            body.extend(
                [
                    f"#{event.id} · {event.get_categoria_display()} · {event.sucursal.nombre}",
                    f"Usuario: {event.usuario.username}",
                    f"Pregunta: {event.pregunta}",
                    "",
                ]
            )
        try:
            send_mail(
                subject=f"[IPAC] Resumen diario del Asistente — {len(events)} consulta(s)",
                message="\n".join(body),
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                recipient_list=config.destinatarios,
                fail_silently=False,
            )
        except Exception:
            result["reason"] = "email_error"
            return result

        timestamp = timezone.now()
        AsistenteConsultaNoResuelta.objects.filter(
            pk__in=[event.pk for event in events]
        ).update(notificado_en=timestamp, actualizado=timestamp)
        result.update({"sent": True, "count": len(events), "reason": "sent"})

    config.ultimo_resumen_exitoso_en = timezone.now()
    config.save(update_fields=["ultimo_resumen_exitoso_en", "actualizado"])
    if not events:
        result["reason"] = "empty"
    return result
