from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True)
class CajaHistorial:
    id: int
    fecha: date
    sucursal: int
    sucursal_nombre: str
    usuario: int
    usuario_nombre: str
    estado: str
    saldo_inicial: Decimal
    total_esperado: Decimal
    total_contado: Decimal
    diferencia: Decimal | None
    cantidad_movimientos: int
    cerrada_en: datetime | None


@dataclass(frozen=True)
class UsuarioCaja:
    id: int
    nombre: str


@dataclass(frozen=True)
class PaginaHistorialCajas:
    count: int
    page: int
    page_size: int
    results: tuple[CajaHistorial, ...]
    usuarios: tuple[UsuarioCaja, ...]


class HistorialCajasReader(Protocol):
    def consultar_historial(
        self,
        *,
        desde: date | None,
        hasta: date | None,
        sucursal_ids: tuple[int, ...],
        usuario_id: int | None,
        propietario_id: int | None,
        page: int,
        page_size: int,
    ) -> PaginaHistorialCajas: ...


@dataclass
class ConsultarHistorialCajas:
    reader: HistorialCajasReader

    def execute(
        self,
        *,
        desde: date | None,
        hasta: date | None,
        sucursal_ids: tuple[int, ...],
        usuario_id: int | None,
        propietario_id: int | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> PaginaHistorialCajas:
        return self.reader.consultar_historial(
            desde=desde,
            hasta=hasta,
            sucursal_ids=sucursal_ids,
            usuario_id=usuario_id,
            propietario_id=propietario_id,
            page=page,
            page_size=page_size,
        )
