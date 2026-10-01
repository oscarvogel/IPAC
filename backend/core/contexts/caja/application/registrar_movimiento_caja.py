"""Caso de uso: registrar un movimiento de caja emitiendo su comprobante.

Coordinación únicamente. Las reglas viven en ``domain.comprobante_caja`` y la
escritura en el adaptador de persistencia.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from ..domain.comprobante_caja import validar_comprobante


class MovimientoCajaWriter(Protocol):
    """Puerto de salida: persiste el movimiento dentro de una transacción."""

    def registrar(self, *, actor, solicitud) -> object: ...


@dataclass(frozen=True)
class SolicitudMovimientoCaja:
    caja_id: int
    tipo: str
    medio: str
    importe: Decimal
    descripcion: str
    recibido_por_id: int | None = None


@dataclass
class RegistrarMovimientoCaja:
    repository: MovimientoCajaWriter

    def execute(self, *, actor, solicitud: SolicitudMovimientoCaja):
        """Valida la invariante del comprobante y delega la escritura.

        Un ingreso o egreso corriente no exige comprobante, así que la
        validación sólo restringe a los pases y retiros.
        """
        validar_comprobante(
            tipo=solicitud.tipo,
            importe=solicitud.importe,
            descripcion=solicitud.descripcion,
            recibido_por_id=solicitud.recibido_por_id,
        )
        return self.repository.registrar(actor=actor, solicitud=solicitud)


__all__ = [
    "MovimientoCajaWriter",
    "RegistrarMovimientoCaja",
    "SolicitudMovimientoCaja",
]