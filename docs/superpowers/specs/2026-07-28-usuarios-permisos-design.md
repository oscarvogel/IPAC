# Módulo de Usuarios y Permisos — IPAC

## Resumen

Agregar gestión de usuarios y perfiles desde el frontend: alta, edición, activación/desactivación, asignación de rol, sucursal y permiso de supervisión.

## Roles

- `superadmin` — Acceso completo, ve todas las sucursales
- `administracion` — CRUD completo, restringido a su sucursal
- `tesoreria` — Solo lectura de usuarios, acceso a módulo financiero
- `caja` — Solo lectura, acceso a caja diaria
- `consulta` — Solo lectura, acceso a reportes

## Backend

### Modelos
- `PerfilUsuario.Rol`: agregar `SUPERADMIN = "superadmin", "Superadmin"`

### Serializers
- `UserSerializer`: crea/edita `User` + `PerfilUsuario` en un solo request.
  - `password` write-only, requerido en create, opcional en update.
  - `rol`, `sucursal`, `puede_ver_todas_las_sucursales` mapeados a `PerfilUsuario`.

### Views
- `UserViewSet`:
  - `get_queryset`: superadmin ve todos; resto solo usuarios de su sucursal.
  - `perform_create`: crea `User` + `PerfilUsuario`.
  - `perform_update`: actualiza ambos.
  - `perform_destroy`: `user.is_active = False` (baja lógica).
  - Filtros: `?sucursal=`, `?rol=`, `?activo=`.

### URLs
- `router.register("usuarios", UserViewSet, basename="usuario")`

## Frontend

### Router
- Ruta `/usuarios` con `UsuariosView`.

### Sidebar
- Entrada "Usuarios" visible si el usuario es superadmin o administración (controlado por `v-if` en template).

### Composable
- `useUsuarios.js`: estado singleton con lista de usuarios, `loadUsuarios`, `createUsuario`, `updateUsuario`, `deactivateUsuario`.

### Componentes
- `UsuariosView.vue`: tabla con columnas `username`, `nombre`, `rol`, `sucursal`, `activo`, acciones (editar, desactivar).
- `UsuarioForm.vue`: modal inline. Campos:
  - `username` (text, requerido)
  - `password` (text, solo create, no mostrar en edit)
  - `first_name`, `last_name`, `email`
  - `is_active` (checkbox)
  - `rol` (select con los 5 roles)
  - `sucursal` (select de sucursales)
  - `puede_ver_todas_las_sucursales` (checkbox)
