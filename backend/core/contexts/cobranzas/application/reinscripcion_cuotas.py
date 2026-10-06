"""Generación de cuotas al reinscribir un alumno.

Contexto: Alumnos y Trayectoria Académica es dueño de la matrícula, Cobranzas
es dueño de la cuota. Este caso de uso vive en Cobranzas porque lo que produce
son cuotas, pero recibe la matrícula como DTO y no como modelo: Trayectoria no
presta su modelo interno, solo publica los datos que la reinscripción necesita.

Por qué existe un caso de uso aparte y no alcanza con llamar a ``GenerarCuotas``
desde la vista: hay dos invariantes que no pueden quedar en manos de quien
llama. La generación apunta a **un solo alumno**, el de la matrícula, y las
cuotas quedan **enlazadas a esa matrícula**. Si eso dependiera del payload, un
``alumnos: [...]`` equivocado desde cualquier pantalla generaría deuda al
alumno que no es.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from ..domain.planificacion_cuotas import (
    DIA_VENCIMIENTO_POR_DEFECTO,
    ErrorPlanificacionCuotas,
    PlanificacionCuotas,
    planificar_secuencia,
    planificacion_sugerida,
)
from .generar_cuotas import (
    CuotaGenerator,
    GeneracionCuotasError,
    GenerarCuotas,
    ResultadoGeneracionCuotas,
)


@dataclass(frozen=True)
class MatriculaReinscribible:
    """Lo que Cobranzas necesita saber de una matrícula, y nada más."""

    matricula_id: int
    alumno_id: int
    fecha_inicio: date
    #: ``CarreraCurso.plan_cuotas``. Puede venir en None si la carrera no tiene
    #: plan cargado en el catálogo.
    plan_cuotas: int | None = None

    def __post_init__(self):
        # Se normaliza acá y no en el punto de uso porque este DTO cruza un
        # limite de contexto: quien lo arma puede tener la fecha recien
        # guardada y todavia en memoria como texto. Que el contrato acepte las
        # dos formas evita que un AttributeError aparezca tres capas mas abajo,
        # adentro del dominio, con un error que no dice nada de matriculas.
        if not isinstance(self.fecha_inicio, date):
            try:
                coerced = date.fromisoformat(str(self.fecha_inicio))
            except (TypeError, ValueError):
                raise GeneracionCuotasError(
                    "La fecha de inicio de la matrícula no es válida."
                ) from None
            object.__setattr__(self, "fecha_inicio", coerced)


def _dia(valor):
    """Dia de vencimiento a usar, o el que maneja IPAC si no vino.

    Solo "sin dato" trae el default. Un ``0`` es un dato escrito y es invalido:
    con ``or`` caeria al dia 10 en silencio y el operador veria un vencimiento
    que nunca eligio, que es justo lo que el dominio quiere evitar.
    """
    if valor is None or valor == "":
        return DIA_VENCIMIENTO_POR_DEFECTO
    return valor


def sugerir_plan(*, matricula: MatriculaReinscribible, dia_vencimiento=None):
    """Plan por defecto de la reinscripción, o ``None`` si la carrera no tiene plan.

    Devolver ``None`` es una decisión, no una falla: sin plan cargado en el
    catálogo no hay forma honesta de saber cuántas cuotas debe el alumno, y un
    número inventado es deuda que el alumno no contrajo.
    """
    return planificacion_sugerida(
        plan_cuotas=matricula.plan_cuotas,
        fecha_inicio=matricula.fecha_inicio,
        dia_vencimiento=_dia(dia_vencimiento),
    )


def _plan_sugerido(matricula: MatriculaReinscribible, dia):
    """Sugerencia del plan, con los errores ya traducidos.

    Mismo criterio que ``_plan_para``: el dominio lanza
    ``ErrorPlanificacionCuotas`` y quien llama al caso de uso —la vista—
    maneja ``GeneracionCuotasError``. Sin esta traduccion, un dia de
    vencimiento invalido escapaba hasta Django y salia un 500.
    """
    try:
        return sugerir_plan(matricula=matricula, dia_vencimiento=dia)
    except ErrorPlanificacionCuotas as exc:
        raise GeneracionCuotasError(exc.detail) from exc


class GenerarCuotasDeMatricula:
    """Genera el año de cuotas de un alumno a partir de su matrícula activa."""

    def __init__(self, generator: CuotaGenerator):
        self._generar = GenerarCuotas(generator)

    def execute(
        self,
        *,
        actor,
        matricula: MatriculaReinscribible,
        concepto_id,
        cantidad=None,
        dia_vencimiento=None,
        fecha_emision: date,
        importe: Decimal | None = None,
        descuento: Decimal = Decimal("0"),
        recargo: Decimal = Decimal("0"),
        tipo_descuento_id=None,
        motivo_descuento="",
    ) -> ResultadoGeneracionCuotas:
        dia = _dia(dia_vencimiento)
        sugerencia = _plan_sugerido(matricula, dia)

        if cantidad in (None, ""):
            if sugerencia is None:
                raise GeneracionCuotasError(
                    "La carrera no tiene un plan de cuotas configurado. "
                    "Indicá cuántas cuotas se generan."
                )
            cantidad = sugerencia.cantidad

        planificacion = _plan_para(
            cantidad=cantidad,
            fecha_inicio=matricula.fecha_inicio,
            dia_vencimiento=dia,
        )

        # Se delega a GenerarCuotas y no se reimplementa la validación: la
        # previsualización y esta reinscripción tienen que aplicar exactamente
        # las mismas reglas, o el operador previsualiza un lote y genera otro.
        return self._generar.execute(
            actor=actor,
            payload={
                "alumnos": [matricula.alumno_id],
                "concepto": concepto_id,
                "matricula": matricula.matricula_id,
                "cantidad": planificacion.cantidad,
                "mes_inicial": planificacion.primero.mes,
                "anio_inicial": planificacion.primero.anio,
                "dia_vencimiento": dia,
                "fecha_emision": fecha_emision,
                "importe": importe,
                "descuento": descuento,
                "recargo": recargo,
                "tipo_descuento": tipo_descuento_id,
                "motivo_descuento": motivo_descuento,
            },
        )


def _plan_para(*, cantidad, fecha_inicio, dia_vencimiento) -> PlanificacionCuotas:
    try:
        return planificar_secuencia(
            cantidad=cantidad,
            mes_inicial=fecha_inicio.month,
            anio_inicial=fecha_inicio.year,
            dia_vencimiento=dia_vencimiento,
        )
    except ErrorPlanificacionCuotas as exc:
        raise GeneracionCuotasError(exc.detail) from exc
