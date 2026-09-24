from unittest import mock

from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase, override_settings

from core.models import (
    AsistenteConfig,
    AsistenteConsultaNoResuelta,
    PerfilUsuario,
    Sucursal,
)


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="ipac@example.com",
)
class AssistantNotificationTests(TestCase):
    def setUp(self):
        self.branch = Sucursal.objects.create(codigo="MAIL-AI", nombre="Mail AI")
        self.user = User.objects.create_user(username="mail-ai", password="secret")
        PerfilUsuario.objects.create(
            user=self.user,
            rol=PerfilUsuario.Rol.ADMINISTRACION,
            sucursal=self.branch,
        )
        self.config = AsistenteConfig.get_solo()
        self.config.email_habilitado = True
        self.config.modo_email = AsistenteConfig.ModoEmail.INMEDIATO
        self.config.destinatarios = ["oscar@example.com"]
        self.config.save()

    def _event(self, categoria):
        return AsistenteConsultaNoResuelta.objects.create(
            usuario=self.user,
            sucursal=self.branch,
            pregunta="¿Cómo refinancio una cuota?",
            pregunta_normalizada="como refinancio una cuota",
            categoria=categoria,
            respuesta="No tengo información suficiente.",
        )

    def _notifier(self):
        try:
            from core.contexts.asistente.infrastructure.django_email_notifier import (
                DjangoEmailNotifier,
            )
        except ImportError as exc:
            self.fail(f"Debe existir DjangoEmailNotifier: {exc}")
        return DjangoEmailNotifier()

    def test_immediate_notification_for_unknown_ipac_question(self):
        event = self._event(AsistenteConsultaNoResuelta.Categoria.NO_DOCUMENTADA)
        sent = self._notifier().notify_immediate(event.id)

        self.assertTrue(sent)
        self.assertEqual(len(mail.outbox), 1)
        event.refresh_from_db()
        self.assertIsNotNone(event.notificado_en)

    def test_out_of_scope_does_not_email_by_default(self):
        event = self._event(AsistenteConsultaNoResuelta.Categoria.FUERA_DE_ALCANCE)
        self.assertFalse(self._notifier().notify_immediate(event.id))
        self.assertEqual(len(mail.outbox), 0)

    @mock.patch("core.contexts.asistente.infrastructure.django_email_notifier.send_mail", side_effect=OSError("smtp down"))
    def test_smtp_failure_leaves_event_unnotified_and_does_not_raise(self, _send):
        event = self._event(AsistenteConsultaNoResuelta.Categoria.ERROR_IA)
        self.assertFalse(self._notifier().notify_immediate(event.id))
        event.refresh_from_db()
        self.assertIsNone(event.notificado_en)
