from django.db import connection, transaction
from django.db.models import Q, Sum, Count, Min, Value, F, OuterRef, Subquery, DecimalField, IntegerField, ExpressionWrapper
from django.db.models.functions import Coalesce, Greatest
from django.http import HttpResponse
from django.core import signing
from django.utils import timezone
from decimal import Decimal, InvalidOperation
from datetime import date
import csv
import hashlib
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

from .models import AplicacionPago, Alumno, CajaDiaria, CarreraCurso, ConceptoCobrable, Cuota, EventoAuditoria, Matricula, MovimientoCaja, Pago, PerfilUsuario, ReglaRecargo, Sucursal, TipoDescuento
from .contexts.importacion.application.import_ipac_workbook import IPACWorkbookImporter
from .contexts.cobranzas.application.registrar_pago import RegistrarPago
from .contexts.cobranzas.application.anular_pago import AnularPago, PagoAnulacionError
from .contexts.caja.application.validar_caja import CajaCerradaError, asegurar_caja_abierta
from .contexts.caja.application.gestionar_caja import CerrarCaja, GestionarSaldoAnterior
from .contexts.caja.domain.resumen_caja import CajaOperacionError
from .contexts.caja.infrastructure.django_caja_repository import DjangoCajaRepository
from .contexts.alumnos.application.gestionar_matricula import GestionarMatricula, MatriculaError
from .contexts.auditoria.presentation.mixins import AuditableViewSetMixin, snapshot
from .contexts.auditoria.application.registrar_evento import RegistrarEventoAuditoria
from .contexts.auditoria.infrastructure.django_auditoria_repository import DjangoAuditoriaRepository
from .contexts.reportes.infrastructure.xlsx_exporter import XlsxReportExporter
from .contexts.cobranzas.application.recalcular_recargos import RecalcularRecargos
from .contexts.cobranzas.infrastructure.django_recargo_repository import DjangoRecargoRepository
from .contexts.identidad.application.cambiar_clave import CambiarClave
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
    AuditoriaPermission,
)
from .serializers import (
    AlumnoSerializer,
    AplicacionPagoSerializer,
    CajaDiariaSerializer,
    CarreraCursoSerializer,
    ConceptoCobrableSerializer,
    CobroSerializer,
    ChangePasswordSerializer,
    CurrentUserSerializer,
    CuotaSerializer,
    DeudorSerializer,
    LoginSerializer,
    MatriculaSerializer,
    MovimientoCajaSerializer,
    PagoSerializer,
    SucursalSerializer,
    UserSerializer,
    EventoAuditoriaSerializer,
    TipoDescuentoSerializer,
    ReglaRecargoSerializer,
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


def filtered_payments(request):
    queryset = scoped_queryset_for_user(
        Pago.objects.filter(estado=Pago.Estado.ACTIVO).select_related(
            "alumno", "concepto", "sucursal", "registrado_por"
        ),
        request.user,
    )
    filters = {
        "sucursal_id": request.query_params.get("sucursal"),
        "medio": request.query_params.get("medio"),
        "registrado_por_id": request.query_params.get("usuario"),
        "fecha__gte": request.query_params.get("desde"),
        "fecha__lte": request.query_params.get("hasta"),
    }
    for field, value in filters.items():
        if value:
            queryset = queryset.filter(**{field: value})
    return queryset


class LoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        token, _ = Token.objects.get_or_create(user=serializer.validated_data["user"])
        return Response({
            "key": token.key,
            "debe_cambiar_clave": serializer.validated_data["user"].perfil.debe_cambiar_clave,
        })


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            CambiarClave().execute(
                user=request.user,
                profile=request.user.perfil,
                new_password=serializer.validated_data["new_password"],
            )
        return Response({"debe_cambiar_clave": False})


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(CurrentUserSerializer(request.user).data)


class HealthView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        connection.ensure_connection()
        return Response({"status": "ok"})


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

        pagos = Pago.objects.filter(
            sucursal__in=sucursales,
            fecha__range=(desde, hasta),
            estado=Pago.Estado.ACTIVO,
        )
        if medio := request.query_params.get("medio"):
            pagos = pagos.filter(medio=medio)
        if usuario := request.query_params.get("usuario"):
            pagos = pagos.filter(registrado_por_id=usuario)
        cuotas = Cuota.objects.filter(sucursal__in=sucursales).exclude(estado=Cuota.Estado.ANULADA).prefetch_related("aplicaciones")
        cajas = CajaDiaria.objects.filter(sucursal__in=sucursales, fecha__range=(desde, hasta))
        deuda = sum((cuota.saldo for cuota in cuotas), Decimal("0"))
        cuotas_con_saldo = [cuota for cuota in cuotas if cuota.saldo > 0]
        alumnos_con_deuda = len({cuota.alumno_id for cuota in cuotas_con_saldo})
        cuotas_vencidas = sum(1 for cuota in cuotas_con_saldo if cuota.fecha_vencimiento < hoy)
        saldo_a_favor = sum((pago.saldo_a_favor for pago in Pago.objects.filter(
            sucursal__in=sucursales,
            estado=Pago.Estado.ACTIVO,
        ).prefetch_related("aplicaciones")), Decimal("0"))
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
                    "hoy": pagos.filter(fecha=hoy).aggregate(total=Sum("importe"))["total"] or Decimal("0"),
                    "por_medio": cobrado_por_medio,
                    "por_sucursal": list(
                        pagos.values("sucursal_id", "sucursal__nombre")
                        .annotate(total=Sum("importe"), cantidad=Count("id"))
                        .order_by("sucursal__nombre")
                    ),
                },
                "cuenta_corriente": {
                    "deuda": deuda,
                    "saldo_a_favor": saldo_a_favor,
                    "saldo_neto": deuda - saldo_a_favor,
                    "alumnos_con_deuda": alumnos_con_deuda,
                    "cuotas_vencidas": cuotas_vencidas,
                },
                "cajas": {
                    "abiertas": cajas.filter(estado=CajaDiaria.Estado.ABIERTA).count(),
                    "cerradas": cajas.filter(estado=CajaDiaria.Estado.CERRADA).count(),
                    "diferencia_acumulada": sum(
                        (caja.diferencia for caja in cajas.filter(estado=CajaDiaria.Estado.CERRADA)),
                        Decimal("0"),
                    ),
                },
            }
        )


