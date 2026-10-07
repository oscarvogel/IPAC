"""Aplica e informa la matriz de permisos acordada con IPAC el 07/10/2026.

Responde el punto 4 del mail del 01/10/2026 y el punto 5 de los próximos pasos
de la reunión del 24/09: *"Informe detallado sobre los permisos asignados a los
diferentes usuarios"*.

Uso:

    python manage.py configurar_matriz_permisos              # informe (sólo lectura)
    python manage.py configurar_matriz_permisos --aplicar    # asigna los roles

La matriz está en `config/matriz_permisos.json`, no acá adentro. La primera
versión de este comando traía los usernames escritos en el módulo, tomados de
un entorno de prueba, y en la instalación real falló de punta a punta: los
cinco aparecían como NO EXISTE y no aplicaba nada. El username de una persona
es dato de la instalación, no del dominio.

Este comando **no crea usuarios**. Las personas se dan de alta desde la pantalla
Usuarios y permisos, que pide la contraseña y la valida. Acá sólo se asigna el
rol y el alcance, que es lo que IPAC definió.

Por qué los errores no son silenciosos: el rol `superadmin` puede crear otros
superadmins y conceder alcance global. Si un nombre de la matriz no existe, no
se lo inventa: no aplica **nada** y lo reporta para que alguien lo cree desde la
pantalla.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from core.models import PerfilUsuario, Sucursal

ALCANCES = ("global", "sucursal")

RUTA_POR_DEFECTO = Path(settings.BASE_DIR) / "config" / "matriz_permisos.json"


@dataclass(frozen=True)
class EntradaMatriz:
    username: str
    rol: str
    alcance: str
    definicion: str

    @property
    def todas_las_sucursales(self) -> bool:
        return self.alcance == "global"


@dataclass(frozen=True)
class Matriz:
    entradas: tuple[EntradaMatriz, ...]
    sucursal_por_defecto: str
    pendientes: tuple[str, ...]


def cargar_matriz(ruta: Path) -> Matriz:
    """Lee y valida la matriz. Función pura: no toca la base ni Django.

    Cada error de formasale como CommandError nombrando el archivo y el
    problema, porque un JSON mal editado en producción no se puede
    descubrir por otra vía que el traceback.
    """
    try:
        crudo = Path(ruta).read_text(encoding="utf-8")
    except FileNotFoundError:
        raise CommandError(
            f"No existe el archivo de matriz {ruta}. "
            "Pasalo con --matriz o crealo en config/matriz_permisos.json."
        ) from None

    try:
        datos = json.loads(crudo)
    except json.JSONDecodeError as exc:
        raise CommandError(f"{ruta} no es JSON válido: {exc}") from None

    if not isinstance(datos, dict):
        raise CommandError(f"{ruta}: se esperaba un objeto JSON en la raíz.")

    usuarios = datos.get("usuarios")
    if not isinstance(usuarios, list):
        raise CommandError(f"{ruta}: falta la lista 'usuarios'.")

    roles_validos = {valor for valor, _ in PerfilUsuario.Rol.choices}
    entradas: list[EntradaMatriz] = []
    vistos: set[str] = set()

    for numero, item in enumerate(usuarios, start=1):
        donde = f"{ruta}: usuario #{numero}"
        if not isinstance(item, dict):
            raise CommandError(f"{donde} no es un objeto.")

        username = str(item.get("username", "")).strip()
        if not username:
            raise CommandError(f"{donde} no tiene 'username'.")
        if username in vistos:
            raise CommandError(
                f"{donde} repite el username {username!r}. "
                "Con duplicados no se sabe cuál de los dos roles gana."
            )
        vistos.add(username)

        rol = str(item.get("rol", "")).strip()
        if rol not in roles_validos:
            raise CommandError(
                f"{donde} ({username}) tiene rol {rol!r}, que no existe. "
                f"Validos: {', '.join(sorted(roles_validos))}."
            )

        alcance = str(item.get("alcance", "")).strip()
        if alcance not in ALCANCES:
            raise CommandError(
                f"{donde} ({username}) tiene alcance {alcance!r}. "
                f"Validos: {', '.join(ALCANCES)}."
            )

        entradas.append(
            EntradaMatriz(
                username=username,
                rol=rol,
                alcance=alcance,
                definicion=str(item.get("definicion", "")).strip(),
            )
        )

    sucursal_por_defecto = str(datos.get("sucursal_por_defecto", "")).strip()
    if not sucursal_por_defecto:
        raise CommandError(f"{ruta}: falta 'sucursal_por_defecto'.")

    pendientes = tuple(
        str(linea).strip()
        for linea in datos.get("pendientes", [])
        if str(linea).strip()
    )

    return Matriz(tuple(entradas), sucursal_por_defecto, pendientes)


class Command(BaseCommand):
    help = "Informa los permisos de cada usuario y, con --aplicar, asigna la matriz de IPAC."

    def add_arguments(self, parser):
        parser.add_argument(
            "--aplicar",
            action="store_true",
            help="Asigna los roles de la matriz en lugar de sólo informar.",
        )
        parser.add_argument(
            "--matriz",
            default=str(RUTA_POR_DEFECTO),
            help=f"Archivo JSON con la matriz (por defecto {RUTA_POR_DEFECTO}).",
        )
        parser.add_argument(
            "--sucursal",
            default=None,
            help="Sucursal para los usuarios sin alcance global. "
            "Por defecto, la que dice el archivo.",
        )

    def handle(self, *args, **options):
        matriz = cargar_matriz(Path(options["matriz"]))
        sucursal = self._sucursal(options["sucursal"] or matriz.sucursal_por_defecto)

        # Se resuelve todo antes de escribir una sola vez. Antes se aplicaba lo
        # que se encontraba, se comiteaba ese transaction.atomic, y recién
        # después el informe tiraba el CommandError: matriz a medias y un
        # codigo de salida de error que noaba que hubo cambios.
        resueltos = [(entrada, self._perfil_de(entrada)) for entrada in matriz.entradas]
        faltantes = [entrada.username for entrada, perfil in resueltos if perfil is None]

        if faltantes:
            self._informe(resueltos, sucursal, matriz)
            raise CommandError(
                "Faltan usuarios de la matriz: "
                + ", ".join(faltantes)
                + ". No se aplicó nada. Crealos desde Usuarios y permisos "
                "o corregí el username en "
                f"{options['matriz']}, y volvé a correr el comando."
            )

        if options["aplicar"]:
            self._aplicar(resueltos, sucursal)
        self._informe(resueltos, sucursal, matriz)

    def _sucursal(self, codigo):
        try:
            return Sucursal.objects.get(codigo=codigo)
        except Sucursal.DoesNotExist:
            disponibles = ", ".join(Sucursal.objects.values_list("codigo", flat=True))
            raise CommandError(
                f"No existe la sucursal {codigo!r}. Disponibles: {disponibles or 'ninguna'}."
            ) from None

    @transaction.atomic
    def _aplicar(self, resueltos, sucursal):
        for entrada, perfil in resueltos:
            cambios = []
            if perfil.rol != entrada.rol:
                cambios.append(f"rol {perfil.rol} -> {entrada.rol}")
            if perfil.puede_ver_todas_las_sucursales != entrada.todas_las_sucursales:
                cambios.append(
                    f"alcance {'global' if perfil.puede_ver_todas_las_sucursales else 'sucursal'}"
                    f" -> {'global' if entrada.todas_las_sucursales else 'sucursal'}"
                )
            if not entrada.todas_las_sucursales and perfil.sucursal_id != sucursal.id:
                cambios.append(f"sucursal {perfil.sucursal.codigo} -> {sucursal.codigo}")

            if not cambios:
                continue
            perfil.rol = entrada.rol
            perfil.puede_ver_todas_las_sucursales = entrada.todas_las_sucursales
            if not entrada.todas_las_sucursales:
                perfil.sucursal = sucursal
            perfil.save()
            self.stdout.write(f"{entrada.username}: " + "; ".join(cambios))

    def _informe(self, resueltos, sucursal, matriz):
        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING("Matriz de permisos de IPAC (07/10/2026)"))
        self.stdout.write("")
        encabezado = f"{'usuario':<20} {'rol':<16} {'sucursal':<10} {'alcance':<18} estado"
        self.stdout.write(encabezado)
        self.stdout.write("-" * len(encabezado))

        for entrada, perfil in resueltos:
            if perfil is None:
                self.stdout.write(
                    f"{entrada.username:<20} {'-':<16} {'-':<10} {'-':<18} NO EXISTE"
                )
                self.stdout.write(f"{'':<20} {entrada.definicion}")
                continue
            alcance = "todas las sedes" if perfil.puede_ver_todas_las_sucursales else "su sucursal"
            coincide = (
                perfil.rol == entrada.rol
                and perfil.puede_ver_todas_las_sucursales == entrada.todas_las_sucursales
            )
            estado = (
                self.style.SUCCESS("coincide")
                if coincide
                else self.style.WARNING("DIFIERE de la matriz")
            )
            self.stdout.write(
                f"{entrada.username:<20} {perfil.get_rol_display():<16} "
                f"{perfil.sucursal.codigo:<10} {alcance:<18} {estado}"
            )
            self.stdout.write(f"{'':<20} {entrada.definicion}")

        otros = self._usuarios_fuera_de_la_matriz(matriz)
        if otros:
            self.stdout.write("")
            self.stdout.write(self.style.MIGRATE_HEADING("Usuarios que no están en la matriz"))
            for perfil in otros:
                alcance = "todas" if perfil.puede_ver_todas_las_sucursales else perfil.sucursal.codigo
                self.stdout.write(
                    f"  {perfil.user.username:<20} {perfil.get_rol_display():<16} {alcance}"
                )
            self.stdout.write("")
            self.stdout.write(
                "  `admin` es la cuenta de arranque que crea el seed. Necesita superadmin porque\n"
                "  sólo un superadmin puede dar de alta a otro superadmin: sin ella no hay por\n"
                "  dónde empezar. Los demás que aparezcan acá hay que mirarlos antes de tocarles\n"
                "  el rol."
            )

        if matriz.pendientes:
            self.stdout.write("")
            self.stdout.write(self.style.MIGRATE_HEADING("Pendientes de la matriz"))
            for linea in matriz.pendientes:
                self.stdout.write(f"  {linea}")

    def _perfil_de(self, entrada):
        return PerfilUsuario.objects.select_related("sucursal").filter(
            user__username=entrada.username
        ).first()

    def _usuarios_fuera_de_la_matriz(self, matriz):
        """Todo perfil que no es de la matriz, sin excepciones.

        `admin` se muestra a propósito: quedó con superadmin para poder dar de
        alta a los directivos, y esconderlo haría que el informe dijera que
        no hay nadie más cuando sí lo hay.
        """
        nombres = {entrada.username for entrada in matriz.entradas}
        return list(
            PerfilUsuario.objects.select_related("user", "sucursal")
            .exclude(user__username__in=nombres)
            .order_by("user__username")
        )