from ....access_scope import scoped_queryset_for_user
from ....models import CajaDiaria


class DjangoCajaExportReader:
    """Adaptador de lectura XLSX para cajas, limitado por el alcance del actor."""

    def leer_cajas(self, *, actor, filtros):
        cajas = scoped_queryset_for_user(
            CajaDiaria.objects.select_related("sucursal", "usuario"),
            actor,
        )
        if filtros.sucursal_id:
            cajas = cajas.filter(sucursal_id=filtros.sucursal_id)
        if filtros.desde:
            cajas = cajas.filter(fecha__gte=filtros.desde)
        if filtros.hasta:
            cajas = cajas.filter(fecha__lte=filtros.hasta)
        if filtros.usuario_id:
            cajas = cajas.filter(usuario_id=filtros.usuario_id)

        return [
            [
                caja.fecha,
                caja.sucursal.nombre,
                caja.usuario.username,
                caja.get_estado_display(),
                caja.saldo_inicial,
                caja.total_esperado,
                caja.total_contado,
                caja.diferencia,
                caja.saldo_arrastrable,
            ]
            for caja in cajas.order_by("-fecha", "usuario__username", "id")
        ]
