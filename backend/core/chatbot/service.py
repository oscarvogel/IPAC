from decimal import Decimal

from django.conf import settings

from .knowledge import PROCEDURES, format_procedure, match_procedure
from .planner import MiniMaxPlanner, PlannerError
from .tools import (
    InvalidToolArguments,
    ReadToolRegistry,
    ToolContext,
    ToolForbidden,
    UnknownTool,
)


OUT_OF_SCOPE_MESSAGE = (
    "Mi función está limitada al sistema IPAC. No puedo responder consultas generales "
    "sobre temas ajenos al sistema."
)

UNKNOWN_MESSAGE = (
    "No tengo una capacidad disponible para responder esa consulta de IPAC de forma confiable."
)

AI_UNAVAILABLE_MESSAGE = (
    "El componente de IA no está disponible en este momento. "
    "Los procedimientos conocidos del sistema siguen disponibles."
)


def _role_context(user):
    profile = getattr(user, "perfil", None)
    if profile is None:
        return "Usuario sin perfil operativo."
    return (
        f"rol={profile.rol}; "
        f"sucursal={profile.sucursal.nombre}; "
        f"sucursal_id={profile.sucursal_id}; "
        f"acceso_global={'si' if profile.puede_ver_todas_las_sucursales else 'no'}"
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


def _money(value):
    amount = Decimal(str(value or 0)).quantize(Decimal("0.01"))
    return f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _format_tool_result(name, data):
    scope = data.get("scope", "alcance autorizado")
    as_of = data.get("as_of", "")

    if name == "resumen_deuda":
        body = (
            f"La deuda pendiente es de $ {_money(data['deuda_total'])}. "
            f"De ese total, $ {_money(data['deuda_vencida'])} está vencido. "
            f"Hay {data['alumnos_con_deuda']} alumno(s) con saldo pendiente, "
            f"{data['cuotas_pendientes']} cuota(s) pendientes y "
            f"{data['cuotas_vencidas']} vencida(s)."
        )
    elif name == "alumnos_con_deuda":
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
                f"Mostrando {len(rows)} de {data['total_alumnos']} alumno(s)."
            )
        body = "\n".join(lines)
    else:
        raise UnknownTool(name)

    suffix = f"\n\nAlcance: {scope}."
    if as_of:
        suffix += f" Datos al {as_of}."
    return body + suffix


def _procedure_response(key):
    procedure = PROCEDURES[key]
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


def answer_message(user, content, history):
    if not getattr(settings, "IPAC_AI_ENABLED", False):
        matched = match_procedure(content)
        if matched:
            key, _ = matched
            return _procedure_response(key)
        return {
            "content": (
                "Puedo ayudarte con los procedimientos del sistema IPAC. "
                "La IA para consultas abiertas está deshabilitada."
            ),
            "tokens_used": None,
            "source": "fallback",
            "procedure": None,
            "action": None,
        }

    try:
        decision = MiniMaxPlanner().decide(
            question=content,
            history=history,
            role_context=_role_context(user),
        )
    except PlannerError:
        return {
            "content": AI_UNAVAILABLE_MESSAGE,
            "tokens_used": None,
            "source": "fallback",
            "procedure": None,
            "action": None,
        }

    if decision.kind == "out_of_scope":
        return {
            "content": OUT_OF_SCOPE_MESSAGE,
            "tokens_used": None,
            "source": "out_of_scope",
            "procedure": None,
            "action": None,
        }

    if decision.kind == "unknown":
        return {
            "content": UNKNOWN_MESSAGE,
            "tokens_used": None,
            "source": "unknown",
            "procedure": None,
            "action": None,
        }

    if decision.kind == "knowledge":
        if decision.knowledge_key not in PROCEDURES:
            return {
                "content": UNKNOWN_MESSAGE,
                "tokens_used": None,
                "source": "unknown",
                "procedure": None,
                "action": None,
            }
        return _procedure_response(decision.knowledge_key)

    if decision.kind == "tool":
        try:
            result = ReadToolRegistry().execute(
                decision.tool,
                decision.arguments or {},
                _tool_context(user),
            )
            text = _format_tool_result(decision.tool, result)
        except ToolForbidden:
            text = "Tu usuario no tiene acceso al alcance solicitado."
            source = "forbidden"
        except (UnknownTool, InvalidToolArguments, KeyError, TypeError, ValueError):
            text = UNKNOWN_MESSAGE
            source = "unknown"
        else:
            source = "tool"

        return {
            "content": text,
            "tokens_used": None,
            "source": source,
            "procedure": None,
            "action": None,
        }

    return {
        "content": UNKNOWN_MESSAGE,
        "tokens_used": None,
        "source": "unknown",
        "procedure": None,
        "action": None,
    }
