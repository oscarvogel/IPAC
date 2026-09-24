import json
import re
import urllib.error
import urllib.request

from django.conf import settings

from .knowledge import format_procedure, knowledge_for_prompt, match_procedure


SYSTEM_PROMPT = """Sos el Asistente IPAC, un asistente operacional del sistema web de administración, tesorería y cobranzas de IPAC.

Tu trabajo es explicar cómo usar ESTE sistema. Respondé en español rioplatense, claro y breve.

REGLAS:
- No inventes botones, pantallas, estados, datos ni operaciones.
- No digas que ejecutaste una acción: este asistente V1 sólo orienta.
- Usá el conocimiento operativo suministrado como fuente principal.
- Si la pregunta depende de información real de un alumno, pago, caja o cuota que no fue incluida en el contexto, explicá dónde consultarla; no inventes valores.
- Respetá el rol y la sucursal del usuario. Si una acción requiere otro permiso, indicalo.
- Si la pregunta no es sobre IPAC, explicá que tu alcance es ayudar con el sistema IPAC.
- Preferí pasos numerados cuando el usuario pregunta "cómo".
- Para caja, distinguí efectivo físico de medios electrónicos.
- Para cuotas y pagos, preservá trazabilidad y evitá sugerir borrar registros.
"""


def _strip_reasoning(text):
    return re.sub(r"<think>.*?</think>", "", text or "", flags=re.DOTALL | re.IGNORECASE).strip()


def _role_context(user):
    profile = getattr(user, "perfil", None)
    if not profile:
        return "Usuario sin perfil operativo disponible."
    branch = getattr(profile, "sucursal", None)
    return (
        f"Usuario actual: {user.username}. "
        f"Rol: {profile.get_rol_display()}. "
        f"Sucursal: {getattr(branch, 'nombre', 'Sin sucursal')}. "
        f"Acceso a todas las sucursales: {'sí' if profile.puede_ver_todas_las_sucursales else 'no'}."
    )


def answer_message(user, content, history):
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

    if not getattr(settings, "IPAC_AI_ENABLED", False):
        return {
            "content": (
                "Puedo ayudarte con los procedimientos del sistema IPAC. "
                "Probá, por ejemplo: “¿Cómo doy de alta un alumno?”, "
                "“¿Cómo genero cuotas?”, “¿Cómo registro un pago?” o "
                "“¿Cómo cierro la caja?”."
            ),
            "tokens_used": None,
            "source": "fallback",
            "procedure": None,
            "action": None,
        }

    api_key = getattr(settings, "IPAC_AI_API_KEY", "").strip()
    model = getattr(settings, "IPAC_AI_MODEL", "").strip()
    base_url = getattr(settings, "IPAC_AI_BASE_URL", "").strip()
    if not api_key or not model or not base_url:
        return {
            "content": (
                "La ayuda guiada está disponible, pero la IA para preguntas abiertas todavía no está configurada. "
                "Podés preguntarme cómo dar de alta alumnos, generar cuotas, registrar pagos o cerrar caja."
            ),
            "tokens_used": None,
            "source": "fallback",
            "procedure": None,
            "action": None,
        }

    messages = [
        {
            "role": "system",
            "content": (
                f"{SYSTEM_PROMPT}\n\nCONTEXTO DEL USUARIO:\n{_role_context(user)}"
                f"\n\nCONOCIMIENTO OPERATIVO IPAC:\n{knowledge_for_prompt()}"
            ),
        }
    ]
    for item in history[-12:]:
        role = item.get("role")
        body = (item.get("content") or "").strip()
        if role in {"user", "assistant"} and body:
            messages.append({"role": role, "content": body})

    payload = json.dumps(
        {
            "model": model,
            "messages": messages,
            "temperature": 0.2,
            "max_completion_tokens": 1200,\n            "reasoning_split": True,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        base_url,
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=getattr(settings, "IPAC_AI_TIMEOUT_SECONDS", 30),
        ) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError):
        return {
            "content": (
                "No pude consultar la IA en este momento. La ayuda operativa conocida sigue disponible: "
                "alta de alumnos, matrículas, cuotas, pagos, estado de cuenta y caja."
            ),
            "tokens_used": None,
            "source": "fallback",
            "procedure": None,
            "action": None,
        }

    choices = data.get("choices") or []
    message = choices[0].get("message", {}) if choices else {}
    content = _strip_reasoning(message.get("content", ""))
    if not content:
        content = "No pude generar una respuesta útil. Probá reformulando la consulta sobre el sistema IPAC."

    usage = data.get("usage") or {}
    return {
        "content": content,
        "tokens_used": usage.get("total_tokens"),
        "source": "ai",
        "procedure": None,
        "action": None,
    }
