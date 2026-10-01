"""Traduce el payload de la API al lote de períodos que pide el operador.

Vive en aplicación y no en el controller porque la decisión de qué camino se
toma (lote de N meses o un período suelto) es una regla de negocio, no un
detalle del transporte. Previsualizar y generar tienen que aplicar exactamente
la misma, o el operador previsualiza un lote y genera otro.
"""

from ..domain.planificacion_cuotas import (
    ErrorPlanificacionCuotas,
    planificar_periodo_unico,
    planificar_secuencia,
)

DIA_VENCIMIENTO_POR_DEFECTO = 10


class PayloadDeCuotasInvalido(ValueError):
    def __init__(self, detail):
        super().__init__(detail)
        self.detail = detail


def es_lote(payload) -> bool:
    """El lote se pide con ``cantidad``; el período único no lo envía.

    Ojo con comparar contra la verdadiness del valor: ``cantidad: 0`` es un
    lote con error, no la ausencia del campo. Si se dejara pasar por el camino
    del período único, el operador vería "el período es obligatorio" cuando lo
    que hizo fue escribir cero.
    """
    valor = payload.get("cantidad")
    return valor is not None and str(valor).strip() != ""


def planificacion_desde_payload(payload):
    """Arma el lote, o falla con un mensaje que el operador pueda corregir.

    Son dos caminos y no uno con campos opcionales porque significan cosas
    distintas: el lote reparte el vencimiento con una regla (día fijo del mes),
    mientras que el período único deja que el operador elija la fecha a mano.
    """
    try:
        if es_lote(payload):
            return planificar_secuencia(
                cantidad=payload.get("cantidad"),
                mes_inicial=payload.get("mes_inicial", payload.get("mes")),
                anio_inicial=payload.get("anio_inicial", payload.get("anio")),
                dia_vencimiento=payload.get(
                    "dia_vencimiento", DIA_VENCIMIENTO_POR_DEFECTO
                ),
            )
        return planificar_periodo_unico(
            periodo=payload.get("periodo"),
            fecha_vencimiento=payload.get("fecha_vencimiento"),
        )
    except ErrorPlanificacionCuotas as exc:
        raise PayloadDeCuotasInvalido(exc.detail) from exc
