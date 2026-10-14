# Contrato HTTP de transferencias entre cajas

Contexto dueño: Caja y Tesorería, en transición en el monolito. Actor autenticado: administración o superadmin con alcance vigente sobre ambas sucursales.

## Comando e idempotencia

`POST /api/transferencias-caja/` conserva el cuerpo `origen_id`, `destino_id`, `importe` (decimal de dos posiciones) y `motivo` (hasta 180 caracteres). El actor proviene de la sesión autenticada.

El cliente envía `Idempotency-Key: <UUID>` por intención de transferencia. La pantalla reutiliza esa clave y el mismo cuerpo después de un error ambiguo de red/servidor. Una respuesta confirmada o un cambio del comando inicia otra intención con un UUID nuevo. Actualizar las consultas no renueva la clave pendiente. La clave se conserva durante la vida de la pantalla; recargar o abandonar la pantalla descarta su formulario y ese estado.

- Primer éxito: HTTP 201 con evidencia completa.
- Misma clave, actor y comando: HTTP 201 con la evidencia de la primera respuesta, incluidas fecha, ejecutor, cajas, saldos de esa respuesta y ambos IDs de movimiento. No crea registros ni eventos de auditoría adicionales. El importe se compara como decimal y el motivo se compara después de quitar espacios en sus extremos.
- Misma clave con otro actor, origen, destino, importe o motivo válido: HTTP 409 y `detail` genérico, sin datos de la transferencia original.
- Encabezado presente vacío o con formato distinto de UUID: HTTP 400.
- El replay comprueba el alcance vigente sobre ambas cajas. Revocar una sucursal impide recuperar esa evidencia y responde HTTP 404 `Caja no disponible.`. Un replay autorizado de una operación ya confirmada puede recuperar su evidencia aunque las cajas estén cerradas o su fecha operativa haya cambiado; no vuelve a modificarlas.
- Los permisos de rol, perfil y cambio obligatorio de clave siguen aplicándose a todos los POST.
- Para compatibilidad, omitir el encabezado genera una clave nueva en el servidor en cada POST. Esos clientes deben añadir el encabezado para que sus reintentos sean idempotentes.

La clave es única globalmente y no tiene vencimiento: se guarda con la evidencia de la transferencia. Las filas previas a la migración 0019 conservan ambos metadatos en NULL. La restricción única y los savepoints resuelven las carreras sin dejar una transacción inutilizable; las cajas siguen bloqueándose en orden ascendente.

La transferencia, sus dos movimientos, el único evento de auditoría y el snapshot de respuesta se confirman o revierten juntos. El dominio puro no conoce UUID, encabezados, HTTP ni persistencia del replay.

## Lecturas

`GET /api/transferencias-caja/cajas-abiertas/` y `GET /api/transferencias-caja/` conservan su alcance. El historial sigue consultando evidencia y saldos según su contrato anterior; el snapshot técnico sirve a la respuesta del reintento.

Las listas/detalles de movimientos y las respuestas anidadas de caja precargan transferencia, actor, ambas cajas, sucursales y cajeros. Se mantienen la propiedad de caja y la redacción de contraparte y receptor fuera del alcance. Precargar una relación no concede permisos para publicar sus datos.
