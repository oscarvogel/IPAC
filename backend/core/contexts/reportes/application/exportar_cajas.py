from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class FiltrosExportacionCajas:
    desde: str | None = None
    hasta: str | None = None
    sucursal_id: str | None = None
    usuario_id: str | None = None


class CajaExportReader(Protocol):
    def leer_cajas(self, *, actor, filtros: FiltrosExportacionCajas) -> list[list]: ...


class ExportarCajas:
    """Prepara el conjunto de cajas exportable dentro del alcance autorizado."""

    encabezados = [
        "Fecha", "Sucursal", "Usuario", "Estado", "Saldo inicial",
        "Efectivo esperado", "Total contado", "Diferencia", "Saldo siguiente",
    ]

    def __init__(self, reader: CajaExportReader):
        self._reader = reader

    def execute(self, *, actor, filtros):
        return {
            "headers": self.encabezados,
            "rows": self._reader.leer_cajas(actor=actor, filtros=filtros),
        }
