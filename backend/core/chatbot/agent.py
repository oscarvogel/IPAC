import json
import logging
import re
import urllib.error
import urllib.request
from dataclasses import dataclass

from django.conf import settings


logger = logging.getLogger(__name__)


class AgentProviderError(RuntimeError):
    pass


@dataclass(frozen=True)
class AgentResponse:
    content: str
    tool_calls: list[dict]
    tokens_used: int | None = None


def _content_text(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("text"):
                parts.append(str(block["text"]))
        return "\n".join(parts)
    return str(content or "")


def _clean_content(content):
    return re.sub(
        r"<think>.*?</think>",
        "",
        _content_text(content),
        flags=re.IGNORECASE | re.DOTALL,
    ).strip()


def _parse_tool_calls(message):
    calls = []
    for item in message.get("tool_calls") or []:
        function = item.get("function") or {}
        name = str(function.get("name") or "").strip()
        raw_args = function.get("arguments", "{}")
        if isinstance(raw_args, dict):
            arguments = raw_args
        else:
            try:
                arguments = json.loads(str(raw_args or "{}"))
            except json.JSONDecodeError as exc:
                raise AgentProviderError(
                    f"La IA devolvió argumentos inválidos para la herramienta {name or '(sin nombre)'}."
                ) from exc
        if not name or not isinstance(arguments, dict):
            raise AgentProviderError("La IA devolvió una llamada de herramienta inválida.")
        calls.append(
            {
                "id": str(item.get("id") or ""),
                "name": name,
                "arguments": arguments,
            }
        )
    return calls


class MiniMaxAgentProvider:
    def send(self, messages, tools):
        api_key = getattr(settings, "IPAC_AI_API_KEY", "").strip()
        model = getattr(settings, "IPAC_AI_MODEL", "").strip()
        url = getattr(settings, "IPAC_AI_BASE_URL", "").strip()
        timeout = getattr(settings, "IPAC_AI_TIMEOUT_SECONDS", 30)

        if not api_key or not model or not url:
            raise AgentProviderError("El proveedor IA no está configurado.")

        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 2048,
            "stream": False,
        }
        if tools:
            payload["tools"] = tools

        request = urllib.request.Request(
            url,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            method="POST",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )

        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            body = ""
            try:
                body = exc.read().decode("utf-8", errors="replace")[:1200]
            except Exception:
                pass
            logger.error(
                "MiniMax agent HTTP error status=%s body=%s",
                exc.code,
                body,
            )
            raise AgentProviderError(f"Error HTTP {exc.code} del proveedor IA.") from exc
        except urllib.error.URLError as exc:
            logger.error(
                "MiniMax agent network error type=%s",
                type(exc.reason).__name__,
            )
            raise AgentProviderError("No se pudo conectar con el proveedor IA.") from exc

        try:
            data = json.loads(raw)
            message = (data.get("choices") or [])[0].get("message") or {}
        except (json.JSONDecodeError, IndexError, AttributeError) as exc:
            logger.error("MiniMax agent invalid response body=%s", raw[:1200])
            raise AgentProviderError("El proveedor IA devolvió una respuesta inválida.") from exc

        return AgentResponse(
            content=_clean_content(message.get("content")),
            tool_calls=_parse_tool_calls(message),
            tokens_used=(data.get("usage") or {}).get("total_tokens"),
        )
