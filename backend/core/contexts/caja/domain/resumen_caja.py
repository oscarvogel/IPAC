from dataclasses import dataclass
from decimal import Decimal


ZERO = Decimal("0")
TIPOS_EGRESO = {"egreso", "retiro", "pase", "reverso"}


def _decimal(value):
    return Decimal(str(value or 0))


@dataclass(frozen=True)
class ResumenCaja:
    saldo_inicial: Decimal
    cobranzas_efectivo: Decimal
    otros_ingresos_efectivo: Decimal
    egresos_efectivo: Decimal
    retiros_efectivo: Decimal
    efectivo_esperado: Decimal
    total_ingresos: Decimal
    total_egresos: Decimal
    total_cobrado: Decimal
    efectivo: Decimal
    transferencia: Decimal
    mercado_pago: Decimal
    tarjeta: Decimal
    otro: Decimal

    def as_dict(self):
        return {
            field: getattr(self, field)
            for field in self.__dataclass_fields__
        }


def calcular_resumen_caja(*, saldo_inicial=ZERO, movimientos=()):
    """Calcula caja física y cobranzas sin mezclar medios electrónicos."""
    saldo_inicial = _decimal(saldo_inicial)
    cobranzas = {
        "efectivo": ZERO,
        "transferencia": ZERO,
        "mercado_pago": ZERO,
        "tarjeta": ZERO,
        "otro": ZERO,
    }
    otros_ingresos_efectivo = ZERO
    egresos_efectivo = ZERO
    retiros_efectivo = ZERO
    total_ingresos = ZERO
    total_egresos = ZERO

    for movimiento in movimientos:
        tipo = movimiento.tipo
        medio = movimiento.medio
        importe = _decimal(movimiento.importe)
        es_egreso = tipo in TIPOS_EGRESO

        if es_egreso:
            total_egresos += importe
        else:
            total_ingresos += importe

        if tipo == "pago":
            cobranzas[medio if medio in cobranzas else "otro"] += importe
        elif tipo == "reverso":
            cobranzas[medio if medio in cobranzas else "otro"] -= importe

        if medio != "efectivo":
            continue
        if tipo == "ingreso":
            otros_ingresos_efectivo += importe
        elif tipo == "egreso":
            egresos_efectivo += importe
        elif tipo in {"retiro", "pase", "reverso"}:
            retiros_efectivo += importe

    efectivo_esperado = (
        saldo_inicial
        + cobranzas["efectivo"]
        + otros_ingresos_efectivo
        - egresos_efectivo
        - retiros_efectivo
    )
    return ResumenCaja(
        saldo_inicial=saldo_inicial,
        cobranzas_efectivo=cobranzas["efectivo"],
        otros_ingresos_efectivo=otros_ingresos_efectivo,
        egresos_efectivo=egresos_efectivo,
        retiros_efectivo=retiros_efectivo,
        efectivo_esperado=efectivo_esperado,
        total_ingresos=total_ingresos,
        total_egresos=total_egresos,
        total_cobrado=sum(cobranzas.values(), ZERO),
        efectivo=cobranzas["efectivo"],
        transferencia=cobranzas["transferencia"],
        mercado_pago=cobranzas["mercado_pago"],
        tarjeta=cobranzas["tarjeta"],
        otro=cobranzas["otro"],
    )


class CajaOperacionError(ValueError):
    """Error funcional al cerrar una caja o trasladar su saldo."""


def validar_distribucion_cierre(*, total_contado, importe_retirado, saldo_arrastrable):
    total_contado = _decimal(total_contado)
    importe_retirado = _decimal(importe_retirado)
    saldo_arrastrable = _decimal(saldo_arrastrable)
    if min(total_contado, importe_retirado, saldo_arrastrable) < ZERO:
        raise CajaOperacionError("Los importes del cierre no pueden ser negativos.")
    if saldo_arrastrable > total_contado:
        raise CajaOperacionError("El saldo para la próxima apertura no puede superar el efectivo contado.")
    if importe_retirado + saldo_arrastrable != total_contado:
        raise CajaOperacionError("El efectivo retirado más el saldo para próxima apertura debe coincidir con el total contado.")
    return total_contado, importe_retirado, saldo_arrastrable
