from django.db import transaction
from django.core.paginator import Paginator
from django.utils import timezone

from ....models import CajaDiaria, SaldoArrastrableCaja
from ..application.consultar_historial_cajas import (
    CajaHistorial,
    PaginaHistorialCajas,
    UsuarioCaja,
)
from ..application.validar_caja import asegurar_caja_abierta
from ..domain.resumen_caja import CajaOperacionError, calcular_resumen_caja


class DjangoCajaRepository:
    def consultar_historial(
        self,
        *,
        desde,
        hasta,
        sucursal_ids,
        usuario_id,
        propietario_id,
        page,
        page_size,
    ):
        cajas_visibles = CajaDiaria.objects.filter(
            sucursal_id__in=sucursal_ids,
        )
        if desde:
            cajas_visibles = cajas_visibles.filter(fecha__gte=desde)
        if hasta:
            cajas_visibles = cajas_visibles.filter(fecha__lte=hasta)
        if propietario_id:
            cajas_visibles = cajas_visibles.filter(usuario_id=propietario_id)

        usuarios = tuple(
            UsuarioCaja(id=item["usuario_id"], nombre=item["usuario__username"])
            for item in cajas_visibles.order_by("usuario__username", "usuario_id")
            .values("usuario_id", "usuario__username")
            .distinct()
        )

        cajas_filtradas = cajas_visibles
        if usuario_id:
            cajas_filtradas = cajas_filtradas.filter(usuario_id=usuario_id)
        cajas_filtradas = cajas_filtradas.select_related(
            "sucursal",
            "usuario",
        ).prefetch_related("movimientos")

        pagina = Paginator(cajas_filtradas, page_size).get_page(page)
        resultados = []
        for caja in pagina.object_list:
            movimientos = tuple(caja.movimientos.all())
            resumen = calcular_resumen_caja(
                saldo_inicial=caja.saldo_inicial,
                movimientos=movimientos,
            )
            resultados.append(
                CajaHistorial(
                    id=caja.id,
                    fecha=caja.fecha,
                    sucursal=caja.sucursal_id,
                    sucursal_nombre=caja.sucursal.nombre,
                    usuario=caja.usuario_id,
                    usuario_nombre=caja.usuario.username,
                    estado=caja.estado,
                    saldo_inicial=caja.saldo_inicial,
                    total_esperado=resumen.efectivo_esperado,
                    total_contado=caja.total_contado,
                    diferencia=(
                        caja.total_contado - resumen.efectivo_esperado
                        if caja.estado == CajaDiaria.Estado.CERRADA
                        else None
                    ),
                    cantidad_movimientos=len(movimientos),
                    cerrada_en=caja.cerrada_en,
                )
            )

        return PaginaHistorialCajas(
            count=pagina.paginator.count,
            page=pagina.number,
            page_size=pagina.paginator.per_page,
            results=tuple(resultados),
            usuarios=usuarios,
        )

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
