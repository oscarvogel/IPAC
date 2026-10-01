"""Desglose programático/extraprogramático de una cuota.

Regla de negocio: el Ministerio de Educación exige que el valor total de la
cuota figure desglosado en conceptos programáticos y extraprogramáticos, tanto
en los recibos como en las facturas oficiales.

El desglose se toma del catálogo de la carrera o curso y se congela en la cuota
al generarla. Congelarlo evita que un cambio posterior de precios del catálogo
altere comprobantes que ya fueron emitidos.
"""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

CENTIMO = Decimal("0.01")
ZERO = Decimal("0")


class DesgloseCuotaError(ValueError):
    """Los datos de la cuota no permiten derivar un desglose válido."""


@dataclass(frozen=True)
class DesgloseCuota:
    importe_programatico: Decimal
    importe_extraprogramatica: Decimal

    @property
    def total(self):
        return self.importe_programatico + self.importe_extraprogramatica


def _a_decimal(valor):
    if valor is None or valor == "":
        return None
    try:
        monto = Decimal(str(valor))
    except (InvalidOperation, TypeError, ValueError):
        return None
    return monto if monto.is_finite() else None


def calcular_desglose(*, importe, programatico_catalogo, extraprogramatica_catalogo):
    """Deriva el desglose de una cuota a partir del catálogo de su carrera.

    Devuelve ``None`` cuando el catálogo no tiene un desglose configurado. En ese
    caso la cuota no se puede desglosar y el comprobante se emite sin desglose,
    en lugar de mostrar un reparto inventado.

    Cuando el importe de la cuota difiere del total del catálogo, el reparto se
    prorratea. El importe programático se redondea a centavo y el extraprogramático
    recibe la diferencia, de modo que la suma sea exactamente igual al importe de
    la cuota y el comprobante nunca muestre un total descuadrado.
    """
    monto_cuota = _a_decimal(importe)
    if monto_cuota is None or monto_cuota <= ZERO:
        raise DesgloseCuotaError("El importe de la cuota debe ser mayor a cero para desglosarla.")

    programatico = _a_decimal(programatico_catalogo)
    extraprogramatica = _a_decimal(extraprogramatica_catalogo)
    if programatico is None or extraprogramatica is None:
        return None

    if programatico < ZERO or extraprogramatica < ZERO:
        raise DesgloseCuotaError("El catálogo no puede tener importes programáticos o extraprogramáticos negativos.")

    total_catalogo = programatico + extraprogramatica
    if total_catalogo <= ZERO:
        return None

    if monto_cuota == total_catalogo:
        return DesgloseCuota(programatico, extraprogramatica)

    parte_programatica = (monto_cuota * programatico / total_catalogo).quantize(
        CENTIMO, rounding=ROUND_HALF_UP
    )
    if parte_programatica > monto_cuota:
        parte_programatica = monto_cuota
    return DesgloseCuota(parte_programatica, monto_cuota - parte_programatica)