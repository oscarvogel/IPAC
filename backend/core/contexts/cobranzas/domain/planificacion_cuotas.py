"""Planificación de un lote de cuotas de un mismo concepto.

El dominio no sabe nada de Django, ORM ni HTTP. Solo decide qué períodos
componen el lote y qué fecha de vencimiento lleva cada uno.

Contexto: Alumnos y Trayectoria Académica define *quién* está matriculado;
Cobranzas define *qué* se le cobra. Este módulo pertenece a Cobranzas.

Por qué existe: la generación de cuotas venía siendo de un período a la vez
("2026-08"), lo que obligaba a repetir la misma operación diez veces para
cubrir un año lectivo. En temporada de rematriculación eso no es viable a mano.
"""

from dataclasses import dataclass
from datetime import date

#: Tope de cuotas por lote. Es una guarda contra errores de tipeo (escribir
#: 100 en lugar de 10 genera 100 filas por alumno de un golpe), no una regla
#: de negocio: dos años lectivos seguidos es un caso razonable y entra.
CANTIDAD_MAXIMA = 24

#: El día de vencimiento se limita a 28 a propósito. February tiene 28 días
#: en años no bisiestos, así que un día 29, 30 o 31 haría inválida la fecha de
#:febrero. Preferimos rechazar el dato a ajustarlo en silencio: si el operador
#: elige el 30 y le corremos al 28 sin avisarle, el vencimiento ya no es el que
#: él decidió y no lo va a notar hasta que un alumno diga que se le venció
#: antes de tiempo.
DIA_VENCIMIENTO_MAXIMO = 28

MESES = (
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
)

#: Día de vencimiento por defecto. Es el que declaró IPAC en la reunión del
#: 24/09/2026: las cuotas vencen el día 10, aunque los intereses se calculen
#: desde el día 1 del mes.
DIA_VENCIMIENTO_POR_DEFECTO = 10


class ErrorPlanificacionCuotas(ValueError):
    def __init__(self, detail):
        super().__init__(detail)
        self.detail = detail


@dataclass(frozen=True)
class PeriodoCuota:
    """Un período del lote y la fecha en que su cuota vence.

    ``fecha_vencimiento`` puede ser ``None``: la previsualización solo necesita
    saber qué períodos existen, no cuándo vencen. La obligatoriedad se verifica
    al generar, no al planificar, para que previsualizar un período suelto no
    exija una fecha que la pantalla de vista previa nunca usa.
    """

    periodo: str
    fecha_vencimiento: date | None = None

    def __post_init__(self):
        if not _es_periodo_valido(self.periodo):
            raise ErrorPlanificacionCuotas(
                f"El período {self.periodo!r} no tiene el formato AAAA-MM."
            )

    @property
    def anio(self) -> int:
        return int(self.periodo[:4])

    @property
    def mes(self) -> int:
        return int(self.periodo[5:7])

    @property
    def etiqueta(self) -> str:
        """Texto para mostrar al operador: período más su vencimiento."""
        mes = f"{MESES[self.mes - 1]} {self.anio}"
        if self.fecha_vencimiento is None:
            return mes
        return f"{mes} (vence el {self.fecha_vencimiento.day})"


@dataclass(frozen=True)
class PlanificacionCuotas:
    """La lista ordenada de períodos que componen el lote."""

    periodos: tuple[PeriodoCuota, ...]

    def __post_init__(self):
        if not self.periodos:
            raise ErrorPlanificacionCuotas("El lote debe tener al menos un período.")
        vistos = {p.periodo for p in self.periodos}
        if len(vistos) != len(self.periodos):
            raise ErrorPlanificacionCuotas("El lote tiene períodos repetidos.")

    @property
    def cantidad(self) -> int:
        return len(self.periodos)

    @property
    def primero(self) -> PeriodoCuota:
        return self.periodos[0]

    @property
    def ultimo(self) -> PeriodoCuota:
        return self.periodos[-1]

    @property
    def nombres(self) -> list[str]:
        return [p.periodo for p in self.periodos]

    @property
    def etiquetas(self) -> list[str]:
        return [p.etiqueta for p in self.periodos]

    def total_para(self, cantidad_alumnos: int) -> int:
        """Cuántas filas genera el lote, sin contar las que ya existen."""
        return self.cantidad * max(0, cantidad_alumnos)


def _es_periodo_valido(periodo) -> bool:
    if not isinstance(periodo, str) or len(periodo) != 7 or periodo[4] != "-":
        return False
    anio, mes = periodo[:4], periodo[5:]
    if not (anio.isdigit() and mes.isdigit()):
        return False
    return 1 <= int(mes) <= 12 and 2000 <= int(anio) <= 2100


