from django.db import transaction
from django.db.models import Sum
from django.http import HttpResponse
from django.utils import timezone
from decimal import Decimal, InvalidOperation
from datetime import date
import csv
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from django.contrib.auth.models import User

from .models import AplicacionPago, Alumno, CajaDiaria, CarreraCurso, ConceptoCobrable, Cuota, Matricula, MovimientoCaja, Pago, PerfilUsuario, Sucursal
from .serializers import (
    AlumnoSerializer,
    AplicacionPagoSerializer,
    CajaDiariaSerializer,
    CarreraCursoSerializer,
    ConceptoCobrableSerializer,
    CobroSerializer,
    CurrentUserSerializer,
    CuotaSerializer,
    LoginSerializer,
    MatriculaSerializer,
    MovimientoCajaSerializer,
    PagoSerializer,
    SucursalSerializer,
    UserSerializer,
)


def scoped_queryset_for_user(queryset, user):
    perfil = getattr(user, "perfil", None)
    if not perfil:
        return queryset.none()
    if perfil.puede_ver_todas_las_sucursales:
        return queryset
    return queryset.filter(sucursal=perfil.sucursal)


def get_user_sucursal(user):
    perfil = getattr(user, "perfil", None)
    return perfil.sucursal if perfil else None


def get_or_create_cashbox(user, sucursal):
    return CajaDiaria.objects.get_or_create(
        fecha=timezone.localdate(),
        sucursal=sucursal,
        usuario=user,
        defaults={"estado": CajaDiaria.Estado.ABIERTA},
    )[0]


class LoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        token, _ = Token.objects.get_or_create(user=serializer.validated_data["user"])
        return Response({"key": token.key})


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(CurrentUserSerializer(request.user).data)


