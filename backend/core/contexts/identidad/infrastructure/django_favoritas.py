from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from core.models import ConsultaFavorita as RegistroFavorita, Sucursal
from ..domain.consulta_favorita import ConsultaFavorita, FavoritaInvalida


def entidad(row):
    return ConsultaFavorita(row.id, row.propietario_id, row.nombre, row.pantalla, row.configuracion)


class DjangoFavoritasRepository:
    def listar(self, propietario_id, pantalla=None):
        rows = RegistroFavorita.objects.filter(propietario_id=propietario_id)
        if pantalla:
            rows = rows.filter(pantalla=pantalla)
        return [entidad(row) for row in rows]

    def obtener(self, propietario_id, id):
        row = RegistroFavorita.objects.filter(propietario_id=propietario_id, pk=id).first()
        return entidad(row) if row else None

    def guardar(self, favorita):
        try:
            with transaction.atomic():
                if favorita.id:
                    row = RegistroFavorita.objects.select_for_update().get(pk=favorita.id, propietario_id=favorita.propietario_id)
                    row.nombre, row.configuracion = favorita.nombre, favorita.configuracion
                    row.save(update_fields=["nombre", "configuracion"])
                else:
                    row = RegistroFavorita.objects.create(propietario_id=favorita.propietario_id, nombre=favorita.nombre, pantalla=favorita.pantalla, configuracion=favorita.configuracion)
                return entidad(row)
        except IntegrityError:
            raise FavoritaInvalida("Ya existe una favorita con ese nombre en esta pantalla.")

    def eliminar(self, propietario_id, id):
        RegistroFavorita.objects.filter(pk=id, propietario_id=propietario_id).delete()


class DjangoAlcanceConsultas:
    """Traduce el alcance de Identidad a filtros; nunca amplía permisos."""
    def validar(self, actor_id, pantalla, configuracion):
        actor = User.objects.select_related("perfil").get(pk=actor_id)
        perfil = actor.perfil
        if pantalla == "caja":
            if perfil.rol == "consulta":
                raise FavoritaInvalida("Tu perfil solo permite reportes agregados de caja.")
            return
        sucursal_id = configuracion["sucursal"]
        sucursales = Sucursal.objects.filter(activa=True)
        if not perfil.puede_ver_todas_las_sucursales:
            sucursales = sucursales.filter(pk=perfil.sucursal_id)
        if sucursal_id and not sucursales.filter(pk=sucursal_id).exists():
            raise FavoritaInvalida("La sucursal ya no está disponible. Editá la favorita para elegir una sucursal autorizada.")
        usuario_id = configuracion["usuario"]
        if usuario_id:
            if configuracion["seccion"] == "caja" and perfil.rol not in {"superadmin", "administracion", "tesoreria"}:
                raise FavoritaInvalida("Tu perfil no permite elegir cajero en el historial de cajas.")
            usuarios = User.objects.filter(is_active=True, perfil__sucursal_id__in=sucursales.values("pk"))
            if sucursal_id:
                usuarios = usuarios.filter(perfil__sucursal_id=sucursal_id)
            if not usuarios.filter(pk=usuario_id).exists():
                raise FavoritaInvalida("El cajero ya no está disponible. Editá la favorita para elegir un cajero autorizado.")
