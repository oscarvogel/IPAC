# Cambio obligatorio de clave en el primer ingreso — IPAC

## Objetivo

Permitir altas de usuarios con una clave temporal y obligar a reemplazarla en el primer ingreso antes de habilitar el uso del CRM.

## Alcance aprobado

Se modifica únicamente el contexto lógico de Identidad y Acceso y sus adaptadores existentes. No se crean roles nuevos, no se cambia la política de sucursales y no se introduce CQRS, event sourcing ni un servicio externo.

Asignación inicial de usuarios:

| Persona | Rol IPAC | Alcance | Sucursal |
|---|---|---|---|
| Osten Mario Ruben | `superadmin` | Todas las sedes | Posadas como sucursal de perfil |
| Rodriguez Aguero Claudio | `superadmin` | Todas las sedes | Posadas como sucursal de perfil |
| Rodriguez Zulma | `administracion` | Todas las sedes | Posadas como sucursal de perfil |
| Acosta Laura | `tesoreria` | Todas las sedes | Posadas como sucursal de perfil |
| Casco Gerardo | `caja` | Sólo su caja | Posadas |

La sucursal de perfil para los usuarios con alcance global será Posadas porque el modelo actual la exige, pero su autorización seguirá siendo global mediante `puede_ver_todas_las_sucursales`.

## Diseño técnico

### Persistencia

Agregar `debe_cambiar_clave` al perfil de usuario, con valor predeterminado `False` para conservar el acceso de usuarios existentes. Las altas que reciban una clave temporal se crearán con el valor `True`.

La bandera pertenece al perfil de Identidad y Acceso, no al usuario Django ni a los contextos operativos. El cambio de clave la establece en `False` dentro de la misma operación de persistencia.

### API

- `POST /api/auth/login/` mantiene el token actual y agrega `debe_cambiar_clave` en la respuesta.
- `GET /api/auth/me/` expone la bandera para hidratar el frontend.
- `POST /api/auth/change-password/` recibe `new_password` y `new_password_confirmation`, exige autenticación, valida longitud mínima y coincidencia, actualiza la clave y elimina la obligación.
- Mientras la bandera esté activa, los endpoints operativos devolverán `403` con un código estable (`password_change_required`). Se exceptúan `auth/me` y `auth/change-password` para permitir completar el flujo.
- La administración de usuarios conservará la posibilidad de establecer una clave temporal; al modificar una clave desde el formulario de administración se marcará nuevamente el cambio obligatorio.

Los controladores sólo traducen HTTP, autenticación y errores. La coordinación de la operación de cambio se ubicará en la aplicación del contexto de Identidad y Acceso, reutilizando adaptadores existentes mientras el monolito modular continúa en transición.

### Frontend

- Después del login y al hidratar la sesión, el router redirigirá a `/cambiar-clave` si la bandera está activa.
- La vista será una pantalla bloqueante con clave nueva y confirmación; no mostrará navegación operativa.
- Al completar el cambio, actualizará el usuario actual y enviará al dashboard.
- Se mantendrán los estados de carga, error, accesibilidad de formularios y soporte desktop/mobile.

### Seguridad y errores

- Las claves nunca se devuelven en respuestas ni se registran en auditoría o logs.
- La clave temporal será generada para esta alta y se comunicará por un canal separado del sistema; no se usarán `admin123` ni credenciales demo.
- Un usuario inactivo seguirá sin poder autenticarse.
- Un token existente con cambio pendiente no podrá acceder a módulos operativos hasta cambiar la clave.

## Verificación

Backend:

- prueba de login que informa obligación;
- prueba de bloqueo de endpoint operativo;
- prueba de cambio exitoso y desbloqueo;
- pruebas de rechazo por claves no coincidentes o demasiado cortas;
- regresión de usuarios existentes con bandera `False`;
- `manage.py check` y tests de `core`.

Frontend:

- pruebas del composable y la vista de cambio;
- prueba del guard de router;
- `npm --prefix frontend run build`.

Operación:

- `git diff --check`;
- backup PostgreSQL antes del deploy en FASA 189;
- deploy fast-forward/reconstrucción controlada preservando `.env` y volúmenes;
- health backend/frontend y apertura pública del sitio;
- alta de los cinco usuarios sólo después de confirmar la migración y el flujo de primer ingreso.

## Fuera de alcance

- Envío automático de correos desde IPAC.
- Recuperación de contraseña olvidada.
- Nuevos roles “Bedel” o permisos más finos por módulo.
- Cambios de datos, cajas o movimientos existentes.
