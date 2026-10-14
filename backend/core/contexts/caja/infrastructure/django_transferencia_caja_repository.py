"""Persistencia atómica de transferencia, ambas partidas y auditoría.

CajaDiaria y MovimientoCaja siguen en el legado compartido. El adaptador
operable aplica el contrato de alcance vigente antes de bloquear ambas cajas.
"""

from dataclasses import asdict
from datetime import date, datetime
from decimal import Decimal
import json
from uuid import uuid4

from django.db import IntegrityError, transaction
from django.utils import timezone

from ....access_scope import scoped_queryset_for_user
from ....models import CajaDiaria, MovimientoCaja, Pago, Sucursal, TransferenciaCaja
from ...auditoria.application.registrar_evento import RegistrarEventoAuditoria
from ...auditoria.infrastructure.django_auditoria_repository import DjangoAuditoriaRepository
from ..application.consultar_transferencias_caja import (
    ActorTransferenciaResumen,
    CajaTransferenciaNoDisponible,
    CajaTransferenciaResumen,
    TransferenciaCajaEvidencia,
)
from ..application.transferir_entre_cajas import TransferenciaIdempotenciaConflicto
from ..domain.transferencia_caja import (
    SolicitudTransferenciaCaja,
    TransferenciaCajaError,
    validar_solicitud_transferencia,
)


class DjangoTransferenciaCajaRepository:
    def _cajas_para_transferir(self, *, actor, caja_ids):
        return list(
            CajaDiaria.objects.select_for_update()
            .filter(pk__in=caja_ids)
            .order_by("pk")
        )

    @transaction.atomic
    def transferir(self, *, actor, solicitud: SolicitudTransferenciaCaja,
                   idempotency_key=None) -> TransferenciaCaja:
        validar_solicitud_transferencia(solicitud)
        motivo = solicitud.motivo.strip()
        if len(motivo) > 180:
            raise TransferenciaCajaError("El motivo no puede superar los 180 caracteres.")

        caja_ids = sorted((solicitud.origen_id, solicitud.destino_id))
        cajas = self._cajas_para_transferir(actor=actor, caja_ids=caja_ids)
        if len(cajas) != 2:
            raise TransferenciaCajaError("La caja de origen o destino no existe.")
        cajas_por_id = {caja.pk: caja for caja in cajas}
        origen = cajas_por_id[solicitud.origen_id]
        destino = cajas_por_id[solicitud.destino_id]

        fecha_operativa = timezone.localdate()
        for caja in cajas:
            if caja.estado != CajaDiaria.Estado.ABIERTA or caja.fecha != fecha_operativa:
                raise TransferenciaCajaError("Ambas cajas deben estar abiertas y ser del día actual.")
        # El cálculo lee partidas vigentes después de obtener ambos bloqueos.
        if origen.total_esperado < solicitud.importe:
            raise TransferenciaCajaError("El importe supera el efectivo esperado de la caja de origen.")

        transferencia = TransferenciaCaja.objects.create(
            origen=origen, destino=destino, actor=actor,
            importe=solicitud.importe, motivo=motivo, idempotency_key=idempotency_key,
        )
        salida = MovimientoCaja.objects.create(
            caja=origen, tipo=MovimientoCaja.Tipo.PASE,
            medio=Pago.Medio.EFECTIVO, importe=solicitud.importe,
            descripcion=motivo, recibido_por_id=destino.usuario_id,
            transferencia=transferencia,
        )
        entrada = MovimientoCaja.objects.create(
            caja=destino, tipo=MovimientoCaja.Tipo.INGRESO,
            medio=Pago.Medio.EFECTIVO, importe=solicitud.importe,
            descripcion=motivo, transferencia=transferencia,
        )
        RegistrarEventoAuditoria(DjangoAuditoriaRepository()).execute(
            usuario=actor,
            sucursal=origen.sucursal,
            modulo="caja",
            accion="transferencia",
            entidad="core.TransferenciaCaja",
            entidad_id=transferencia.pk,
            descripcion=f"{transferencia.numero_comprobante}: transferencia entre cajas",
            valores_nuevos={
                "origen_id": origen.pk,
                "destino_id": destino.pk,
                "origen_sucursal_id": origen.sucursal_id,
                "destino_sucursal_id": destino.sucursal_id,
                "actor_id": actor.pk,
                "importe": solicitud.importe,
                "motivo": motivo,
                "numero_comprobante": transferencia.numero_comprobante,
                "creado": transferencia.creado,
                "movimiento_origen_id": salida.pk,
                "movimiento_destino_id": entrada.pk,
            },
        )
        return transferencia


