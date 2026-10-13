"""Reglas puras para solicitar una transferencia entre cajas."""

from dataclasses import dataclass
from decimal import Decimal


class TransferenciaCajaError(ValueError):
    """Solicitud de transferencia que incumple una regla de Caja."""


@dataclass(frozen=True)
class SolicitudTransferenciaCaja:
    origen_id: int
    destino_id: int
    importe: Decimal
    motivo: str


def validar_solicitud_transferencia(solicitud: SolicitudTransferenciaCaja) -> None:
    """Valida que la transferencia tenga cajas distintas, importe positivo y motivo."""
    if solicitud.origen_id == solicitud.destino_id:
        raise TransferenciaCajaError("La caja de origen y destino deben ser distintas.")
    if solicitud.importe <= Decimal("0"):
        raise TransferenciaCajaError("El importe de la transferencia debe ser mayor a cero.")
    if not solicitud.motivo or not solicitud.motivo.strip():
        raise TransferenciaCajaError("El motivo de la transferencia es obligatorio.")


__all__ = [
    "SolicitudTransferenciaCaja",
    "TransferenciaCajaError",
    "validar_solicitud_transferencia",
]
