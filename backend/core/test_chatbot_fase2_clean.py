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
class CleanPlannerContractTests(SimpleTestCase):
    @patch("urllib.request.urlopen")
    def test_planner_uses_generic_tool_catalog_and_working_minimax_contract(self, urlopen):
        urlopen.return_value = FakeResponse(
            {
                "choices": [
                    {
                        "message": {
                            "content": '{"kind":"tool","tool":"resumen_deuda","arguments":{}}'
                        }
                    }
                ]
            }
        )

        from core.chatbot.planner import MiniMaxPlanner

        decision = MiniMaxPlanner().decide(
            question="consulta arbitraria",
            history=[],
            role_context="rol=administracion;sucursal=Posadas;global=no",
        )

        request = urlopen.call_args.args[0]
        payload = json.loads(request.data.decode("utf-8"))
        system = payload["messages"][0]["content"]

        self.assertEqual(payload["model"], "MiniMax-M3")
        self.assertEqual(payload["thinking"], {"type": "disabled"})
        self.assertNotIn("reasoning_split", payload)
        self.assertIn("resumen_deuda", system)
        self.assertIn("alumnos_con_deuda", system)
        self.assertNotIn("Ejemplos de decisión", system)
        self.assertEqual(decision.kind, "tool")
        self.assertEqual(decision.tool, "resumen_deuda")

    @patch("urllib.request.urlopen")
    def test_planner_accepts_content_blocks(self, urlopen):
        urlopen.return_value = FakeResponse(
            {
                "choices": [
                    {
                        "message": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": '{"kind":"tool","tool":"alumnos_con_deuda","arguments":{}}',
                                }
                            ]
                        }
                    }
                ]
            }
        )

        from core.chatbot.planner import MiniMaxPlanner

        decision = MiniMaxPlanner().decide(
            question="seguimiento contextual",
            history=[
                {"role": "assistant", "content": "Hay alumnos con saldo pendiente."},
            ],
            role_context="rol=administracion;sucursal=Posadas;global=no",
        )

        self.assertEqual(decision.kind, "tool")
        self.assertEqual(decision.tool, "alumnos_con_deuda")


class CleanReadToolsTests(TestCase):
    def setUp(self):
        self.posadas = Sucursal.objects.create(codigo="POS-C", nombre="Posadas Clean")
        self.eldorado = Sucursal.objects.create(codigo="ELD-C", nombre="Eldorado Clean")

        self.user = User.objects.create_user(username="clean-admin", password="secret")
        PerfilUsuario.objects.create(
            user=self.user,
            rol=PerfilUsuario.Rol.ADMINISTRACION,
            sucursal=self.posadas,
            puede_ver_todas_las_sucursales=False,
        )
        self.global_user = User.objects.create_user(username="clean-super", password="secret")
        PerfilUsuario.objects.create(
            user=self.global_user,
            rol=PerfilUsuario.Rol.SUPERADMIN,
            sucursal=self.posadas,
            puede_ver_todas_las_sucursales=True,
        )

        concept_pos = ConceptoCobrable.objects.create(
            nombre="Cuota Clean POS",
            tipo=ConceptoCobrable.Tipo.CUOTA,
            importe=Decimal("1000"),
            sucursal=self.posadas,
        )
        concept_eld = ConceptoCobrable.objects.create(
            nombre="Cuota Clean ELD",
            tipo=ConceptoCobrable.Tipo.CUOTA,
            importe=Decimal("500"),
            sucursal=self.eldorado,
        )

        juan = Alumno.objects.create(
            legajo="CL-POS-1",
            nombre="Juan",
            apellido="Perez",
            sucursal=self.posadas,
        )
        ana = Alumno.objects.create(
            legajo="CL-ELD-1",
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

    def test_restricted_user_debt_only_uses_own_branch(self):
        from core.chatbot.tools import ReadToolRegistry

        result = ReadToolRegistry().execute(
            "resumen_deuda",
            {},
            self._context(self.user),
        )

        self.assertEqual(result["scope"], "Posadas Clean")
        self.assertEqual(result["deuda_total"], Decimal("700.00"))
        self.assertEqual(result["alumnos_con_deuda"], 1)

    def test_global_user_can_list_all_debtors(self):
        from core.chatbot.tools import ReadToolRegistry

        result = ReadToolRegistry().execute(
            "alumnos_con_deuda",
            {},
            self._context(self.global_user),
        )

        self.assertEqual(result["scope"], "Todas las sucursales")
        self.assertEqual(result["total_alumnos"], 2)
        self.assertEqual(result["deuda_total"], Decimal("1200.00"))
        self.assertEqual(
            [(row["legajo"], row["deuda_total"]) for row in result["alumnos"]],
            [
                ("CL-POS-1", Decimal("700.00")),
                ("CL-ELD-1", Decimal("500.00")),
            ],
        )

    def test_restricted_user_cannot_expand_scope_by_argument(self):
        from core.chatbot.tools import ReadToolRegistry, ToolForbidden

        with self.assertRaises(ToolForbidden):
            ReadToolRegistry().execute(
                "resumen_deuda",
                {"sucursal": "Eldorado Clean"},
                self._context(self.user),
            )
