from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from rest_framework.test import APITestCase

from core.chatbot.planner import PlannerDecision
from core.models import ChatbotConversation, ChatbotMessage, PerfilUsuario, Sucursal


class FakeToolRegistry:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def execute(self, name, arguments, context):
        self.calls.append((name, arguments, context))
        return self.result


@override_settings(
    IPAC_AI_ENABLED=True,
    IPAC_AI_API_KEY="test",
    IPAC_AI_MODEL="MiniMax-M3",
    IPAC_AI_BASE_URL="https://example.invalid/v1/chat/completions",
)
class CleanServiceTests(TestCase):
    def setUp(self):
        self.branch = Sucursal.objects.create(codigo="SRV-C", nombre="Service Clean")
        self.user = User.objects.create_user(username="srv-clean", password="secret")
        PerfilUsuario.objects.create(
            user=self.user,
            rol=PerfilUsuario.Rol.ADMINISTRACION,
            sucursal=self.branch,
        )

    @patch("core.chatbot.service.MiniMaxPlanner")
    def test_ai_selects_knowledge_key_instead_of_phrase_router(self, planner_cls):
        planner_cls.return_value.decide.return_value = PlannerDecision(
            kind="knowledge",
            knowledge_key="cerrar_caja",
        )

        from core.chatbot.service import answer_message

        result = answer_message(
            self.user,
            "una formulación cualquiera sobre el procedimiento",
            [],
        )

        self.assertEqual(result["source"], "procedure")
        self.assertEqual(result["procedure"], "cerrar_caja")
        self.assertIn("Total contado", result["content"])
        planner_cls.return_value.decide.assert_called_once()

    @patch("core.chatbot.service.ReadToolRegistry")
    @patch("core.chatbot.service.MiniMaxPlanner")
    def test_ai_tool_decision_executes_only_selected_tool(self, planner_cls, registry_cls):
        planner_cls.return_value.decide.return_value = PlannerDecision(
            kind="tool",
            tool="resumen_deuda",
            arguments={},
        )
        registry = FakeToolRegistry(
            {
                "scope": "Service Clean",
                "as_of": "2026-09-24",
                "deuda_total": 103666,
                "deuda_vencida": 91666,
                "alumnos_con_deuda": 3,
                "cuotas_pendientes": 3,
                "cuotas_vencidas": 2,
            }
        )
        registry_cls.return_value = registry

        from core.chatbot.service import answer_message

        result = answer_message(
            self.user,
            "pregunta de datos",
            [],
        )

        self.assertEqual(result["source"], "tool")
        self.assertEqual(registry.calls[0][0], "resumen_deuda")
        self.assertIn("103.666,00", result["content"])
        self.assertIn("Service Clean", result["content"])

    @patch("core.chatbot.service.MiniMaxPlanner")
    def test_out_of_scope_is_controlled(self, planner_cls):
        planner_cls.return_value.decide.return_value = PlannerDecision(kind="out_of_scope")

        from core.chatbot.service import answer_message

        result = answer_message(self.user, "tema externo", [])

        self.assertEqual(result["source"], "out_of_scope")
        self.assertIn("limitada al sistema IPAC", result["content"])


@override_settings(IPAC_AI_ENABLED=True)
class CleanConversationHistoryTests(APITestCase):
    def setUp(self):
        self.branch = Sucursal.objects.create(codigo="HIS-C", nombre="History Clean")
        self.user = User.objects.create_user(username="history-clean", password="secret")
        PerfilUsuario.objects.create(
            user=self.user,
            rol=PerfilUsuario.Rol.ADMINISTRACION,
            sucursal=self.branch,
        )
        self.client.force_authenticate(self.user)

    @patch("core.chatbot.views.answer_message")
    def test_current_message_is_not_duplicated_inside_history(self, answer_mock):
        conversation = ChatbotConversation.objects.create(
            usuario=self.user,
            sucursal=self.branch,
            titulo="Historia",
        )
        ChatbotMessage.objects.create(
            conversacion=conversation,
            role=ChatbotMessage.Role.USER,
            content="consulta anterior",
        )
        ChatbotMessage.objects.create(
            conversacion=conversation,
            role=ChatbotMessage.Role.ASSISTANT,
            content="respuesta anterior",
        )
        answer_mock.return_value = {
            "content": "respuesta actual",
            "tokens_used": None,
            "source": "tool",
            "procedure": None,
            "action": None,
        }

        response = self.client.post(
            "/api/chatbot/messages/",
            {
                "conversation_id": conversation.id,
                "content": "seguimiento actual",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        history = answer_mock.call_args.args[2]
        self.assertEqual(
            [item["content"] for item in history],
            ["consulta anterior", "respuesta anterior"],
        )
