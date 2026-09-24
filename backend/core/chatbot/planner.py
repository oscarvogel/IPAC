import json
import logging
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass

from django.conf import settings

from .tools import TOOL_CATALOG


logger = logging.getLogger(__name__)


class PlannerError(RuntimeError):
    pass


@dataclass(frozen=True)
class PlannerDecision:
    kind: str
    tool: str | None = None
    arguments: dict | None = None


SYSTEM_PROMPT = """Sos el planner del Asistente IPAC.

Tu función es elegir UNA acción para atender el mensaje actual usando el historial de la conversación y las capacidades disponibles.

Acciones válidas:
- knowledge: el usuario necesita orientación sobre cómo usar el sistema o un procedimiento.
- tool: la respuesta requiere datos actuales del sistema y debe obtenerse con una herramienta.
- out_of_scope: la consulta no pertenece al sistema IPAC.
- unknown: la consulta pertenece a IPAC pero no puede resolverse con las capacidades disponibles.

Reglas:
- No respondas la pregunta del usuario.
- No inventes herramientas, parámetros, datos ni permisos.
- Usá el historial para comprender referencias y continuaciones.
- El historial no es fuente de verdad para datos actuales: cuando hagan falta datos reales elegí una herramienta.
- No escribas SQL ni solicites ejecutar código.
- Devolvé exclusivamente un objeto JSON válido con este esquema:
  {"kind":"knowledge|tool|out_of_scope|unknown","tool":null|string,"arguments":{}}
"""


def _response_content(payload):
    try:
        content = payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise PlannerError("El proveedor IA devolvió un formato no compatible.") from exc

    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("text"):
                parts.append(str(block["text"]))
        return "\n".join(parts)
    return str(content or "")


def _parse_json(text):
    cleaned = re.sub(
        r"<think>.*?</think>",
        "",
        text or "",
        flags=re.I | re.S,
    ).strip()
    cleaned = re.sub(r"^\s*\x60\x60\x60(?:json)?\s*", "", cleaned, flags=re.I)
    cleaned = re.sub(r"\s*\x60\x60\x60\s*$", "", cleaned)

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start < 0 or end < start:
        raise PlannerError("La IA no devolvió JSON reconocible.")
    try:
        value = json.loads(cleaned[start : end + 1])
    except json.JSONDecodeError as exc:
        raise PlannerError("La IA devolvió JSON inválido.") from exc
    if not isinstance(value, dict):
        raise PlannerError("La decisión IA no es un objeto.")
    return value


def _catalog_for_prompt():
    return json.dumps(
        {
            name: {
                "description": spec["description"],
                "arguments": spec["arguments"],
            }
            for name, spec in TOOL_CATALOG.items()
        },
        ensure_ascii=False,
        sort_keys=True,
    )


def _validate_decision(payload):
    kind = payload.get("kind")
    if kind not in {"knowledge", "tool", "out_of_scope", "unknown"}:
        raise PlannerError("La IA devolvió una acción no permitida.")

    tool = payload.get("tool")
    arguments = payload.get("arguments") or {}
    if not isinstance(arguments, dict):
        raise PlannerError("Los argumentos de la IA no son válidos.")

    if kind == "tool":
        if tool not in TOOL_CATALOG:
            raise PlannerError("La IA eligió una herramienta no permitida.")
    else:
        tool = None
        arguments = {}

    return PlannerDecision(kind=kind, tool=tool, arguments=arguments)


class MiniMaxPlanner:
    def decide(self, *, question, history, role_context):
        api_key = getattr(settings, "IPAC_AI_API_KEY", "").strip()
        model = getattr(settings, "IPAC_AI_MODEL", "").strip()
        url = getattr(settings, "IPAC_AI_BASE_URL", "").strip()
        timeout = getattr(settings, "IPAC_AI_TIMEOUT_SECONDS", 30)

        if not api_key or not model or not url:
            raise PlannerError("El proveedor IA no está configurado.")

        recent = [
            {
                "role": item.get("role"),
                "content": str(item.get("content") or "")[:1600],
            }
            for item in history[-10:]
            if item.get("role") in {"user", "assistant"}
            and str(item.get("content") or "").strip()
        ]
        messages = [
            {
                "role": "system",
                "content": (
                    SYSTEM_PROMPT
                    + "\n\nContexto de autorización:\n"
                    + role_context
                    + "\n\nCatálogo de herramientas disponibles:\n"
                    + _catalog_for_prompt()
                ),
            },
            *recent,
            {"role": "user", "content": question},
        ]
        payload = {
            "model": model,
            "thinking": {"type": "disabled"},
            "temperature": 0,
            "max_completion_tokens": 600,
            "messages": messages,
        }

        last_error = None
        for attempt in range(1, 4):
            request = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                method="POST",
            )
            try:
                with urllib.request.urlopen(request, timeout=timeout) as response:
                    raw = response.read().decode("utf-8")
                provider_payload = json.loads(raw)
                return _validate_decision(
                    _parse_json(_response_content(provider_payload))
                )
            except urllib.error.HTTPError as exc:
                last_error = exc
                if exc.code in {429, 500, 502, 503, 504} and attempt < 3:
                    time.sleep(float(attempt))
                    continue
                logger.warning("MiniMax planner HTTP error status=%s", exc.code)
                break
            except urllib.error.URLError as exc:
                last_error = exc
                if attempt < 3:
                    time.sleep(float(attempt))
                    continue
                logger.warning(
                    "MiniMax planner network error type=%s",
                    type(exc.reason).__name__,
                )
            except (json.JSONDecodeError, PlannerError) as exc:
                last_error = exc
                if attempt < 2:
                    time.sleep(0.2)
                    continue
                logger.warning(
                    "MiniMax planner invalid response error=%s",
                    type(exc).__name__,
                )
                break

        raise PlannerError("No se pudo obtener una decisión válida de la IA.") from last_error
