from django.db import transaction
from django.utils import timezone

from ....models import CajaDiaria, SaldoArrastrableCaja
from ..application.validar_caja import asegurar_caja_abierta
from ..domain.resumen_caja import CajaOperacionError


class DjangoCajaRepository:
    @transaction.atomic
    def cerrar(self, *, caja_id, total_contado, importe_retirado, saldo_arrastrable):
        caja = CajaDiaria.objects.select_for_update().get(pk=caja_id)
        asegurar_caja_abierta(caja)

        if saldo_arrastrable and SaldoArrastrableCaja.objects.select_for_update().filter(
            sucursal=caja.sucursal,
            caja_destino__isnull=True,
        ).exists():
            raise CajaOperacionError(
                "Existe un saldo de cierre anterior pendiente. Debe aplicarlo antes de dejar un nuevo saldo."
            )

        caja.total_contado = total_contado
        caja.importe_retirado = importe_retirado
        caja.saldo_arrastrable = saldo_arrastrable
        caja.estado = CajaDiaria.Estado.CERRADA
        caja.cerrada_en = timezone.now()
        caja.save(
            update_fields=[
                "total_contado",
                "importe_retirado",
                "saldo_arrastrable",
                "estado",
                "cerrada_en",
                "actualizado",
            ]
        )
        if saldo_arrastrable:
            SaldoArrastrableCaja.objects.create(
                sucursal=caja.sucursal,
                caja_origen=caja,
                importe=saldo_arrastrable,
            )
        return caja

    def saldo_pendiente(self, *, caja_id):
        caja = CajaDiaria.objects.get(pk=caja_id)
        return (
            SaldoArrastrableCaja.objects.select_related("caja_origen__usuario")
            .filter(sucursal=caja.sucursal, caja_destino__isnull=True)
            .exclude(caja_origen=caja)
            .order_by("-caja_origen__fecha", "-id")
            .first()
        )

    @transaction.atomic
    def aplicar_saldo_pendiente(self, *, caja_id, saldo_id=None):
        caja = CajaDiaria.objects.select_for_update().get(pk=caja_id)
        asegurar_caja_abierta(caja)
        if caja.saldo_inicial:
            raise CajaOperacionError("La caja ya tiene un saldo inicial aplicado.")

        saldos = SaldoArrastrableCaja.objects.select_for_update().filter(
            sucursal=caja.sucursal,
            caja_destino__isnull=True,
        ).exclude(caja_origen=caja)
        saldo = saldos.filter(pk=saldo_id).first() if saldo_id else saldos.order_by(
            "-caja_origen__fecha", "-id"
        ).first()
        if not saldo:
            raise CajaOperacionError("No hay un saldo de cierre anterior disponible para esta sucursal.")

        caja.saldo_inicial = saldo.importe
        caja.save(update_fields=["saldo_inicial", "actualizado"])
        saldo.caja_destino = caja
        saldo.utilizado_en = timezone.now()
        saldo.save(update_fields=["caja_destino", "utilizado_en", "actualizado"])
        return caja
