from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Protocol


class GeneracionCuotasError(ValueError):
    def __init__(self, detail, *, alumnos=None):
        super().__init__(detail)
        self.detail = detail
        self.alumnos = alumnos


@dataclass(frozen=True)
class SolicitudGeneracionCuotas:
    alumno_ids: tuple[int, ...]
    concepto_id: int
    periodo: str
    fecha_emision: date
    fecha_vencimiento: date
    importe: Decimal | None
    descuento: Decimal
    recargo: Decimal
    tipo_descuento_id: int | None
    motivo_descuento: str


class CuotaGenerator(Protocol):
    def generar(self, *, actor, solicitud: SolicitudGeneracionCuotas) -> list: ...


def _identifier(value, label):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        raise GeneracionCuotasError(f"{label} inválido.") from None
    if parsed <= 0:
        raise GeneracionCuotasError(f"{label} inválido.")
    return parsed


def _date(value, label):
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        raise GeneracionCuotasError(f"{label} debe ser una fecha válida.") from None


def _amount(value, label, *, default=Decimal("0")):
    if value is None:
        return default
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise GeneracionCuotasError("Los importes deben ser numéricos.") from None
    if not amount.is_finite():
        raise GeneracionCuotasError(f"{label} debe ser un importe válido.")
    return amount


class GenerarCuotas:
    """Valida la solicitud y delega la operación transaccional al puerto de Cobranzas."""

    def __init__(self, generator: CuotaGenerator):
        self._generator = generator

    def execute(self, *, actor, payload):
        raw_alumnos = payload.get("alumnos", [])
        if not isinstance(raw_alumnos, list) or not raw_alumnos:
            raise GeneracionCuotasError("Debe indicar al menos un alumno.")
        alumno_ids = tuple(dict.fromkeys(_identifier(item, "Alumno") for item in raw_alumnos))

        required = (payload.get("concepto"), payload.get("periodo"), payload.get("fecha_emision"), payload.get("fecha_vencimiento"))
        if not all(required):
            raise GeneracionCuotasError("Concepto, periodo y fechas son obligatorios.")

        importe = None if payload.get("importe") in (None, "") else _amount(payload["importe"], "Importe")
        descuento = _amount(payload.get("descuento", 0), "Descuento")
        recargo = _amount(payload.get("recargo", 0), "Recargo")
        if descuento < 0 or recargo < 0 or (importe is not None and (importe <= 0 or descuento > importe + recargo)):
            raise GeneracionCuotasError("Los importes, descuentos o recargos no son válidos.")

        tipo_descuento_id = payload.get("tipo_descuento")
        if tipo_descuento_id in (None, ""):
            tipo_descuento_id = None
        else:
            tipo_descuento_id = _identifier(tipo_descuento_id, "Tipo de descuento")

        solicitud = SolicitudGeneracionCuotas(
            alumno_ids=alumno_ids,
            concepto_id=_identifier(payload.get("concepto"), "Concepto"),
            periodo=str(payload.get("periodo")).strip(),
            fecha_emision=_date(payload.get("fecha_emision"), "La fecha de emisión"),
            fecha_vencimiento=_date(payload.get("fecha_vencimiento"), "La fecha de vencimiento"),
            importe=importe,
            descuento=descuento,
            recargo=recargo,
            tipo_descuento_id=tipo_descuento_id,
            motivo_descuento=str(payload.get("motivo_descuento") or "").strip(),
        )
        if not solicitud.periodo:
            raise GeneracionCuotasError("El período es obligatorio.")
        return self._generator.generar(actor=actor, solicitud=solicitud)
