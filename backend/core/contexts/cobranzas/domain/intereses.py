"""Interés de mora de las cuotas, con la tasa parametrizada por vigencia.

Qué respondió IPAC el 07/10/2026 (punto 3 del mail) y qué quedó asumido:

Confirmado por IPAC:

- La tasa mensual es **parametrizable** porque va a cambiar con la inflación.
- El interés **no se cuenta desde la fecha de vencimiento**: se cuenta desde el
  **día 1 del mes**. Textualmente: *"las cuotas vencen el día 10, pero el interés
  se cuenta desde el día 1 del mes si se paga al mes siguiente"*.
- **Aplica igual para todas las cuotas**, sin excepción por carrera ni alumno.

Todavía NO contestado, y por eso este módulo no persiste nada:

- El **número exacto** de la tasa mensual y desde qué fecha rige. En la reunión
  del 24/09/2026 se consolidationó un rango de 5,2% a 5,5%. No se carga ninguna
  tasa por omisión: este módulo sólo dice *cómo* se calcula. Cargar un número
  inventado es peor que no cargar nada, porque un interés mal aplicado se
  devuelve con nota de crédito o con demanda.
- Si el interés **se suma a la cuota** o se emite como **concepto separado**.
  La respuesta de IPAC al punto 1 dice que el recargo *"se registra bajo el
  concepto: otros conceptos educativos"*, lo que sugiere concepto separado,
  pero no lo especificaciones. Por eso acá no se decide: se calcula y se informa.
- El **descuento por pago anticipado en efectivo**. IPAC dijo que existe un
  descuento en ese caso, pero no especificó en cuánto ni en qué condiciones.

Supuestos por defecto, marcados abajo con SUPUESTO. Si la planilla manual que
mandaron por WhatsApp dice otra cosa, se corrigen estas constantes y los tests
que las fijan avisan: no hay que reescribir el cálculo.

Este módulo es puro. No conoce Django ni la base de datos.
"""

from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from .planificacion_cuotas import PeriodoCuota

CENT = Decimal("0.01")
CERO = Decimal("0.00")

#: Base desde la que se cuenta el interés.
BASE_DESDE_DIA_1 = "dia_1_del_mes"
BASE_DESDE_VENCIMIENTO = "fecha_vencimiento"
BASES_CALCULO = (BASE_DESDE_DIA_1, BASE_DESDE_VENCIMIENTO)

#: Unidad en la que se aplica la tasa mensual.
UNIDAD_MESES = "meses"
UNIDAD_DIAS = "dias"
UNIDADES_CALCULO = (UNIDAD_MESES, UNIDAD_DIAS)

#: Mes de 30 días para prorratear. Es una convención, no un calendario: el
#: interés es un costo financiero, no un plazo judicial.
DIAS_POR_MES = 30

BASE_MSG = (
    f"La base de cálculo del interés debe ser una de: {', '.join(BASES_CALCULO)}."
)
UNIDAD_MSG = (
    f"La unidad de cálculo del interés debe ser una de: {', '.join(UNIDADES_CALCULO)}."
)
TASA_NEGATIVA_MSG = "La tasa de interés no puede ser negativa."
VIGENCIA_INVERTIDA_MSG = "La vigencia de la tasa de interés está invertida."
TASA_VIGENTE_MSG = (
    "No hay tasa de interés vigente para la fecha evaluada. "
    "Cargá una tasa antes de calcular el interés de las cuotas."
)


class ErrorInteres(ValueError):
    """Error funcional al calcular el interés de una cuota."""

    def __init__(self, detail):
        super().__init__(detail)
        self.detail = detail


