from django.contrib.auth.models import User
from django.db import transaction

from ....models import CajaDiaria, MovimientoCaja
from ..application.validar_caja import asegurar_caja_abierta
from ..domain.comprobante_caja import ComprobanteCajaError


class DjangoMovimientoCajaRepository:
    """Adaptador ORM de Caja.

    El número de comprobante no se asigna acá: lo asigna ``MovimientoCaja.save``
    usando el formato del dominio, de modo que ningún pase ni retiro pueda
    quedar sin numerar, sin importar por qué camino se haya creado.
    """

    @transaction.atomic
    def registrar(self, *, actor, solicitud):
        caja = CajaDiaria.objects.select_for_update().get(pk=solicitud.caja_id)
        asegurar_caja_abierta(caja)
        if caja.usuario_id != actor.id:
            raise ComprobanteCajaError(
                "No puede registrar movimientos en una caja de otro usuario."
            )

        recibido_por = None
        if solicitud.recibido_por_id:
            recibido_por = User.objects.filter(
                pk=solicitud.recibido_por_id, is_active=True
            ).first()
            if recibido_por is None:
                raise ComprobanteCajaError(
                    "El usuario que recibe el dinero no existe o está inactivo."
                )

        return MovimientoCaja.objects.create(
            caja=caja,
            tipo=solicitud.tipo,
            medio=solicitud.medio,
            importe=solicitud.importe,
            descripcion=solicitud.descripcion,
            recibido_por=recibido_por,
        )