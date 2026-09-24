from django.contrib.auth.models import User
from django.test import TestCase

from core.models import AsistenteKnowledgeArticle, PerfilUsuario, Sucursal


class AssistantKnowledgeRepositoryTests(TestCase):
    def setUp(self):
        self.branch = Sucursal.objects.create(codigo="KB", nombre="Knowledge")
        self.user = User.objects.create_user(username="kb-admin", password="secret")
        PerfilUsuario.objects.create(
            user=self.user,
            rol=PerfilUsuario.Rol.ADMINISTRACION,
            sucursal=self.branch,
        )

    def _repo(self):
        try:
            from core.contexts.asistente.infrastructure.django_knowledge_repository import (
                DjangoKnowledgeRepository,
            )
        except ImportError as exc:
            self.fail(f"Debe existir DjangoKnowledgeRepository: {exc}")
        return DjangoKnowledgeRepository()

    def test_article_change_is_visible_without_restart(self):
        article = AsistenteKnowledgeArticle.objects.get(clave="cerrar_caja")
        repo = self._repo()
        first = repo.find_match("como cierro caja", "administracion")
        self.assertIsNotNone(first)
        self.assertEqual(first.key, "cerrar_caja")

        article.titulo = "Cerrar caja diaria"
        article.save(update_fields=["titulo", "actualizado"])

        second = repo.find_match("como cierro caja", "administracion")
        self.assertEqual(second.title, "Cerrar caja diaria")

    def test_inactive_article_stops_matching(self):
        article = AsistenteKnowledgeArticle.objects.get(clave="cerrar_caja")
        article.activo = False
        article.save(update_fields=["activo", "actualizado"])

        self.assertIsNone(self._repo().find_match("como cierro caja", "administracion"))

    def test_article_role_filters_visibility(self):
        article = AsistenteKnowledgeArticle.objects.get(clave="cerrar_caja")
        article.roles_permitidos = ["superadmin"]
        article.save(update_fields=["roles_permitidos", "actualizado"])

        self.assertIsNone(self._repo().find_match("como cierro caja", "caja"))

    def test_typo_still_matches_persisted_article(self):
        match = self._repo().find_match("como cderrar la caja", "administracion")
        self.assertIsNotNone(match)
        self.assertEqual(match.key, "cerrar_caja")