class ReporteResumenView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        hoy = timezone.localdate()
        try:
            desde = date.fromisoformat(request.query_params.get("desde", hoy.replace(day=1).isoformat()))
            hasta = date.fromisoformat(request.query_params.get("hasta", hoy.isoformat()))
        except ValueError:
            return Response({"detail": "Las fechas deben tener formato AAAA-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
        if desde > hasta:
            return Response({"detail": "La fecha desde no puede ser posterior a hasta."}, status=status.HTTP_400_BAD_REQUEST)

        sucursal_id = request.query_params.get("sucursal")
        sucursales = scoped_queryset_for_user(Sucursal.objects.all(), request.user)
        if sucursal_id:
            sucursales = sucursales.filter(pk=sucursal_id)
            if not sucursales.exists():
                return Response({"detail": "Sucursal invalida o sin acceso."}, status=status.HTTP_400_BAD_REQUEST)

        pagos = Pago.objects.filter(sucursal__in=sucursales, fecha__range=(desde, hasta))
        cuotas = Cuota.objects.filter(sucursal__in=sucursales).exclude(estado=Cuota.Estado.ANULADA).prefetch_related("aplicaciones")
        cajas = CajaDiaria.objects.filter(sucursal__in=sucursales, fecha__range=(desde, hasta))
        deuda = sum((cuota.saldo for cuota in cuotas), Decimal("0"))
        saldo_a_favor = sum((pago.saldo_a_favor for pago in Pago.objects.filter(sucursal__in=sucursales).prefetch_related("aplicaciones")), Decimal("0"))
        cobrado_por_medio = {
            medio: pagos.filter(medio=medio).aggregate(total=Sum("importe"))["total"] or Decimal("0")
            for medio, _ in Pago.Medio.choices
        }
        return Response(
            {
                "periodo": {"desde": desde, "hasta": hasta},
                "sucursales": list(sucursales.values("id", "codigo", "nombre")),
                "cobranzas": {
                    "cantidad_pagos": pagos.count(),
                    "total": pagos.aggregate(total=Sum("importe"))["total"] or Decimal("0"),
                    "por_medio": cobrado_por_medio,
                },
                "cuenta_corriente": {"deuda": deuda, "saldo_a_favor": saldo_a_favor, "saldo_neto": deuda - saldo_a_favor},
                "cajas": {
                    "abiertas": cajas.filter(estado=CajaDiaria.Estado.ABIERTA).count(),
                    "cerradas": cajas.filter(estado=CajaDiaria.Estado.CERRADA).count(),
                    "diferencia_acumulada": sum((caja.diferencia for caja in cajas), Decimal("0")),
                },
            }
        )


class SucursalViewSet(viewsets.ModelViewSet):
    serializer_class = SucursalSerializer

    def get_queryset(self):
        queryset = Sucursal.objects.all()
        perfil = getattr(self.request.user, "perfil", None)
        if perfil and not perfil.puede_ver_todas_las_sucursales:
            return queryset.filter(id=perfil.sucursal_id)
        return queryset


class CarreraCursoViewSet(viewsets.ModelViewSet):
    serializer_class = CarreraCursoSerializer

    def get_queryset(self):
        return scoped_queryset_for_user(CarreraCurso.objects.select_related("sucursal"), self.request.user)


class AlumnoViewSet(viewsets.ModelViewSet):
    serializer_class = AlumnoSerializer

    def get_queryset(self):
        return scoped_queryset_for_user(
            Alumno.objects.select_related("sucursal", "carrera"),
            self.request.user,
        )

    @action(detail=True, methods=["get"], url_path="estado-cuenta")
    def estado_cuenta(self, request, pk=None):
        alumno = self.get_object()
        cuotas = Cuota.objects.filter(alumno=alumno).select_related("concepto").prefetch_related("aplicaciones")
        pagos = Pago.objects.filter(alumno=alumno).select_related("concepto").prefetch_related("aplicaciones")
        cuotas_activas = [cuota for cuota in cuotas if cuota.estado != Cuota.Estado.ANULADA]
        total_deuda = sum((cuota.saldo for cuota in cuotas_activas), 0)
        saldo_a_favor = sum((pago.saldo_a_favor for pago in pagos), 0)
        return Response(
            {
                "alumno": AlumnoSerializer(alumno).data,
                "resumen": {
                    "total_cuotas": sum((cuota.total for cuota in cuotas_activas), 0),
                    "saldo_pendiente": total_deuda,
                    "saldo_a_favor": saldo_a_favor,
                    "saldo_neto": total_deuda - saldo_a_favor,
                },
                "cuotas": CuotaSerializer(cuotas, many=True).data,
                "pagos": PagoSerializer(pagos, many=True).data,
            }
        )


class ConceptoCobrableViewSet(viewsets.ModelViewSet):
    serializer_class = ConceptoCobrableSerializer

    def get_queryset(self):
        return scoped_queryset_for_user(
            ConceptoCobrable.objects.select_related("sucursal", "carrera"),
            self.request.user,
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.activo = False
        instance.save(update_fields=["activo", "actualizado"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class MatriculaViewSet(viewsets.ModelViewSet):
    serializer_class = MatriculaSerializer

    def get_queryset(self):
        queryset = scoped_queryset_for_user(Matricula.objects.select_related("alumno", "carrera", "sucursal"), self.request.user)
        alumno_id = self.request.query_params.get("alumno")
        return queryset.filter(alumno_id=alumno_id) if alumno_id else queryset


class CuotaViewSet(viewsets.ModelViewSet):
    serializer_class = CuotaSerializer

    def get_queryset(self):
        queryset = scoped_queryset_for_user(Cuota.objects.select_related("alumno", "matricula", "concepto", "sucursal").prefetch_related("aplicaciones"), self.request.user)
        alumno_id = self.request.query_params.get("alumno")
        estado = self.request.query_params.get("estado")
        if alumno_id:
            queryset = queryset.filter(alumno_id=alumno_id)
        return queryset.filter(estado=estado) if estado else queryset

    @action(detail=False, methods=["post"], url_path="generar")
    def generar(self, request):
        alumno_ids = request.data.get("alumnos", [])
        concepto_id = request.data.get("concepto")
        periodo = request.data.get("periodo")
        fecha_emision = request.data.get("fecha_emision")
        fecha_vencimiento = request.data.get("fecha_vencimiento")
        if not isinstance(alumno_ids, list) or not alumno_ids:
            return Response({"detail": "Debe indicar al menos un alumno."}, status=status.HTTP_400_BAD_REQUEST)
        if not all([concepto_id, periodo, fecha_emision, fecha_vencimiento]):
            return Response({"detail": "Concepto, periodo y fechas son obligatorios."}, status=status.HTTP_400_BAD_REQUEST)

        conceptos = scoped_queryset_for_user(ConceptoCobrable.objects.filter(activo=True), request.user)
        concepto = conceptos.filter(pk=concepto_id).first()
        if not concepto:
            return Response({"detail": "Concepto invalido o sin acceso."}, status=status.HTTP_400_BAD_REQUEST)
        alumnos = scoped_queryset_for_user(Alumno.objects.filter(id__in=alumno_ids, estado=Alumno.Estado.ACTIVO), request.user)
        if alumnos.count() != len(set(alumno_ids)):
            return Response({"detail": "Hay alumnos invalidos, inactivos o de otra sucursal."}, status=status.HTTP_400_BAD_REQUEST)
        if alumnos.exclude(sucursal=concepto.sucursal).exists():
            return Response({"detail": "El concepto debe pertenecer a la sucursal de todos los alumnos."}, status=status.HTTP_400_BAD_REQUEST)
        existentes = Cuota.objects.filter(alumno__in=alumnos, concepto=concepto, periodo=periodo)
        if existentes.exists():
            return Response(
                {"detail": "Ya existen cuotas para este concepto y periodo.", "alumnos": list(existentes.values_list("alumno_id", flat=True))},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            importe = Decimal(str(request.data.get("importe", concepto.importe)))
            descuento = Decimal(str(request.data.get("descuento", 0)))
            recargo = Decimal(str(request.data.get("recargo", 0)))
        except (InvalidOperation, TypeError):
            return Response({"detail": "Los importes deben ser numericos."}, status=status.HTTP_400_BAD_REQUEST)
        if importe <= 0 or descuento < 0 or recargo < 0 or descuento > importe + recargo:
            return Response({"detail": "Los importes, descuentos o recargos no son validos."}, status=status.HTTP_400_BAD_REQUEST)
        with transaction.atomic():
            cuotas = [
                Cuota(
                    alumno=alumno,
                    concepto=concepto,
                    sucursal=alumno.sucursal,
                    periodo=periodo,
                    fecha_emision=fecha_emision,
                    fecha_vencimiento=fecha_vencimiento,
                    importe=importe,
                    descuento=descuento,
                    recargo=recargo,
                )
                for alumno in alumnos
            ]
            Cuota.objects.bulk_create(cuotas)
        return Response(CuotaSerializer(cuotas, many=True).data, status=status.HTTP_201_CREATED)


class AplicacionPagoViewSet(viewsets.ModelViewSet):
    serializer_class = AplicacionPagoSerializer

    def get_queryset(self):
        cuotas = scoped_queryset_for_user(Cuota.objects.all(), self.request.user)
        return AplicacionPago.objects.select_related("pago", "cuota").filter(cuota__in=cuotas)


class PagoViewSet(viewsets.ModelViewSet):
    serializer_class = PagoSerializer

    def get_queryset(self):
        queryset = scoped_queryset_for_user(
            Pago.objects.select_related("alumno", "concepto", "sucursal"),
            self.request.user,
        )
        alumno_id = self.request.query_params.get("alumno")
        if alumno_id:
            queryset = queryset.filter(alumno_id=alumno_id)
        sucursal_id = self.request.query_params.get("sucursal")
        medio = self.request.query_params.get("medio")
        desde = self.request.query_params.get("desde")
        hasta = self.request.query_params.get("hasta")
        if sucursal_id:
            queryset = queryset.filter(sucursal_id=sucursal_id)
        if medio:
            queryset = queryset.filter(medio=medio)
        if desde:
            queryset = queryset.filter(fecha__gte=desde)
        if hasta:
            queryset = queryset.filter(fecha__lte=hasta)
        return queryset

    def perform_create(self, serializer):
        pago = serializer.save()
        caja = get_or_create_cashbox(self.request.user, pago.sucursal)
        MovimientoCaja.objects.create(
            caja=caja,
            tipo=MovimientoCaja.Tipo.PAGO,
            medio=pago.medio,
            importe=pago.importe,
            descripcion=f"Pago {pago.alumno}",
            pago=pago,
        )

    @action(detail=False, methods=["post"], url_path="cobrar")
    def cobrar(self, request):
        """Crea un pago, lo aplica a las cuotas y registra el movimiento de caja en una sola transaccion.

        Acepta los modos:
        - aplicaciones ausente o lista vacia: pago a cuenta (sin aplicaciones, todo como saldo a favor).
        - aplicaciones="auto" o modo_automatico=true: aplica a la cuota mas antigua primero.
        - aplicaciones=[{cuota_id, importe}, ...]: aplica exactamente esos importes a esas cuotas.
        """
        serializer = CobroSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        alumno = data["alumno"]
        importe = data["importe"]
        medio = data["medio"]
        observacion = data.get("observacion", "")
        concepto = data.get("concepto")
        aplicaciones = data.get("aplicaciones") or []
        modo_automatico = bool(data.get("modo_automatico", False))

        caja = get_or_create_cashbox(request.user, alumno.sucursal)
        if caja.estado == CajaDiaria.Estado.CERRADA:
            return Response(
                {"detail": "La caja del dia esta cerrada. No se pueden registrar cobros."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            pago = Pago.objects.create(
                alumno=alumno,
                concepto=concepto,
                sucursal=alumno.sucursal,
                importe=importe,
                medio=medio,
                observacion=observacion,
            )
            self._aplicar_pago_a_cuotas(pago, aplicaciones, modo_automatico=modo_automatico)
            MovimientoCaja.objects.create(
                caja=caja,
                tipo=MovimientoCaja.Tipo.PAGO,
                medio=medio,
                importe=importe,
                descripcion=f"Cobro {alumno}",
                pago=pago,
            )

        return Response(self.get_serializer(pago).data, status=status.HTTP_201_CREATED)

    def _aplicar_pago_a_cuotas(self, pago, aplicaciones, *, modo_automatico):
        """Aplica el pago a las cuotas segun el modo elegido sin exceder el importe del pago."""
        restante = pago.importe
        if aplicaciones and not modo_automatico:
            items = []
            for item in aplicaciones:
                cid = item.get("cuota_id") or item.get("cuota")
                items.append((cid, item["importe"]))
            items.sort(key=lambda x: x[0])
            for cid, importe in items:
                if restante <= Decimal("0"):
                    break
                cuota = Cuota.objects.get(pk=cid)
                importe_item = min(importe, restante, cuota.saldo)
                if importe_item <= Decimal("0"):
                    continue
                AplicacionPago.objects.create(pago=pago, cuota=cuota, importe=importe_item)
                cuota.actualizar_estado()
                restante -= importe_item
        elif modo_automatico:
            cuotas = list(
                Cuota.objects.filter(alumno=pago.alumno)
                .exclude(estado=Cuota.Estado.ANULADA)
                .exclude(estado=Cuota.Estado.PAGADA)
                .order_by("fecha_vencimiento", "id")
            )
            for cuota in cuotas:
                if restante <= Decimal("0"):
                    break
                saldo = cuota.saldo
                if saldo <= Decimal("0"):
                    continue
                importe_item = min(restante, saldo)
                AplicacionPago.objects.create(pago=pago, cuota=cuota, importe=importe_item)
                cuota.actualizar_estado()
                restante -= importe_item
        # Si no hay aplicaciones y no es automatico: pago a cuenta (sin aplicaciones).

    @action(detail=True, methods=["get"], url_path="recibo")
    def recibo(self, request, pk=None):
        pago = self.get_object()
        return Response(
            {
                "numero": pago.numero_recibo,
                "emitido_en": pago.creado,
                "pago": self.get_serializer(pago).data,
                "aplicaciones": [
                    {
                        "cuota_id": aplicacion.cuota_id,
                        "periodo": aplicacion.cuota.periodo,
                        "concepto": aplicacion.cuota.concepto.nombre,
                        "importe": aplicacion.importe,
                    }
                    for aplicacion in pago.aplicaciones.select_related("cuota__concepto")
                ],
            }
        )

    @action(detail=False, methods=["get"], url_path="exportar-csv")
    def exportar_csv(self, request):
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="pagos-ipac.csv"'
        response.write("\ufeff")
        writer = csv.writer(response)
        writer.writerow(["Recibo", "Fecha", "Alumno", "Legajo", "Concepto", "Sucursal", "Medio", "Importe", "Observacion"])
        for pago in self.get_queryset():
            writer.writerow([
                pago.numero_recibo,
                pago.fecha.isoformat(),
                f"{pago.alumno.apellido}, {pago.alumno.nombre}",
                pago.alumno.legajo,
                pago.concepto.nombre if pago.concepto else "Pago a cuenta",
                pago.sucursal.nombre,
                pago.get_medio_display(),
                pago.importe,
                pago.observacion,
            ])
        return response


class CajaDiariaViewSet(viewsets.ModelViewSet):
    serializer_class = CajaDiariaSerializer

    def get_queryset(self):
        return scoped_queryset_for_user(
            CajaDiaria.objects.select_related("sucursal", "usuario").prefetch_related("movimientos"),
            self.request.user,
        )

    @action(detail=False, methods=["get"], url_path="hoy")
    def hoy(self, request):
        sucursal_id = request.query_params.get("sucursal")
        sucursal = get_user_sucursal(request.user)
        if sucursal_id:
            allowed = Sucursal.objects.filter(id=sucursal_id)
            if not getattr(request.user, "perfil", None).puede_ver_todas_las_sucursales:
                allowed = allowed.filter(id=sucursal.id)
            sucursal = allowed.first()
        if not sucursal:
            return Response({"detail": "Sucursal invalida."}, status=status.HTTP_400_BAD_REQUEST)
        caja = get_or_create_cashbox(request.user, sucursal)
        return Response(self.get_serializer(caja).data)

    @action(detail=True, methods=["post"], url_path="cerrar")
    def cerrar(self, request, pk=None):
        caja = self.get_object()
        if caja.estado == CajaDiaria.Estado.CERRADA:
            return Response({"detail": "La caja ya esta cerrada."}, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(caja, data={"total_contado": request.data.get("total_contado", 0)}, partial=True)
        serializer.is_valid(raise_exception=True)
        caja.total_contado = serializer.validated_data["total_contado"]
        caja.estado = CajaDiaria.Estado.CERRADA
        caja.cerrada_en = timezone.now()
        caja.save(update_fields=["total_contado", "estado", "cerrada_en", "actualizado"])
        return Response(self.get_serializer(caja).data)


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer

    def get_queryset(self):
        perfil = getattr(self.request.user, "perfil", None)
        qs = User.objects.select_related("perfil__sucursal").order_by("username")
        if perfil and perfil.rol == PerfilUsuario.Rol.SUPERADMIN:
            return qs
        if perfil:
            return qs.filter(perfil__sucursal=perfil.sucursal)
        return qs.none()

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=["is_active"])


class MovimientoCajaViewSet(viewsets.ModelViewSet):
    serializer_class = MovimientoCajaSerializer

    def get_queryset(self):
        queryset = MovimientoCaja.objects.select_related("caja", "pago")
        caja_id = self.request.query_params.get("caja")
        queryset = queryset.filter(caja__in=scoped_queryset_for_user(CajaDiaria.objects.all(), self.request.user))
        if caja_id:
            queryset = queryset.filter(caja_id=caja_id)
        return queryset
