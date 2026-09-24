from django.contrib.auth.models import User
from decimal import Decimal

from django.test import TestCase, override_settings

from core.models import (
    AsistenteConsultaNoResuelta,
    AsistenteKnowledgeArticle,
    ChatbotConversation,
    ChatbotMessage,
    PerfilUsuario,
    Sucursal,
)
from core.contexts.asistente.domain.models import (
    Classification,
    IntentKind,
    ScopeKind,
    ToolResult,
)


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



class FakeClassifier:
    def __init__(self, classification):
        self.classification = classification
        self.calls = []

    def classify(self, *, question, history, tool_names, role_context):
        self.calls.append(
            {
                "question": question,
                "history": history,
                "tool_names": tuple(tool_names),
                "role_context": role_context,
            }
        )
        return self.classification


class FakeToolRegistry:
    names = (
        "resumen_deuda",
        "alumnos_con_deuda",
        "estado_cuenta_alumno",
        "resumen_cobranzas",
        "caja_hoy",
        "resumen_cuotas",
        "resumen_alumnos",
        "buscar_alumno",
    )

    def __init__(self, result=None):
        self.result = result or ToolResult(
            status="ok",
            data={
                "deuda_total": Decimal("700.00"),
                "deuda_vencida": Decimal("500.00"),
                "alumnos_con_deuda": 2,
                "cuotas_pendientes": 3,
                "cuotas_vencidas": 2,
            },
            scope_label="Knowledge",
            as_of="2026-09-24",
        )
        self.calls = []

    def execute(self, name, arguments, context):
        self.calls.append((name, arguments, context))
        from core.contexts.asistente.application.tools import TOOL_SPECS, UnknownTool
        if name not in TOOL_SPECS:
            raise UnknownTool(name)
        return self.result


class FakeNotifier:
    def __init__(self):
        self.event_ids = []

    def notify_immediate(self, event_id):
        self.event_ids.append(event_id)
        return True


