"""Comprobante auditable de los movimientos que mueven plata entre cajas.

Regla de negocio acordada: todo pase o retiro de dinero entre cajas debe dejar un
comprobante auditable, con la conformidad de quien recibe. La impresión es
opcional: el comprobante es digital y se imprime cuando haga falta.

Este módulo es puro. No conoce Django ni la base de datos.
"""

from dataclasses import dataclass
from decimal import Decimal

ZERO = Decimal("0")

#: Movimientos que mueven dinero entre cajas o fuera de ellas y por lo tanto
#: exigen comprobante. Un pago o un ingreso corriente no lo requieren.
TIPOS_CON_COMPROBANTE = frozenset({"pase", "retiro"})

CONFORMIDAD_MESSAGE = (
    "El pase y el retiro exigen indicar quién recibe el dinero para emitir el comprobante."
)
IMPORTE_MESSAGE = "El comprobante de caja requiere un importe mayor a cero."
DESCRIPCION_MESSAGE = "Indique el motivo del pase o del retiro para emitir el comprobante."


class ComprobanteCajaError(ValueError):
    """Error funcional al emitir el comprobante de un movimiento de caja."""


@dataclass(frozen=True)
class ComprobanteCaja:
    numero: str
    tipo: str
    importe: Decimal
    descripcion: str
    recibido_por_id: int
    movimiento_id: int


def requiere_comprobante(tipo):
    """Indica si el tipo de movimiento debe emitir comprobante."""
    return tipo in TIPOS_CON_COMPROBANTE


def numero_comprobante(movimiento_id):
    """Formato de numeración del comprobante, estable y ordenable por fecha."""
    return f"COM-{int(movimiento_id):08d}"


def _decimal(valor):
    try:
        return Decimal(str(valor if valor is not None else 0))
    except Exception:
        return ZERO


def validar_comprobante(*, tipo, importe, descripcion, recibido_por_id):
    """Valida la invariante del comprobante antes de emitirlo.

    Sólo exige datos a los movimientos que necesitan comprobante, para no romper
    los ingresos y egresos corrientes que hoy se registran sin comprobante.
    """
    if not requiere_comprobante(tipo):
        return

    if _decimal(importe) <= ZERO:
        raise ComprobanteCajaError(IMPORTE_MESSAGE)

    if not str(descripcion or "").strip():
        raise ComprobanteCajaError(DESCRIPCION_MESSAGE)

    try:
        receptor = int(recibido_por_id)
    except (TypeError, ValueError):
        raise ComprobanteCajaError(CONFORMIDAD_MESSAGE) from None
    if receptor <= 0:
        raise ComprobanteCajaError(CONFORMIDAD_MESSAGE)