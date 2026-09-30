from typing import Protocol
from ..domain.consulta_favorita import ConsultaFavorita, FavoritaInvalida, FavoritaNoEncontrada


class FavoritasRepository(Protocol):
    def listar(self, propietario_id: int, pantalla: str | None): ...
    def obtener(self, propietario_id: int, id: int): ...
    def guardar(self, favorita: ConsultaFavorita): ...
    def eliminar(self, propietario_id: int, id: int): ...


class AlcanceConsultas(Protocol):
    def validar(self, actor_id: int, pantalla: str, configuracion: dict): ...


class ConsultasFavoritas:
    def __init__(self, repository: FavoritasRepository, alcance: AlcanceConsultas):
        self.repository = repository
        self.alcance = alcance

    def listar(self, *, actor_id, pantalla=None):
        if pantalla and pantalla not in {"caja", "reportes"}:
            raise FavoritaInvalida("Pantalla desconocida.")
        return self.repository.listar(actor_id, pantalla)

    def obtener(self, *, actor_id, id, validar_alcance=True):
        favorita = self.repository.obtener(actor_id, id)
        if favorita is None:
            raise FavoritaNoEncontrada()
        if validar_alcance:
            self.alcance.validar(actor_id, favorita.pantalla, favorita.configuracion)
        return favorita

    def guardar(self, *, actor_id, datos, id=None):
        if not isinstance(datos, dict):
            raise FavoritaInvalida("La consulta debe ser un objeto.")
        if set(datos) - {"nombre", "pantalla", "configuracion"}:
            raise FavoritaInvalida("Solo se pueden editar nombre, pantalla y configuración.")
        anterior = self.obtener(actor_id=actor_id, id=id, validar_alcance=False) if id else None
        values = {"nombre": anterior.nombre, "pantalla": anterior.pantalla, "configuracion": anterior.configuracion} if anterior else {}
        values.update(datos)
        if set(values) != {"nombre", "pantalla", "configuracion"}:
            raise FavoritaInvalida("Indicá nombre, pantalla y configuración.")
        if anterior and values["pantalla"] != anterior.pantalla:
            raise FavoritaInvalida("La pantalla de una favorita no se puede cambiar.")
        favorita = ConsultaFavorita.crear(id=id, propietario_id=actor_id, **values)
        self.alcance.validar(actor_id, favorita.pantalla, favorita.configuracion)
        return self.repository.guardar(favorita)

    def eliminar(self, *, actor_id, id):
        self.obtener(actor_id=actor_id, id=id, validar_alcance=False)
        self.repository.eliminar(actor_id, id)
