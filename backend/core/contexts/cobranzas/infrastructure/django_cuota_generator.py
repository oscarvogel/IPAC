from django.db import transaction

from ....access_scope import scoped_queryset_for_user
from ....models import (
    Alumno,
    CarreraCurso,
    ConceptoCobrable,
    Cuota,
    Matricula,
    TipoDescuento,
)
from ..application.generar_cuotas import (
    GeneracionCuotasError,
    ResultadoGeneracionCuotas,
)
from ..domain.desglose_cuota import DesgloseCuotaError, calcular_desglose


def alumnos_bloqueados(*, alumno_ids, actor):
    """Alumnos a cotizar, con bloqueo de fila para evitar que dos pagos los generen a la vez.

    Esta consulta no debe usar ``select_related``. ``Alumno.carrera`` es
    nullable, asi que el join seria un LEFT OUTER y PostgreSQL rechaza el
    ``FOR UPDATE`` sobre el lado nullable de un outer join. Ademas en SQLite
    ``select_for_update`` es un no-op, de modo que el problema solo aparece
    cuando la base es PostgreSQL. Las carreras se cargan aparte, en una sola
    consulta, para no perder la garantia de no-N+1.
    """
    return scoped_queryset_for_user(
        Alumno.objects.filter(
            id__in=alumno_ids,
            estado=Alumno.Estado.ACTIVO,
        ),
        actor,
    ).select_for_update().order_by("apellido", "nombre", "id")


