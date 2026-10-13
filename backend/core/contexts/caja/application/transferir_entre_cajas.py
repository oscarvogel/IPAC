"""Caso de uso para transferir fondos entre dos cajas."""

from dataclasses import dataclass
from typing import Protocol

from ..domain.transferencia_caja import (
    SolicitudTransferenciaCaja,
    validar_solicitud_transferencia,
)


class TransferenciaCajaRepository(Protocol):
    """Puerto de salida que realiza la transferencia de forma atómica."""

    def transferir(self, *, actor, solicitud: SolicitudTransferenciaCaja) -> object: ...


@dataclass
class TransferirEntreCajas:
    repository: TransferenciaCajaRepository

    def execute(self, *, actor, solicitud: SolicitudTransferenciaCaja) -> object:
        validar_solicitud_transferencia(solicitud)
        return self.repository.transferir(actor=actor, solicitud=solicitud)


__all__ = ["TransferenciaCajaRepository", "TransferirEntreCajas"]
