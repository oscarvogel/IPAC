"""Consulta ORM para las relaciones publicadas del detalle de movimientos."""

from django.db.models import Prefetch, prefetch_related_objects

from ....models import MovimientoCaja


def movimientos_caja_con_evidencia():
    return MovimientoCaja.objects.select_related(
        "caja", "caja__usuario", "pago", "recibido_por",
        "transferencia", "transferencia__actor",
        "transferencia__origen__sucursal", "transferencia__origen__usuario",
        "transferencia__destino__sucursal", "transferencia__destino__usuario",
    )


def precargar_movimientos_de_caja(caja):
    # Las acciones hoy/cerrar devuelven instancias que no vienen del queryset
    # de lectura. El prefetch se omite automáticamente si ya está cacheado.
    prefetch_related_objects(
        [caja], Prefetch("movimientos", queryset=movimientos_caja_con_evidencia()),
    )
