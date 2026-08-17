# Plantillas de importación IPAC

Las plantillas se descargan desde `Administración → Cargar datos` o desde:

- `GET /api/importaciones/plantillas/alumnos/`
- `GET /api/importaciones/plantillas/carreras/`

Son archivos CSV UTF-8 separados por `;`, compatibles con Excel. También se aceptan archivos `.xlsx`.

## Alumnos

Columnas: `sucursal_codigo`, `legajo`, `apellido`, `nombre`, `dni`, `cuil`, `fecha_nacimiento`, `email`, `telefono`, `domicilio`, `carrera`.

`dni` identifica al alumno cuando está informado. Si falta, se utiliza `legajo`; si también falta, el sistema genera un legajo de importación y muestra una advertencia.

## Carreras y cursos

Columnas: `sucursal_codigo`, `nombre`, `tipo`, `duracion`, `plan_cuotas`, `importe_matricula`, `cuota_programatica`, `cuota_extraprogramatica`, `cuota_total`, `cuota_convenio_20`, `cuota_convenio_15`, `descripcion`.

`tipo` debe ser `carrera` o `curso`. Los importes son números sin símbolo de moneda. La importación crea o actualiza también los conceptos `Matrícula 2026` y `Cuota mensual 2026` cuando los importes están informados.

La carga es idempotente: volver a subir una plantilla actualiza registros identificados, no crea copias por cada ejecución. Las inconsistencias de la fuente se devuelven como advertencias para revisión.
