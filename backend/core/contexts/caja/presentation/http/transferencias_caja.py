"""Entrada HTTP de transferencias; compone casos de uso sin consultar el ORM."""

from dataclasses import asdict

from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response

from core.permissions import ADMIN_ROLES, RolePermission
from ...application.consultar_transferencias_caja import (
    CajaTransferenciaNoDisponible,
    ConsultarCajasAbiertasParaTransferir,
    ConsultarTransferenciasCaja,
)
from ...application.transferir_entre_cajas import TransferirEntreCajas
from ...domain.transferencia_caja import SolicitudTransferenciaCaja, TransferenciaCajaError
from ...infrastructure.django_transferencia_caja_repository import (
    DjangoTransferenciaCajaOperableRepository,
)


class TransferenciasCajaPermission(RolePermission):
    read_roles = ADMIN_ROLES
    write_roles = ADMIN_ROLES


class SolicitudTransferenciaSerializer(serializers.Serializer):
    origen_id = serializers.IntegerField(min_value=1)
    destino_id = serializers.IntegerField(min_value=1)
    importe = serializers.DecimalField(max_digits=12, decimal_places=2)
    motivo = serializers.CharField(max_length=180, allow_blank=False)


def contrato_caja(caja):
    datos = asdict(caja)
    datos["fecha"] = caja.fecha.isoformat()
    datos["total_esperado"] = format(caja.total_esperado, ".2f")
    return datos


def contrato_transferencia(evidencia):
    datos = asdict(evidencia)
    datos["creado"] = evidencia.creado.isoformat()
    datos["importe"] = format(evidencia.importe, ".2f")
    datos["origen"] = contrato_caja(evidencia.origen)
    datos["destino"] = contrato_caja(evidencia.destino)
    return datos


class TransferenciaCajaViewSet(viewsets.ViewSet):
    permission_classes = [TransferenciasCajaPermission]

    def list(self, request):
        caso = ConsultarTransferenciasCaja(DjangoTransferenciaCajaOperableRepository())
        return Response([contrato_transferencia(item) for item in caso.execute(actor=request.user)])

    @action(detail=False, methods=["get"], url_path="cajas-abiertas")
    def cajas_abiertas(self, request):
        caso = ConsultarCajasAbiertasParaTransferir(DjangoTransferenciaCajaOperableRepository())
        return Response([contrato_caja(item) for item in caso.execute(actor=request.user)])

    def create(self, request):
        serializer = SolicitudTransferenciaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        solicitud = SolicitudTransferenciaCaja(**serializer.validated_data)
        caso = TransferirEntreCajas(DjangoTransferenciaCajaOperableRepository())
        try:
            evidencia = caso.execute(actor=request.user, solicitud=solicitud)
        except CajaTransferenciaNoDisponible:
            raise NotFound("Caja no disponible.")
        except TransferenciaCajaError as error:
            raise ValidationError({"detail": str(error)})
        return Response(contrato_transferencia(evidencia), status=status.HTTP_201_CREATED)
