from dataclasses import dataclass
from typing import Protocol

from ..domain.resumen_caja import CajaOperacionError, validar_distribucion_cierre


class CajaRepository(Protocol):
    def cerrar(self, *, caja_id, total_contado, importe_retirado, saldo_arrastrable): ...

    def saldo_pendiente(self, *, caja_id): ...

    def aplicar_saldo_pendiente(self, *, caja_id, saldo_id=None): ...


@dataclass
class CerrarCaja:
    repository: CajaRepository

    def execute(self, *, caja_id, total_contado, importe_retirado=None, saldo_arrastrable=None):
        if importe_retirado is None and saldo_arrastrable is None:
            importe_retirado = total_contado
            saldo_arrastrable = 0
        total_contado, importe_retirado, saldo_arrastrable = validar_distribucion_cierre(
            total_contado=total_contado,
            importe_retirado=importe_retirado,
            saldo_arrastrable=saldo_arrastrable,
        )
        return self.repository.cerrar(
            caja_id=caja_id,
            total_contado=total_contado,
            importe_retirado=importe_retirado,
            saldo_arrastrable=saldo_arrastrable,
        )


@dataclass
class GestionarSaldoAnterior:
    repository: CajaRepository

    def consultar(self, *, caja_id):
        return self.repository.saldo_pendiente(caja_id=caja_id)

    def aplicar(self, *, caja_id, saldo_id=None):
        return self.repository.aplicar_saldo_pendiente(caja_id=caja_id, saldo_id=saldo_id)


__all__ = ["CajaOperacionError", "CerrarCaja", "GestionarSaldoAnterior"]
