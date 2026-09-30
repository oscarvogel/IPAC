# Evidencia local — Consultas y operación

Capturas del 30/09/2026 con datos ficticios, perfil Administración y SQLite desechable. No son capturas productivas. Ver [checklist de QA](../../QA_CONSULTAS_OPERACION_2026-09-30.md).

## Pantallas

- `reportes-preview-local.jpg`: vista local final tras restaurar el navegador a su tamaño habitual.
- `reportes-final-1366-claro.jpg`: favorita Hoy aplicada y filtros de los resultados.
- `reportes-1366-claro.jpg`, `reportes-1366-oscuro-reducido.jpg`: escritorio.
- `reportes-1280-claro-reducido.jpg`, `reportes-1280-oscuro-reducido.jpg`: laptop.
- `reportes-390-claro-reducido.jpg`, `reportes-390-oscuro-reducido.jpg`: móvil.
- `pago-confirmacion-1366-claro.jpg`, `pago-confirmacion-1280-claro.jpg`, `pago-confirmacion-390-oscuro-reducido.jpg`: confirmaciones persistentes de pagos ficticios.
- `detalle-pago-1280-claro.jpg`: detalle de un pago con fecha local.
- `caja-filtros-1280-oscuro.jpg`, `caja-390-oscuro-reducido.jpg`: filtros y favoritas de movimientos.
- `detalle-movimiento-390-oscuro.jpg`, `recibo-390-oscuro.jpg`: navegación interna del panel móvil.
- `ayuda-390-claro.jpg`, `novedades-390-claro.jpg`, `ayuda-cierre-390-oscuro-reducido.jpg`: contenido y guía desplegada.

Las capturas se tomaron durante distintas operaciones de prueba: los totales pueden variar entre ellas. Las de diálogos pueden incluir el fondo completo de la página por el modo de captura.

## Documentos impresos

Cada PDF tiene una página; PNG del mismo nombre sirve para inspección visual:

- `recibo-listado.pdf`: recibo seleccionado en Reportes.
- `recibo-cuenta-corriente.pdf`: recibo seleccionado en el estado de cuenta.
- `recibo-confirmacion.pdf`: recibo del nuevo pago desde su confirmación móvil.
- `recibo-detalle.pdf`: recibo desde el detalle de movimiento, con tema oscuro.
- `resumen-caja.pdf`: resumen de la jornada, con tema oscuro.

Renderizados mediante Chromium con encabezados y pies de navegador desactivados. No prueban salida en una impresora física.
