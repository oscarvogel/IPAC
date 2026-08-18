from django.db import transaction
from django.db.models import Q, Sum, Count, Min, Value, F, OuterRef, Subquery, DecimalField, IntegerField, ExpressionWrapper
from django.db.models.functions import Coalesce
from django.http import HttpResponse
from django.utils import timezone
from decimal import Decimal, InvalidOperation
from datetime import date
import csv
import io
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.views import APIView

from django.contrib.auth.models import User

from .models import AplicacionPago, Alumno, CajaDiaria, CarreraCurso, ConceptoCobrable, Cuota, Matricula, MovimientoCaja, Pago, PerfilUsuario, Sucursal
from .contexts.importacion.application.import_ipac_workbook import IPACWorkbookImporter
from .contexts.cobranzas.application.registrar_pago import RegistrarPago
from .contexts.caja.application.validar_caja import CajaCerradaError, asegurar_caja_abierta
from .contexts.alumnos.application.gestionar_matricula import GestionarMatricula, MatriculaError
from .pagination import AlumnoPagination
from .permissions import (
    AcademicManagementPermission,
    AplicacionPagoPermission,
    CASH_ROLES,
    CajaPermission,
    CuotaPermission,
    ImportacionPermission,
    MovimientoCajaPermission,
    PagoPermission,
    ReadOnlyPermission,
    SucursalPermission,
    UserManagementPermission,
)
from .serializers import (
    AlumnoSerializer,
    AplicacionPagoSerializer,
    CajaDiariaSerializer,
    CarreraCursoSerializer,
    ConceptoCobrableSerializer,
    CurrentUserSerializer,
    CuotaSerializer,
    DeudorSerializer,
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
    if queryset.model is Sucursal:
        return queryset.filter(pk=perfil.sucursal_id)
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
    permission_classes = [ReadOnlyPermission]

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
    permission_classes = [SucursalPermission]

    def get_queryset(self):
        queryset = Sucursal.objects.all()
        perfil = getattr(self.request.user, "perfil", None)
        if perfil and not perfil.puede_ver_todas_las_sucursales:
            return queryset.filter(id=perfil.sucursal_id)
        return queryset


class CarreraCursoViewSet(viewsets.ModelViewSet):
    serializer_class = CarreraCursoSerializer
    permission_classes = [AcademicManagementPermission]

    def get_queryset(self):
        return scoped_queryset_for_user(CarreraCurso.objects.select_related("sucursal"), self.request.user)


class AlumnoViewSet(viewsets.ModelViewSet):
    serializer_class = AlumnoSerializer
    pagination_class = AlumnoPagination
    permission_classes = [AcademicManagementPermission]

    def get_queryset(self):
        queryset = scoped_queryset_for_user(
            Alumno.objects.select_related("sucursal", "carrera"),
            self.request.user,
        )

        search = self.request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(
                Q(nombre__icontains=search)
                | Q(apellido__icontains=search)
                | Q(dni__icontains=search)
                | Q(legajo__icontains=search)
            )
        sucursal = self.request.query_params.get("sucursal")
        estado = self.request.query_params.get("estado")
        carrera = self.request.query_params.get("carrera")
        if sucursal:
            queryset = queryset.filter(sucursal_id=sucursal)
        if estado:
            queryset = queryset.filter(estado=estado)
        if carrera:
            queryset = queryset.filter(carrera_id=carrera)
        return queryset

    @action(detail=False, methods=["get"], url_path="estadisticas")
    def estadisticas(self, request):
        queryset = self.get_queryset()
        return Response(queryset.aggregate(
            total=Count("id"),
            activos=Count("id", filter=Q(estado=Alumno.Estado.ACTIVO)),
            inactivos=Count("id", filter=~Q(estado=Alumno.Estado.ACTIVO)),
        ))

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


class DeudoresView(APIView):
    permission_classes = [ReadOnlyPermission]

    def get(self, request):
        today = timezone.localdate()
        cuotas = scoped_queryset_for_user(Cuota.objects.all(), request.user).exclude(
            estado=Cuota.Estado.ANULADA,
        )
        paid_for_cuota = AplicacionPago.objects.filter(cuota_id=OuterRef("pk")).values("cuota_id").annotate(
            total=Sum("importe"),
        ).values("total")[:1]
        cuotas = cuotas.annotate(
            saldo_calculado=ExpressionWrapper(
                F("importe") - F("descuento") + F("recargo") - Coalesce(
                    Subquery(paid_for_cuota, output_field=DecimalField(max_digits=12, decimal_places=2)),
                    Value(Decimal("0")),
                ),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            ),
        ).filter(saldo_calculado__gt=0)

        deuda_total = cuotas.filter(alumno_id=OuterRef("pk")).values("alumno_id").annotate(
            total=Sum("saldo_calculado"),
        ).values("total")[:1]
        cuotas_pendientes = cuotas.filter(alumno_id=OuterRef("pk")).values("alumno_id").annotate(
            total=Count("id"),
        ).values("total")[:1]
        cuotas_vencidas = cuotas.filter(
            alumno_id=OuterRef("pk"),
            fecha_vencimiento__lt=today,
        ).values("alumno_id").annotate(total=Count("id")).values("total")[:1]
        cuota_vencida_mas_antigua = cuotas.filter(
            alumno_id=OuterRef("pk"),
            fecha_vencimiento__lt=today,
        ).values("alumno_id").annotate(first=Min("fecha_vencimiento")).values("first")[:1]

        queryset = Alumno.objects.select_related("sucursal", "carrera").filter(
            pk__in=Subquery(cuotas.values("alumno_id").distinct()),
        ).annotate(
            deuda_total=Subquery(deuda_total, output_field=DecimalField(max_digits=12, decimal_places=2)),
            cuotas_pendientes=Subquery(cuotas_pendientes, output_field=IntegerField()),
            cuotas_vencidas=Subquery(cuotas_vencidas, output_field=IntegerField()),
            cuota_vencida_mas_antigua=Subquery(cuota_vencida_mas_antigua),
            fecha_ultimo_pago=Subquery(
                Pago.objects.filter(alumno_id=OuterRef("pk"))
                .order_by("-fecha", "-id")
                .values("fecha")[:1],
            ),
        )

        search = request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(
                Q(nombre__icontains=search)
                | Q(apellido__icontains=search)
                | Q(dni__icontains=search)
                | Q(legajo__icontains=search),
            )
        sucursal = request.query_params.get("sucursal")
        carrera = request.query_params.get("carrera")
        if sucursal:
            queryset = queryset.filter(sucursal_id=sucursal)
        if carrera:
            queryset = queryset.filter(carrera_id=carrera)
        if request.query_params.get("vencidas", "").lower() in {"1", "true", "si", "sí"}:
            queryset = queryset.filter(cuotas_vencidas__gt=0)

        for parameter, lookup in (("deuda_min", "deuda_total__gte"), ("deuda_max", "deuda_total__lte")):
            value = request.query_params.get(parameter)
            if value:
                try:
                    queryset = queryset.filter(**{lookup: Decimal(value)})
                except (InvalidOperation, TypeError):
                    return Response({"detail": f"{parameter} debe ser numérico."}, status=status.HTTP_400_BAD_REQUEST)

        ordering = request.query_params.get("orden", "deuda")
        if ordering == "antiguedad":
            queryset = queryset.order_by(F("cuota_vencida_mas_antigua").asc(nulls_last=True), "-deuda_total", "apellido", "nombre")
        else:
            queryset = queryset.order_by("-deuda_total", F("cuota_vencida_mas_antigua").asc(nulls_last=True), "apellido", "nombre")

        paginator = AlumnoPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        return paginator.get_paginated_response(DeudorSerializer(page, many=True).data)
class ConceptoCobrableViewSet(viewsets.ModelViewSet):
    serializer_class = ConceptoCobrableSerializer
    permission_classes = [AcademicManagementPermission]

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
    permission_classes = [AcademicManagementPermission]

    def get_queryset(self):
        queryset = scoped_queryset_for_user(Matricula.objects.select_related("alumno", "carrera", "sucursal"), self.request.user)
        alumno_id = self.request.query_params.get("alumno")
        return queryset.filter(alumno_id=alumno_id) if alumno_id else queryset

    @action(detail=True, methods=["post"], url_path="finalizar")
    def finalizar(self, request, pk=None):
        matricula = self.get_object()
        try:
            finalized = GestionarMatricula().finalizar(matricula, fecha_fin=request.data.get("fecha_fin") or timezone.localdate())
        except MatriculaError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(self.get_serializer(finalized).data)


class CuotaViewSet(viewsets.ModelViewSet):
    serializer_class = CuotaSerializer
    permission_classes = [CuotaPermission]

    def get_queryset(self):
        queryset = scoped_queryset_for_user(Cuota.objects.select_related("alumno", "matricula", "concepto", "sucursal").prefetch_related("aplicaciones"), self.request.user)
        alumno_id = self.request.query_params.get("alumno")
        estado = self.request.query_params.get("estado")
        if alumno_id:
            queryset = queryset.filter(alumno_id=alumno_id)
        return queryset.filter(estado=estado) if estado else queryset

    @action(detail=False, methods=["post"], url_path="evaluar-generacion")
    def evaluar_generacion(self, request):
        sucursal_id = request.data.get("sucursal")
        carrera_id = request.data.get("carrera")
        concepto_id = request.data.get("concepto")
        periodo = request.data.get("periodo")
        if not all([sucursal_id, concepto_id, periodo]):
            return Response(
                {"detail": "Sucursal, concepto y periodo son obligatorios."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        conceptos = scoped_queryset_for_user(ConceptoCobrable.objects.filter(activo=True), request.user)
        concepto = conceptos.filter(pk=concepto_id, sucursal_id=sucursal_id).first()
        if not concepto:
            return Response({"detail": "Concepto invalido o sin acceso."}, status=status.HTTP_400_BAD_REQUEST)

        alumnos = scoped_queryset_for_user(
            Alumno.objects.filter(estado=Alumno.Estado.ACTIVO, sucursal_id=sucursal_id),
            request.user,
        )
        if carrera_id:
            carrera = scoped_queryset_for_user(CarreraCurso.objects.all(), request.user).filter(
                pk=carrera_id,
                sucursal_id=sucursal_id,
            ).first()
            if not carrera:
                return Response({"detail": "Carrera invalida o sin acceso."}, status=status.HTTP_400_BAD_REQUEST)
            alumnos = alumnos.filter(carrera_id=carrera.id)

        existing_alumnos = Cuota.objects.filter(
            alumno_id__in=alumnos.values("id"),
            concepto_id=concepto.id,
            periodo=periodo,
        ).values("alumno_id")
        eligible_ids = list(alumnos.exclude(id__in=existing_alumnos).values_list("id", flat=True))
        found_count = alumnos.count()
        return Response({
            "alumnos_encontrados": found_count,
            "omitidas": found_count - len(eligible_ids),
            "alumnos_elegibles": eligible_ids,
        })

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
    permission_classes = [AplicacionPagoPermission]

    def get_queryset(self):
        cuotas = scoped_queryset_for_user(Cuota.objects.all(), self.request.user)
        return AplicacionPago.objects.select_related("pago", "cuota").filter(cuota__in=cuotas)


class PagoViewSet(viewsets.ModelViewSet):
    serializer_class = PagoSerializer
    permission_classes = [PagoPermission]

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

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            pago = RegistrarPago().execute(user=request.user, **serializer.validated_data)
        except ValueError as exc:
            raise ValidationError({"detail": str(exc)}) from exc
        response_serializer = self.get_serializer(pago)
        headers = self.get_success_headers(response_serializer.data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

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
    permission_classes = [CajaPermission]

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
        if request.user.perfil.rol in CASH_ROLES:
            caja = get_or_create_cashbox(request.user, sucursal)
        else:
            caja = CajaDiaria.objects.filter(
                fecha=timezone.localdate(),
                sucursal=sucursal,
                usuario=request.user,
            ).first()
            if not caja:
                return Response({"detail": "No hay una caja disponible para consultar."}, status=status.HTTP_404_NOT_FOUND)
        return Response(self.get_serializer(caja).data)

    @action(detail=True, methods=["post"], url_path="cerrar")
    @transaction.atomic
    def cerrar(self, request, pk=None):
        caja_ref = self.get_object()
        caja = CajaDiaria.objects.select_for_update().get(pk=caja_ref.pk)
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
    permission_classes = [UserManagementPermission]

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
    permission_classes = [MovimientoCajaPermission]

    def get_queryset(self):
        queryset = MovimientoCaja.objects.select_related("caja", "pago")
        caja_id = self.request.query_params.get("caja")
        queryset = queryset.filter(caja__in=scoped_queryset_for_user(CajaDiaria.objects.all(), self.request.user))
        if caja_id:
            queryset = queryset.filter(caja_id=caja_id)
        return queryset

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        caja_id = request.data.get("caja")
        if caja_id:
            caja = CajaDiaria.objects.select_for_update().filter(pk=caja_id).first()
            if caja:
                try:
                    asegurar_caja_abierta(caja)
                except CajaCerradaError as exc:
                    raise ValidationError({"caja": str(exc)}) from exc
        return super().create(request, *args, **kwargs)


IMPORT_ROLES = {PerfilUsuario.Rol.SUPERADMIN, PerfilUsuario.Rol.ADMINISTRACION}
TEMPLATE_COLUMNS = {
    "alumnos": [
        "sucursal_codigo", "legajo", "apellido", "nombre", "dni", "cuil",
        "fecha_nacimiento", "email", "telefono", "domicilio", "carrera",
    ],
    "carreras": [
        "sucursal_codigo", "nombre", "tipo", "duracion", "plan_cuotas",
        "importe_matricula", "cuota_programatica", "cuota_extraprogramatica",
        "cuota_total", "cuota_convenio_20", "cuota_convenio_15", "descripcion",
    ],
}


def _can_import(user):
    perfil = getattr(user, "perfil", None)
    return bool(perfil and perfil.rol in IMPORT_ROLES)


class ImportacionPlantillasView(APIView):
    permission_classes = [ImportacionPermission]

    def get(self, request):
        return Response(
            {
                "formato": "CSV UTF-8 separado por punto y coma; también se aceptan XLSX.",
                "plantillas": {
                    key: {
                        "columnas": columns,
                        "descarga": f"/api/importaciones/plantillas/{key}/",
                    }
                    for key, columns in TEMPLATE_COLUMNS.items()
                },
            }
        )


class ImportacionPlantillaCsvView(APIView):
    permission_classes = [ImportacionPermission]

    def get(self, request, kind):
        columns = TEMPLATE_COLUMNS.get(kind)
        if not columns:
            return Response({"detail": "Plantilla desconocida."}, status=status.HTTP_404_NOT_FOUND)
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="plantilla_ipac_{kind}.csv"'
        response.write("\ufeff")
        writer = csv.writer(response, delimiter=";")
        writer.writerow(columns)
        return response


class ImportacionWorkbookView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [ImportacionPermission]

    def post(self, request):
        if not _can_import(request.user):
            return Response({"detail": "Solo Administración puede importar datos."}, status=status.HTTP_403_FORBIDDEN)
        source = request.FILES.get("archivo")
        if not source:
            return Response({"detail": "Debe seleccionar un archivo XLSX o CSV."}, status=status.HTTP_400_BAD_REQUEST)
        filename = source.name or "archivo.xlsx"
        if not filename.lower().endswith((".xlsx", ".csv")):
            return Response({"detail": "El archivo debe tener extensión .xlsx o .csv."}, status=status.HTTP_400_BAD_REQUEST)
        perfil = request.user.perfil
        default_branch = request.data.get("sucursal") or perfil.sucursal.codigo
        default_career = request.data.get("carrera", "")
        allowed_branches = None if perfil.puede_ver_todas_las_sucursales else {perfil.sucursal.codigo}
        try:
            result = IPACWorkbookImporter().import_file(
                source,
                filename,
                default_branch_code=default_branch,
                default_career_name=default_career,
                allowed_branch_codes=allowed_branches,
            )
        except (ValueError, KeyError, OSError, ImportError) as exc:
            return Response({"detail": f"No se pudo leer el archivo: {exc}"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(result.as_dict(), status=status.HTTP_200_OK)