class DjangoTransferenciaCajaOperableRepository:
    """Puerto del comando HTTP y lector de DTOs con autorización por sucursal.

    Conserva el adaptador de persistencia interno como detalle; el caso de uso
    recibe evidencia inmutable sin exponer modelos ORM al controlador.
    """

    def _cajas_abiertas(self, *, actor):
        return scoped_queryset_for_user(
            CajaDiaria.objects.filter(
                estado=CajaDiaria.Estado.ABIERTA, fecha=timezone.localdate(),
            ),
            actor,
        )

    @transaction.atomic
    def transferir(self, *, actor, solicitud: SolicitudTransferenciaCaja,
                   idempotency_key=None) -> TransferenciaCajaEvidencia:
        key = idempotency_key or uuid4()
        existente = TransferenciaCaja.objects.filter(idempotency_key=key).first()
        if existente:
            return self._replay(existente, actor=actor, solicitud=solicitud)

        try:
            # El savepoint permite resolver una carrera de la clave única sin
            # continuar sobre una transacción marcada para rollback.
            with transaction.atomic():
                caja_ids = sorted((solicitud.origen_id, solicitud.destino_id))
                cajas = list(
                    self._cajas_abiertas(actor=actor).select_for_update()
                    .filter(pk__in=caja_ids).order_by("pk")
                )
                # Un contendiente pudo confirmar mientras esperábamos las cajas.
                existente = TransferenciaCaja.objects.filter(idempotency_key=key).first()
                if existente:
                    return self._replay(existente, actor=actor, solicitud=solicitud)
                if len(cajas) != 2:
                    raise CajaTransferenciaNoDisponible()
                transferencia = DjangoTransferenciaCajaRepository().transferir(
                    actor=actor, solicitud=solicitud, idempotency_key=key,
                )
                evidencia = self._evidencia(transferencia)
                # Snapshot técnico, en la misma transacción que las dos partidas
                # y auditoría. No altera una transferencia previamente confirmada.
                TransferenciaCaja.objects.filter(pk=transferencia.pk).update(
                    idempotency_evidence=self._snapshot(evidencia),
                )
                return evidencia
        except IntegrityError:
            # Cajas disjuntas no comparten bloqueos; la restricción única decide
            # el ganador. Solo se resuelve este error si existe la misma clave.
            existente = TransferenciaCaja.objects.filter(idempotency_key=key).first()
            if existente is None:
                raise
            return self._replay(existente, actor=actor, solicitud=solicitud)

    def _replay(self, transferencia, *, actor, solicitud):
        if (
            transferencia.actor_id != actor.pk
            or transferencia.origen_id != solicitud.origen_id
            or transferencia.destino_id != solicitud.destino_id
            or transferencia.importe != solicitud.importe
            or transferencia.motivo != solicitud.motivo.strip()
        ):
            raise TransferenciaIdempotenciaConflicto()
        # La clave no concede permisos. Releer alcance, sin exigir que una
        # operación ya confirmada siga siendo operable hoy.
        cajas_visibles = scoped_queryset_for_user(CajaDiaria.objects.all(), actor)
        if cajas_visibles.filter(
            pk__in=(transferencia.origen_id, transferencia.destino_id),
        ).count() != 2:
            raise CajaTransferenciaNoDisponible()
        datos = transferencia.idempotency_evidence
        return TransferenciaCajaEvidencia(
            id=datos["id"], numero_comprobante=datos["numero_comprobante"],
            creado=datetime.fromisoformat(datos["creado"]),
            actor=ActorTransferenciaResumen(**datos["actor"]),
            origen=self._caja_desde_snapshot(datos["origen"]),
            destino=self._caja_desde_snapshot(datos["destino"]),
            importe=Decimal(datos["importe"]), motivo=datos["motivo"],
            movimiento_origen_id=datos["movimiento_origen_id"],
            movimiento_destino_id=datos["movimiento_destino_id"],
        )

    @staticmethod
    def _snapshot(evidencia):
        def valor_json(valor):
            if isinstance(valor, (date, datetime)):
                return valor.isoformat()
            if isinstance(valor, Decimal):
                return str(valor)
            raise TypeError(f"Tipo no serializable: {type(valor).__name__}")

        return json.loads(json.dumps(asdict(evidencia), default=valor_json))

    @staticmethod
    def _caja_desde_snapshot(datos):
        return CajaTransferenciaResumen(
            **dict(datos, fecha=date.fromisoformat(datos["fecha"]),
                   total_esperado=Decimal(datos["total_esperado"])),
        )

    def cajas_abiertas(self, *, actor) -> tuple[CajaTransferenciaResumen, ...]:
        cajas = (
            self._cajas_abiertas(actor=actor)
            .select_related("sucursal", "usuario").prefetch_related("movimientos")
            .order_by("sucursal__nombre", "usuario__username", "pk")
        )
        return tuple(self._resumen_caja(caja) for caja in cajas)

    def historial(self, *, actor) -> tuple[TransferenciaCajaEvidencia, ...]:
        sucursales = scoped_queryset_for_user(Sucursal.objects.all(), actor)
        transferencias = (
            TransferenciaCaja.objects.filter(
                origen__sucursal__in=sucursales, destino__sucursal__in=sucursales,
            )
            .select_related("actor", "origen__sucursal", "origen__usuario",
                            "destino__sucursal", "destino__usuario")
            .prefetch_related("movimientos", "origen__movimientos", "destino__movimientos")
            .order_by("-creado", "-pk")[:50]
        )
        return tuple(self._evidencia(transferencia) for transferencia in transferencias)

    @staticmethod
    def _resumen_caja(caja) -> CajaTransferenciaResumen:
        return CajaTransferenciaResumen(
            id=caja.pk, fecha=caja.fecha,
            sucursal=caja.sucursal_id, sucursal_nombre=caja.sucursal.nombre,
            usuario=caja.usuario_id,
            usuario_nombre=caja.usuario.get_full_name() or caja.usuario.username,
            total_esperado=caja.total_esperado,
        )

    def _evidencia(self, transferencia) -> TransferenciaCajaEvidencia:
        movimientos = {movimiento.caja_id: movimiento.pk for movimiento in transferencia.movimientos.all()}
        actor = transferencia.actor
        return TransferenciaCajaEvidencia(
            id=transferencia.pk, numero_comprobante=transferencia.numero_comprobante,
            creado=transferencia.creado,
            actor=ActorTransferenciaResumen(
                id=actor.pk, username=actor.username,
                nombre=actor.get_full_name() or actor.username,
            ),
            origen=self._resumen_caja(transferencia.origen),
            destino=self._resumen_caja(transferencia.destino),
            importe=transferencia.importe, motivo=transferencia.motivo,
            movimiento_origen_id=movimientos[transferencia.origen_id],
            movimiento_destino_id=movimientos[transferencia.destino_id],
        )
