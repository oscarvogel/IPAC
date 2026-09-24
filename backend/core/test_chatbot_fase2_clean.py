import json
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import timezone

from core.models import (
    Alumno,
    AplicacionPago,
    ConceptoCobrable,
    Cuota,
    Pago,
    PerfilUsuario,
    Sucursal,
)


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
class NativeMiniMaxProviderTests(SimpleTestCase):
    @patch("urllib.request.urlopen")
    def test_provider_sends_openai_style_tools_and_parses_tool_calls(self, urlopen):
        urlopen.return_value = FakeResponse(
            {
                "choices": [
                    {
                        "message": {
                            "content": "",
                            "tool_calls": [
                                {
                                    "id": "call_1",
                                    "type": "function",
                                    "function": {
                                        "name": "resumen_deuda",
                                        "arguments": "{}",
                                    },
                                }
                            ],
                        }
                    }
                ],
                "usage": {"total_tokens": 123},
            }
        )

        from core.chatbot.agent import MiniMaxAgentProvider
        from core.chatbot.tools import ReadToolRegistry

        response = MiniMaxAgentProvider().send(
            [{"role": "user", "content": "consulta"}],
            ReadToolRegistry().schemas(),
        )

        request = urlopen.call_args.args[0]
        payload = json.loads(request.data.decode("utf-8"))

        self.assertEqual(payload["model"], "MiniMax-M3")
        self.assertIn("tools", payload)
        self.assertEqual(payload["tools"][0]["type"], "function")
        self.assertIn(
            payload["tools"][0]["function"]["name"],
            {"resumen_deuda", "alumnos_con_deuda"},
        )
        self.assertEqual(response.tool_calls[0]["name"], "resumen_deuda")
        self.assertEqual(response.tool_calls[0]["arguments"], {})
        self.assertEqual(response.tokens_used, 123)

    @patch("urllib.request.urlopen")
    def test_provider_accepts_content_blocks(self, urlopen):
        urlopen.return_value = FakeResponse(
            {
                "choices": [
                    {
                        "message": {
                            "content": [
                                {"type": "text", "text": "Respuesta final"},
                            ]
                        }
                    }
                ]
            }
        )

        from core.chatbot.agent import MiniMaxAgentProvider

        response = MiniMaxAgentProvider().send(
            [{"role": "user", "content": "consulta"}],
            [],
        )

        self.assertEqual(response.content, "Respuesta final")
        self.assertEqual(response.tool_calls, [])


class NativeReadToolsTests(TestCase):
    def setUp(self):
        self.posadas = Sucursal.objects.create(codigo="POS-N", nombre="Posadas Native")
        self.eldorado = Sucursal.objects.create(codigo="ELD-N", nombre="Eldorado Native")

        self.user = User.objects.create_user(username="native-admin", password="secret")
        PerfilUsuario.objects.create(
            user=self.user,
            rol=PerfilUsuario.Rol.ADMINISTRACION,
            sucursal=self.posadas,
            puede_ver_todas_las_sucursales=False,
        )
        self.global_user = User.objects.create_user(username="native-super", password="secret")
        PerfilUsuario.objects.create(
            user=self.global_user,
            rol=PerfilUsuario.Rol.SUPERADMIN,
            sucursal=self.posadas,
            puede_ver_todas_las_sucursales=True,
        )

        concept_pos = ConceptoCobrable.objects.create(
            nombre="Cuota Native POS",
            tipo=ConceptoCobrable.Tipo.CUOTA,
            importe=Decimal("1000"),
            sucursal=self.posadas,
        )
        concept_eld = ConceptoCobrable.objects.create(
            nombre="Cuota Native ELD",
            tipo=ConceptoCobrable.Tipo.CUOTA,
            importe=Decimal("500"),
            sucursal=self.eldorado,
        )
        juan = Alumno.objects.create(
            legajo="N-POS-1",
            nombre="Juan",
            apellido="Perez",
            sucursal=self.posadas,
        )
        ana = Alumno.objects.create(
            legajo="N-ELD-1",
            nombre="Ana",
            apellido="Gomez",
            sucursal=self.eldorado,
        )
        today = timezone.localdate()
        cuota_pos = Cuota.objects.create(
            alumno=juan,
            concepto=concept_pos,
            sucursal=self.posadas,
            periodo="2026-09",
            fecha_emision=today,
            fecha_vencimiento=today,
            importe=Decimal("1000"),
            descuento=Decimal("100"),
        )
        Cuota.objects.create(
            alumno=ana,
            concepto=concept_eld,
            sucursal=self.eldorado,
            periodo="2026-09",
            fecha_emision=today,
            fecha_vencimiento=today,
            importe=Decimal("500"),
        )
        pago = Pago.objects.create(
            alumno=juan,
            sucursal=self.posadas,
            importe=Decimal("200"),
            medio=Pago.Medio.EFECTIVO,
        )
        AplicacionPago.objects.create(
            pago=pago,
            cuota=cuota_pos,
            importe=Decimal("200"),
            activa=True,
        )

    def _context(self, user):
        from core.chatbot.tools import ToolContext

        profile = user.perfil
        return ToolContext(
            user_id=user.id,
            branch_id=profile.sucursal_id,
            global_access=profile.puede_ver_todas_las_sucursales,
        )

    def test_tools_remain_server_side_scoped(self):
        from core.chatbot.tools import ReadToolRegistry, ToolForbidden

        registry = ReadToolRegistry()
        own = registry.execute("resumen_deuda", {}, self._context(self.user))
        self.assertEqual(own["deuda_total"], Decimal("700.00"))

        with self.assertRaises(ToolForbidden):
            registry.execute(
                "resumen_deuda",
                {"sucursal": "Eldorado Native"},
                self._context(self.user),
            )

    def test_global_debtors_are_sorted_by_debt(self):
        from core.chatbot.tools import ReadToolRegistry

        result = ReadToolRegistry().execute(
            "alumnos_con_deuda",
            {},
            self._context(self.global_user),
        )

        self.assertEqual(result["deuda_total"], Decimal("1200.00"))
        self.assertEqual(
            [row["legajo"] for row in result["alumnos"]],
            ["N-POS-1", "N-ELD-1"],
        )
