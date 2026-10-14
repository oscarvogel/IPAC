# Diseño: transferencias entre cajas

**Fecha:** 13 de octubre de 2026  
**Contexto dueño:** Caja y Tesorería (en transición dentro del monolito modular IPAC)  
**Actor principal:** `superadmin` o `administracion` con alcance a las cajas involucradas

## Objetivo

Permitir que una persona administradora transfiera efectivo entre dos cajas diarias abiertas, incluso entre Posadas y Eldorado cuando su perfil tenga acceso a ambas. El traspaso acredita automáticamente el destino y deja evidencia consultable en ambas cajas.

## Lenguaje y comando

- **Transferencia entre cajas:** operación que retira efectivo de una caja diaria y lo acredita a otra.
- **Caja de origen:** caja abierta de la que se descuenta el importe.
- **Caja de destino:** caja abierta que recibe el importe.
- **Efectivo esperado:** saldo físico calculado por Caja con el saldo inicial y los movimientos registrados.
- **Comando:** transferir efectivo entre dos cajas abiertas, indicando origen, destino, importe y motivo.

La Caja existente y `MovimientoCaja` continúan en `core.models`; este cambio añade comportamiento al contexto lógico Caja y Tesorería sin afirmar que los modelos heredados ya estén aislados.

## Reglas aprobadas

1. Solo `superadmin` y `administracion` pueden iniciar transferencias.
2. Origen y destino deben ser cajas distintas, abiertas y correspondientes a la fecha operativa actual.
3. La persona debe tener alcance autorizado sobre ambas sucursales. Un usuario con alcance limitado opera dentro de su sucursal; el cruce Posadas/Eldorado requiere acceso a ambas.
4. El importe representa efectivo físico, debe ser mayor que cero y no puede superar el efectivo esperado disponible en origen.
5. El destino se acredita automáticamente al confirmar; no requiere confirmación posterior del cajero receptor.
6. Cada transferencia registra origen, destino, importe, motivo, fecha y hora, y el usuario que la ejecutó.
7. Una transferencia queda completa únicamente cuando se registran tanto el débito de origen como el crédito de destino. El débito, el crédito, la transferencia y su evento de auditoría se guardan en una sola transacción.
8. Los movimientos enlazados deben reflejarse en los saldos y cierres existentes: débito como pase de salida y crédito como ingreso de efectivo.
9. Las cajas cerradas no se modifican. No se incluye en este alcance anular o editar transferencias ya confirmadas.

## Enfoque recomendado

Crear un registro de transferencia con identificador/comprobante único que enlace los dos `MovimientoCaja`. El registro es la evidencia principal; los movimientos vinculados mantienen compatibles los cálculos, cierres y consultas de caja existentes. La transferencia guarda de forma explícita al actor porque el usuario dueño de una caja no necesariamente es quien ejecutó el traslado.

El nuevo caso de uso del contexto Caja coordina la operación. El dominio valida las reglas puras de importe y cajas distintas; un puerto de escritura y su adaptador Django cargan y bloquean ambas cajas en orden estable, vuelven a validar estado y saldo bajo bloqueo, y persisten la transferencia y los movimientos. El adaptador HTTP comprueba rol y alcance, traduce la solicitud al caso de uso y devuelve la evidencia. El contexto Auditoría recibe un evento por la transferencia, con origen, destino, importe, motivo y actor. Los modelos Django siguen en `core` por compatibilidad durante la transición.

## Interfaz y contrato

Se agrega una pantalla independiente **Transferencias entre cajas**, accesible para administración y superadmin. No depende de que el usuario tenga una caja propia abierta. Permite seleccionar una caja de origen y otra de destino entre las cajas abiertas disponibles para ese usuario, completar importe y motivo, revisar un resumen y confirmar. Después muestra el comprobante y una lista de transferencias recientes con sus dos cajas.

La API expone:

- una consulta de cajas abiertas y operables dentro del alcance del usuario;
- un comando para crear la transferencia sin permitir que el cliente determine el actor ni omita validaciones;
- una consulta de historial/evidencia, filtrada al alcance autorizado.

Los nombres concretos de rutas y campos se fijan durante el plan de implementación siguiendo los contratos actuales de `/api/`.

## Errores y concurrencia

La operación se rechaza sin escrituras si el actor no tiene rol o alcance, una caja no existe/no está abierta/no es del día, origen y destino coinciden, el importe es inválido o supera el efectivo esperado. Se vuelve a comprobar el saldo después de bloquear las cajas para impedir dos transferencias concurrentes que juntas excedan el disponible. Cualquier fallo al guardar una de las partes revierte la transacción completa.

## Criterios de aceptación

- Una transferencia válida resta efectivo esperado al origen y lo suma al destino por el mismo importe.
- La evidencia permite identificar actor, fecha, motivo, importe, cajas y los movimientos asociados.
- Un administrador sin caja propia abierta puede operar entre dos cajas abiertas autorizadas.
- El cruce entre sucursales funciona solo si ambas están dentro del alcance del actor.
- Se rechazan cajas iguales, cerradas, de otra fecha, fuera de alcance, importes no positivos y montos mayores al efectivo esperado de origen.
- Una falla de persistencia no deja una sola pata del movimiento ni una transferencia incompleta.
- La interfaz de Caja existente y el historial muestran las transferencias como salidas y entradas con un vínculo a su evidencia.

## Fuera de alcance

- Confirmación manual del receptor.
- Transferencias entre cajas cerradas o de días distintos.
- Transferencia de medios no efectivos.
- Anulación, edición o reversión de una transferencia confirmada.
- Reestructuración general de los modelos heredados de Caja o separación del contexto.
