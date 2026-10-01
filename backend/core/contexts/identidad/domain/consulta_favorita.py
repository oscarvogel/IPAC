"""Preferencias personales; no contienen datos ni conceden autorizaciones."""
from dataclasses import dataclass
from datetime import date
import re


class FavoritaInvalida(ValueError):
    pass


class FavoritaNoEncontrada(LookupError):
    pass


MEDIOS = {"", "efectivo", "transferencia", "mercado_pago", "tarjeta", "otro"}
SECCIONES = {"resumen", "cobranzas", "morosidad", "caja", "alumnos"}


def validar_configuracion(pantalla, configuracion):
    if not isinstance(configuracion, dict):
        raise FavoritaInvalida("La configuración debe ser un objeto.")
    config = dict(configuracion)
    for field in ("medio", "tipo", "ordenamiento", "seccion", "periodo", "desde", "hasta"):
        if field in config and not isinstance(config[field], str):
            raise FavoritaInvalida("Los filtros de texto deben ser cadenas.")
    if pantalla == "caja":
        keys = {"tipo", "medio", "ordenamiento"}
        if set(config) != keys or config.get("tipo") not in {"", "pago", "ingreso", "egreso", "retiro", "pase", "reverso"} or config.get("ordenamiento") not in {"recent", "oldest", "amount"}:
            raise FavoritaInvalida("Los filtros de Caja no son válidos.")
    elif pantalla == "reportes":
        keys = {"seccion", "periodo", "desde", "hasta", "sucursal", "medio", "usuario"}
        if set(config) != keys or config.get("seccion") not in SECCIONES or config.get("periodo") not in {"hoy", "mes", "personalizado", "todos"}:
            raise FavoritaInvalida("La consulta de Reportes no es válida.")
        for field in ("sucursal", "usuario"):
            value = config[field]
            if value is not None and (type(value) is not int or value <= 0):
                raise FavoritaInvalida("Sucursal y cajero deben ser identificadores válidos.")
        if config["periodo"] == "personalizado":
            try:
                if not all(re.fullmatch(r"\d{4}-\d{2}-\d{2}", config[field]) for field in ("desde", "hasta")):
                    raise ValueError()
                start, end = date.fromisoformat(config["desde"]), date.fromisoformat(config["hasta"])
                if start > end:
                    raise ValueError()
            except (TypeError, ValueError):
                raise FavoritaInvalida("Indicá fechas válidas, con Desde anterior o igual a Hasta.")
        elif config["desde"] or config["hasta"]:
            raise FavoritaInvalida("Los períodos relativos no guardan fechas fijas.")
        if config["seccion"] not in {"cobranzas", "caja"} and config["usuario"] is not None:
            raise FavoritaInvalida("Esta sección no permite filtrar por cajero.")
        if config["seccion"] not in {"resumen", "cobranzas"} and config["medio"]:
            raise FavoritaInvalida("Esta sección no se filtra por medio de pago.")
        if config["seccion"] in {"alumnos", "morosidad"} and config["periodo"] != "todos":
            raise FavoritaInvalida("Este listado refleja el estado actual y no admite un período.")
    else:
        raise FavoritaInvalida("Pantalla desconocida.")
    if config.get("medio") not in MEDIOS:
        raise FavoritaInvalida("Medio de pago desconocido.")
    return config


@dataclass(frozen=True)
class ConsultaFavorita:
    id: int | None
    propietario_id: int
    nombre: str
    pantalla: str
    configuracion: dict

    @classmethod
    def crear(cls, *, propietario_id, nombre, pantalla, configuracion, id=None):
        if not isinstance(nombre, str) or not nombre.strip() or len(nombre.strip()) > 80:
            raise FavoritaInvalida("Usá un nombre de entre 1 y 80 caracteres.")
        return cls(id, propietario_id, nombre.strip(), pantalla, validar_configuracion(pantalla, configuracion))
