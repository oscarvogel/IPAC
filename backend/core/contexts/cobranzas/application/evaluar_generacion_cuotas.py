from typing import Protocol


class AlumnoElegibleCuotaReader(Protocol):
    """Puerto de lectura para obtener alumnos candidatos a un lote de cuotas."""

    def obtener_candidatos(
        self,
        *,
        actor,
        sucursal_id,
        carrera_id,
        concepto_id,
        periodos,
    ) -> list[dict]: ...


class EvaluarGeneracionCuotas:
    """Arma el resumen de una previsualización de un lote de cuotas.

    La unidad de evaluación ya no es el alumno sino el par (alumno, período).
    Un alumno que ya tiene 7 de las 10 cuotas del lote sigue siendo elegible
    para las 3 que le faltan, así que la pregunta no es "¿tiene cuota?" sino
    "¿le falta alguna?". Marcarlo como omitido en ese caso obligaría al
    operador a generar de a un período, que es justo lo que esta pantalla
    viene a evitar.
    """

    def __init__(self, reader: AlumnoElegibleCuotaReader):
        self._reader = reader

    def execute(self, *, actor, sucursal_id, carrera_id, concepto_id, planificacion):
        periodos = list(planificacion.nombres)
        candidatos = self._reader.obtener_candidatos(
            actor=actor,
            sucursal_id=sucursal_id,
            carrera_id=carrera_id,
            concepto_id=concepto_id,
            periodos=periodos,
        )

        detalle_alumnos = []
        elegibles = []
        cuotas_a_generar = 0
        for alumno in candidatos:
            existentes = set(alumno["periodos_existentes"])
            faltantes = [p for p in periodos if p not in existentes]
            ya_completo = not faltantes
            detalle_alumnos.append({
                "id": alumno["id"],
                "legajo": alumno["legajo"],
                "nombre_completo": alumno["nombre_completo"],
                "carrera_nombre": alumno["carrera_nombre"],
                "estado": alumno["estado"],
                "faltantes": faltantes,
                "existentes": [p for p in periodos if p in existentes],
                "motivo": "Ya tiene todas las cuotas del lote." if ya_completo else "",
            })
            if not ya_completo:
                elegibles.append(alumno["id"])
                cuotas_a_generar += len(faltantes)

        return {
            "cantidad_periodos": len(periodos),
            "periodos": periodos,
            "etiquetas_periodo": planificacion.etiquetas,
            "alumnos_encontrados": len(candidatos),
            "omitidas": len(candidatos) - len(elegibles),
            "alumnos_elegibles": elegibles,
            "cuotas_a_generar": cuotas_a_generar,
            "detalle_alumnos": detalle_alumnos,
        }
