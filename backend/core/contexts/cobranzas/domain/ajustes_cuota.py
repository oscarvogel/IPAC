from datetime import timedelta
from decimal import Decimal


def calcular_ajuste(*, modalidad, valor, importe_base):
    valor = Decimal(valor)
    importe_base = Decimal(importe_base)
    if modalidad == "porcentaje":
        return (importe_base * valor / Decimal("100")).quantize(Decimal("0.01"))
    return valor.quantize(Decimal("0.01"))


def corresponde_recargo(*, fecha_vencimiento, dias_tolerancia, fecha_evaluacion):
    return fecha_evaluacion > fecha_vencimiento + timedelta(days=int(dias_tolerancia or 0))
