from decimal import Decimal

from django.db import transaction

from ....access_scope import scoped_queryset_for_user
from ....models import Alumno, ConceptoCobrable, Cuota, TipoDescuento
from ..application.generar_cuotas import GeneracionCuotasError


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
            ).select_for_update().order_by("apellido", "nombre", "id")
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

        cuotas = [
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
            )
            for alumno in alumnos
        ]
        return Cuota.objects.bulk_create(cuotas)