@dataclass(frozen=True)
class TasaInteres:
    """Una tasa mensual de interés con su período de vigencia.

    La tasa vive en la base pero la regla no: varias tasas pueden coexistir y el
    cálculo elige la que estaba vigente el día de la evaluación. Sirve para que
    subir la tasa por inflación no requiera tocar código.
    """

    porcentaje_mensual: Decimal
    vigencia_desde: date
    vigencia_hasta: date | None = None

    def __post_init__(self):
        if Decimal(str(self.porcentaje_mensual)) < 0:
            raise ErrorInteres(TASA_NEGATIVA_MSG)
        if self.vigencia_hasta and self.vigencia_hasta < self.vigencia_desde:
            raise ErrorInteres(VIGENCIA_INVERTIDA_MSG)

    def vigente_en(self, fecha: date) -> bool:
        if fecha < self.vigencia_desde:
            return False
        return self.vigencia_hasta is None or fecha <= self.vigencia_hasta


@dataclass(frozen=True)
class PoliticaInteres:
    """Con qué regla se cuenta el interés de una cuota vencida.

    Los dos parámetros existen porque IPAC todavía no cerró la planilla
    manual. Cambiar de regla debe ser cambiar un parámetro, no el cálculo.
    """

    base_calculo: str = BASE_DESDE_DIA_1
    unidad_calculo: str = UNIDAD_MESES

    def __post_init__(self):
        if self.base_calculo not in BASES_CALCULO:
            raise ErrorInteres(BASE_MSG)
        if self.unidad_calculo not in UNIDADES_CALCULO:
            raise ErrorInteres(UNIDAD_MSG)


#: SUPUESTO 1: el interés arranca recién cuando la cuota pasa de su mes. Una
#: cuota de marzo vencía el 10/03 y se paga el 25/03 sin interés; recién al día
#: 1 de abril se cuenta, porque "si se paga al mes siguiente" es lo que IPAC
#: describió. Con la base desde el vencimiento, el 25/03 pagaría 15 días.
#: SUPUESTO 2: se cobran meses completos, no días prorrateados. Es la lectura
#: literal de "tasa mensual", y además es la que menos cobra al alumno. Si la
#: planilla prorratea por días, se cambia ``unidad_calculo`` a ``UNIDAD_DIAS``.
POLITICA_POR_DEFECTO = PoliticaInteres()


@dataclass(frozen=True)
class InteresCuota:
    """Interés calculado para una cuota en una fecha de evaluación."""

    dias_interesables: int
    periodos: Decimal
    importe: Decimal

    @property
    def periodos_legibles(self) -> Decimal:
        """Períodos redondeados para mostrar. El importe ya viene redondeado."""
        return self.periodos.quantize(CENT, rounding=ROUND_HALF_UP)


def _dia_1_del_mes(anio: int, mes: int) -> date:
    return date(anio, mes, 1)


def _mes_siguiente(anio: int, mes: int) -> tuple[int, int]:
    return (anio + 1, 1) if mes == 12 else (anio, mes + 1)


def fecha_base_interes(*, periodo: str, fecha_vencimiento: date, politica=POLITICA_POR_DEFECTO) -> date:
    """Día desde el que se cuenta el interés de la cuota.

    Con la base por defecto es el día 1 del mes del período, no la fecha de
    vencimiento: esa es la diferencia exacta que describió IPAC.
    """
    if politica.base_calculo == BASE_DESDE_VENCIMIENTO:
        return fecha_vencimiento
    p = PeriodoCuota(periodo=periodo)
    return _dia_1_del_mes(p.anio, p.mes)


def fecha_inicio_interes(*, periodo: str, fecha_vencimiento: date, politica=POLITICA_POR_DEFECTO) -> date:
    """Primer día en el que la cuota genera interés."""
    if politica.base_calculo == BASE_DESDE_VENCIMIENTO:
        return fecha_vencimiento
    p = PeriodoCuota(periodo=periodo)
    anio, mes = _mes_siguiente(p.anio, p.mes)
    return _dia_1_del_mes(anio, mes)


