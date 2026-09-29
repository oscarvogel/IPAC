from .models import Sucursal


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
