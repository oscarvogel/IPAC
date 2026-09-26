from typing import Protocol


class AlumnoElegibleCuotaReader(Protocol):
    """Puerto de lectura para obtener alumnos candidatos a una cuota."""

    def obtener_candidatos(
        self,
        *,
        actor,
        sucursal_id,
        carrera_id,
        concepto_id,
        periodo,
    ) -> list[dict]: ...


class EvaluarGeneracionCuotas:
    """Arma el resumen compatible y el detalle seguro de una previsualización."""

    def __init__(self, reader: AlumnoElegibleCuotaReader):
        self._reader = reader

    def execute(self, *, actor, sucursal_id, carrera_id, concepto_id, periodo):
        candidatos = self._reader.obtener_candidatos(
            actor=actor,
            sucursal_id=sucursal_id,
            carrera_id=carrera_id,
            concepto_id=concepto_id,
            periodo=periodo,
        )
        detalle_alumnos = []
        elegibles = []
        for alumno in candidatos:
            motivo = (
                "Ya existe una cuota para este concepto y período."
                if alumno["cuota_existente"]
                else ""
            )
            detalle_alumnos.append({
                "id": alumno["id"],
                "legajo": alumno["legajo"],
                "nombre_completo": alumno["nombre_completo"],
                "carrera_nombre": alumno["carrera_nombre"],
                "estado": alumno["estado"],
                "motivo": motivo,
            })
            if not motivo:
                elegibles.append(alumno["id"])

        return {
            "alumnos_encontrados": len(candidatos),
            "omitidas": len(candidatos) - len(elegibles),
            "alumnos_elegibles": elegibles,
            "detalle_alumnos": detalle_alumnos,
        }
