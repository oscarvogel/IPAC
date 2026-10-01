from decimal import Decimal

from django.db import transaction

from ....access_scope import scoped_queryset_for_user
from ....models import Alumno, ConceptoCobrable, Cuota, Matricula, TipoDescuento
from ..application.generar_cuotas import GeneracionCuotasError
from ..domain.desglose_cuota import calcular_desglose


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
            scoped_queryset_for_user(
                Alumno.objects.filter(
                    id__in=solicitud.alumno_ids,
                    estado=Alumno.Estado.ACTIVO,
                ),
                actor,
            ).select_for_update().select_related("carrera").order_by("apellido", "nombre", "id")
        )
        if len(alumnos) != len(solicitud.alumno_ids):
            raise GeneracionCuotasError("Hay alumnos inválidos, inactivos o de otra sucursal.")
        if any(alumno.sucursal_id != concepto.sucursal_id for alumno in alumnos):
            raise GeneracionCuotasError("El concepto debe pertenecer a la sucursal de todos los alumnos.")

        existentes = list(
            Cuota.objects.select_for_update().filter(
                alumno_id__in=solicitud.alumno_ids,
                concepto=concepto,
                periodo=solicitud.periodo,
            ).values_list("alumno_id", flat=True)
        )
        if existentes:
            raise GeneracionCuotasError(
                "Ya existen cuotas para este concepto y período.",
                alumnos=existentes,
            )

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
        carreras_por_alumno = {
            matricula.alumno_id: matricula.carrera
            for matricula in Matricula.objects.filter(
                alumno_id__in=solicitud.alumno_ids,
                estado=Matricula.Estado.ACTIVA,
            ).select_related("carrera")
        }
        for alumno in alumnos:
            if alumno.carrera_id and alumno.carrera_id not in carreras_por_alumno:
                carreras_por_alumno[alumno.id] = alumno.carrera

        # El desglose se congela aqui con los precios del catalogo vigentes en el
        # momento de generar la cuota. Si el catalogo cambia despues, los recibos
        # ya emitidos conservan el reparto con el que se cobraron.
        cuotas = []
        for alumno in alumnos:
            carrera = carreras_por_alumno.get(alumno.id)
            desglose = calcular_desglose(
                importe=importe,
                programatico_catalogo=getattr(carrera, "cuota_programatica", None),
                extraprogramatica_catalogo=getattr(carrera, "cuota_extraprogramatica", None),
            )
            cuotas.append(
                Cuota(
                    alumno=alumno,
                    concepto=concepto,
                    sucursal_id=alumno.sucursal_id,
                    periodo=solicitud.periodo,
                    fecha_emision=solicitud.fecha_emision,
                    fecha_vencimiento=solicitud.fecha_vencimiento,
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
        return Cuota.objects.bulk_create(cuotas)
