from .models import PerfilUsuario, Sucursal


def scoped_queryset_for_user(queryset, user):
    """Limit a legacy ORM queryset to the branches available to this actor."""
    perfil = getattr(user, "perfil", None)
    if not perfil:
        return queryset.none()
    if perfil.puede_ver_todas_las_sucursales:
        return queryset
    if queryset.model is Sucursal:
        return queryset.filter(pk=perfil.sucursal_id)
    return queryset.filter(sucursal=perfil.sucursal)


def scoped_cajas_for_user(queryset, user):
    """Cajas que este actor puede ver, según la matriz de permisos.

    El rol `caja` es el único amo de su caja. IPAC lo definió así el 07/10/2026:
    *"Casco Gerardo sólo puede ver los movimientos de su caja"*. Los roles de
    supervisión ven todas las cajas de su sucursal, o de todas si tienen
    alcance global. El rol `consulta` no ve ninguna.

    Esta regla vivía escrita a mano en dos lugares —el listado de cajas y el
    reporte exportable— y sólo uno la tenía. El reporte terminó mostrando las
    cajas de los demás cajeros de la sucursal. Por eso vive acá y los dos la
    llaman: una regla duplicada puede divergir sin que nadie lo note.
    """
    perfil = getattr(user, "perfil", None)
    if not perfil:
        return queryset.none()
    if perfil.rol == PerfilUsuario.Rol.CAJA:
        return scoped_queryset_for_user(queryset, user).filter(usuario=user)
    if perfil.rol == PerfilUsuario.Rol.CONSULTA:
        return queryset.none()
    return scoped_queryset_for_user(queryset, user)