"""Caso de uso para transferir fondos entre dos cajas."""

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID, uuid4

from ..domain.transferencia_caja import (
    SolicitudTransferenciaCaja,
    validar_solicitud_transferencia,
)


class TransferenciaIdempotenciaConflicto(Exception):
    """La clave ya identifica otro actor o comando."""


class TransferenciaCajaRepository(Protocol):
    """Puerto de salida que realiza la transferencia de forma atómica."""

    def transferir(self, *, actor, solicitud: SolicitudTransferenciaCaja,
                   idempotency_key: UUID) -> object: ...


@dataclass
class TransferirEntreCajas:
    repository: TransferenciaCajaRepository

    def execute(self, *, actor, solicitud: SolicitudTransferenciaCaja,
                idempotency_key: UUID | None = None) -> object:
        validar_solicitud_transferencia(solicitud)
        return self.repository.transferir(
            actor=actor, solicitud=solicitud, idempotency_key=idempotency_key or uuid4(),
        )


__all__ = ["TransferenciaCajaRepository", "TransferirEntreCajas", "TransferenciaIdempotenciaConflicto"]
