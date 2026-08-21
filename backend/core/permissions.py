from rest_framework.permissions import BasePermission, SAFE_METHODS

from .models import PerfilUsuario


SUPERADMIN = PerfilUsuario.Rol.SUPERADMIN
ADMINISTRACION = PerfilUsuario.Rol.ADMINISTRACION
TESORERIA = PerfilUsuario.Rol.TESORERIA
CAJA = PerfilUsuario.Rol.CAJA
CONSULTA = PerfilUsuario.Rol.CONSULTA

ALL_ROLES = frozenset({SUPERADMIN, ADMINISTRACION, TESORERIA, CAJA, CONSULTA})
ADMIN_ROLES = frozenset({SUPERADMIN, ADMINISTRACION})
OPERATIONAL_ROLES = frozenset({SUPERADMIN, ADMINISTRACION, TESORERIA, CAJA})
CASH_ROLES = frozenset({SUPERADMIN, ADMINISTRACION, TESORERIA, CAJA})
FEE_MANAGEMENT_ROLES = frozenset({SUPERADMIN, ADMINISTRACION, TESORERIA})
PAYMENT_VOID_ROLES = frozenset({SUPERADMIN, TESORERIA})


class RolePermission(BasePermission):
    """Permission policy shared by all HTTP adapters in the core context."""

    read_roles = ALL_ROLES
    write_roles = frozenset()
    action_roles = {}

    def has_permission(self, request, view):
        profile = getattr(request.user, "perfil", None)
        if not profile:
            return False
        action = getattr(view, "action", None)
        allowed_roles = self.action_roles.get(action)
        if allowed_roles is None:
            allowed_roles = self.read_roles if request.method in SAFE_METHODS else self.write_roles
        return profile.rol in allowed_roles


class ReadOnlyPermission(RolePermission):
    pass


class AcademicManagementPermission(RolePermission):
    write_roles = ADMIN_ROLES


class SucursalPermission(RolePermission):
    write_roles = ADMIN_ROLES
    action_roles = {
        "create": ADMIN_ROLES,
    }

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        profile = request.user.perfil
        return not (
            getattr(view, "action", None) == "create"
            and profile.rol == ADMINISTRACION
            and not profile.puede_ver_todas_las_sucursales
        )


class CuotaPermission(RolePermission):
    write_roles = FEE_MANAGEMENT_ROLES
    action_roles = {
        "generar": FEE_MANAGEMENT_ROLES,
    }


class PagoPermission(RolePermission):
    write_roles = OPERATIONAL_ROLES
    action_roles = {
        "update": frozenset({SUPERADMIN}),
        "partial_update": frozenset({SUPERADMIN}),
        "destroy": frozenset(),
        "anular": PAYMENT_VOID_ROLES,
    }


class AplicacionPagoPermission(RolePermission):
    write_roles = OPERATIONAL_ROLES
    action_roles = {
        "update": frozenset({SUPERADMIN}),
        "partial_update": frozenset({SUPERADMIN}),
        "destroy": frozenset({SUPERADMIN}),
    }


class CajaPermission(RolePermission):
    write_roles = frozenset()
    action_roles = {
        "hoy": ALL_ROLES,
        "cerrar": CASH_ROLES,
        "saldo_anterior": CASH_ROLES,
    }


class MovimientoCajaPermission(RolePermission):
    action_roles = {
        "create": CASH_ROLES,
    }


class UserManagementPermission(RolePermission):
    read_roles = ADMIN_ROLES
    write_roles = ADMIN_ROLES


class ImportacionPermission(RolePermission):
    read_roles = ADMIN_ROLES
    write_roles = ADMIN_ROLES


class AuditoriaPermission(RolePermission):
    read_roles = ADMIN_ROLES
    write_roles = frozenset()


def can_manage_user(actor, target=None, proposed_role=None, global_access=None):
    """Central policy for role, scope and self-escalation changes."""
    actor_profile = getattr(actor, "perfil", None)
    if not actor_profile or actor_profile.rol not in ADMIN_ROLES:
        return False, "No tiene permisos para administrar usuarios."

    if actor_profile.rol == SUPERADMIN:
        return True, ""

    target_profile = getattr(target, "perfil", None) if target else None
    target_role = proposed_role or getattr(target_profile, "rol", None)
    if target_role == SUPERADMIN or getattr(target_profile, "rol", None) == SUPERADMIN:
        return False, "Sólo un superadmin puede crear o modificar superadmins."
    if global_access:
        return False, "Sólo un superadmin puede conceder acceso a todas las sucursales."
    if target and target.pk == actor.pk:
        if proposed_role and proposed_role != actor_profile.rol:
            return False, "No puede cambiar su propio rol."
        if global_access is not None and bool(global_access) != actor_profile.puede_ver_todas_las_sucursales:
            return False, "No puede modificar su propio alcance de sucursales."
    return True, ""
