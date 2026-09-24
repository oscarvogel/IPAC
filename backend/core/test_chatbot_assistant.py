from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.utils import timezone
from django.test import override_settings
from rest_framework.test import APITestCase

from core.chatbot.knowledge import match_procedure
from core.models import (
    ChatbotConversation,
    ChatbotMessage,
    ConceptoCobrable,
    Cuota,
    PerfilUsuario,
    Sucursal,
)
from core.contexts.asistente.domain.models import Classification, IntentKind, ScopeKind


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


    def test_total_debt_question_returns_live_data_through_api(self):
        concept = ConceptoCobrable.objects.create(
            nombre="Cuota Chat Live",
            tipo=ConceptoCobrable.Tipo.CUOTA,
            importe=Decimal("1250"),
            sucursal=self.branch,
        )
        today = timezone.localdate()
        student_model = __import__("core.models", fromlist=["Alumno"]).Alumno
        student = student_model.objects.create(
            legajo="CHAT-LIVE-1",
            nombre="Ana",
            apellido="Prueba",
            sucursal=self.branch,
        )
        Cuota.objects.create(
            alumno=student,
            concepto=concept,
            sucursal=self.branch,
            periodo="2026-09",
            fecha_emision=today,
            fecha_vencimiento=today,
            importe=Decimal("1250"),
        )
        start = self.client.post("/api/chatbot/conversations/", {}, format="json")

        response = self.client.post(
            "/api/chatbot/messages/",
            {
                "conversation_id": start.data["conversation"]["id"],
                "content": "¿cuánto es la deuda total?",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["source"], "tool")
        self.assertIn("1.250,00", response.data["messages"][-1]["content"])
        self.assertIn("Alcance: Posadas", response.data["messages"][-1]["content"])

    @override_settings(
        IPAC_AI_ENABLED=True,
        IPAC_AI_API_KEY="test",
        IPAC_AI_MODEL="MiniMax-M3",
        IPAC_AI_BASE_URL="https://example.invalid/v1/chat/completions",
    )
    @patch(
        "core.contexts.asistente.infrastructure.minimax_provider.MiniMaxIntentClassifier.classify",
        return_value=Classification(ScopeKind.OUT_OF_SCOPE, IntentKind.UNKNOWN),
    )
    def test_api_rejects_general_health_question(self, _classify):
        start = self.client.post("/api/chatbot/conversations/", {}, format="json")

        response = self.client.post(
            "/api/chatbot/messages/",
            {
                "conversation_id": start.data["conversation"]["id"],
                "content": "¿cómo se cura la gripe?",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["source"], "out_of_scope")
        self.assertIn(
            "Mi función está limitada al sistema IPAC",
            response.data["messages"][-1]["content"],
        )

    @patch("core.chatbot.views.answer_message")
    def test_planner_history_excludes_current_user_message(self, answer_mock):
        conversation = ChatbotConversation.objects.create(
            usuario=self.user,
            sucursal=self.branch,
            titulo="Contexto",
        )
        ChatbotMessage.objects.create(
            conversacion=conversation,
            role=ChatbotMessage.Role.ASSISTANT,
            content="Hay 3 alumnos con saldo pendiente.",
        )
        ChatbotMessage.objects.create(
            conversacion=conversation,
            role=ChatbotMessage.Role.USER,
            content="¿quiénes son?",
        )
        ChatbotMessage.objects.create(
            conversacion=conversation,
            role=ChatbotMessage.Role.ASSISTANT,
            content="Decime si querés que los liste.",
        )
        answer_mock.return_value = {
            "content": "Respuesta",
            "tokens_used": None,
            "source": "tool",
            "procedure": None,
            "action": None,
            "clarification": None,
        }

        response = self.client.post(
            "/api/chatbot/messages/",
            {
                "conversation_id": conversation.id,
                "content": "sí, quiero saber quiénes son esos alumnos",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        history = answer_mock.call_args.args[2]
        self.assertEqual(history[-1]["content"], "Decime si querés que los liste.")
        self.assertNotIn(
            "sí, quiero saber quiénes son esos alumnos",
            [item["content"] for item in history],
        )

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
