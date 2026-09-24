from django.contrib.auth.models import User
from django.test import TestCase

from core import models as core_models


class AssistantPhase2ModelTests(TestCase):
    def setUp(self):
        self.branch = core_models.Sucursal.objects.create(codigo="POS2", nombre="Posadas Fase 2")
        self.user = User.objects.create_user(username="assistant-fase2", password="secret")

    def test_knowledge_article_is_ordered_and_defaults_active(self):
        article_model = getattr(core_models, "AsistenteKnowledgeArticle", None)
        self.assertIsNotNone(article_model, "Debe existir AsistenteKnowledgeArticle")
        article = article_model.objects.create(
            clave="alta_alumno_fase2",
            titulo="Dar de alta un alumno",
            modulo="alumnos",
            preguntas_equivalentes=["alta alumno"],
            pasos=["Entrá a Alumnos."],
            roles_permitidos=["superadmin", "administracion"],
        )
        self.assertTrue(article.activo)
        self.assertEqual(article.orden, 0)

    def test_unresolved_keeps_original_question_and_status(self):
        unresolved_model = getattr(core_models, "AsistenteConsultaNoResuelta", None)
        self.assertIsNotNone(unresolved_model, "Debe existir AsistenteConsultaNoResuelta")
        event = unresolved_model.objects.create(
            usuario=self.user,
            sucursal=self.branch,
            pregunta="¿Cómo refinancio una cuota?",
            pregunta_normalizada="como refinancio una cuota",
            categoria="no_documentada",
            respuesta="No tengo información suficiente.",
        )
        self.assertEqual(event.estado, "pendiente")
        self.assertIsNone(event.notificado_en)

    def test_assistant_config_singleton(self):
        config_model = getattr(core_models, "AsistenteConfig", None)
        self.assertIsNotNone(config_model, "Debe existir AsistenteConfig")
        first = config_model.get_solo()
        second = config_model.get_solo()
        self.assertEqual(first.pk, second.pk)

    def test_seeded_knowledge_contains_core_procedures(self):
        article_model = getattr(core_models, "AsistenteKnowledgeArticle", None)
        self.assertIsNotNone(article_model, "Debe existir AsistenteKnowledgeArticle")
        expected = {
            "alta_alumno",
            "matricular_alumno",
            "generar_cuotas",
            "registrar_pago",
            "estado_cuenta",
            "cerrar_caja",
            "saldo_anterior_caja",
            "anular_pago",
            "importar_datos",
        }
        self.assertTrue(expected.issubset(set(article_model.objects.values_list("clave", flat=True))))
