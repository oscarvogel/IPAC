from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from ....models import AplicacionPago, CajaDiaria, Cuota, MovimientoCaja, Pago
from ...caja.application.validar_caja import asegurar_caja_abierta


class RegistrarPago:
    """Registra un pago y sus efectos contables como una única operación."""

    @transaction.atomic
    def execute(self, *, user, alumno, importe, medio, observacion="", concepto=None, cuota=None):
        caja, _ = CajaDiaria.objects.select_for_update().get_or_create(
            fecha=timezone.localdate(),
            sucursal=alumno.sucursal,
            usuario=user,
            defaults={"estado": CajaDiaria.Estado.ABIERTA},
        )
        asegurar_caja_abierta(caja)

        if cuota is not None:
            cuota = (
                Cuota.objects.select_for_update()
                .select_related("alumno", "concepto", "sucursal")
                .get(pk=cuota.pk)
            )
            if cuota.alumno_id != alumno.id:
                raise ValueError("La cuota no pertenece al alumno seleccionado.")
            if cuota.estado == Cuota.Estado.ANULADA or cuota.saldo <= 0:
                raise ValueError("La cuota seleccionada no tiene saldo pendiente.")
            concepto = cuota.concepto

        pago = Pago.objects.create(
            alumno=alumno,
            concepto=concepto,
            sucursal=alumno.sucursal,
            importe=importe,
            medio=medio,
            observacion=observacion,
        )

        if cuota is not None:
            importe_aplicable = min(Decimal(importe), cuota.saldo)
            AplicacionPago.objects.create(
                pago=pago,
                cuota=cuota,
                importe=importe_aplicable,
            )
            cuota.actualizar_estado()

        MovimientoCaja.objects.create(
            caja=caja,
            tipo=MovimientoCaja.Tipo.PAGO,
            medio=pago.medio,
            importe=pago.importe,
            descripcion=f"Pago {pago.alumno}",
            pago=pago,
        )
        return pago
