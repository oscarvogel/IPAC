from decimal import Decimal

from django.conf import settings

from core.models import AsistenteConsultaNoResuelta

from .matching import format_article, normalize_text
from .no_resueltas import RegistrarNoResuelta
from .tools import InvalidToolArguments, UnknownTool
from ..domain.models import AssistantResponse, Classification, IntentKind, ScopeKind, ToolContext
from ..infrastructure.minimax_provider import AIProviderError


OUT_OF_SCOPE_MESSAGE = (
    "Mi función está limitada al sistema IPAC. No puedo responder consultas generales "
    "sobre salud, noticias u otros temas."
)
UNKNOWN_MESSAGE = (
    "No tengo información suficiente para responder esa consulta de forma confiable. "
    "La registré para que pueda incorporarse a mi base de conocimiento."
)
UNCERTAIN_MESSAGE = (
    "No pude determinar con suficiente seguridad qué necesitás dentro de IPAC. "
    "Reformulá la consulta indicando el módulo, alumno, caja o dato que querés consultar. "
    "La registré para revisión."
)
AI_ERROR_MESSAGE = (
    "No pude interpretar esa consulta en este momento. La registré para revisión. "
    "Las consultas conocidas del sistema siguen disponibles."
)
FORBIDDEN_MESSAGE = (
    "Esa consulta requiere información de una sucursal a la que tu usuario no tiene acceso."
)
NO_DATA_MESSAGE = (
    "No hay datos disponibles para responder esa consulta con el alcance o período indicado."
)


def _money(value):
    value = Decimal(str(value or 0)).quantize(Decimal("0.01"))
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _role_context(user):
    profile = getattr(user, "perfil", None)
    if profile is None:
        return "Usuario sin perfil operativo."
    return (
        f"rol={profile.rol}; "
        f"sucursal_id={profile.sucursal_id}; "
        f"acceso_global={'si' if profile.puede_ver_todas_las_sucursales else 'no'}"
    )


def _tool_context(user):
    profile = getattr(user, "perfil", None)
    if profile is None:
        raise ValueError("El usuario no tiene perfil operativo.")
    return ToolContext(
        user_id=user.id,
        role=profile.rol,
        sucursal_id=profile.sucursal_id,
        global_access=profile.puede_ver_todas_las_sucursales,
    )


def _format_tool(name, result):
    data = result.data
    suffix = f"\n\nAlcance: {result.scope_label}. Datos al {result.as_of}."

    if name == "resumen_deuda":
        return (
            f"La deuda pendiente es de $ {_money(data['deuda_total'])}. "
            f"De ese total, $ {_money(data['deuda_vencida'])} está vencido. "
            f"Hay {data['alumnos_con_deuda']} alumno(s) con saldo pendiente, "
            f"{data['cuotas_pendientes']} cuota(s) pendientes y "
            f"{data['cuotas_vencidas']} vencida(s)."
            + suffix
        )
    if name == "alumnos_con_deuda":
        rows = data.get("alumnos") or []
        lines = [
            f"Hay {data['total_alumnos']} alumno(s) con saldo pendiente por "
            f"$ {_money(data['deuda_total'])}:"
        ]
        for row in rows:
            line = (
                f"- {row['nombre']} — Legajo {row['legajo']} — {row['sucursal']} — "
                f"$ {_money(row['deuda_total'])} pendientes"
            )
            if Decimal(str(row.get("deuda_vencida") or 0)) > 0:
                line += f" — $ {_money(row['deuda_vencida'])} vencidos"
            lines.append(line)
        if data.get("truncated"):
            lines.append(
                f"Mostrando {len(rows)} de {data['total_alumnos']} alumno(s). "
                "Podés pedirme que acote la consulta por sucursal."
            )
        return "\n".join(lines) + suffix
    if name == "estado_cuenta_alumno":
        student = data["alumno"]
        return (
            f"{student['nombre']} (legajo {student['legajo']}) tiene una deuda pendiente "
            f"de $ {_money(data['deuda_total'])}, de la cual $ {_money(data['deuda_vencida'])} "
            f"está vencida. Saldo a favor: $ {_money(data['saldo_a_favor'])}. "
            f"Cuotas pendientes: {data['cuotas_pendientes']}; vencidas: {data['cuotas_vencidas']}."
            + suffix
        )
    if name == "resumen_cobranzas":
        breakdown = ", ".join(
            f"{key}: $ {_money(value)}"
            for key, value in data["por_medio"].items()
            if Decimal(str(value or 0)) != 0
        )
        extra = f" Por medio: {breakdown}." if breakdown else ""
        return (
            f"Se registraron {data['cantidad_pagos']} pago(s) por un total de "
            f"$ {_money(data['total_cobrado'])} entre {data['desde']} y {data['hasta']}."
            + extra
            + suffix
        )
    if name == "caja_hoy":
        return (
            f"La caja está {data['estado']}. Saldo inicial: $ {_money(data['saldo_inicial'])}; "
            f"efectivo esperado: $ {_money(data['efectivo_esperado'])}; "
            f"total contado: $ {_money(data['total_contado'])}; "
            f"diferencia: $ {_money(data['diferencia'])}."
            + suffix
        )
    if name == "resumen_cuotas":
        return (
            f"Hay {data['cantidad']} cuota(s) en el filtro consultado; "
            f"{data['con_saldo']} tienen saldo, por $ {_money(data['saldo_pendiente'])}."
            + suffix
        )
    if name == "resumen_alumnos":
        return f"Hay {data['cantidad']} alumno(s) en el filtro consultado." + suffix
    if name == "buscar_alumno":
        candidates = data.get("candidates") or []
        if len(candidates) == 1:
            student = candidates[0]
            return (
                f"Encontré a {student['nombre']}, legajo {student['legajo']}, "
                f"sucursal {student['sucursal']}."
                + suffix
            )
    return "Consulta realizada correctamente." + suffix


