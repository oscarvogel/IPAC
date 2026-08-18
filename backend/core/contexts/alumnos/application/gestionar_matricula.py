from django.db import transaction

from ....models import Alumno, CarreraCurso, Matricula


class MatriculaError(ValueError):
    """Regla de negocio de la trayectoria académica."""


class GestionarMatricula:
    """Caso de uso para mantener el ciclo de vida de una matrícula."""

    @staticmethod
    def _validate_same_branch(alumno, carrera):
        if alumno.sucursal_id != carrera.sucursal_id:
            raise MatriculaError("El alumno y la carrera deben pertenecer a la misma sucursal.")

    @staticmethod
    def _validate_active_uniqueness(alumno, carrera, instance=None):
        active = Matricula.objects.filter(
            alumno_id=alumno.id,
            carrera_id=carrera.id,
            estado=Matricula.Estado.ACTIVA,
        )
        if instance is not None:
            active = active.exclude(pk=instance.pk)
        if active.exists():
            raise MatriculaError("El alumno ya tiene una matrícula activa para esta carrera.")

    @staticmethod
    def _sync_legacy_career(alumno):
        active = Matricula.objects.filter(
            alumno_id=alumno.id,
            estado=Matricula.Estado.ACTIVA,
        ).order_by("-fecha_inicio", "-id").first()
        career_id = active.carrera_id if active else None
        if alumno.carrera_id != career_id:
            Alumno.objects.filter(pk=alumno.pk).update(carrera_id=career_id)
            alumno.carrera_id = career_id

    @transaction.atomic
    def crear(self, *, alumno, carrera, fecha_inicio, fecha_fin=None, estado=Matricula.Estado.ACTIVA, observacion=""):
        alumno = Alumno.objects.select_for_update().select_related("sucursal").get(pk=alumno.pk)
        carrera = CarreraCurso.objects.select_related("sucursal").get(pk=carrera.pk)
        self._validate_same_branch(alumno, carrera)
        if estado == Matricula.Estado.ACTIVA:
            self._validate_active_uniqueness(alumno, carrera)

        matricula = Matricula.objects.create(
            alumno=alumno,
            carrera=carrera,
            sucursal=alumno.sucursal,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            estado=estado,
            observacion=observacion,
        )
        if estado == Matricula.Estado.ACTIVA:
            self._sync_legacy_career(alumno)
        return matricula

    @transaction.atomic
    def actualizar(self, matricula, **changes):
        current = Matricula.objects.select_for_update().select_related("alumno", "carrera", "sucursal").get(pk=matricula.pk)
        alumno = current.alumno
        carrera = changes.get("carrera", current.carrera)
        estado = changes.get("estado", current.estado)
        self._validate_same_branch(alumno, carrera)
        if estado == Matricula.Estado.ACTIVA:
            self._validate_active_uniqueness(alumno, carrera, instance=current)

        for field, value in changes.items():
            if field in {"alumno", "sucursal"}:
                continue
            setattr(current, field, value)
        current.sucursal = alumno.sucursal
        current.save()
        self._sync_legacy_career(alumno)
        return current

    @transaction.atomic
    def finalizar(self, matricula, *, fecha_fin):
        current = Matricula.objects.select_for_update().select_related("alumno", "carrera", "sucursal").get(pk=matricula.pk)
        if current.estado != Matricula.Estado.ACTIVA:
            raise MatriculaError("La matrícula seleccionada ya no está activa.")
        current.estado = Matricula.Estado.FINALIZADA
        current.fecha_fin = fecha_fin
        current.save(update_fields=["estado", "fecha_fin", "actualizado"])
        self._sync_legacy_career(current.alumno)
        return current
