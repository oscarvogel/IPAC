from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AplicacionPago, Alumno, CajaDiaria, CarreraCurso, ConceptoCobrable, Cuota, Matricula, MovimientoCaja, Pago, PerfilUsuario, Sucursal
from .serializers import (
    AlumnoSerializer,
    AplicacionPagoSerializer,
    CajaDiariaSerializer,
    CarreraCursoSerializer,
    ConceptoCobrableSerializer,
    CurrentUserSerializer,
    CuotaSerializer,
    LoginSerializer,
    MatriculaSerializer,
    MovimientoCajaSerializer,
    PagoSerializer,
    SucursalSerializer,
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


class MovimientoCajaViewSet(viewsets.ModelViewSet):
    serializer_class = MovimientoCajaSerializer

    def get_queryset(self):
        queryset = MovimientoCaja.objects.select_related("caja", "pago")
        caja_id = self.request.query_params.get("caja")
        queryset = queryset.filter(caja__in=scoped_queryset_for_user(CajaDiaria.objects.all(), self.request.user))
        if caja_id:
            queryset = queryset.filter(caja_id=caja_id)
        return queryset