def dias_interesables(
    *, periodo: str, fecha_vencimiento: date, fecha_evaluacion: date, politica=POLITICA_POR_DEFECTO
) -> int:
    """Días que se cobraron como interés.

    Cero mientras la cuota esté dentro de su mes de período. Después se cuenta
    desde el día 1 de ese mes, así que pagar el primer día del mes siguiente
    son 31 días y no uno.
    """
    inicio = fecha_inicio_interes(
        periodo=periodo, fecha_vencimiento=fecha_vencimiento, politica=politica
    )
    if fecha_evaluacion < inicio:
        return 0
    base = fecha_base_interes(
        periodo=periodo, fecha_vencimiento=fecha_vencimiento, politica=politica
    )
    return max((fecha_evaluacion - base).days, 0)


def periodos_interesables(dias: int, politica=POLITICA_POR_DEFECTO) -> Decimal:
    """Cuántos períodos de la tasa se aplican a esos días.

    Devuelve el valor **exacto**, sin redondear. Redondear acá y después
    multiplicar mete error en el importe: 35 días a 5,5% sobre 10.000 da
    641,67, pero si los períodos se truncan a 1,17 el resultado sube a 643,50.
    El redondeo a moneda ocurre una sola vez, al final, en ``calcular_interes``.
    """
    if dias <= 0:
        return Decimal("0")
    if politica.unidad_calculo == UNIDAD_MESES:
        return Decimal(dias // DIAS_POR_MES)
    return Decimal(dias) / Decimal(DIAS_POR_MES)


def calcular_interes(*, importe_base, tasa: TasaInteres, dias: int, politica=POLITICA_POR_DEFECTO) -> Decimal:
    """Interés simple sobre el importe adeudado, sin capitalización.

    El importe base lo decide quien llama. Para una cuota totalmente impaga es
    ``importe - descuento``, igual que el recargo. Para una cuota parcialmente
    paga tiene que ser el **saldo pendiente**, o se cobra interés sobre plata
    que el alumno ya abonó.
    """
    base = Decimal(str(importe_base))
    if base <= 0 or dias <= 0:
        return CERO
    porcentaje = Decimal(str(tasa.porcentaje_mensual))
    if porcentaje <= 0:
        return CERO
    return (base * porcentaje * periodos_interesables(dias, politica) / Decimal("100")).quantize(
        CENT, rounding=ROUND_HALF_UP
    )


def evaluar_interes_cuota(
    *,
    periodo: str,
    fecha_vencimiento: date,
    importe_base,
    fecha_evaluacion: date,
    tasa: TasaInteres,
    politica=POLITICA_POR_DEFECTO,
) -> InteresCuota:
    """Calcula el interés de una cuota en una fecha. Entrada del caso de uso."""
    dias = dias_interesables(
        periodo=periodo,
        fecha_vencimiento=fecha_vencimiento,
        fecha_evaluacion=fecha_evaluacion,
        politica=politica,
    )
    return InteresCuota(
        dias_interesables=dias,
        periodos=periodos_interesables(dias, politica),
        importe=calcular_interes(
            importe_base=importe_base, tasa=tasa, dias=dias, politica=politica
        ),
    )


def seleccionar_tasa(tasas, fecha_evaluacion: date) -> TasaInteres:
    """Tasa vigente en la fecha de evaluación.

    Si varias rigen el mismo día gana la más reciente, y a igualdad de inicio
    la de vigencia más acotada: una tasa de emergencia para un mes puntual
    pisa a una general abierta.
    """
    vigentes = [tasa for tasa in tasas if tasa.vigente_en(fecha_evaluacion)]
    if not vigentes:
        raise ErrorInteres(TASA_VIGENTE_MSG)
    return max(
        vigentes,
        key=lambda t: (
            t.vigencia_desde,
            # Sin fecha de cierre la tasa general tiene que perder contra la
            # acotada, aunque su `vigencia_hasta` sea "infinito".
            t.vigencia_hasta is not None,
            t.vigencia_hasta or date.min,
        ),
    )