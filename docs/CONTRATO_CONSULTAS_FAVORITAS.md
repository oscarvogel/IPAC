# Consultas favoritas — Identidad y Acceso

## Caso de uso y propiedad

Actor: usuario autenticado con perfil habilitado. Comandos: guardar, renombrar, actualizar y eliminar una consulta personal. Consultas: listar por pantalla y obtener una favorita para aplicarla. Resultado: preferencia persistente de la cuenta, independiente de sesión o equipo.

Agregado: `ConsultaFavorita`, una sola raíz y repositorio. Invariantes: propietario asignado por el servidor e inmutable; nombre recortado de 1–80 caracteres, único sin distinguir mayúsculas por cuenta y pantalla; configuración con claves y valores permitidos; pantalla inmutable al editar; alcance vigente validado al guardar y obtener para aplicar.

Dominio y aplicación independientes de Django en `core/contexts/identidad`. Puertos: `FavoritasRepository` y `AlcanceConsultas`. Composición en presentación HTTP; adaptadores Django en infraestructura. La declaración ORM permanece en `core.models` para el registro de modelos del monolito en transición. Autenticación y permisos generales existentes siguen compartidos con el legado.

Integración Published Language: Experiencia Web guarda filtros; Caja y Reportes mantienen sus consultas y permisos. No se almacenan resultados ni se reconstruyen reglas contables. No se incorporan eventos ni CQRS.

## API

Requiere la autenticación existente (Token o sesión). Todos los roles pueden gestionar sus preferencias de Reportes. Consulta no puede guardar filtros de movimientos detallados de Caja.

| Método | Ruta | Resultado |
|---|---|---|
| GET | `/api/consultas-favoritas/?pantalla=reportes` | Array de favoritas propias; `pantalla` opcional (`reportes`, `caja`) |
| POST | `/api/consultas-favoritas/` | 201 con nueva favorita |
| GET | `/api/consultas-favoritas/{id}/` | 200; valida alcance actual antes de aplicar |
| PUT/PATCH | `/api/consultas-favoritas/{id}/` | 200; valida configuración y alcance completo resultante |
| DELETE | `/api/consultas-favoritas/{id}/` | 204 |

DTO: `id`, `nombre`, `pantalla`, `configuracion`. No admite campos de propietario ni otros campos desconocidos. Identificadores ajenos o inexistentes: 404. Configuración inválida, duplicado o alcance perdido: 400 con `detail` legible. Sin autenticación/perfil habilitado: política de acceso existente.

Reportes:

```json
{"nombre":"Cobros del mes","pantalla":"reportes","configuracion":{"seccion":"cobranzas","periodo":"mes","desde":"","hasta":"","sucursal":null,"medio":"efectivo","usuario":null}}
```

- `seccion`: resumen, cobranzas, morosidad, caja, alumnos.
- `periodo`: hoy, mes, personalizado, todos. Hoy/mes se recalculan al aplicar usando fechas locales. Solo personalizado almacena ambas fechas ISO válidas y ordenadas; el resto guarda fechas vacías.
- `sucursal`, `usuario`: entero positivo o null; validados contra sucursales activas autorizadas y usuarios activos de esas sucursales. Si se elige sucursal, el cajero debe pertenecer a ella.
- `usuario` solo para cobranzas o caja; en historial de cajas elegir cajero exige Superadmin, Administración o Tesorería. Caja conserva la consulta de sus propias jornadas; Consulta conserva el agregado.
- `medio`: vacío, efectivo, transferencia, mercado_pago, tarjeta, otro; únicamente resumen y cobranzas admiten un medio distinto de vacío.
- Alumnos y morosidad consultan el estado actual: guardan `periodo: todos` y fechas vacías, y no presentan controles de fechas que sus exportaciones no aplican.

Caja:

```json
{"nombre":"Pagos en efectivo","pantalla":"caja","configuracion":{"tipo":"pago","medio":"efectivo","ordenamiento":"recent"}}
```

`tipo`: vacío, pago, ingreso, egreso, retiro, pase, reverso. `ordenamiento`: recent, oldest, amount. `medio`: catálogo anterior. No se admiten búsqueda libre, IDs de jornadas ni selección de movimientos.

La lista conserva favoritas que quedaron fuera del alcance para que puedan actualizarse con filtros válidos o eliminarse. Obtenerlas para aplicar responde 400 y no ejecuta la consulta. Renombrar también valida el alcance; actualizar su configuración permite corregirlas. Las consultas operativas vuelven a verificar permisos independientemente de esta validación.

## Persistencia y estado web

Migración `0016_consultas_favoritas`: únicamente tabla nueva, FK del propietario y restricciones de nombre/pantalla. No cambia tablas operativas ni datos existentes. Favoritas se cargan por instancia y pantalla, con revisión de petición; el cambio de cuenta/cierre de sesión vacía el estado y descarta respuestas de la cuenta anterior.

Reportes mantiene filtros aplicados separados del borrador. Solo una consulta exitosa actualiza las etiquetas. Los errores muestran una recuperación explícita; los atajos, quitar etiquetas y favoritas consultan directamente. Exportar usa los filtros de la consulta aplicada.

Las opciones de cajero se consultan dentro del alcance autorizado y la sucursal, independientemente del período seleccionado. El historial de cajas devuelve esas opciones antes de filtrar fechas; cobranzas reutiliza su consulta existente de usuarios sin fechas. Un período sin movimientos no elimina un cajero válido de una favorita.

El pago confirma únicamente el POST exitoso y emite `saved(pago)` una vez. Actualizar las listas y leer el recibo son lecturas separadas con reintento; no vuelven a registrar pagos. El panel de detalle navega internamente al recibo y la impresión selecciona un solo elemento de documento.
