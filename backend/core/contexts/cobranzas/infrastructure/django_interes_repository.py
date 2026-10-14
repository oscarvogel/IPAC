"""Adaptadores Django de la consulta de intereses de mora.

Acá vive el detalle externo: el SQL, el `annotate` y la traducción entre el ORM
y los value objects del dominio. La regla de cálculo no se toca en esta capa.
"""

from decimal import Decimal

from django.db.models import (
    DecimalField,
    ExpressionWrapper,
    F,
    OuterRef,
    Subquery,
    Sum,
    Value,
)
from django.db.models.functions import Coalesce

from ....models import AplicacionPago, Cuota
from ....models import TasaInteres as TasaInteresModel
from ..application.consultar_intereses import ConfiguracionInteres, CuotaParaInteres
from ..domain.intereses import PoliticaInteres, TasaInteres

MONEDA = DecimalField(max_digits=12, decimal_places=2)


class DjangoTasaInteresRepository:
    """Lee las tasas configuradas y las traduce al vocabulario del dominio."""

    def configuraciones(self, *, sucursal_ids):
        consulta = TasaInteresModel.objects.filter(activa=True)
        # `is not None` y no truthiness: un usuario sin sucursales en alcance
        # llega con la lista vacía, y `if sucursal_ids:` la tomaría como "sin
        # filtro" y le devolvería las tasas de todas las sucursales.
        if sucursal_ids is not None:
            consulta = consulta.filter(sucursal_id__in=sucursal_ids)

        return [
            ConfiguracionInteres(
                sucursal_id=fila.sucursal_id,
                tasa=TasaInteres(
                    porcentaje_mensual=fila.porcentaje_mensual,
                    vigencia_desde=fila.vigencia_desde,
                    vigencia_hasta=fila.vigencia_hasta,
                ),
                politica=PoliticaInteres(
                    base_calculo=fila.base_calculo,
                    unidad_calculo=fila.unidad_calculo,
                ),
            )
            for fila in consulta
        ]


class DjangoCuotaInteresReader:
    """Cuotas con saldo al día de la evaluación.

    El saldo se calcula con un `annotate` y no con la propiedad `Cuota.saldo`,
    que suma las aplicaciones una por una: con treinta alumnos pendientes eso
    son treinta consultas por cada informe de intereses.
    """

    def cuotas_con_saldo(self, *, sucursal_ids, fecha_evaluacion):
        pagado = (
            AplicacionPago.objects.filter(cuota_id=OuterRef("pk"), activa=True)
            .values("cuota_id")
            .annotate(total=Sum("importe"))
            .values("total")[:1]
        )
        consulta = Cuota.objects.filter(
            estado__in=[Cuota.Estado.PENDIENTE, Cuota.Estado.PARCIAL]
        )
        if sucursal_ids is not None:
            consulta = consulta.filter(sucursal_id__in=sucursal_ids)
        consulta = consulta.annotate(
            saldo_calculado=ExpressionWrapper(
                F("importe")
                - F("descuento")
                + F("recargo")
                # El Coalesce no es decorativo: una cuota sin aplicaciones
                # devuelve NULL del Subquery, y en SQL `10000 - NULL` es NULL.
                # Sin esto el filtro `saldo_calculado__gt=0` descarta justamente
                # las cuotas más impagas, que son las que más interés deben.
                - Coalesce(
                    Subquery(pagado, output_field=MONEDA),
                    Value(Decimal("0")),
                    output_field=MONEDA,
                ),
                output_field=MONEDA,
            )
        ).filter(saldo_calculado__gt=0)

        return [
            CuotaParaInteres(
                cuota_id=fila.id,
                sucursal_id=fila.sucursal_id,
                periodo=fila.periodo,
                fecha_vencimiento=fila.fecha_vencimiento,
                # El DecimalField del annotate devuelve float si no se le pasa
                # la salida; se.Decimal() evita que el interés herede error de
                # coma flotante desde el saldo.
                saldo_pendiente=Decimal(fila.saldo_calculado).quantize(Decimal("0.01")),
            )
            for fila in consulta.select_related("sucursal")
        ]