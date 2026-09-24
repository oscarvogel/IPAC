from dataclasses import dataclass

from ..domain.models import ToolContext, ToolResult


class UnknownTool(ValueError):
    pass


class InvalidToolArguments(ValueError):
    pass


TOOL_SPECS = {
    "resumen_deuda": {"allowed": {"sucursal_id", "sucursal"}},
    "alumnos_con_deuda": {"allowed": {"sucursal_id", "sucursal", "limit"}},
    "estado_cuenta_alumno": {
        "required_any": {"alumno_id", "search"},
        "allowed": {"alumno_id", "search"},
    },
    "resumen_cobranzas": {
        "allowed": {"sucursal_id", "sucursal", "desde", "hasta", "medio"},
    },
    "caja_hoy": {"allowed": {"sucursal_id", "sucursal"}},
    "resumen_cuotas": {
        "allowed": {"sucursal_id", "sucursal", "periodo", "estado"},
    },
    "resumen_alumnos": {
        "allowed": {"sucursal_id", "sucursal", "estado", "carrera_id"},
    },
    "buscar_alumno": {
        "required": {"search"},
        "allowed": {"search"},
    },
}


class ReadToolRegistry:
    def __init__(self, gateway):
        self.gateway = gateway

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(TOOL_SPECS.keys())

    def execute(
        self,
        name: str,
        arguments: dict,
        context: ToolContext,
    ) -> ToolResult:
        spec = TOOL_SPECS.get(name)
        if spec is None:
            raise UnknownTool(name)
        if not isinstance(arguments, dict):
            raise InvalidToolArguments("Los argumentos deben ser un objeto.")

        keys = set(arguments)
        unknown = keys - spec.get("allowed", set())
        if unknown:
            raise InvalidToolArguments(
                f"Argumentos no permitidos para {name}: {sorted(unknown)}"
            )

        required = spec.get("required", set())
        missing = required - {key for key, value in arguments.items() if value not in (None, "")}
        if missing:
            raise InvalidToolArguments(f"Faltan argumentos: {sorted(missing)}")

        required_any = spec.get("required_any", set())
        if required_any and not any(arguments.get(key) not in (None, "") for key in required_any):
            raise InvalidToolArguments(
                f"Debe indicar al menos uno de: {sorted(required_any)}"
            )

        method = getattr(self.gateway, name)
        return method(context=context, **arguments)
