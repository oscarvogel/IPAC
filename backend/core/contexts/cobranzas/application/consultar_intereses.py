"""Consulta el interés de mora de las cuotas con saldo, sin escribir nada.

Por qué este caso de uso **no** persiste el interés calculado:

IPAC no contestar si el interés *"se suma a la cuota original o se emite como
concepto separado"* (punto 3 del mail del 07/10/2026). Esa respuesta cambia la
forma de guardarlo: si se suma, alcanza con una columna en `Cuota`; si va como
concepto separado, hay que crear una cuota o un concepto por alumno y mes. Elegir
una de las dos ahora y equivocarse obliga a una migración con datos ya cobrados.

Por eso este caso de uso sólo **informa**. Cuando IPAC responda, el ajuste es un
caso de uso nuevo que escriba, y este queda como el preview que lo acompaña.
"""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Protocol

from ..domain.intereses import (
    ErrorInteres,
    PoliticaInteres,
    TasaInteres,
    evaluar_interes_cuota,
    seleccionar_tasa,
)

CERO = Decimal("0.00")

SIN_TASA_CARGA_MSG = (
    "No hay ninguna tasa de interés cargada para el alcance consultado. "
    "Cargá una tasa con vigencia antes de calcular el interés de las cuotas."
)


@dataclass(frozen=True)
class CuotaParaInteres:
    """Lo mínimo de una cuota que el cálculo necesita. Sin Django."""

    cuota_id: int
    sucursal_id: int
    periodo: str
    fecha_vencimiento: date
    saldo_pendiente: Decimal


@dataclass(frozen=True)
class ConfiguracionInteres:
    """Una tasa persistida con la política con la que se va a aplicar.

    Tasa y política se guardan en la misma fila, así que viajan juntas. Si se
    separaran, la política podría terminar aplicándose con la tasa equivocada.
    """

    sucursal_id: int
    tasa: TasaInteres
    politica: PoliticaInteres


class TasaInteresReader(Protocol):
    def configuraciones(self, *, sucursal_ids) -> list: ...


class CuotaInteresReader(Protocol):
    def cuotas_con_saldo(self, *, sucursal_ids, fecha_evaluacion) -> list: ...


@dataclass(frozen=True)
class InteresDeCuota:
    cuota_id: int
    sucursal_id: int
    saldo_pendiente: Decimal
    dias_interesables: int
    periodos: Decimal
    importe: Decimal


@dataclass(frozen=True)
class ResumenIntereses:
    fecha_evaluacion: date
    cuotas_evaluadas: int = 0
    cuotas_con_interes: int = 0
    total_interes: Decimal = CERO
    sin_tasa: list = field(default_factory=list)
    detalle: list = field(default_factory=list)


class ConsultarIntereses:
    """Interés de mora proyectado para las cuotas con saldo.

    Cada sucursal va con la suya: las tasas pueden tener vigencias distintas por
    sucursal y, con ellas, distinta base y unidad de cálculo.
    """

    def __init__(self, tasas: TasaInteresReader, cuotas: CuotaInteresReader):
        self.tasas = tasas
        self.cuotas = cuotas

    def execute(self, *, sucursal_ids, fecha_evaluacion: date) -> ResumenIntereses:
        vigentes = self._vigentes_por_sucursal(sucursal_ids, fecha_evaluacion)
        pendientes = self.cuotas.cuotas_con_saldo(
            sucursal_ids=sucursal_ids, fecha_evaluacion=fecha_evaluacion
        )

        detalle = []
        sin_tasa = []
        total = CERO
        for cuota in pendientes:
            configuracion = vigentes.get(cuota.sucursal_id)
            if configuracion is None:
                sin_tasa.append(cuota.cuota_id)
                continue
            resultado = evaluar_interes_cuota(
                periodo=cuota.periodo,
                fecha_vencimiento=cuota.fecha_vencimiento,
                importe_base=cuota.saldo_pendiente,
                fecha_evaluacion=fecha_evaluacion,
                tasa=configuracion.tasa,
                politica=configuracion.politica,
            )
            total += resultado.importe
            detalle.append(
                InteresDeCuota(
                    cuota_id=cuota.cuota_id,
                    sucursal_id=cuota.sucursal_id,
                    saldo_pendiente=cuota.saldo_pendiente,
                    dias_interesables=resultado.dias_interesables,
                    periodos=resultado.periodos_legibles,
                    importe=resultado.importe,
                )
            )

        return ResumenIntereses(
            fecha_evaluacion=fecha_evaluacion,
            cuotas_evaluadas=len(pendientes),
            cuotas_con_interes=sum(1 for i in detalle if i.importe > 0),
            total_interes=total,
            sin_tasa=sorted(sin_tasa),
            detalle=detalle,
        )

    def _vigentes_por_sucursal(self, sucursal_ids, fecha_evaluacion: date) -> dict:
        """Configuración vigente de cada sucursal en la fecha de evaluación.

        Una sucursal sin tasa cargada no es un error: sus cuotas se listan aparte
        en ``sin_tasa`` para que el operador vea el hueco. Si no hay ninguna tasa
        en todo el alcance, sí es un error de configuración y lo dice con todas
        las letras, porque el cálculo no puede dar un número creíble.
        """
        candidatas = self.tasas.configuraciones(sucursal_ids=sucursal_ids)
        if not candidatas:
            raise ErrorInteres(SIN_TASA_CARGA_MSG)

        por_sucursal = {}
        for configuracion in candidatas:
            por_sucursal.setdefault(configuracion.sucursal_id, []).append(configuracion)

        vigentes = {}
        for sucursal_id, configuraciones in por_sucursal.items():
            candidates_en_fecha = [
                c for c in configuraciones if c.tasa.vigente_en(fecha_evaluacion)
            ]
            if not candidates_en_fecha:
                continue
            # Se delega el desempate al dominio: la más reciente, y a igualdad
            # de inicio la de vigencia más acotada.
            elegida = seleccionar_tasa(
                [c.tasa for c in candidates_en_fecha], fecha_evaluacion
            )
            vigentes[sucursal_id] = next(
                c for c in candidates_en_fecha if c.tasa == elegida
            )
        return vigentes