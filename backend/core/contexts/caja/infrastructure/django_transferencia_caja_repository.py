"""Persistencia atómica de la transferencia y sus dos partidas de efectivo.

CajaDiaria y MovimientoCaja siguen siendo modelos compartidos del monolito.
La operación bloquea ambas cajas por ID y vuelve a leer su saldo bajo bloqueo.
"""

from django.db import transaction
from django.utils import timezone

from ....models import CajaDiaria, MovimientoCaja, Pago, TransferenciaCaja
from ..domain.transferencia_caja import (
    SolicitudTransferenciaCaja,
    TransferenciaCajaError,
    validar_solicitud_transferencia,
)


class DjangoTransferenciaCajaRepository:
    @transaction.atomic
    def transferir(self, *, actor, solicitud: SolicitudTransferenciaCaja) -> TransferenciaCaja:
        validar_solicitud_transferencia(solicitud)
        motivo = solicitud.motivo.strip()
        if len(motivo) > 180:
            raise TransferenciaCajaError("El motivo no puede superar los 180 caracteres.")

        caja_ids = sorted((solicitud.origen_id, solicitud.destino_id))
        cajas = list(
            CajaDiaria.objects.select_for_update()
            .filter(pk__in=caja_ids)
            .order_by("pk")
        )
        if len(cajas) != 2:
            raise TransferenciaCajaError("La caja de origen o destino no existe.")
        cajas_por_id = {caja.pk: caja for caja in cajas}
        origen = cajas_por_id[solicitud.origen_id]
        destino = cajas_por_id[solicitud.destino_id]

        fecha_operativa = timezone.localdate()
        for caja in cajas:
            if caja.estado != CajaDiaria.Estado.ABIERTA or caja.fecha != fecha_operativa:
                raise TransferenciaCajaError("Ambas cajas deben estar abiertas y ser del día actual.")
        # Estas instancias no tienen movimientos prefetched: el cálculo consulta
        # las partidas vigentes después de obtener ambos bloqueos de caja.
        if origen.total_esperado < solicitud.importe:
            raise TransferenciaCajaError("El importe supera el efectivo esperado de la caja de origen.")

        transferencia = TransferenciaCaja.objects.create(
            origen=origen, destino=destino, actor=actor,
            importe=solicitud.importe, motivo=motivo,
        )
        MovimientoCaja.objects.create(
            caja=origen, tipo=MovimientoCaja.Tipo.PASE,
            medio=Pago.Medio.EFECTIVO, importe=solicitud.importe,
            descripcion=motivo, recibido_por_id=destino.usuario_id,
            transferencia=transferencia,
        )
        MovimientoCaja.objects.create(
            caja=destino, tipo=MovimientoCaja.Tipo.INGRESO,
            medio=Pago.Medio.EFECTIVO, importe=solicitud.importe,
            descripcion=motivo, transferencia=transferencia,
        )
        return transferencia
