"""Contratos de lectura para elegir cajas y consultar evidencia de transferencias."""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Protocol


class CajaTransferenciaNoDisponible(Exception):
    """Un ID no corresponde a una caja operable dentro del alcance vigente."""


@dataclass(frozen=True)
class CajaTransferenciaResumen:
    id: int
    fecha: date
    sucursal: int
    sucursal_nombre: str
    usuario: int
    usuario_nombre: str
    total_esperado: Decimal


@dataclass(frozen=True)
class ActorTransferenciaResumen:
    id: int
    username: str
    nombre: str


@dataclass(frozen=True)
class TransferenciaCajaEvidencia:
    id: int
    numero_comprobante: str
    creado: datetime
    actor: ActorTransferenciaResumen
    origen: CajaTransferenciaResumen
    destino: CajaTransferenciaResumen
    importe: Decimal
    motivo: str
    movimiento_origen_id: int
    movimiento_destino_id: int


class TransferenciasCajaReader(Protocol):
    def cajas_abiertas(self, *, actor) -> tuple[CajaTransferenciaResumen, ...]: ...

    def historial(self, *, actor) -> tuple[TransferenciaCajaEvidencia, ...]: ...


@dataclass
class ConsultarCajasAbiertasParaTransferir:
    reader: TransferenciasCajaReader

    def execute(self, *, actor) -> tuple[CajaTransferenciaResumen, ...]:
        return self.reader.cajas_abiertas(actor=actor)


@dataclass
class ConsultarTransferenciasCaja:
    reader: TransferenciasCajaReader

    def execute(self, *, actor) -> tuple[TransferenciaCajaEvidencia, ...]:
        return self.reader.historial(actor=actor)