class ReporteCobranzasUsuariosView(APIView):
    permission_classes = [ReadOnlyPermission]

    def get(self, request):
        pagos = filtered_payments(request)
        groups = pagos.values("registrado_por_id", "registrado_por__username").annotate(
            cantidad=Count("id"),
            efectivo=Coalesce(Sum("importe", filter=Q(medio=Pago.Medio.EFECTIVO)), Value(Decimal("0"))),
            transferencia=Coalesce(Sum("importe", filter=Q(medio=Pago.Medio.TRANSFERENCIA)), Value(Decimal("0"))),
            mercado_pago=Coalesce(Sum("importe", filter=Q(medio=Pago.Medio.MERCADO_PAGO)), Value(Decimal("0"))),
            tarjeta=Coalesce(Sum("importe", filter=Q(medio=Pago.Medio.TARJETA)), Value(Decimal("0"))),
            otro=Coalesce(Sum("importe", filter=Q(medio=Pago.Medio.OTRO)), Value(Decimal("0"))),
            total=Coalesce(Sum("importe"), Value(Decimal("0"))),
        ).order_by("registrado_por__username")

        cajas = scoped_queryset_for_user(CajaDiaria.objects.select_related("usuario"), request.user)
        if sucursal := request.query_params.get("sucursal"):
            cajas = cajas.filter(sucursal_id=sucursal)
        if usuario := request.query_params.get("usuario"):
            cajas = cajas.filter(usuario_id=usuario)
        if desde := request.query_params.get("desde"):
            cajas = cajas.filter(fecha__gte=desde)
        if hasta := request.query_params.get("hasta"):
            cajas = cajas.filter(fecha__lte=hasta)
        diferencias = {}
        for caja in cajas.filter(estado=CajaDiaria.Estado.CERRADA):
            diferencias[caja.usuario_id] = diferencias.get(caja.usuario_id, Decimal("0")) + caja.diferencia

        results = []
        for row in groups:
            actor_id = row.pop("registrado_por_id")
            row["usuario_id"] = actor_id
            row["usuario"] = row.pop("registrado_por__username") or "Sin usuario registrado"
            row["diferencia_caja"] = diferencias.get(actor_id, Decimal("0"))
            results.append(row)
        return Response({"resultados": results, "total": pagos.aggregate(total=Sum("importe"))["total"] or Decimal("0")})


