from dataclasses import dataclass
from decimal import Decimal

from django.db.models import DecimalField, ExpressionWrapper, F, OuterRef, Q, Subquery, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone

from core.models import AplicacionPago, Cuota, Sucursal


class UnknownTool(ValueError):
    pass


class InvalidToolArguments(ValueError):
    pass


class ToolForbidden(PermissionError):
    pass


@dataclass(frozen=True)
class ToolContext:
    user_id: int
    branch_id: int
    global_access: bool


TOOL_CATALOG = {
    "resumen_deuda": {
        "description": (
            "Obtiene la deuda pendiente consolidada: total, vencida, cantidad de alumnos "
            "con deuda y cantidad de cuotas pendientes/vencidas."
        ),
        "arguments": {
            "sucursal": "Nombre o código de sucursal. Omitir para usar el alcance autorizado del usuario.",
        },
    },
    "alumnos_con_deuda": {
        "description": (
            "Obtiene la lista de alumnos que tienen saldo pendiente, con legajo, sucursal, "
            "deuda total y deuda vencida."
        ),
        "arguments": {
            "sucursal": "Nombre o código de sucursal. Omitir para usar el alcance autorizado del usuario.",
            "limit": "Cantidad máxima de alumnos a devolver. Entero entre 1 y 50.",
        },
    },
}


_MONEY = DecimalField(max_digits=14, decimal_places=2)


class ReadToolRegistry:
    @property
    def names(self):
        return tuple(TOOL_CATALOG.keys())

    @property
    def catalog(self):
        return TOOL_CATALOG

    def execute(self, name, arguments, context):
        if name not in TOOL_CATALOG:
            raise UnknownTool(name)
        if not isinstance(arguments, dict):
            raise InvalidToolArguments("Los argumentos deben ser un objeto.")

        allowed = set(TOOL_CATALOG[name]["arguments"])
        unknown = set(arguments) - allowed
        if unknown:
            raise InvalidToolArguments(
                f"Argumentos no permitidos para {name}: {sorted(unknown)}"
            )

        return getattr(self, f"_tool_{name}")(arguments, context)

    def _resolve_scope(self, context, requested_branch=None):
        own = Sucursal.objects.filter(pk=context.branch_id).first()
        if own is None:
            raise ToolForbidden("El usuario no tiene una sucursal válida.")

        requested = str(requested_branch or "").strip()
        if not context.global_access:
            if requested and requested.casefold() not in {
                own.nombre.casefold(),
                own.codigo.casefold(),
            }:
                raise ToolForbidden("La sucursal solicitada no está autorizada.")
            return [own.id], own.nombre

        if requested:
            branch = Sucursal.objects.filter(
                Q(nombre__iexact=requested) | Q(codigo__iexact=requested)
            ).first()
            if branch is None:
                raise InvalidToolArguments("La sucursal indicada no existe.")
            return [branch.id], branch.nombre

        ids = list(Sucursal.objects.order_by("id").values_list("id", flat=True))
        return ids, "Todas las sucursales"

    def _fees_with_balance(self, branch_ids):
        paid = (
            AplicacionPago.objects.filter(cuota_id=OuterRef("pk"), activa=True)
            .values("cuota_id")
            .annotate(total=Sum("importe"))
            .values("total")[:1]
        )
        return (
            Cuota.objects.filter(sucursal_id__in=branch_ids)
            .exclude(estado=Cuota.Estado.ANULADA)
            .annotate(
                saldo_calculado=ExpressionWrapper(
                    F("importe")
                    - F("descuento")
                    + F("recargo")
                    - Coalesce(
                        Subquery(paid, output_field=_MONEY),
                        Value(Decimal("0")),
                        output_field=_MONEY,
                    ),
                    output_field=_MONEY,
                )
            )
        )

    def _tool_resumen_deuda(self, arguments, context):
        branch_ids, scope = self._resolve_scope(
            context,
            arguments.get("sucursal"),
        )
        fees = self._fees_with_balance(branch_ids).filter(saldo_calculado__gt=0)
        today = timezone.localdate()

        total = fees.aggregate(value=Sum("saldo_calculado"))["value"] or Decimal("0")
        overdue_qs = fees.filter(fecha_vencimiento__lt=today)
        overdue = overdue_qs.aggregate(value=Sum("saldo_calculado"))["value"] or Decimal("0")

        return {
            "scope": scope,
            "as_of": today.isoformat(),
            "deuda_total": total,
            "deuda_vencida": overdue,
            "alumnos_con_deuda": fees.values("alumno_id").distinct().count(),
            "cuotas_pendientes": fees.count(),
            "cuotas_vencidas": overdue_qs.count(),
        }

    def _tool_alumnos_con_deuda(self, arguments, context):
        branch_ids, scope = self._resolve_scope(
            context,
            arguments.get("sucursal"),
        )
        raw_limit = arguments.get("limit", 20)
        try:
            limit = int(raw_limit)
        except (TypeError, ValueError) as exc:
            raise InvalidToolArguments("limit debe ser un entero.") from exc
        if not 1 <= limit <= 50:
            raise InvalidToolArguments("limit debe estar entre 1 y 50.")

        fees = self._fees_with_balance(branch_ids).filter(saldo_calculado__gt=0)
        today = timezone.localdate()

        debt_rows = list(
            fees.values(
                "alumno_id",
                "alumno__apellido",
                "alumno__nombre",
                "alumno__legajo",
                "sucursal__nombre",
            )
            .annotate(deuda_total=Sum("saldo_calculado"))
            .order_by("-deuda_total", "alumno__apellido", "alumno__nombre", "alumno_id")
        )
        overdue_rows = (
            fees.filter(fecha_vencimiento__lt=today)
            .values("alumno_id")
            .annotate(deuda_vencida=Sum("saldo_calculado"))
        )
        overdue_by_student = {
            row["alumno_id"]: row["deuda_vencida"]
            for row in overdue_rows
        }

        alumnos = [
            {
                "id": row["alumno_id"],
                "nombre": f"{row['alumno__apellido']}, {row['alumno__nombre']}",
                "legajo": row["alumno__legajo"],
                "sucursal": row["sucursal__nombre"],
                "deuda_total": row["deuda_total"],
                "deuda_vencida": overdue_by_student.get(
                    row["alumno_id"],
                    Decimal("0"),
                ),
            }
            for row in debt_rows[:limit]
        ]

        return {
            "scope": scope,
            "as_of": today.isoformat(),
            "total_alumnos": len(debt_rows),
            "deuda_total": sum(
                (row["deuda_total"] for row in debt_rows),
                Decimal("0"),
            ),
            "alumnos": alumnos,
            "truncated": len(debt_rows) > limit,
        }
