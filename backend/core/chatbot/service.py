import json
import logging

from django.conf import settings

from .agent import AgentProviderError, MiniMaxAgentProvider
from .knowledge import format_procedure, knowledge_for_prompt, match_procedure
from .tools import (
    InvalidToolArguments,
    ReadToolRegistry,
    ToolContext,
    ToolForbidden,
    UnknownTool,
)


logger = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 4

SYSTEM_PROMPT = """Sos el Asistente IPAC.
Tu alcance está estrictamente limitado al sistema IPAC y a la documentación/datos que el backend te proporciona.

REGLAS:
- Respondé siempre en español rioplatense, de forma breve y profesional.
- Si el usuario pide datos actuales del sistema, usá las herramientas disponibles. No inventes importes, alumnos, cuotas, saldos ni estados.
- Podés encadenar varias herramientas cuando haga falta para resolver una consulta.
- Usá el historial para comprender referencias y continuaciones de la conversación.
- Nunca amplíes permisos ni sucursales por tu cuenta; el backend valida el alcance real.
- Nunca escribas SQL, nunca pidas credenciales y nunca inventes herramientas.
- Si una herramienta devuelve un error o falta de acceso, explicalo claramente.
- Para preguntas sobre cómo usar IPAC, respondé únicamente a partir de la documentación operativa incluida abajo.
- Para preguntas ajenas a IPAC, respondé exactamente: "Esa consulta está fuera del alcance de este sistema. Puedo ayudarte únicamente con el sistema IPAC."

DOCUMENTACIÓN OPERATIVA DE IPAC:
"""


def _role_context(user):
    profile = getattr(user, "perfil", None)
    if profile is None:
        return "Usuario sin perfil operativo."
    return (
        f"Rol: {profile.rol}. "
        f"Sucursal base: {profile.sucursal.nombre} (id={profile.sucursal_id}). "
        f"Acceso global: {'sí' if profile.puede_ver_todas_las_sucursales else 'no'}."
    )


def _tool_context(user):
    profile = getattr(user, "perfil", None)
    if profile is None:
        raise ToolForbidden("El usuario no tiene perfil operativo.")
    return ToolContext(
        user_id=user.id,
        branch_id=profile.sucursal_id,
        global_access=profile.puede_ver_todas_las_sucursales,
    )


def _assistant_tool_call_message(response):
    return {
        "role": "assistant",
        "content": response.content or "",
        "tool_calls": [
            {
                "id": call["id"],
                "type": "function",
                "function": {
                    "name": call["name"],
                    "arguments": json.dumps(
                        call.get("arguments") or {},
                        ensure_ascii=False,
                    ),
                },
            }
            for call in response.tool_calls
        ],
    }


def _tool_result_message(call, payload):
    return {
        "role": "tool",
        "tool_call_id": call["id"],
        "name": call["name"],
        "content": json.dumps(
            payload,
            ensure_ascii=False,
            default=str,
            separators=(",", ":"),
        ),
    }


def _safe_execute_tool(registry, call, context):
    try:
        result = registry.execute(
            call["name"],
            call.get("arguments") or {},
            context,
        )
        return {"success": True, "result": result}
    except ToolForbidden as exc:
        return {"success": False, "error": str(exc), "code": "forbidden"}
    except (UnknownTool, InvalidToolArguments) as exc:
        return {"success": False, "error": str(exc), "code": "invalid_tool"}
    except Exception as exc:
        logger.exception("Chatbot tool execution failed tool=%s", call.get("name"))
        return {
            "success": False,
            "error": "No se pudo consultar ese dato en este momento.",
            "code": type(exc).__name__,
        }


def _fallback_without_ai(content):
    matched = match_procedure(content)
    if matched:
        key, procedure = matched
        return {
            "content": format_procedure(procedure),
            "tokens_used": None,
            "source": "procedure",
            "procedure": key,
            "action": {
                "label": procedure["action_label"],
                "path": procedure["route"],
            },
        }
    return {
        "content": (
            "La IA está deshabilitada. Puedo responder únicamente los procedimientos "
            "documentados del sistema IPAC."
        ),
        "tokens_used": None,
        "source": "fallback",
        "procedure": None,
        "action": None,
    }


def answer_message(user, content, history):
    if not getattr(settings, "IPAC_AI_ENABLED", False):
        return _fallback_without_ai(content)

    registry = ReadToolRegistry()
    provider = MiniMaxAgentProvider()
    messages = [
        {
            "role": "system",
            "content": (
                SYSTEM_PROMPT
                + "\n"
                + knowledge_for_prompt()
                + "\n\nCONTEXTO DE AUTORIZACIÓN DEL USUARIO:\n"
                + _role_context(user)
            ),
        },
        *[
            {
                "role": item["role"],
                "content": item["content"],
            }
            for item in history
            if item.get("role") in {"user", "assistant"}
            and str(item.get("content") or "").strip()
        ],
        {"role": "user", "content": content},
    ]

    used_tool = False
    tokens_used = 0

    try:
        response = provider.send(messages, registry.schemas())

        for round_number in range(MAX_TOOL_ROUNDS):
            if not response.tool_calls:
                if not response.content:
                    raise AgentProviderError("La IA devolvió una respuesta vacía.")
                if response.tokens_used:
                    tokens_used += response.tokens_used
                return {
                    "content": response.content,
                    "tokens_used": tokens_used or None,
                    "source": "tool" if used_tool else "ai",
                    "procedure": None,
                    "action": None,
                }

            used_tool = True
            if response.tokens_used:
                tokens_used += response.tokens_used

            normalized_calls = []
            for index, call in enumerate(response.tool_calls, start=1):
                normalized_calls.append(
                    {
                        "id": call.get("id") or f"call_{round_number + 1}_{index}",
                        "name": call["name"],
                        "arguments": call.get("arguments") or {},
                    }
                )

            response = type(response)(
                content=response.content,
                tool_calls=normalized_calls,
                tokens_used=response.tokens_used,
            )

            messages.append(_assistant_tool_call_message(response))

            context = _tool_context(user)
            for call in normalized_calls:
                result = _safe_execute_tool(registry, call, context)
                messages.append(_tool_result_message(call, result))

            response = provider.send(messages, registry.schemas())

        raise AgentProviderError("Se alcanzó el límite de pasos de herramientas.")

    except AgentProviderError as exc:
        logger.error("Chatbot AI provider error: %s", exc)
        return {
            "content": (
                "El componente de IA no está disponible en este momento. "
                "Intentá nuevamente en unos instantes."
            ),
            "tokens_used": tokens_used or None,
            "source": "fallback",
            "procedure": None,
            "action": None,
        }
