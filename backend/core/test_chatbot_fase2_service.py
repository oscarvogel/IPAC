from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from rest_framework.test import APITestCase

from core.models import ChatbotConversation, ChatbotMessage, PerfilUsuario, Sucursal


class FakeAgentResponse:
    def __init__(self, content="", tool_calls=None, tokens_used=None):
        self.content = content
        self.tool_calls = tool_calls or []
        self.tokens_used = tokens_used


@override_settings(
    IPAC_AI_ENABLED=True,
    IPAC_AI_API_KEY="test",
    IPAC_AI_MODEL="MiniMax-M3",
    IPAC_AI_BASE_URL="https://example.invalid/v1/chat/completions",
)
class NativeAgentServiceTests(TestCase):
    def setUp(self):
        self.branch = Sucursal.objects.create(codigo="AG-C", nombre="Agent Clean")
        self.user = User.objects.create_user(username="agent-clean", password="secret")
        PerfilUsuario.objects.create(
            user=self.user,
            rol=PerfilUsuario.Rol.ADMINISTRACION,
            sucursal=self.branch,
        )

    @patch("core.chatbot.service.MiniMaxAgentProvider")
    def test_simple_answer_comes_directly_from_ai(self, provider_cls):
        provider_cls.return_value.send.return_value = FakeAgentResponse(
            content="Para dar de alta un alumno, ingresá a Alumnos y usá Nuevo alumno."
        )

        from core.chatbot.service import answer_message

        result = answer_message(
            self.user,
            "¿Cómo doy de alta un alumno?",
            [],
        )

        self.assertEqual(result["source"], "ai")
        self.assertIn("Nuevo alumno", result["content"])
        sent_messages = provider_cls.return_value.send.call_args.args[0]
        self.assertEqual(sent_messages[-1]["role"], "user")
        self.assertIn("¿Cómo doy de alta", sent_messages[-1]["content"])

    @patch("core.chatbot.service.ReadToolRegistry")
    @patch("core.chatbot.service.MiniMaxAgentProvider")
    def test_ai_tool_call_is_executed_then_result_returns_to_ai(self, provider_cls, registry_cls):
        provider_cls.return_value.send.side_effect = [
            FakeAgentResponse(
                tool_calls=[
                    {
                        "id": "call_1",
                        "name": "resumen_deuda",
                        "arguments": {},
                    }
                ]
            ),
            FakeAgentResponse(
                content="La deuda total autorizada es de $ 103.666,00.",
                tokens_used=77,
            ),
        ]

        registry = registry_cls.return_value
        registry.schemas.return_value = [
            {
                "type": "function",
                "function": {
                    "name": "resumen_deuda",
                    "description": "Consulta deuda",
                    "parameters": {"type": "object", "properties": {}, "required": []},
                },
            }
        ]
        registry.execute.return_value = {
            "scope": "Agent Clean",
            "as_of": "2026-09-24",
            "deuda_total": 103666,
            "deuda_vencida": 91666,
            "alumnos_con_deuda": 3,
            "cuotas_pendientes": 3,
            "cuotas_vencidas": 2,
        }

        from core.chatbot.service import answer_message

        result = answer_message(self.user, "¿Cuánto es la deuda total?", [])

        self.assertEqual(result["source"], "tool")
        self.assertEqual(result["content"], "La deuda total autorizada es de $ 103.666,00.")
        self.assertEqual(result["tokens_used"], 77)
        registry.execute.assert_called_once()
        self.assertEqual(registry.execute.call_args.args[0], "resumen_deuda")

        second_messages = provider_cls.return_value.send.call_args_list[1].args[0]
        self.assertEqual(second_messages[-2]["role"], "assistant")
        self.assertEqual(second_messages[-1]["role"], "tool")
        self.assertEqual(second_messages[-1]["tool_call_id"], "call_1")
        self.assertIn("103666", second_messages[-1]["content"])

    @patch("core.chatbot.service.ReadToolRegistry")
    @patch("core.chatbot.service.MiniMaxAgentProvider")
    def test_ai_can_chain_multiple_read_tools(self, provider_cls, registry_cls):
        provider_cls.return_value.send.side_effect = [
            FakeAgentResponse(
                tool_calls=[{"id": "c1", "name": "resumen_deuda", "arguments": {}}]
            ),
            FakeAgentResponse(
                tool_calls=[{"id": "c2", "name": "alumnos_con_deuda", "arguments": {}}]
            ),
            FakeAgentResponse(content="El alumno con mayor deuda es Perez, Juan."),
        ]

        registry = registry_cls.return_value
        registry.schemas.return_value = []
        registry.execute.side_effect = [
            {"deuda_total": 1200, "scope": "Todas", "as_of": "2026-09-24"},
            {
                "total_alumnos": 2,
                "deuda_total": 1200,
                "scope": "Todas",
                "as_of": "2026-09-24",
                "alumnos": [
                    {"nombre": "Perez, Juan", "legajo": "1", "sucursal": "P", "deuda_total": 700, "deuda_vencida": 500},
                    {"nombre": "Gomez, Ana", "legajo": "2", "sucursal": "E", "deuda_total": 500, "deuda_vencida": 500},
                ],
            },
        ]

        from core.chatbot.service import answer_message

        result = answer_message(self.user, "¿Quién debe más?", [])

        self.assertEqual(result["content"], "El alumno con mayor deuda es Perez, Juan.")
        self.assertEqual(registry.execute.call_count, 2)
        self.assertEqual(provider_cls.return_value.send.call_count, 3)

    @patch("core.chatbot.service.MiniMaxAgentProvider")
    def test_no_phrase_router_runs_before_ai(self, provider_cls):
        provider_cls.return_value.send.return_value = FakeAgentResponse(
            content="Respuesta elegida por la IA."
        )

        from core.chatbot.service import answer_message

        result = answer_message(self.user, "cuanto es la deuda total?", [])

        self.assertEqual(result["content"], "Respuesta elegida por la IA.")
        self.assertEqual(result["source"], "ai")
        provider_cls.return_value.send.assert_called_once()


@override_settings(IPAC_AI_ENABLED=True)
class NativeConversationHistoryTests(APITestCase):
    def setUp(self):
        self.branch = Sucursal.objects.create(codigo="HIS-N", nombre="History Native")
        self.user = User.objects.create_user(username="history-native", password="secret")
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
            "source": "ai",
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
