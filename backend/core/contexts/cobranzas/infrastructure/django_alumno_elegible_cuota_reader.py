from django.db.models import Exists, OuterRef

from ....access_scope import scoped_queryset_for_user
from ....models import Alumno, CarreraCurso, ConceptoCobrable, Cuota, Sucursal
from ..application.evaluar_generacion_cuotas import AlumnoElegibleCuotaReader


class DatosGeneracionCuotasInvalidos(ValueError):
    pass


class DjangoAlumnoElegibleCuotaReader(AlumnoElegibleCuotaReader):
    """Adaptador ORM; el contexto sigue en transición mientras usa core.models."""

    def obtener_candidatos(
        self,
        *,
        actor,
        sucursal_id,
        carrera_id,
        concepto_id,
        periodo,
    ):
        sucursal = scoped_queryset_for_user(Sucursal.objects.all(), actor).filter(pk=sucursal_id).first()
        if not sucursal:
            raise DatosGeneracionCuotasInvalidos("Sucursal invalida o sin acceso.")

        concepto = scoped_queryset_for_user(
            ConceptoCobrable.objects.filter(activo=True), actor
        ).filter(pk=concepto_id, sucursal_id=sucursal.id).first()
        if not concepto:
            raise DatosGeneracionCuotasInvalidos("Concepto invalido o sin acceso.")

        alumnos = scoped_queryset_for_user(
            Alumno.objects.filter(estado=Alumno.Estado.ACTIVO, sucursal_id=sucursal.id),
            actor,
        )
        if carrera_id:
            carrera = scoped_queryset_for_user(CarreraCurso.objects.all(), actor).filter(
                pk=carrera_id,
                sucursal_id=sucursal.id,
            ).first()
            if not carrera:
                raise DatosGeneracionCuotasInvalidos("Carrera invalida o sin acceso.")
            alumnos = alumnos.filter(carrera_id=carrera.id)

        cuota_existente = Cuota.objects.filter(
            alumno_id=OuterRef("pk"),
            concepto_id=concepto.id,
            periodo=periodo,
        )
        rows = list(
            alumnos.annotate(cuota_existente=Exists(cuota_existente))
            .select_related("carrera")
            .order_by("apellido", "nombre", "id")
            .values(
                "id",
                "legajo",
                "nombre",
                "apellido",
                "carrera__nombre",
                "estado",
                "cuota_existente",
            )
        )
        return [
            {
                "id": row["id"],
                "legajo": row["legajo"],
                "nombre_completo": f'{row["apellido"]}, {row["nombre"]}',
                "carrera_nombre": row["carrera__nombre"] or "",
                "estado": row["estado"],
                "cuota_existente": row["cuota_existente"],
            }
            for row in rows
        ]
