# QA de recorridos IPAC — 26 de septiembre de 2026

## Alcance y entorno

La revisión funcional y visual se realizó en local con una SQLite desechable y registros sintéticos (`Alumno Prueba Uno`, `QA-001`, etc.). Se usó el perfil local de administración para la navegación; no se consultaron ni se modificaron datos de producción. Las pruebas automáticas cubren además permisos y alcance por sucursal para los perfiles operativos.

Los viewports CSS fueron 390 × 844 y 1440 × 900. La captura del navegador puede medir 375 × 812 y 1425 × 891 por la escala del sistema. Para revisar el reflow equivalente a 200% se usó 720 × 450 CSS px; no representa una comprobación con el zoom nativo del navegador.

## Checklist de recorridos

| Recorrido | Resultado revisado | Estado |
|---|---|---|
| Generación masiva de cuotas | La sucursal inicial coincide con el perfil autorizado; se revisaron grupo elegible, importe total y confirmación final. La vista se canceló antes de emitir. El comando, duplicados y alcance por sucursal se ejercitaron en pruebas API y de aplicación. | Verificado con pruebas locales; la confirmación visual no emitió cuotas. |
| Deuda y cuenta corriente | El estado de cuenta incluye saldo pendiente, vencido, por vencer, saldo a favor y saldo neto. Se verificó el cálculo de fecha local y la exclusión de cuotas anuladas/sin saldo; la ficha conserva pagos y recibos. | Verificado en API, frontend y vista local. |
| Pago, recibo y movimiento | Se registró un pago de prueba en la SQLite desechable; el recibo quedó disponible en la cuenta y se reflejó en los movimientos de Caja. Los recorridos automático, manual, pago a cuenta, excedente, cuota ajena y caja cerrada se cubren con la suite de backend. | Verificado localmente y en pruebas. |
| Cierre de Caja | El resumen muestra efectivo esperado, contado, diferencia, retiro y saldo trasladado. Se revisó el formulario, sin confirmar el cierre desde la interfaz; las reglas y rechazos se cubren con pruebas del comando y API. | Verificado con vista y pruebas; el submit visual queda pendiente. |
| Roles y sucursales | La suite API verifica autorización por rol, alcance propio, rechazo de sucursal ajena y ausencia de efectos ante rechazo. | Verificado automáticamente. La revisión visual manual usó administración local. |
| Reportes y exportación | Resumen no muestra una exportación engañosa. Caja conserva navegación por URL y aplica fecha, sucursal y usuario en XLSX, respetando el alcance autorizado. | Verificado en frontend, adaptador y contrato API. |

## Accesibilidad y responsive

- En las seis pantallas revisadas —Dashboard, Alumnos, Deudores, Caja y Resumen/Caja de Reportes— no quedaron textos operativos menores a 12 px ni textos normales con contraste calculado inferior a 4,5:1, en tema claro y oscuro.
- Los controles revisados en móvil tienen un objetivo mínimo de 44 × 44 px. La navegación con Tab recorrió filtros y categorías de Reportes con foco visible; se comprobó el foco al devolverlo a la tarjeta de alumno.
- En móvil, abrir una ficha cambia a la vista de ficha con “Volver al directorio”. Al volver se restauran búsqueda, página, desplazamiento y foco, y la ficha se oculta para dejar visible el directorio. En escritorio se conserva la vista de dos paneles.
- No se encontró desbordamiento horizontal del documento a 390 px ni en la vista estrecha de 720 × 450 CSS px. La fila de categorías de Reportes desplaza horizontalmente en móvil.
- Este muestreo no es certificación WCAG de todo IPAC. Quedan pendientes una pasada con lector de pantalla, alto contraste nativo y dispositivos físicos.

## Registro de hallazgos

| ID | Hallazgo | Corrección / resultado |
|---|---|---|
| QA-01 | La tabla de Deudores recortaba acciones en escritorio. | Se fijó la distribución de columnas desde 1181 px; los botones quedan visibles a 1440 px. |
| QA-02 | Ayudas del cierre de Caja medían 9,6 px. | Se elevaron a 12 px. |
| QA-03 | Algunos controles móviles medían entre 36 y 42 px. | Se fijó un mínimo de 44 px para los controles revisados. |
| QA-04 | Los estados semánticos de deuda, crédito y retiro no llegaban a AA en superficies claras. | Se ajustaron los tokens claros de éxito, advertencia y peligro; la nueva medición de las seis pantallas no encuentra valores menores a 4,5:1. |
| QA-05 | Al volver desde una ficha móvil seguía apareciendo la ficha debajo del directorio; el breakpoint del botón no coincidía con el de selección. | La vista móvil ahora muestra directorio o ficha de forma excluyente y usa el mismo breakpoint de 760 px que la selección. Revisión visual posterior confirmada. |
| QA-06 | El rango por defecto convertía medianoche local a UTC y podía mostrar el día siguiente. | Dashboard, Reportes y formularios de fechas usan ahora la fecha calendario local. Se comprobó a las 23:27 locales: fecha local 26/09 y UTC 27/09; la UI conserva 26/09. |

## Evidencia automatizada

- `python backend/manage.py check`
- `python backend/manage.py test core`
- `npm --prefix frontend test`
- `npm --prefix frontend run build`
- `git diff --check`

La comprobación productiva posterior al despliegue debe limitarse a salud HTTP (`/api/health/`) y navegación de solo lectura. No crear pagos, cuotas ni cierres de prueba en producción.

## Capturas

Ver el [índice de capturas y dimensiones](screenshots/qa-seis-etapas-2026-09-26/README.md). Las imágenes usan exclusivamente el conjunto local sintético anonimizado.
