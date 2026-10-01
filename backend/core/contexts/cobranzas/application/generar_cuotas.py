from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Protocol

from ..domain.planificacion_cuotas import (
    ErrorPlanificacionCuotas,
    PlanificacionCuotas,
    exigir_vencimientos,
)
from .planificacion_desde_payload import PayloadDeCuotasInvalido, planificacion_desde_payload


class GeneracionCuotasError(ValueError):
    def __init__(self, detail, *, alumnos=None):
        super().__init__(detail)
        self.detail = detail
        self.alumnos = alumnos


@dataclass(frozen=True)
class SolicitudGeneracionCuotas:
    alumno_ids: tuple[int, ...]
    concepto_id: int
    planificacion: PlanificacionCuotas
    fecha_emision: date
    importe: Decimal | None
    descuento: Decimal
    recargo: Decimal
    tipo_descuento_id: int | None
    motivo_descuento: str
    #: Matrícula a la que quedan enlazadas las cuotas, si la generación viene
    #: de una reinscripción. Antes este campo existía en el modelo y nunca se
    #: llenaba, así que las cuotas quedaban huérfanas de la trayectoria.
    matricula_id: int | None = None


@dataclass(frozen=True)
class ResultadoGeneracionCuotas:
    """Qué se creó y qué se salteó.

    ``omitidas`` no es un error: son los pares (alumno, período) que ya tenían
    cuota. Devolverlos permite que el operador vuelva a correr la misma
    operación sin miedo y vea qué quedó afuera y por qué.
    """

    creadas: list = field(default_factory=list)
    omitidas: list = field(default_factory=list)

    @property
    def total_creadas(self) -> int:
        return len(self.creadas)

    @property
    def total_omitidas(self) -> int:
        return len(self.omitidas)


class CuotaGenerator(Protocol):
    def generar(self, *, actor, solicitud: SolicitudGeneracionCuotas) -> ResultadoGeneracionCuotas: ...


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


def _planificar(payload):
    try:
        return planificacion_desde_payload(payload)
    except PayloadDeCuotasInvalido as exc:
        raise GeneracionCuotasError(exc.detail) from exc


class GenerarCuotas:
    """Valida la solicitud y delega la operación transaccional al puerto de Cobranzas."""

    def __init__(self, generator: CuotaGenerator):
        self._generator = generator

    def execute(self, *, actor, payload):
        raw_alumnos = payload.get("alumnos", [])
        if not isinstance(raw_alumnos, list) or not raw_alumnos:
            raise GeneracionCuotasError("Debe indicar al menos un alumno.")
        alumno_ids = tuple(dict.fromkeys(_identifier(item, "Alumno") for item in raw_alumnos))

        if not all((payload.get("concepto"), payload.get("fecha_emision"))):
            raise GeneracionCuotasError("Concepto y fecha de emisión son obligatorios.")

        planificacion = _planificar(payload)
        # La fecha es opcional en la previsualización, pero acá sí o sí hace
        # falta: se está por escribir la cuota.
        try:
            exigir_vencimientos(planificacion)
        except ErrorPlanificacionCuotas as exc:
            raise GeneracionCuotasError(exc.detail) from exc

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

        matricula_id = payload.get("matricula")
        if matricula_id in (None, ""):
            matricula_id = None
        else:
            matricula_id = _identifier(matricula_id, "Matrícula")

        solicitud = SolicitudGeneracionCuotas(
            alumno_ids=alumno_ids,
            concepto_id=_identifier(payload.get("concepto"), "Concepto"),
            planificacion=planificacion,
            fecha_emision=_date(payload.get("fecha_emision"), "La fecha de emisión"),
            importe=importe,
            descuento=descuento,
            recargo=recargo,
            tipo_descuento_id=tipo_descuento_id,
            motivo_descuento=str(payload.get("motivo_descuento") or "").strip(),
            matricula_id=matricula_id,
        )
        return self._generator.generar(actor=actor, solicitud=solicitud)