def _entero(valor, etiqueta, *, minimo, maximo):
    if valor in (None, ""):
        raise ErrorPlanificacionCuotas(f"{etiqueta} es obligatorio.")
    try:
        parsed = int(valor)
    except (TypeError, ValueError):
        raise ErrorPlanificacionCuotas(f"{etiqueta} debe ser un número entero.") from None
    if not minimo <= parsed <= maximo:
        raise ErrorPlanificacionCuotas(
            f"{etiqueta} debe estar entre {minimo} y {maximo}."
        )
    return parsed


def planificar_secuencia(*, cantidad, mes_inicial, anio_inicial, dia_vencimiento):
    """Arma un lote de cuotas mensuales consecutivas.

    El lote puede cruzar el cambio de año: empezar en noviembre con cantidad 3
    produce 2026-11, 2026-12 y 2027-01. Cada cuota vence el ``dia_vencimiento``
    de su propio mes.
    """
    total = _entero(cantidad, "La cantidad de cuotas", minimo=1, maximo=CANTIDAD_MAXIMA)
    mes = _entero(mes_inicial, "El mes inicial", minimo=1, maximo=12)
    anio = _entero(anio_inicial, "El año inicial", minimo=2000, maximo=2100)
    dia = _entero(
        dia_vencimiento, "El día de vencimiento", minimo=1, maximo=DIA_VENCIMIENTO_MAXIMO
    )

    periodos = []
    cursor_anio, cursor_mes = anio, mes
    for _ in range(total):
        periodos.append(
            PeriodoCuota(
                periodo=f"{cursor_anio:04d}-{cursor_mes:02d}",
                fecha_vencimiento=date(cursor_anio, cursor_mes, dia),
            )
        )
        cursor_mes += 1
        if cursor_mes > 12:
            cursor_mes = 1
            cursor_anio += 1
    return PlanificacionCuotas(periodos=tuple(periodos))


def planificar_periodo_unico(*, periodo, fecha_vencimiento=None):
    """Lote de un solo período. Es el camino que ya usaba el sistema.

    Se conserva para la generación individual, donde el operador elige el mes y
    la fecha a mano. No es un atajo de ``planificar_secuencia`` porque el
    vencimiento es libre: no siempre cae en el mismo día del mes.

    ``fecha_vencimiento`` es opcional porque la previsualización de un período
    suelto no la necesita. Quien genera tiene que exigirla antes de escribir.
    """
    if periodo in (None, ""):
        raise ErrorPlanificacionCuotas("El período es obligatorio.")
    if isinstance(fecha_vencimiento, str):
        if not fecha_vencimiento.strip():
            fecha_vencimiento = None
        else:
            try:
                fecha_vencimiento = date.fromisoformat(fecha_vencimiento)
            except (TypeError, ValueError):
                raise ErrorPlanificacionCuotas(
                    "La fecha de vencimiento debe ser una fecha válida."
                ) from None
    if fecha_vencimiento is not None and not isinstance(fecha_vencimiento, date):
        raise ErrorPlanificacionCuotas("La fecha de vencimiento debe ser una fecha válida.")

    return PlanificacionCuotas(
        periodos=(PeriodoCuota(periodo=str(periodo).strip(), fecha_vencimiento=fecha_vencimiento),)
    )


def planificacion_sugerida(
    *,
    plan_cuotas,
    fecha_inicio,
    dia_vencimiento=DIA_VENCIMIENTO_POR_DEFECTO,
):
    """Plan por defecto de una reinscripción: tantas cuotas como el plan, desde
    el mes en que arranca la matrícula.

    Devuelve ``None`` cuando la carrera no tiene plan configurado. No se inventa
    un número: si el catálogo no dice cuántas cuotas tiene el plan, el operador
    tiene que decidirlo, y un número inventado sería una deuda que el alumno no
    Debe.

    El lote puede cruzar el año: una reinscripción de noviembre con plan de 10
    produce de noviembre a agosto del año siguiente, que es como funciona una
    cohorte anual.
    """
    if not plan_cuotas or int(plan_cuotas) <= 0:
        return None
    return planificar_secuencia(
        cantidad=plan_cuotas,
        mes_inicial=fecha_inicio.month,
        anio_inicial=fecha_inicio.year,
        dia_vencimiento=dia_vencimiento,
    )


def exigir_vencimientos(planificacion):
    """Verifica que todo período tenga fecha antes de escribir cuotas.

    Vive acá y no en el caso de uso porque es una invariante de la
    ``PlanificacionCuotas``: una planificación que se va a persistir no puede
    tener períodos sin fecha. Quien solo previsualiza nunca la llama.
    """
    sin_fecha = [p.periodo for p in planificacion.periodos if p.fecha_vencimiento is None]
    if sin_fecha:
        raise ErrorPlanificacionCuotas(
            "Falta la fecha de vencimiento para el período " + sin_fecha[0] + "."
        )
    return planificacion
