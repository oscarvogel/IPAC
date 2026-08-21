from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from ....models import AplicacionPago, CajaDiaria, Cuota, MovimientoCaja, Pago
from ...caja.application.validar_caja import asegurar_caja_abierta


def calcular_saldo_pendiente_alumno(alumno):
    cuotas = (
        Cuota.objects.filter(alumno=alumno)
        .exclude(estado=Cuota.Estado.ANULADA)
        .prefetch_related("aplicaciones")
    )
    return sum((cuota.saldo for cuota in cuotas), Decimal("0"))


def actualizar_saldo_pendiente_posterior(pago):
    saldo = calcular_saldo_pendiente_alumno(pago.alumno)
    Pago.objects.filter(pk=pago.pk).update(saldo_pendiente_posterior=saldo)
    pago.saldo_pendiente_posterior = saldo
    return saldo


class RegistrarPago:
    """Registra un pago y sus efectos contables como una única operación."""

    @transaction.atomic
    def execute(
        self,
        *,
        user,
        alumno,
        importe,
        medio,
        observacion="",
        concepto=None,
        cuota=None,
        cuotas=None,
        aplicacion_automatica=False,
    ):
        caja, _ = CajaDiaria.objects.select_for_update().get_or_create(
            fecha=timezone.localdate(),
            sucursal=alumno.sucursal,
            usuario=user,
            defaults={"estado": CajaDiaria.Estado.ABIERTA},
        )
        asegurar_caja_abierta(caja)

        cuotas_solicitadas = list(cuotas or [])
        if cuota is not None:
            cuotas_solicitadas.append(cuota)
        if aplicacion_automatica and cuotas_solicitadas:
            raise ValueError("No puede combinar aplicación automática con selección manual de cuotas.")

        cuotas_query = Cuota.objects.select_for_update().select_related(
            "alumno", "concepto", "sucursal"
        ).prefetch_related("aplicaciones")
        if aplicacion_automatica:
            cuotas_a_aplicar = list(
                cuotas_query.filter(alumno=alumno)
                .exclude(estado=Cuota.Estado.ANULADA)
                .order_by("fecha_vencimiento", "id")
            )
        elif cuotas_solicitadas:
            ids = {item.pk for item in cuotas_solicitadas}
            cuotas_a_aplicar = list(
                cuotas_query.filter(pk__in=ids).order_by("fecha_vencimiento", "id")
            )
            if len(cuotas_a_aplicar) != len(ids):
                raise ValueError("Una o más cuotas seleccionadas no existen.")
        else:
            cuotas_a_aplicar = []

        for cuota_item in cuotas_a_aplicar:
            if cuota_item.alumno_id != alumno.id:
                raise ValueError("Todas las cuotas deben pertenecer al alumno seleccionado.")
            if cuota_item.sucursal_id != alumno.sucursal_id:
                raise ValueError("Todas las cuotas deben pertenecer a la sucursal del alumno.")
            if cuota_item.estado == Cuota.Estado.ANULADA or cuota_item.saldo <= 0:
                raise ValueError("Una de las cuotas seleccionadas no tiene saldo pendiente.")

        conceptos = {item.concepto_id for item in cuotas_a_aplicar}
        if len(conceptos) == 1:
            concepto = cuotas_a_aplicar[0].concepto
        elif len(conceptos) > 1:
            concepto = None

        pago = Pago.objects.create(
            alumno=alumno,
            concepto=concepto,
            sucursal=alumno.sucursal,
            importe=importe,
            medio=medio,
            observacion=observacion,
            registrado_por=user,
        )

        saldo_disponible = Decimal(importe)
        for cuota_item in cuotas_a_aplicar:
            if saldo_disponible <= 0:
                break
            importe_aplicable = min(saldo_disponible, cuota_item.saldo)
            AplicacionPago.objects.create(
                pago=pago,
                cuota=cuota_item,
                importe=importe_aplicable,
            )
            saldo_disponible -= importe_aplicable
            cuota_item._prefetched_objects_cache.pop("aplicaciones", None)
            cuota_item.actualizar_estado()

        MovimientoCaja.objects.create(
            caja=caja,
            tipo=MovimientoCaja.Tipo.PAGO,
            medio=pago.medio,
            importe=pago.importe,
            descripcion=f"Pago {pago.alumno}",
            pago=pago,
        )
        actualizar_saldo_pendiente_posterior(pago)
        return pago
