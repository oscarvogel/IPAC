from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AplicacionPagoViewSet,
    AlumnoViewSet,
    CajaDiariaViewSet,
    CarreraCursoViewSet,
    ConceptoCobrableViewSet,
    CuotaViewSet,
    CurrentUserView,
    LoginView,
    MatriculaViewSet,
    MovimientoCajaViewSet,
    PagoViewSet,
    ReporteResumenView,
    SucursalViewSet,
    UserViewSet,
)
from .views import ImportacionPlantillaCsvView, ImportacionPlantillasView, ImportacionWorkbookView

router = DefaultRouter()
router.register("sucursales", SucursalViewSet, basename="sucursal")
router.register("alumnos", AlumnoViewSet, basename="alumno")
router.register("carreras", CarreraCursoViewSet, basename="carrera")
router.register("conceptos", ConceptoCobrableViewSet, basename="concepto")
router.register("matriculas", MatriculaViewSet, basename="matricula")
router.register("cuotas", CuotaViewSet, basename="cuota")
router.register("pagos", PagoViewSet, basename="pago")
router.register("usuarios", UserViewSet, basename="usuario")
router.register("aplicaciones-pago", AplicacionPagoViewSet, basename="aplicacion-pago")
router.register("cajas", CajaDiariaViewSet, basename="caja")
router.register("movimientos-caja", MovimientoCajaViewSet, basename="movimiento-caja")

urlpatterns = [
    path("auth/login/", LoginView.as_view(), name="api-login"),
    path("auth/me/", CurrentUserView.as_view(), name="api-current-user"),
    path("reportes/resumen/", ReporteResumenView.as_view(), name="api-reporte-resumen"),
    path("importaciones/plantillas/", ImportacionPlantillasView.as_view(), name="api-importacion-plantillas"),
    path("importaciones/plantillas/<str:kind>/", ImportacionPlantillaCsvView.as_view(), name="api-importacion-plantilla"),
    path("importaciones/workbook/", ImportacionWorkbookView.as_view(), name="api-importacion-workbook"),
    path("", include(router.urls)),
]