class ResponderConsulta:
    def __init__(
        self,
        *,
        knowledge_repository,
        classifier,
        tool_registry,
        assistant_repository,
        notifier=None,
    ):
        self.knowledge_repository = knowledge_repository
        self.classifier = classifier
        self.tool_registry = tool_registry
        self.assistant_repository = assistant_repository
        self.notifier = notifier

    def _record(
        self,
        *,
        user,
        content,
        category,
        response,
        conversation,
        user_message,
        intent="",
        tool="",
        metadata=None,
    ):
        return RegistrarNoResuelta(
            self.assistant_repository,
            self.notifier,
        ).execute(
            user=user,
            question=content,
            category=category,
            response=response,
            conversation=conversation,
            user_message=user_message,
            intent=intent,
            tool=tool,
            metadata=metadata,
        )

    def execute(self, user, content, history, conversation=None, user_message=None, selected_alumno_id=None):
        profile = getattr(user, "perfil", None)
        if profile is None:
            return AssistantResponse(
                content="Tu usuario no tiene un perfil operativo configurado.",
                source="fallback",
            )

        if selected_alumno_id:
            classification = Classification(
                ScopeKind.IPAC,
                IntentKind.READ_TOOL,
                "estado_cuenta_alumno",
                {"alumno_id": selected_alumno_id},
            )
        elif getattr(settings, "IPAC_AI_ENABLED", False):
            try:
                classification = self.classifier.classify(
                    question=content,
                    history=history,
                    tool_names=self.tool_registry.names,
                    role_context=_role_context(user),
                )
            except AIProviderError:
                self._record(
                    user=user,
                    content=content,
                    category=AsistenteConsultaNoResuelta.Categoria.ERROR_IA,
                    response=AI_ERROR_MESSAGE,
                    conversation=conversation,
                    user_message=user_message,
                )
                return AssistantResponse(content=AI_ERROR_MESSAGE, source="unresolved")
        else:
            article = self.knowledge_repository.find_match(content, profile.rol)
            if article:
                return AssistantResponse(
                    content=format_article(article),
                    source="procedure",
                    procedure=article.key,
                    action=(
                        {"label": article.action_label, "path": article.route}
                        if article.route and article.action_label
                        else None
                    ),
                )
            return AssistantResponse(
                content=(
                    "El componente de IA no está disponible en este momento. "
                    "Puedo seguir respondiendo los procedimientos conocidos del sistema IPAC."
                ),
                source="fallback",
            )

        if classification.scope == ScopeKind.OUT_OF_SCOPE:
            self._record(
                user=user,
                content=content,
                category=AsistenteConsultaNoResuelta.Categoria.FUERA_DE_ALCANCE,
                response=OUT_OF_SCOPE_MESSAGE,
                conversation=conversation,
                user_message=user_message,
            )
            return AssistantResponse(content=OUT_OF_SCOPE_MESSAGE, source="out_of_scope")

        if classification.scope == ScopeKind.UNCERTAIN:
            self._record(
                user=user,
                content=content,
                category=AsistenteConsultaNoResuelta.Categoria.NO_DOCUMENTADA,
                response=UNCERTAIN_MESSAGE,
                conversation=conversation,
                user_message=user_message,
            )
            return AssistantResponse(content=UNCERTAIN_MESSAGE, source="unresolved")

        if classification.intent == IntentKind.KNOWLEDGE:
            article = self.knowledge_repository.find_match(content, profile.rol)
            if article:
                return AssistantResponse(
                    content=format_article(article),
                    source="procedure",
                    procedure=article.key,
                    action=(
                        {"label": article.action_label, "path": article.route}
                        if article.route and article.action_label
                        else None
                    ),
                )
            self._record(
                user=user,
                content=content,
                category=AsistenteConsultaNoResuelta.Categoria.NO_DOCUMENTADA,
                response=UNKNOWN_MESSAGE,
                conversation=conversation,
                user_message=user_message,
                intent=classification.intent.value,
            )
            return AssistantResponse(content=UNKNOWN_MESSAGE, source="unresolved")

        if classification.intent == IntentKind.READ_TOOL and classification.tool:
            try:
                result = self.tool_registry.execute(
                    classification.tool,
                    classification.arguments,
                    _tool_context(user),
                )
            except (UnknownTool, InvalidToolArguments, AttributeError):
                self._record(
                    user=user,
                    content=content,
                    category=AsistenteConsultaNoResuelta.Categoria.NO_DOCUMENTADA,
                    response=UNKNOWN_MESSAGE,
                    conversation=conversation,
                    user_message=user_message,
                    intent=classification.intent.value,
                    tool=classification.tool or "",
                )
                return AssistantResponse(content=UNKNOWN_MESSAGE, source="unresolved")
            except Exception as exc:
                message = (
                    "No pude obtener ese dato de IPAC en este momento. "
                    "La consulta quedó registrada para revisión."
                )
                self._record(
                    user=user,
                    content=content,
                    category=AsistenteConsultaNoResuelta.Categoria.ERROR_HERRAMIENTA,
                    response=message,
                    conversation=conversation,
                    user_message=user_message,
                    intent=classification.intent.value,
                    tool=classification.tool,
                    metadata={"error_type": type(exc).__name__},
                )
                return AssistantResponse(content=message, source="unresolved")

            if result.status == "ambiguous":
                return AssistantResponse(
                    content="Encontré más de un alumno que coincide. Elegí cuál querés consultar.",
                    source="tool",
                    clarification={"candidates": result.data.get("candidates", [])},
                )
            if result.status == "forbidden":
                self._record(
                    user=user,
                    content=content,
                    category=AsistenteConsultaNoResuelta.Categoria.SIN_PERMISO,
                    response=FORBIDDEN_MESSAGE,
                    conversation=conversation,
                    user_message=user_message,
                    tool=classification.tool,
                )
                return AssistantResponse(content=FORBIDDEN_MESSAGE, source="unresolved")
            if result.status == "no_data":
                self._record(
                    user=user,
                    content=content,
                    category=AsistenteConsultaNoResuelta.Categoria.SIN_DATOS,
                    response=NO_DATA_MESSAGE,
                    conversation=conversation,
                    user_message=user_message,
                    tool=classification.tool,
                )
                return AssistantResponse(content=NO_DATA_MESSAGE, source="unresolved")
            if result.status != "ok":
                self._record(
                    user=user,
                    content=content,
                    category=AsistenteConsultaNoResuelta.Categoria.NO_DOCUMENTADA,
                    response=UNKNOWN_MESSAGE,
                    conversation=conversation,
                    user_message=user_message,
                    tool=classification.tool,
                )
                return AssistantResponse(content=UNKNOWN_MESSAGE, source="unresolved")

            return AssistantResponse(
                content=_format_tool(classification.tool, result),
                source="tool",
            )

        self._record(
            user=user,
            content=content,
            category=AsistenteConsultaNoResuelta.Categoria.NO_DOCUMENTADA,
            response=UNKNOWN_MESSAGE,
            conversation=conversation,
            user_message=user_message,
            intent=classification.intent.value,
        )
        return AssistantResponse(content=UNKNOWN_MESSAGE, source="unresolved")
