from django.contrib.auth.models import User
from django.test import override_settings
from rest_framework.test import APITestCase

from core.chatbot.knowledge import match_procedure
from core.models import ChatbotConversation, PerfilUsuario, Sucursal


class ChatbotKnowledgeTests(APITestCase):
    def test_matches_core_procedures_and_typo(self):
        self.assertEqual(match_procedure("¿Cómo doy de alta un alumno?")[0], "alta_alumno")
        self.assertEqual(match_procedure("necesito generar cuotas")[0], "generar_cuotas")
        self.assertEqual(match_procedure("como cderrar la caja")[0], "cerrar_caja")


@override_settings(IPAC_AI_ENABLED=False)
class ChatbotApiTests(APITestCase):
    def setUp(self):
        self.branch = Sucursal.objects.create(codigo="POS", nombre="Posadas")
        self.user = User.objects.create_user(username="admin-chat", password="secret")
        PerfilUsuario.objects.create(
            user=self.user,
            rol=PerfilUsuario.Rol.ADMINISTRACION,
            sucursal=self.branch,
        )
        self.client.force_authenticate(self.user)

    def test_conversation_and_known_procedure_work_without_ai(self):
        start = self.client.post("/api/chatbot/conversations/", {}, format="json")
        self.assertEqual(start.status_code, 201)
        conversation_id = start.data["conversation"]["id"]

        response = self.client.post(
            "/api/chatbot/messages/",
            {"conversation_id": conversation_id, "content": "¿Cómo cierro la caja?"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["source"], "procedure")
        self.assertEqual(response.data["procedure"], "cerrar_caja")
        self.assertEqual(response.data["action"]["path"], "/caja?accion=cerrar")
        self.assertIn("Total contado", response.data["messages"][-1]["content"])

    def test_conversation_is_private_to_owner(self):
        conversation = ChatbotConversation.objects.create(
            usuario=self.user,
            sucursal=self.branch,
            titulo="Privada",
        )
        other = User.objects.create_user(username="otro-chat", password="secret")
        PerfilUsuario.objects.create(
            user=other,
            rol=PerfilUsuario.Rol.CONSULTA,
            sucursal=self.branch,
        )
        self.client.force_authenticate(other)

        response = self.client.get(
            f"/api/chatbot/history/?conversation_id={conversation.id}"
        )
        self.assertEqual(response.status_code, 404)

    def test_unknown_question_has_safe_fallback_when_ai_disabled(self):
        start = self.client.post("/api/chatbot/conversations/", {}, format="json")
        conversation_id = start.data["conversation"]["id"]

        response = self.client.post(
            "/api/chatbot/messages/",
            {"conversation_id": conversation_id, "content": "¿Qué otra cosa puedo hacer?"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["source"], "fallback")
        self.assertIn("procedimientos del sistema IPAC", response.data["messages"][-1]["content"])
