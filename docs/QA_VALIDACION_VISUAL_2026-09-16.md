# Handoff QA visual y funcional — 16/09/2026

## Objetivo y modo de trabajo

Este documento permite que un desarrollador que trabaja desde un fork resuelva los hallazgos en PRs pequeños. Crear una rama e issue por punto; no mezclar los siete cambios.

Para cambios en Cobranzas, Caja, auditoría o autorización, mantener la dependencia `presentation -> application -> domain`: la UI no recalcula saldos ni decide permisos; consume DTOs y casos de uso.

## Evidencia QA

Sesión: `admin`, rol Administración, sucursal principal Posadas, alcance Todas las sedes. Sin errores de consola.

Datos trazables creados:

- Alumno: `QA-ELD-20260916`, DNI `99999999`, Eldorado.
- Matrícula: Auxiliar administrativo.
- Cuota: 09/2026, $22.000, vencimiento 20/09/2026.
- Pagos: `REC-00000005` ($10.000 efectivo) y `REC-00000006` ($12.000 transferencia).
- Caja Posadas: ingreso $1.000, egreso $200, retiro $300, cierre sin diferencia.

La cuenta corriente, Deudores y el reporte de cobranzas reflejan correctamente el pago completo. El directorio de alumnos no.

---

## QA-01 — Deuda incorrecta en directorio tras cancelar una cuota

**Prioridad: P0**

**Reproducción**

1. Buscar `QA-ELD-20260916` en Alumnos.
2. La fila muestra `Debe $22.000`.
3. Abrir Estado de cuenta: total cuotas $22.000, pagado $22.000 y saldo neto $0.
4. Recargar `/alumnos`: la fila continúa mostrando deuda.

`/deudores` no incluye al alumno y Reportes suma los dos pagos correctamente. Esto puede provocar una gestión de cobro equivocada.

**Corrección y aceptación**

- Centralizar el saldo en un read DTO/caso de uso que descuente **aplicaciones de pago**.
- Directorio, ficha, Deudores, cuenta corriente y Reportes deben consumir la misma definición de saldo.
- Con pagos aplicados de $10.000 y $12.000 sobre una cuota de $22.000, todas las pantallas deben indicar $0.
- Cubrir saldo total y parcial con tests de aplicación y contrato API.

---

## QA-02 — Edición de alumno no precarga email ni teléfono

**Prioridad: P1**

La ficha del alumno QA mostraba email y teléfono válidos, pero ambos campos aparecieron vacíos en Editar alumno. Guardar sin reescribirlos puede borrar contacto.

**Corrección y aceptación**

- Mapear todos los campos editables al estado inicial del formulario.
- Guardar una edición sin cambios conserva email y teléfono; editar solo nombre/apellido tampoco los modifica.
- Agregar test de componente/composable para carga inicial y payload de actualización.

---

## QA-03 — Caja sin selector de sucursal para un usuario global

**Prioridad: P1 — requiere definición de negocio**

`admin` pudo operar alumnos y cobros de Eldorado, pero Caja quedó fija en Posadas y no permitió seleccionar Eldorado. Los pagos de Eldorado sí aparecieron en Reportes.

Definir una política explícita:

1. Selector de sucursal de Caja, limitado por autorización.
2. Cambio de contexto operativo que afecte Caja y comandos posteriores.
3. Caja solo en sede principal; en ese caso bloquear/documentar cobros de otras sedes.

**Aceptación**

- Un usuario global consulta y opera la caja correcta de ambas sedes sin mezclar movimientos.
- Un usuario de sede asignada no puede leer ni operar la otra.
- Sucursal se valida dentro del caso de uso, nunca se confía en un valor enviado por el cliente.

---

## QA-04 — Auditoría marca cuota individual como masiva

**Prioridad: P2**

La cuota creada desde la ficha individual se auditó como `Generación masiva de cuota` (`core.Cuota #1`). La semántica de auditoría es incorrecta.

**Corrección y aceptación**

- Diferenciar acciones: `cuota_generada_individualmente` y `cuotas_generadas_masivamente`.
- La auditoría debe guardar actor, operación, entidad y alcance real.
- Añadir test de integración para ambos caminos.

---

## QA-05 — Previsualización masiva sin detalle de afectados

**Prioridad: P2**

El asistente para Eldorado indicó 2 alumnos, $22.000 unitarios y $44.000 totales, pero no mostró quiénes serían facturados, duplicados, cuotas existentes ni exclusiones. El lote no fue emitido.

**Corrección y aceptación**

- Agregar query de previsualización con ID, legajo, nombre, carrera, cuota existente/duplicada y motivo de exclusión.
- Mostrar detalle, cantidad, total, período, concepto, descuento y recargo antes de confirmar.
- El comando final recalcula elegibilidad dentro de su transacción para impedir duplicados alumno/concepto/período.
- No introducir CQRS/eventos nuevos solo para esta mejora; basta una query y el comando existente.

---

## QA-06 — Falta matriz QA de permisos por rol y sucursal

**Prioridad: P2**

Había seis usuarios activos, pero no una cuenta de QA exclusiva de Eldorado ni sesiones disponibles para Tesorería, Caja y Consulta. No se verificaron denegaciones reales ni aislamiento de sucursal.

**Corrección y aceptación**

- Mantener datos semilla no productivos para Administración, Tesorería, Caja y Consulta en Posadas/Eldorado.
- Documentar matriz permitida/denegada para alumnos, cobros, caja, reportes y configuración.
- No versionar claves: provisionarlas con el mecanismo seguro del entorno QA.
- Cubrir autorización y aislamiento mediante tests API.

---

## QA-07 — Pendiente inspección visual manual de recibos

**Prioridad: P3**

Los recibos se generan con número, alumno, concepto, sucursal, medio e importe. `Imprimir recibo` abrió el diálogo nativo de Chrome; ese diálogo impide revisar su maquetación desde la automatización.

**Aceptación**

- Revisar manualmente recibo efectivo y transferencia en vista previa/PDF.
- A4 legible, sin cortes, con número, fecha, alumno, importe, medio, sucursal y cajero.
- Conservar evidencia visual o snapshot de una vista imprimible dedicada.

---

## Validación visual adicional

- Desktop: navegación, filtros, formularios y estados vacíos coherentes.
- Móvil 390x844: Alumnos y Reportes se reacomodan sin overflow horizontal evidente; la navegación pasa a menú.
- Caja Posadas: movimientos y cierre calcularon efectivo esperado $500, contado $500 y diferencia $0.

## Secuencia recomendada desde el fork

1. Abrir issue y rama por punto, por ejemplo `fix/qa-01-saldo-directorio`.
2. Escribir primero el test que reproduzca el defecto.
3. Implementar dominio/aplicación antes de ORM, API y Vue; mantener entradas HTTP y componentes delgados.
4. Ejecutar `manage.py check`, tests relevantes, build frontend y `git diff --check`.
5. Abrir un PR por issue con reproducción, evidencia y decisión de negocio pendiente cuando corresponda.
