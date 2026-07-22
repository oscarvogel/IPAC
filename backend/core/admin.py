from django.contrib import admin

from .models import AplicacionPago, Alumno, CajaDiaria, CarreraCurso, ConceptoCobrable, Cuota, Matricula, MovimientoCaja, Pago, PerfilUsuario, Sucursal


@admin.register(Sucursal)
class SucursalAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nombre", "activa")
    search_fields = ("codigo", "nombre")


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ("user", "rol", "sucursal", "puede_ver_todas_las_sucursales")
    list_filter = ("rol", "sucursal", "puede_ver_todas_las_sucursales")


@admin.register(CarreraCurso)
class CarreraCursoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "sucursal", "activa")
    list_filter = ("sucursal", "activa")
    search_fields = ("nombre",)


@admin.register(Alumno)
class AlumnoAdmin(admin.ModelAdmin):
    list_display = ("legajo", "apellido", "nombre", "dni", "sucursal", "estado")
    list_filter = ("sucursal", "estado")
    search_fields = ("legajo", "apellido", "nombre", "dni")


@admin.register(ConceptoCobrable)
class ConceptoCobrableAdmin(admin.ModelAdmin):
    list_display = ("nombre", "tipo", "importe", "sucursal", "carrera", "activo")
    list_filter = ("tipo", "sucursal", "activo")
    search_fields = ("nombre",)


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ("numero_recibo", "fecha", "alumno", "concepto", "importe", "medio", "sucursal")
    list_filter = ("fecha", "medio", "sucursal")
    search_fields = ("alumno__apellido", "alumno__nombre", "alumno__legajo", "observacion")


@admin.register(CajaDiaria)
class CajaDiariaAdmin(admin.ModelAdmin):
    list_display = ("fecha", "sucursal", "usuario", "estado", "total_contado")
    list_filter = ("fecha", "estado", "sucursal")


@admin.register(MovimientoCaja)
class MovimientoCajaAdmin(admin.ModelAdmin):
    list_display = ("caja", "tipo", "medio", "importe", "descripcion", "pago")
    list_filter = ("tipo", "medio", "caja__sucursal")


@admin.register(Matricula)
class MatriculaAdmin(admin.ModelAdmin):
    list_display = ("alumno", "carrera", "sucursal", "fecha_inicio", "estado")
    list_filter = ("sucursal", "estado")


@admin.register(Cuota)
class CuotaAdmin(admin.ModelAdmin):
    list_display = ("alumno", "concepto", "periodo", "fecha_vencimiento", "importe", "estado")
    list_filter = ("sucursal", "estado", "periodo")


@admin.register(AplicacionPago)
class AplicacionPagoAdmin(admin.ModelAdmin):
    list_display = ("pago", "cuota", "importe", "creado")