@override_settings(IPAC_AI_ENABLED=True, IPAC_AI_API_KEY="test", IPAC_AI_MODEL="MiniMax-M3")
class AssistantResponderTests(TestCase):
    def setUp(self):
        self.branch = Sucursal.objects.create(codigo="ORCH", nombre="Orchestrator")
        self.user = User.objects.create_user(username="orchestrator", password="secret")
        PerfilUsuario.objects.create(
            user=self.user,
            rol=PerfilUsuario.Rol.ADMINISTRACION,
            sucursal=self.branch,
        )
        self.conversation = ChatbotConversation.objects.create(
            usuario=self.user,
            sucursal=self.branch,
            titulo="Prueba",
        )
        self.user_message = ChatbotMessage.objects.create(
            conversacion=self.conversation,
            role=ChatbotMessage.Role.USER,
            content="mensaje",
        )

    def _make_responder(self, classifier, tool_registry=None):
        try:
            from core.contexts.asistente.application.responder_consulta import ResponderConsulta
            from core.contexts.asistente.infrastructure.django_assistant_repository import (
                DjangoAssistantRepository,
            )
            from core.contexts.asistente.infrastructure.django_knowledge_repository import (
                DjangoKnowledgeRepository,
            )
        except ImportError as exc:
            self.fail(f"Debe existir el orquestador del asistente: {exc}")

        return ResponderConsulta(
            knowledge_repository=DjangoKnowledgeRepository(),
            classifier=classifier,
            tool_registry=tool_registry or FakeToolRegistry(),
            assistant_repository=DjangoAssistantRepository(),
            notifier=FakeNotifier(),
        )

    def test_out_of_scope_question_is_rejected_without_general_answer(self):
        classifier = FakeClassifier(
            Classification(ScopeKind.OUT_OF_SCOPE, IntentKind.UNKNOWN)
        )
        result = self._make_responder(classifier).execute(
            self.user,
            "¿Cómo se cura la gripe?",
            [],
            self.conversation,
            self.user_message,
        )
        self.assertEqual(result.source, "out_of_scope")
        self.assertEqual(
            result.content,
            "Mi función está limitada al sistema IPAC. No puedo responder consultas generales sobre salud, noticias u otros temas.",
        )
        self.assertEqual(
            AsistenteConsultaNoResuelta.objects.get().categoria,
            AsistenteConsultaNoResuelta.Categoria.FUERA_DE_ALCANCE,
        )

    def test_uncertain_never_falls_back_to_general_knowledge(self):
        classifier = FakeClassifier(
            Classification(ScopeKind.UNCERTAIN, IntentKind.UNKNOWN)
        )
        result = self._make_responder(classifier).execute(
            self.user,
            "¿Podés decirme algo de eso?",
            [],
            self.conversation,
            self.user_message,
        )
        self.assertEqual(result.source, "unresolved")
        self.assertIn("reformul", result.content.lower())

    def test_total_debt_question_executes_allowed_tool(self):
        classifier = FakeClassifier(
            Classification(
                ScopeKind.IPAC,
                IntentKind.READ_TOOL,
                "resumen_deuda",
                {},
            )
        )
        tools = FakeToolRegistry()
        result = self._make_responder(classifier, tools).execute(
            self.user,
            "¿cuánto es la deuda total?",
            [],
            self.conversation,
            self.user_message,
        )
        self.assertEqual(result.source, "tool")
        self.assertEqual(tools.calls[0][0], "resumen_deuda")
        self.assertIn("Alcance: Knowledge", result.content)
        self.assertIn("700", result.content)

    def test_ai_tool_decision_has_priority_over_procedural_match(self):
        classifier = FakeClassifier(
            Classification(
                ScopeKind.IPAC,
                IntentKind.READ_TOOL,
                "alumnos_con_deuda",
                {},
            )
        )
        tools = FakeToolRegistry(
            ToolResult(
                status="ok",
                data={
                    "total_alumnos": 2,
                    "deuda_total": Decimal("1200.00"),
                    "alumnos": [
                        {
                            "id": 1,
                            "nombre": "Perez, Juan",
                            "legajo": "P-1",
                            "sucursal": "Posadas",
                            "deuda_total": Decimal("700.00"),
                            "deuda_vencida": Decimal("500.00"),
                        },
                        {
                            "id": 2,
                            "nombre": "Gomez, Ana",
                            "legajo": "E-2",
                            "sucursal": "Eldorado",
                            "deuda_total": Decimal("500.00"),
                            "deuda_vencida": Decimal("500.00"),
                        },
                    ],
                    "truncated": False,
                },
                scope_label="Todas las sucursales",
                as_of="2026-09-24",
            )
        )

        result = self._make_responder(classifier, tools).execute(
            self.user,
            "¿cuáles son los alumnos con saldo pendiente?",
            [],
            self.conversation,
            self.user_message,
        )

        self.assertEqual(result.source, "tool")
        self.assertEqual(classifier.calls[0]["question"], "¿cuáles son los alumnos con saldo pendiente?")
        self.assertEqual(tools.calls[0][0], "alumnos_con_deuda")
        self.assertIn("Perez, Juan", result.content)
        self.assertNotIn("Entrá a Alumnos", result.content)

    def test_follow_up_history_is_given_to_ai_planner(self):
        classifier = FakeClassifier(
            Classification(
                ScopeKind.IPAC,
                IntentKind.READ_TOOL,
                "alumnos_con_deuda",
                {},
            )
        )
        tools = FakeToolRegistry(
            ToolResult(
                status="ok",
                data={
                    "total_alumnos": 1,
                    "deuda_total": Decimal("700.00"),
                    "alumnos": [
                        {
                            "id": 1,
                            "nombre": "Perez, Juan",
                            "legajo": "P-1",
                            "sucursal": "Posadas",
                            "deuda_total": Decimal("700.00"),
                            "deuda_vencida": Decimal("500.00"),
                        },
                    ],
                    "truncated": False,
                },
                scope_label="Posadas",
                as_of="2026-09-24",
            )
        )
        history = [
            {"role": "user", "content": "¿cuánto es la deuda total?"},
            {
                "role": "assistant",
                "content": "La deuda pendiente es de $ 700,00. Hay 1 alumno con saldo pendiente.",
            },
        ]

        result = self._make_responder(classifier, tools).execute(
            self.user,
            "sí, pero quiero saber quiénes son esos alumnos",
            history,
            self.conversation,
            self.user_message,
        )

        self.assertEqual(result.source, "tool")
        self.assertEqual(classifier.calls[0]["history"], history)
        self.assertEqual(tools.calls[0][0], "alumnos_con_deuda")
        self.assertIn("Perez, Juan", result.content)

    def test_unknown_ipac_question_is_recorded(self):
        classifier = FakeClassifier(
            Classification(ScopeKind.IPAC, IntentKind.UNKNOWN)
        )
        result = self._make_responder(classifier).execute(
            self.user,
            "¿Cómo refinancio una cuota?",
            [],
            self.conversation,
            self.user_message,
        )
        event = AsistenteConsultaNoResuelta.objects.get()
        self.assertEqual(event.pregunta, "¿Cómo refinancio una cuota?")
        self.assertEqual(event.categoria, "no_documentada")
        self.assertEqual(result.source, "unresolved")
