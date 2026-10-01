from collections import defaultdict

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
        periodos,
        alumno_id=None,
    ):
        periodos = list(periodos or [])
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

        # La reinscripcion necesita previsualizar un alumno en concreto, no el
        # grupo entero de la carrera. Sin este filtro la pantalla de
        # renovacion mostraria el total de la carrera y el operador no veria
        # cuales de esos periodos ya tiene pagos su alumno.
        if alumno_id:
            alumnos = alumnos.filter(pk=alumno_id)

        rows = list(
            alumnos.select_related("carrera")
            .order_by("apellido", "nombre", "id")
            .values(
                "id",
                "legajo",
                "nombre",
                "apellido",
                "carrera__nombre",
                "estado",
            )
        )

        # Los períodos que el alumno ya tiene se resuelven en una sola consulta
        # para todo el lote. Con un lote de 10 períodos, un Exists por período
        # hubiera multiplicado las consultas por diez sin agregar información:
        # lo que importa es el conjunto, no la existencia aislada de cada uno.
        existentes_por_alumno = defaultdict(list)
        if rows and periodos:
            for alumno_id, periodo in (
                Cuota.objects.filter(
                    alumno_id__in=[row["id"] for row in rows],
                    concepto_id=concepto.id,
                    periodo__in=periodos,
                )
                .order_by("periodo")
                .values_list("alumno_id", "periodo")
            ):
                existentes_por_alumno[alumno_id].append(periodo)

        return [
            {
                "id": row["id"],
                "legajo": row["legajo"],
                "nombre_completo": f'{row["apellido"]}, {row["nombre"]}',
                "carrera_nombre": row["carrera__nombre"] or "",
                "estado": row["estado"],
                "periodos_existentes": sorted(existentes_por_alumno[row["id"]]),
            }
            for row in rows
        ]
