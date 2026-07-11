from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AlumnoViewSet,
    CajaDiariaViewSet,
    CarreraCursoViewSet,
    ConceptoCobrableViewSet,
    CurrentUserView,
    LoginView,
    MovimientoCajaViewSet,
    PagoViewSet,
    SucursalViewSet,
)

router = DefaultRouter()
router.register("sucursales", SucursalViewSet, basename="sucursal")
router.register("alumnos", AlumnoViewSet, basename="alumno")
router.register("carreras", CarreraCursoViewSet, basename="carrera")
router.register("conceptos", ConceptoCobrableViewSet, basename="concepto")
router.register("pagos", PagoViewSet, basename="pago")
router.register("cajas", CajaDiariaViewSet, basename="caja")
router.register("movimientos-caja", MovimientoCajaViewSet, basename="movimiento-caja")

urlpatterns = [
    path("auth/login/", LoginView.as_view(), name="api-login"),
    path("auth/me/", CurrentUserView.as_view(), name="api-current-user"),
    path("", include(router.urls)),
]