class DjangoCuotaGenerator:
    """Adaptador ORM para Cobranzas; core.models permanece como infraestructura heredada."""

    @transaction.atomic
    def generar(self, *, actor, solicitud):
        concepto = scoped_queryset_for_user(
            ConceptoCobrable.objects.filter(activo=True), actor
        ).filter(pk=solicitud.concepto_id).first()
        if not concepto:
            raise GeneracionCuotasError("Concepto inválido o sin acceso.")

        alumnos = list(
            alumnos_bloqueados(alumno_ids=solicitud.alumno_ids, actor=actor)
        )
        if len(alumnos) != len(solicitud.alumno_ids):
            raise GeneracionCuotasError("Hay alumnos inválidos, inactivos o de otra sucursal.")
        if any(alumno.sucursal_id != concepto.sucursal_id for alumno in alumnos):
            raise GeneracionCuotasError("El concepto debe pertenecer a la sucursal de todos los alumnos.")

        planificacion = solicitud.planificacion

        # Las cuotas que ya existen se bloquean antes de decidir qué falta. Sin
        # este lock, dos operadores que presionan el botón a la vez en temporada
        # de rematriculacion corren la misma operacion y la segunda choca contra
        # el unique (alumno, concepto, periodo) con un 500 en vez de saltarse
        # los duplicados.
        #
        # Ojo: esta consulta no puede combinarse con la de alumnos mediante
        # select_related. Alumno.carrera es nullable, asi que el join es un
        # LEFT OUTER, y PostgreSQL rechaza el FOR UPDATE sobre el lado nullable
        # de un outer join. Ademas en SQLite el select_for_update es un no-op,
        # por lo que el error solo aparece en PostgreSQL. Las carreras se cargan
        # en su propia consulta: una sola vez, sin N+1 y sin tocar el bloqueo.
        ya_cubiertas = {
            (alumno_id, periodo)
            for alumno_id, periodo in Cuota.objects.select_for_update()
            .filter(
                alumno_id__in=solicitud.alumno_ids,
                concepto=concepto,
                periodo__in=planificacion.nombres,
            )
            .values_list("alumno_id", "periodo")
        }

        importe = solicitud.importe if solicitud.importe is not None else concepto.importe
        descuento = solicitud.descuento
        recargo = solicitud.recargo
        if importe <= 0 or descuento > importe + recargo:
            raise GeneracionCuotasError("Los importes, descuentos o recargos no son válidos.")

        tipo_descuento = None
        motivo_descuento = solicitud.motivo_descuento
        if solicitud.tipo_descuento_id:
            tipo_descuento = scoped_queryset_for_user(
                TipoDescuento.objects.filter(activo=True), actor
            ).filter(pk=solicitud.tipo_descuento_id, sucursal=concepto.sucursal).first()
            if not tipo_descuento:
                raise GeneracionCuotasError("Tipo de descuento inválido o sin acceso.")
            if tipo_descuento.valor > 0:
                descuento = tipo_descuento.calcular(importe)
        elif descuento > 0:
            tipo_descuento, _ = TipoDescuento.objects.get_or_create(
                nombre="Excepción manual",
                sucursal=concepto.sucursal,
                defaults={"modalidad": TipoDescuento.Modalidad.IMPORTE, "valor": 0},
            )
            motivo_descuento = motivo_descuento or "Ajuste manual"

        if descuento < 0 or recargo < 0 or descuento > importe + recargo:
            raise GeneracionCuotasError("Los importes, descuentos o recargos no son válidos.")

        # La carrera se toma de la matricula activa. Cuando el alumno todavia no
        # esta matriculado se recurre a la carrera de su ficha, porque en
        # temporada de inscripcion las matriculas se cargan mas tarde que las
        # cuotas y sin ese respaldo el comprobante saldria sin desglose.
        #
        # Se consulta una sola vez para todo el lote, no una vez por periodo: la
        # carrera no cambia entre las cuotas de un mismo alumno.
        carrera_por_alumno = {
            alumno_id: carrera_id
            for alumno_id, carrera_id in Matricula.objects.filter(
                alumno_id__in=solicitud.alumno_ids,
                estado=Matricula.Estado.ACTIVA,
            ).values_list("alumno_id", "carrera_id")
        }
        for alumno in alumnos:
            if alumno.carrera_id and alumno.id not in carrera_por_alumno:
                carrera_por_alumno[alumno.id] = alumno.carrera_id

        carreras = {
            carrera.id: carrera
            for carrera in CarreraCurso.objects.filter(
                id__in=set(carrera_por_alumno.values())
            )
        }

        # El desglose se congela aqui con los precios del catalogo vigentes en el
        # momento de generar la cuota. Si el catalogo cambia despues, los recibos
        # ya emitidos conservan el reparto con el que se cobraron. Es el mismo
        # reparto para todos los periodos del lote: el importe y el catalogo no
        # cambian entre cuotas del mismo alumno.
        omitidas = []
        a_crear = []
        for alumno in alumnos:
            carrera = carreras.get(carrera_por_alumno.get(alumno.id))
            try:
                desglose = calcular_desglose(
                    importe=importe,
                    programatico_catalogo=getattr(carrera, "cuota_programatica", None),
                    extraprogramatica_catalogo=getattr(carrera, "cuota_extraprogramatica", None),
                )
            except DesgloseCuotaError as exc:
                # Un error de catalogo no debe llegar al usuario como 500.
                raise GeneracionCuotasError(str(exc)) from exc

            for periodo in planificacion.periodos:
                if (alumno.id, periodo.periodo) in ya_cubiertas:
                    omitidas.append({"alumno_id": alumno.id, "periodo": periodo.periodo})
                    continue
                a_crear.append(
                    Cuota(
                        alumno=alumno,
                        concepto=concepto,
                        sucursal_id=alumno.sucursal_id,
                        periodo=periodo.periodo,
                        fecha_emision=solicitud.fecha_emision,
                        fecha_vencimiento=periodo.fecha_vencimiento,
                        importe=importe,
                        descuento=descuento,
                        tipo_descuento=tipo_descuento,
                        motivo_descuento=motivo_descuento,
                        descuento_registrado_por=actor if descuento > 0 else None,
                        recargo=recargo,
                        importe_programatico=(desglose.importe_programatico if desglose else None),
                        importe_extraprogramatica=(desglose.importe_extraprogramatica if desglose else None),
                    )
                )

        creadas = Cuota.objects.bulk_create(a_crear) if a_crear else []
        return ResultadoGeneracionCuotas(creadas=creadas, omitidas=omitidas)
