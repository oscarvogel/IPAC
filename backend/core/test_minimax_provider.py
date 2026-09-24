import json
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from core.contexts.asistente.domain.models import IntentKind, ScopeKind
from core.contexts.asistente.infrastructure.minimax_provider import MiniMaxIntentClassifier


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


@override_settings(
    IPAC_AI_API_KEY="test-key",
    IPAC_AI_MODEL="MiniMax-M3",
    IPAC_AI_BASE_URL="https://api.minimax.io/v1/chat/completions",
    IPAC_AI_TIMEOUT_SECONDS=30,
)
class MiniMaxProviderTests(SimpleTestCase):
    @patch("urllib.request.urlopen")
    def test_uses_known_working_minimax_m3_payload(self, urlopen):
        urlopen.return_value = FakeResponse(
            {
                "choices": [
                    {
                        "message": {
                            "content": '{"scope":"ipac","intent":"read_tool","tool":"resumen_deuda","arguments":{}}'
                        }
                    }
                ]
            }
        )

        result = MiniMaxIntentClassifier().classify(
            question="¿cuánto es la deuda total?",
            history=[],
            tool_names=["resumen_deuda"],
            role_context="rol=administracion;sucursal_id=1;acceso_global=no",
        )

        request = urlopen.call_args.args[0]
        payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(payload["model"], "MiniMax-M3")
        self.assertEqual(payload["thinking"], {"type": "disabled"})
        self.assertNotIn("reasoning_split", payload)
        self.assertEqual(result.scope, ScopeKind.IPAC)
        self.assertEqual(result.intent, IntentKind.READ_TOOL)
        self.assertEqual(result.tool, "resumen_deuda")

    @patch("urllib.request.urlopen")
    def test_accepts_minimax_content_as_text_blocks(self, urlopen):
        urlopen.return_value = FakeResponse(
            {
                "choices": [
                    {
                        "message": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": '{"scope":"ipac","intent":"read_tool","tool":"alumnos_con_deuda","arguments":{}}',
                                }
                            ]
                        }
                    }
                ]
            }
        )

        result = MiniMaxIntentClassifier().classify(
            question="¿quiénes son los alumnos con deuda?",
            history=[
                {
                    "role": "assistant",
                    "content": "Hay 3 alumnos con saldo pendiente.",
                }
            ],
            tool_names=["alumnos_con_deuda"],
            role_context="rol=administracion;sucursal_id=1;acceso_global=no",
        )

        self.assertEqual(result.scope, ScopeKind.IPAC)
        self.assertEqual(result.intent, IntentKind.READ_TOOL)
        self.assertEqual(result.tool, "alumnos_con_deuda")
