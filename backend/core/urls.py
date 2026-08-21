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
    HealthView,
    DeudoresView,
    LoginView,
    MatriculaViewSet,
    MovimientoCajaViewSet,
    PagoViewSet,
    ReporteResumenView,
    ReporteCobranzasUsuariosView,
    ReporteExportarExcelView,
    SucursalViewSet,
    UserViewSet,
    EventoAuditoriaViewSet,
    TipoDescuentoViewSet,
    ReglaRecargoViewSet,
)
from .views import (
    ImportacionPlantillaCsvView,
    ImportacionPlantillasView,
    ImportacionWorkbookPreviewView,
    ImportacionWorkbookView,
)

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
router.register("auditoria", EventoAuditoriaViewSet, basename="auditoria")
router.register("tipos-descuento", TipoDescuentoViewSet, basename="tipo-descuento")
router.register("reglas-recargo", ReglaRecargoViewSet, basename="regla-recargo")

urlpatterns = [
    path("health/", HealthView.as_view(), name="api-health"),
    path("auth/login/", LoginView.as_view(), name="api-login"),
    path("auth/me/", CurrentUserView.as_view(), name="api-current-user"),
    path("reportes/resumen/", ReporteResumenView.as_view(), name="api-reporte-resumen"),
    path("reportes/cobranzas-usuarios/", ReporteCobranzasUsuariosView.as_view(), name="api-reporte-cobranzas-usuarios"),
    path("reportes/exportar.xlsx", ReporteExportarExcelView.as_view(), name="api-reporte-exportar-xlsx"),
    path("deudores/", DeudoresView.as_view(), name="api-deudores"),
    path("importaciones/plantillas/", ImportacionPlantillasView.as_view(), name="api-importacion-plantillas"),
    path("importaciones/plantillas/<str:kind>/", ImportacionPlantillaCsvView.as_view(), name="api-importacion-plantilla"),
    path("importaciones/workbook/preview/", ImportacionWorkbookPreviewView.as_view(), name="api-importacion-workbook-preview"),
    path("importaciones/workbook/", ImportacionWorkbookView.as_view(), name="api-importacion-workbook"),
    path("", include(router.urls)),
]
