# QA — Consultas y operación (30/09/2026)

## Alcance y contexto

Entrega local: filtros, confirmación de pagos, ayuda contextual, detalle de operaciones, favoritas y novedades. Identidad y Acceso es dueño de las preferencias; Experiencia Web coordina su presentación. Cobranzas, Caja y Reportes conservan sus reglas y consultas existentes. Contrato: [consultas favoritas](CONTRATO_CONSULTAS_FAVORITAS.md).

La validación se realizó antes de la entrega Git. El usuario autorizó posteriormente commit y push a su repositorio; no se ejecutó un despliegue desde esta tarea. `Notas_Reunion_IPAC.md` se conserva sin cambios y fuera del commit. Pases entre cajas, permisos permanentes, recargos, ARCA y sitio público quedan fuera del alcance.

## Comprobaciones automatizadas

- [x] `.\.venv\Scripts\python.exe backend\manage.py test core --noinput`: **118 pruebas**, OK (267 s).
- [x] `npm --prefix frontend test -- --reporter=dot --no-file-parallelism`: **46 archivos / 136 pruebas**, OK (81 s), después del último cambio de código.
- [x] `.\.venv\Scripts\python.exe backend\manage.py check`: sin incidencias.
- [x] `.\.venv\Scripts\python.exe backend\manage.py makemigrations --check --dry-run`: sin cambios pendientes.
- [x] `npm --prefix frontend run build`: OK, 485 módulos.
- [x] `git diff --check`: sin errores de espacios; Git avisa de normalización LF/CRLF en Windows.
- [x] Inspección de dependencias: dominio y aplicación nuevos de favoritas no importan Django, DRF ni ORM.

Las pruebas cubren CRUD con puertos falsos y API, aislamiento por propietario, persistencia con un nuevo cliente autenticado, nombres inválidos/duplicados, propietario no editable, configuración inválida, alcance perdido y recuperación mediante edición. Cubren los cinco roles y restricciones de sucursal/cajero. La consulta directa vuelve a validar permisos.

Frontend cubre períodos relativos/personalizados, borrador frente a filtros aplicados, quitar etiquetas, exportación aplicada, recuperación de consultas fallidas, limpieza de favoritas al cambiar cuenta y respuestas antiguas. PagoForm cubre envío único, confirmación persistente y reintento de lecturas sin repetir POST. También se verifica detalle/recibo con un diálogo visible, Escape, retorno del foco, fecha local y documento seleccionado entre varios recibos montados.

Una ejecución paralela inicial encontró una prueba existente de animación de paginación sensible al tiempo. Su ejecución focalizada y las suites completas en serie pasaron. No se modificó esa lógica para ocultar el fallo.

## Migración local

- [x] Se creó SQLite desechable en `%TEMP%/ipac-consultas-20260930.sqlite3` y se migró desde cero hasta `0016_consultas_favoritas`.
- [x] `showmigrations core` confirma `0016` aplicada.
- [x] La migración incorpora únicamente el modelo nuevo, su FK y restricciones; no transforma datos de las tablas operativas.
- [ ] Ejecución de la migración en PostgreSQL/productivo: pendiente de la entrega posterior. La evidencia local corresponde a SQLite.

## Revisión real en navegador local

Backend `127.0.0.1:8000`, frontend `127.0.0.1:5173`. Perfil Administración, sucursal y alumnos ficticios en la base desechable; sin datos productivos. [Índice de capturas](screenshots/qa-consultas-2026-09-30/README.md).

| Resolución | Evidencia | Resultado |
|---|---|---|
| 1366×768 | Reportes claro/oscuro y confirmación de pago | Filtros y acciones legibles, favoritas y atajos disponibles |
| 1280×800 | Reportes claro/oscuro, Caja y detalle de pago | Controles se distribuyen sin superposición |
| 390×844 | Reportes claro/oscuro, Caja, detalle/recibo, pago confirmado, ayuda y novedades | Sin desplazamiento horizontal en Caja/Reportes; panel a pantalla completa |

- [x] Movimiento reducido emulado en Reportes para las tres resoluciones y en flujos móviles.
- [x] Registro real ficticio desde Alumnos y Deudores: confirmación permanece abierta después de actualizar listas.
- [x] Guardar/aplicar favoritas de Reportes y Caja; renombrar favorita de Caja desde móvil. API automatizada cubre actualizar/eliminar y cuentas aisladas.
- [x] Ayuda desplegable por teclado, menú móvil y rutas Ayuda/Novedades con enlaces a pantallas.
- [x] Abrir detalle de cuenta corriente, Escape y foco restaurado a `Ver detalle`; prueba automatizada conserva datos sin volver a consultar y restaura la posición.
- [x] Ayuda de cierre revisada sin confirmar un cierre de caja.
- [x] Sin errores/advertencias de consola en la revisión final.

## Impresión

- [x] PDF de recibo desde listado, cuenta corriente, confirmación y panel de detalle: **una página por documento**, sin documento vacío adicional ni interfaz de aplicación.
- [x] PDF del resumen de Caja: una página para la jornada ficticia, sin recibos anexos.
- [x] Revisión visual de los documentos; se corrigió la herencia de colores del tema oscuro y el usuario del resumen. Impresión mantiene fondo blanco y texto legible.
- [x] El código conserva `window.print()` y limpia el destino al recibir `afterprint`.

Para capturar PDFs sin bloquear la automatización con el diálogo nativo, se sustituyó temporalmente `window.print` en la pestaña de QA y se imprimió con el motor Chromium. La pestaña se recargó al terminar: esa sustitución y las emulaciones no quedan en la aplicación. No se verificó una impresora física ni el diálogo de todos los navegadores. Los encabezados/pies con URL son una opción del navegador; la ayuda indica desactivarlos.

## Límites de aceptación

La revisión visual fue con Administración; los otros roles se verifican por pruebas de API, no por sesiones visuales separadas. No constituye una auditoría exhaustiva WCAG ni una aceptación productiva. Las nuevas preferencias cumplen el límite dominio/aplicación/adaptadores; modelos y consultas operativas legadas continúan compartidos en `core` por compatibilidad.
