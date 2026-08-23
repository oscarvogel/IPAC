from django.db import transaction
from django.utils import timezone

from ....models import AplicacionPago, CajaDiaria, Cuota, MovimientoCaja, Pago
from ...caja.application.validar_caja import asegurar_caja_abierta


class PagoAnulacionError(ValueError):
    """Error funcional al intentar anular una cobranza."""


class AnularPago:
    """Revierte aplicaciones y caja sin eliminar el comprobante original."""

    @transaction.atomic
    def execute(self, *, pago_id, user, motivo):
        motivo = str(motivo or "").strip()
        if not motivo:
            raise PagoAnulacionError("Debe indicar el motivo de la anulación.")

        pago = Pago.objects.select_for_update().select_related("sucursal").get(pk=pago_id)
        if pago.estado == Pago.Estado.ANULADO:
            raise PagoAnulacionError("El pago ya está anulado.")

        try:
            movimiento_original = MovimientoCaja.objects.select_for_update().select_related("caja").get(pago=pago)
        except MovimientoCaja.DoesNotExist as exc:
            raise PagoAnulacionError("El pago no tiene un movimiento de caja asociado para revertir.") from exc
        caja_original = movimiento_original.caja
        if caja_original.estado == CajaDiaria.Estado.ABIERTA and caja_original.usuario_id == user.id:
            caja_reverso = caja_original
        else:
            caja_reverso, _ = CajaDiaria.objects.select_for_update().get_or_create(
                fecha=timezone.localdate(),
                sucursal=pago.sucursal,
                usuario=user,
                defaults={"estado": CajaDiaria.Estado.ABIERTA},
            )
        asegurar_caja_abierta(caja_reverso)

        ahora = timezone.now()
        aplicaciones = list(
            AplicacionPago.objects.select_for_update()
            .select_related("cuota")
            .filter(pago=pago, activa=True)
        )
        cuotas_afectadas = []
        for aplicacion in aplicaciones:
            aplicacion.activa = False
            aplicacion.anulada_en = ahora
            aplicacion.actualizado = ahora
            cuotas_afectadas.append(aplicacion.cuota)
        if aplicaciones:
            AplicacionPago.objects.bulk_update(aplicaciones, ["activa", "anulada_en", "actualizado"])

        for cuota in cuotas_afectadas:
            cuota.actualizar_estado()

        MovimientoCaja.objects.create(
            caja=caja_reverso,
            tipo=MovimientoCaja.Tipo.REVERSO,
            medio=movimiento_original.medio,
            importe=movimiento_original.importe,
            descripcion=f"Anulación {pago.numero_recibo}: {motivo}",
            movimiento_origen=movimiento_original,
        )
        pago.estado = Pago.Estado.ANULADO
        pago.motivo_anulacion = motivo
        pago.anulado_en = ahora
        pago.anulado_por = user
        pago.save(
            update_fields=[
                "estado",
                "motivo_anulacion",
                "anulado_en",
                "anulado_por",
                "actualizado",
            ]
        )
        return pago