class ReporteExportarExcelView(APIView):
    permission_classes = [ReadOnlyPermission]

    def get(self, request):
        report_type = request.query_params.get("tipo", "pagos")
        if report_type == "pagos":
            headers = ["Recibo", "Fecha", "Alumno", "Legajo", "Concepto", "Sucursal", "Usuario", "Medio", "Importe"]
            rows = [
                [
                    pago.numero_recibo, pago.fecha, str(pago.alumno), pago.alumno.legajo,
                    pago.concepto.nombre if pago.concepto else "Pago a cuenta", pago.sucursal.nombre,
                    pago.registrado_por.username if pago.registrado_por else "Sin usuario", pago.get_medio_display(), pago.importe,
                ]
                for pago in filtered_payments(request)
            ]
            title = "Cobranzas"
        elif report_type in {"morosidad", "deuda"}:
            headers = ["Alumno", "Legajo", "Teléfono", "Sucursal", "Carrera", "Deuda total", "Cuotas pendientes", "Cuotas vencidas", "Vencimiento más antiguo", "Días de mora"]
            debtors = DeudoresView.build_queryset(request)
            rows = [
                [
                    str(alumno), alumno.legajo, alumno.telefono, alumno.sucursal.nombre,
                    alumno.carrera.nombre if alumno.carrera else "Sin carrera", alumno.deuda_total,
                    alumno.cuotas_pendientes, alumno.cuotas_vencidas or 0, alumno.cuota_vencida_mas_antigua,
                    max((timezone.localdate() - alumno.cuota_vencida_mas_antigua).days, 0) if alumno.cuota_vencida_mas_antigua else 0,
                ]
                for alumno in debtors
            ]
            title = "Morosidad"
        elif report_type == "cajas":
            headers = ["Fecha", "Sucursal", "Usuario", "Estado", "Saldo inicial", "Efectivo esperado", "Total contado", "Diferencia", "Saldo siguiente"]
            cajas = scoped_queryset_for_user(CajaDiaria.objects.select_related("sucursal", "usuario").prefetch_related("movimientos"), request.user)
            if sucursal := request.query_params.get("sucursal"):
                cajas = cajas.filter(sucursal_id=sucursal)
            if desde := request.query_params.get("desde"):
                cajas = cajas.filter(fecha__gte=desde)
            if hasta := request.query_params.get("hasta"):
                cajas = cajas.filter(fecha__lte=hasta)
            rows = [[c.fecha, c.sucursal.nombre, c.usuario.username, c.get_estado_display(), c.saldo_inicial, c.total_esperado, c.total_contado, c.diferencia, c.saldo_arrastrable] for c in cajas]
            title = "Cajas"
        elif report_type == "alumnos":
            headers = ["Legajo", "Apellido", "Nombre", "DNI", "Sucursal", "Carrera/curso", "Estado", "Teléfono", "Email"]
            alumnos = scoped_queryset_for_user(
                Alumno.objects.select_related("sucursal", "carrera"), request.user
            )
            if sucursal := request.query_params.get("sucursal"):
                alumnos = alumnos.filter(sucursal_id=sucursal)
            if carrera := request.query_params.get("carrera"):
                alumnos = alumnos.filter(carrera_id=carrera)
            if estado_alumno := request.query_params.get("estado"):
                alumnos = alumnos.filter(estado=estado_alumno)
            if search := request.query_params.get("search", "").strip():
                alumnos = alumnos.filter(
                    Q(nombre__icontains=search)
                    | Q(apellido__icontains=search)
                    | Q(dni__icontains=search)
                    | Q(legajo__icontains=search)
                )
            rows = [
                [
                    alumno.legajo, alumno.apellido, alumno.nombre, alumno.dni,
                    alumno.sucursal.nombre,
                    alumno.carrera.nombre if alumno.carrera else "Sin matrícula activa",
                    alumno.get_estado_display(), alumno.telefono, alumno.email,
                ]
                for alumno in alumnos.order_by("apellido", "nombre")
            ]
            title = "Alumnos"
        else:
            raise ValidationError({"detail": "Tipo de reporte Excel no soportado."})

        payload = XlsxReportExporter().export(title=title, headers=headers, rows=rows)
        response = HttpResponse(payload, content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response["Content-Disposition"] = f'attachment; filename="ipac-{report_type}.xlsx"'
        return response


class SucursalViewSet(AuditableViewSetMixin, viewsets.ModelViewSet):
    audit_module = "organizacion"
    serializer_class = SucursalSerializer
    permission_classes = [SucursalPermission]

    def get_queryset(self):
        queryset = Sucursal.objects.all()
        perfil = getattr(self.request.user, "perfil", None)
        if perfil and not perfil.puede_ver_todas_las_sucursales:
            return queryset.filter(id=perfil.sucursal_id)
        return queryset


class CarreraCursoViewSet(AuditableViewSetMixin, viewsets.ModelViewSet):
    audit_module = "trayectoria"
    serializer_class = CarreraCursoSerializer
    permission_classes = [AcademicManagementPermission]

    def get_queryset(self):
        return scoped_queryset_for_user(CarreraCurso.objects.select_related("sucursal"), self.request.user)


class AlumnoViewSet(AuditableViewSetMixin, viewsets.ModelViewSet):
    audit_module = "alumnos"
    serializer_class = AlumnoSerializer
    pagination_class = AlumnoPagination
    permission_classes = [AcademicManagementPermission]

    def get_queryset(self):
        money = DecimalField(max_digits=14, decimal_places=2)
        deuda_por_alumno = (
            Cuota.objects.filter(alumno_id=OuterRef("pk"))
            .exclude(estado=Cuota.Estado.ANULADA)
            .values("alumno_id")
            .annotate(
                total=Sum(F("importe") - F("descuento") + F("recargo"), output_field=money)
                - Coalesce(
                    Sum("aplicaciones__importe", filter=Q(aplicaciones__activa=True)),
                    Value(Decimal("0")),
                    output_field=money,
                )
            )
            .values("total")[:1]
        )
        pagos_por_alumno = (
            Pago.objects.filter(alumno_id=OuterRef("pk"), estado=Pago.Estado.ACTIVO)
            .values("alumno_id")
            .annotate(total=Sum("importe"))
            .values("total")[:1]
        )
        aplicado_por_alumno = (
            AplicacionPago.objects.filter(
                pago__alumno_id=OuterRef("pk"),
                pago__estado=Pago.Estado.ACTIVO,
                activa=True,
            )
            .values("pago__alumno_id")
            .annotate(total=Sum("importe"))
            .values("total")[:1]
        )
        queryset = scoped_queryset_for_user(
            Alumno.objects.select_related("sucursal", "carrera").annotate(
                deuda_total=Greatest(
                    Coalesce(Subquery(deuda_por_alumno, output_field=money), Value(Decimal("0")), output_field=money),
                    Value(Decimal("0")),
                    output_field=money,
                ),
                saldo_a_favor=Greatest(
                    Coalesce(Subquery(pagos_por_alumno, output_field=money), Value(Decimal("0")), output_field=money)
                    - Coalesce(Subquery(aplicado_por_alumno, output_field=money), Value(Decimal("0")), output_field=money),
                    Value(Decimal("0")),
                    output_field=money,
                ),
            ),
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
        con_deuda = self.request.query_params.get("con_deuda")
        con_saldo_favor = self.request.query_params.get("con_saldo_favor")
        if sucursal:
            queryset = queryset.filter(sucursal_id=sucursal)
        if estado:
            queryset = queryset.filter(estado=estado)
        if carrera:
            queryset = queryset.filter(carrera_id=carrera)
        if con_deuda in {"1", "true"}:
            queryset = queryset.filter(deuda_total__gt=0)
        if con_saldo_favor in {"1", "true"}:
            queryset = queryset.filter(saldo_a_favor__gt=0)
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

    @staticmethod
    def build_queryset(request):
        today = timezone.localdate()
        cuotas = scoped_queryset_for_user(Cuota.objects.all(), request.user).exclude(
            estado=Cuota.Estado.ANULADA,
        )
        periodo = request.query_params.get("periodo")
        if periodo:
            cuotas = cuotas.filter(periodo=periodo)
        paid_for_cuota = AplicacionPago.objects.filter(
            cuota_id=OuterRef("pk"),
            activa=True,
        ).values("cuota_id").annotate(
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
                Pago.objects.filter(alumno_id=OuterRef("pk"), estado=Pago.Estado.ACTIVO)
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
        segmento = request.query_params.get("segmento")
        if segmento == "1":
            queryset = queryset.filter(cuotas_vencidas=1)
        elif segmento == "2":
            queryset = queryset.filter(cuotas_vencidas=2)
        elif segmento == "3plus":
            queryset = queryset.filter(cuotas_vencidas__gte=3)

        for parameter, lookup in (("deuda_min", "deuda_total__gte"), ("deuda_max", "deuda_total__lte")):
            value = request.query_params.get(parameter)
            if value:
                try:
                    queryset = queryset.filter(**{lookup: Decimal(value)})
                except (InvalidOperation, TypeError):
                    raise ValidationError({"detail": f"{parameter} debe ser numérico."})

        ordering = request.query_params.get("orden", "deuda")
        if ordering == "antiguedad":
            queryset = queryset.order_by(F("cuota_vencida_mas_antigua").asc(nulls_last=True), "-deuda_total", "apellido", "nombre")
        else:
            queryset = queryset.order_by("-deuda_total", F("cuota_vencida_mas_antigua").asc(nulls_last=True), "apellido", "nombre")
        return queryset

    def get(self, request):
        queryset = self.build_queryset(request)
        paginator = AlumnoPagination()
        page = paginator.paginate_queryset(queryset, request, view=self)
        return paginator.get_paginated_response(DeudorSerializer(page, many=True).data)
class ConceptoCobrableViewSet(AuditableViewSetMixin, viewsets.ModelViewSet):
    audit_module = "cobranzas"
    serializer_class = ConceptoCobrableSerializer
    permission_classes = [AcademicManagementPermission]

    def get_queryset(self):
        return scoped_queryset_for_user(
            ConceptoCobrable.objects.select_related("sucursal", "carrera"),
            self.request.user,
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        before = snapshot(instance)
        instance.activo = False
        instance.save(update_fields=["activo", "actualizado"])
        self._audit(action="baja", instance=instance, before=before, after=snapshot(instance), description="Concepto desactivado")
        return Response(status=status.HTTP_204_NO_CONTENT)


class TipoDescuentoViewSet(AuditableViewSetMixin, viewsets.ModelViewSet):
    audit_module = "cobranzas"
    serializer_class = TipoDescuentoSerializer
    permission_classes = [AcademicManagementPermission]

    def get_queryset(self):
        return scoped_queryset_for_user(TipoDescuento.objects.select_related("sucursal"), self.request.user)


class ReglaRecargoViewSet(AuditableViewSetMixin, viewsets.ModelViewSet):
    audit_module = "cobranzas"
    serializer_class = ReglaRecargoSerializer
    permission_classes = [AcademicManagementPermission]

    def get_queryset(self):
        return scoped_queryset_for_user(ReglaRecargo.objects.select_related("sucursal", "concepto"), self.request.user)

    @action(detail=False, methods=["post"], url_path="recalcular")
    def recalcular(self, request):
        sucursales = scoped_queryset_for_user(Sucursal.objects.all(), request.user)
        if sucursal_id := request.data.get("sucursal"):
            sucursales = sucursales.filter(pk=sucursal_id)
        result = RecalcularRecargos(DjangoRecargoRepository()).execute(
            sucursal_ids=list(sucursales.values_list("id", flat=True)),
        )
        RegistrarEventoAuditoria(DjangoAuditoriaRepository()).execute(
            usuario=request.user,
            sucursal=get_user_sucursal(request.user),
            modulo="cobranzas",
            accion="recalculo",
            entidad="core.ReglaRecargo",
            entidad_id="masivo",
            descripcion="Recargos vencidos recalculados",
            metadata=result,
        )
        return Response(result)


class MatriculaViewSet(AuditableViewSetMixin, viewsets.ModelViewSet):
    audit_module = "trayectoria"
    serializer_class = MatriculaSerializer
    permission_classes = [AcademicManagementPermission]

    def get_queryset(self):
        queryset = scoped_queryset_for_user(Matricula.objects.select_related("alumno", "carrera", "sucursal"), self.request.user)
        alumno_id = self.request.query_params.get("alumno")
        return queryset.filter(alumno_id=alumno_id) if alumno_id else queryset

    @action(detail=True, methods=["post"], url_path="finalizar")
    def finalizar(self, request, pk=None):
        matricula = self.get_object()
        before = snapshot(matricula)
        try:
            finalized = GestionarMatricula().finalizar(matricula, fecha_fin=request.data.get("fecha_fin") or timezone.localdate())
        except MatriculaError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        self._audit(action="finalizacion", instance=finalized, before=before, after=snapshot(finalized))
        return Response(self.get_serializer(finalized).data)

    @action(detail=True, methods=["post"], url_path="anular")
    def anular(self, request, pk=None):
        matricula = self.get_object()
        before = snapshot(matricula)
        try:
            annulled = GestionarMatricula().anular(
                matricula,
                motivo=request.data.get("motivo"),
                fecha_fin=request.data.get("fecha_fin") or timezone.localdate(),
            )
        except MatriculaError as exc:
            raise ValidationError({"detail": str(exc)}) from exc
        self._audit(action="anulacion", instance=annulled, before=before, after=snapshot(annulled))
        return Response(self.get_serializer(annulled).data)

    @action(detail=True, methods=["post"], url_path="cambiar-carrera")
    def cambiar_carrera(self, request, pk=None):
        matricula = self.get_object()
        before = snapshot(matricula)
        carrera = scoped_queryset_for_user(CarreraCurso.objects.filter(activa=True), request.user).filter(
            pk=request.data.get("carrera")
        ).first()
        if not carrera:
            raise ValidationError({"detail": "Carrera inválida o sin acceso."})
        try:
            replacement = GestionarMatricula().cambiar_carrera(
                matricula,
                carrera=carrera,
                fecha_inicio=request.data.get("fecha_inicio") or timezone.localdate(),
                observacion=request.data.get("observacion", ""),
            )
        except MatriculaError as exc:
            raise ValidationError({"detail": str(exc)}) from exc
        matricula.refresh_from_db()
        self._audit(action="cambio_carrera", instance=matricula, before=before, after=snapshot(matricula), description=f"Cambio a matrícula {replacement.pk}")
        self._audit(action="alta", instance=replacement, after=snapshot(replacement), description="Matrícula creada por cambio de carrera")
        return Response(self.get_serializer(replacement).data, status=status.HTTP_201_CREATED)


class CuotaViewSet(AuditableViewSetMixin, viewsets.ModelViewSet):
    audit_module = "cobranzas"
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
        tipo_descuento = None
        motivo_descuento = request.data.get("motivo_descuento", "")
        if tipo_id := request.data.get("tipo_descuento"):
            tipo_descuento = scoped_queryset_for_user(TipoDescuento.objects.filter(activo=True), request.user).filter(
                pk=tipo_id,
                sucursal=concepto.sucursal,
            ).first()
            if not tipo_descuento:
                raise ValidationError({"detail": "Tipo de descuento inválido o sin acceso."})
            if tipo_descuento.valor > 0:
                descuento = tipo_descuento.calcular(importe)
        elif descuento > 0:
            tipo_descuento, _ = TipoDescuento.objects.get_or_create(
                nombre="Excepción manual",
                sucursal=concepto.sucursal,
                defaults={"modalidad": TipoDescuento.Modalidad.IMPORTE, "valor": 0},
            )
            motivo_descuento = motivo_descuento or "Ajuste manual"
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
                    tipo_descuento=tipo_descuento,
                    motivo_descuento=motivo_descuento,
                    descuento_registrado_por=request.user if descuento > 0 else None,
                    recargo=recargo,
                )
                for alumno in alumnos
            ]
            Cuota.objects.bulk_create(cuotas)
            for cuota in cuotas:
                self._audit(action="alta", instance=cuota, after=snapshot(cuota), description="Generación masiva de cuota")
        return Response(CuotaSerializer(cuotas, many=True).data, status=status.HTTP_201_CREATED)


class AplicacionPagoViewSet(AuditableViewSetMixin, viewsets.ModelViewSet):
    audit_module = "cobranzas"
    serializer_class = AplicacionPagoSerializer
    permission_classes = [AplicacionPagoPermission]

    def get_queryset(self):
        cuotas = scoped_queryset_for_user(Cuota.objects.all(), self.request.user)
        return AplicacionPago.objects.select_related("pago", "cuota").filter(cuota__in=cuotas)


class PagoViewSet(AuditableViewSetMixin, viewsets.ModelViewSet):
    audit_module = "cobranzas"
    serializer_class = PagoSerializer
    permission_classes = [PagoPermission]

    def get_queryset(self):
        queryset = scoped_queryset_for_user(
            Pago.objects.select_related(
                "alumno", "concepto", "sucursal", "registrado_por", "anulado_por"
            ).prefetch_related("aplicaciones"),
            self.request.user,
        )
        alumno_id = self.request.query_params.get("alumno")
        if alumno_id:
            queryset = queryset.filter(alumno_id=alumno_id)
        sucursal_id = self.request.query_params.get("sucursal")
        medio = self.request.query_params.get("medio")
        usuario = self.request.query_params.get("usuario")
        desde = self.request.query_params.get("desde")
        hasta = self.request.query_params.get("hasta")
        if sucursal_id:
            queryset = queryset.filter(sucursal_id=sucursal_id)
        if medio:
            queryset = queryset.filter(medio=medio)
        if usuario:
            queryset = queryset.filter(registrado_por_id=usuario)
        if desde:
            queryset = queryset.filter(fecha__gte=desde)
        if hasta:
            queryset = queryset.filter(fecha__lte=hasta)
        return queryset

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            alumno = serializer.validated_data["alumno"]
            RecalcularRecargos(DjangoRecargoRepository()).execute(sucursal_ids=[alumno.sucursal_id])
            pago = RegistrarPago().execute(user=request.user, **serializer.validated_data)
        except ValueError as exc:
            raise ValidationError({"detail": str(exc)}) from exc
        self._audit(action="registro", instance=pago, after=snapshot(pago), description=f"Pago {pago.numero_recibo} registrado")
        response_serializer = self.get_serializer(pago)
        headers = self.get_success_headers(response_serializer.data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @transaction.atomic
    @action(detail=True, methods=["post"], url_path="anular")
    def anular(self, request, pk=None):
        pago_ref = self.get_object()
        before = snapshot(pago_ref)
        try:
            pago = AnularPago().execute(
                pago_id=pago_ref.pk,
                user=request.user,
                motivo=request.data.get("motivo"),
            )
        except (PagoAnulacionError, CajaCerradaError) as exc:
            raise ValidationError({"detail": str(exc)}) from exc
        self._audit(action="anulacion", instance=pago, before=before, after=snapshot(pago), description=f"Pago {pago.numero_recibo} anulado")
        return Response(self.get_serializer(pago).data)

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
                        "activa": aplicacion.activa,
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


class CajaDiariaViewSet(AuditableViewSetMixin, viewsets.ModelViewSet):
    audit_module = "caja"
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
    def cerrar(self, request, pk=None):
        caja_ref = self.get_object()
        before = snapshot(caja_ref)
        try:
            caja = CerrarCaja(DjangoCajaRepository()).execute(
                caja_id=caja_ref.pk,
                total_contado=request.data.get("total_contado", 0),
                importe_retirado=request.data.get("importe_retirado"),
                saldo_arrastrable=request.data.get("saldo_arrastrable"),
            )
        except (CajaOperacionError, CajaCerradaError, InvalidOperation) as exc:
            raise ValidationError({"detail": str(exc)}) from exc
        self._audit(action="cierre", instance=caja, before=before, after=snapshot(caja))
        return Response(self.get_serializer(caja).data)

    @action(detail=True, methods=["get", "post"], url_path="saldo-anterior")
    def saldo_anterior(self, request, pk=None):
        caja_ref = self.get_object()
        service = GestionarSaldoAnterior(DjangoCajaRepository())
        if request.method == "GET":
            saldo = service.consultar(caja_id=caja_ref.pk)
            if not saldo:
                return Response({"disponible": False})
            return Response(
                {
                    "disponible": True,
                    "id": saldo.id,
                    "importe": saldo.importe,
                    "caja_origen": saldo.caja_origen_id,
                    "fecha_origen": saldo.caja_origen.fecha,
                    "usuario_origen": saldo.caja_origen.usuario.username,
                }
            )
        try:
            caja = service.aplicar(
                caja_id=caja_ref.pk,
                saldo_id=request.data.get("saldo_id"),
            )
        except (CajaOperacionError, CajaCerradaError) as exc:
            raise ValidationError({"detail": str(exc)}) from exc
        return Response(self.get_serializer(caja).data)


class UserViewSet(AuditableViewSetMixin, viewsets.ModelViewSet):
    audit_module = "identidad"
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

    @staticmethod
    def _user_snapshot(user):
        data = snapshot(user)
        perfil = getattr(user, "perfil", None)
        data["perfil"] = {
            "rol": getattr(perfil, "rol", None),
            "sucursal_id": getattr(perfil, "sucursal_id", None),
            "puede_ver_todas_las_sucursales": getattr(
                perfil, "puede_ver_todas_las_sucursales", False
            ),
        }
        return data

    def perform_create(self, serializer):
        instance = serializer.save()
        self._audit(action="alta", instance=instance, after=self._user_snapshot(instance))

    def perform_update(self, serializer):
        before = self._user_snapshot(serializer.instance)
        instance = serializer.save()
        instance.refresh_from_db()
        self._audit(
            action="edicion",
            instance=instance,
            before=before,
            after=self._user_snapshot(instance),
        )

    def perform_destroy(self, instance):
        before = self._user_snapshot(instance)
        instance.is_active = False
        instance.save(update_fields=["is_active"])
        self._audit(
            action="desactivacion",
            instance=instance,
            before=before,
            after=self._user_snapshot(instance),
        )


class MovimientoCajaViewSet(AuditableViewSetMixin, viewsets.ModelViewSet):
    audit_module = "caja"
    serializer_class = MovimientoCajaSerializer
    permission_classes = [MovimientoCajaPermission]

    def get_queryset(self):
        queryset = MovimientoCaja.objects.select_related("caja", "caja__usuario", "pago")
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


class EventoAuditoriaViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = EventoAuditoriaSerializer
    permission_classes = [AuditoriaPermission]
    pagination_class = AlumnoPagination

    def get_queryset(self):
        queryset = EventoAuditoria.objects.select_related("usuario", "sucursal")
        perfil = getattr(self.request.user, "perfil", None)
        if not perfil:
            return queryset.none()
        if not perfil.puede_ver_todas_las_sucursales:
            queryset = queryset.filter(Q(sucursal=perfil.sucursal) | Q(sucursal__isnull=True))
        filters = {
            "usuario_id": self.request.query_params.get("usuario"),
            "sucursal_id": self.request.query_params.get("sucursal"),
            "modulo": self.request.query_params.get("modulo"),
            "accion": self.request.query_params.get("accion"),
            "entidad": self.request.query_params.get("entidad"),
        }
        for field, value in filters.items():
            if value:
                queryset = queryset.filter(**{field: value})
        if desde := self.request.query_params.get("desde"):
            queryset = queryset.filter(creado__date__gte=desde)
        if hasta := self.request.query_params.get("hasta"):
            queryset = queryset.filter(creado__date__lte=hasta)
        return queryset


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
    "conceptos": [
        "sucursal_codigo", "nombre", "tipo", "importe", "carrera",
    ],
    "saldos_iniciales": [
        "sucursal_codigo", "legajo", "dni", "tipo", "importe", "fecha",
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


class ImportacionWorkbookBaseView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [ImportacionPermission]

    def _import_arguments(self, request):
        if not _can_import(request.user):
            return None, Response({"detail": "Solo Administración puede importar datos."}, status=status.HTTP_403_FORBIDDEN)
        source = request.FILES.get("archivo")
        if not source:
            return None, Response({"detail": "Debe seleccionar un archivo XLSX o CSV."}, status=status.HTTP_400_BAD_REQUEST)
        filename = source.name or "archivo.xlsx"
        if not filename.lower().endswith((".xlsx", ".csv")):
            return None, Response({"detail": "El archivo debe tener extensión .xlsx o .csv."}, status=status.HTTP_400_BAD_REQUEST)
        perfil = request.user.perfil
        default_branch = request.data.get("sucursal") or perfil.sucursal.codigo
        default_career = request.data.get("carrera", "")
        allowed_branches = None if perfil.puede_ver_todas_las_sucursales else {perfil.sucursal.codigo}
        digest = hashlib.sha256()
        for chunk in source.chunks():
            digest.update(chunk)
        source.seek(0)
        return {
            "source": source,
            "filename": filename,
            "default_branch_code": default_branch,
            "default_career_name": default_career,
            "allowed_branch_codes": allowed_branches,
            "file_hash": digest.hexdigest(),
        }, None

    def _run_import(self, request, preview=False):
        arguments, response = self._import_arguments(request)
        if response:
            return response
        file_hash = arguments.pop("file_hash")
        preview_identity = {
            "user_id": request.user.pk,
            "filename": arguments["filename"],
            "file_hash": file_hash,
            "sucursal": arguments["default_branch_code"],
            "carrera": arguments["default_career_name"],
        }
        if not preview:
            token = request.data.get("preview_token", "")
            try:
                signed_identity = signing.loads(token, salt="ipac-import-preview", max_age=3600)
            except (signing.BadSignature, signing.SignatureExpired):
                return Response(
                    {"detail": "Primero debe revisar este archivo antes de confirmar la importación."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if signed_identity != preview_identity:
                return Response(
                    {"detail": "El archivo o sus opciones cambiaron después de la revisión. Revíselo nuevamente."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        try:
            importer = IPACWorkbookImporter()
            operation = importer.preview_file if preview else importer.import_file
            result = operation(**arguments)
        except (ValueError, KeyError, OSError, ImportError) as exc:
            return Response({"detail": f"No se pudo leer el archivo: {exc}"}, status=status.HTTP_400_BAD_REQUEST)
        result_data = result.as_dict()
        if preview:
            result_data["preview_token"] = signing.dumps(
                preview_identity, salt="ipac-import-preview", compress=True
            )
        else:
            RegistrarEventoAuditoria(DjangoAuditoriaRepository()).execute(
                usuario=request.user,
                sucursal=get_user_sucursal(request.user),
                modulo="importaciones",
                accion="importacion",
                entidad="ImportacionWorkbook",
                entidad_id=arguments["filename"],
                descripcion=f"Importación confirmada: {arguments['filename']}",
                metadata=result_data,
            )
        return Response(result_data, status=status.HTTP_200_OK)


class ImportacionWorkbookPreviewView(ImportacionWorkbookBaseView):
    def post(self, request):
        return self._run_import(request, preview=True)


class ImportacionWorkbookView(ImportacionWorkbookBaseView):
    def post(self, request):
        return self._run_import(request)
