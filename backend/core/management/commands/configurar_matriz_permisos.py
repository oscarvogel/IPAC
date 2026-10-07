"""Matriz de permisos acordada con IPAC el 07/10/2026 y su informe.

Responde al punto 4 del mail del 01/10/2026 y al punto 5 de los próximos pasos
de la reunión del 24/09: *"Informe detallado sobre los permisos asignados a los
diferentes usuarios"*.

Uso:

    python manage.py configurar_matriz_permisos              # informe (sólo lectura)
    python manage.py configurar_matriz_permisos --aplicar    # asigna los roles

Este comando **no crea usuarios**. Las personas se dan de alta desde la pantalla
Usuarios y permisos, que pide la contraseña y la valida. Acá sólo se asigna el
rol y el alcance, que es lo que IPAC definió.

Por qué los errores no son silenciosos: el rol `superadmin` puede crear otros
superadmins y conceder alcance global. Si un nombre de la matriz no existe, no
se lo inventa: lo reporta para que alguien lo cree desde la pantalla.
"""

from dataclasses import dataclass

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from core.models import PerfilUsuario, Sucursal


@dataclass(frozen=True)
class EntradaMatriz:
    username: str
    rol: str
    todas_las_sucursales: bool
    definicion: str


#: Lo que respondió IPAC, palabra por palabra:
#: - Ruben Ostén y Claudio Rodríguez Agüero, directivos: "puede ver todo de
#:   ambas sedes".
#: - Zulma y Laura: carreras/cursos/diplomaturas, alta y matrícula de alumnos,
#:   situaciones, usuarios, movimientos de cajas, caja diaria. "TODAS LAS
#:   FUNCIONES".
#: - Casco Gerardo: "solo realizar cobros de cuotas y su caja diaria", y sólo
#:   puede ver los movimientos de su caja.
#:
#: Los dos directivos van como `superadmin` con alcance global porque es el
#: único rol que hoy ve ambas sedes. Si más adelante IPAC pide gente que *ve*
#: todo pero no *administre* usuarios, eso necesita un rol nuevo, no abusing
#: de superadmin: ver `docs/RESPUESTA_IPAC_2026-10-07.md`.
MATRIZ = (
    EntradaMatriz(
        "ruben",
        PerfilUsuario.Rol.SUPERADMIN,
        True,
        "Directivo: ve todo en ambas sedes.",
    ),
    EntradaMatriz(
        "claudio",
        PerfilUsuario.Rol.SUPERADMIN,
        True,
        "Directivo: ve todo en ambas sedes.",
    ),
    EntradaMatriz(
        "zulma",
        PerfilUsuario.Rol.ADMINISTRACION,
        False,
        "Administración: todo, incluida alta y matrícula de alumnos, usuarios y cajas.",
    ),
    EntradaMatriz(
        "laura",
        PerfilUsuario.Rol.ADMINISTRACION,
        False,
        "Administración: todo, incluida alta y matrícula de alumnos, usuarios y cajas.",
    ),
    EntradaMatriz(
        "gerardo",
        PerfilUsuario.Rol.CAJA,
        False,
        "Caja: sólo cobra cuotas y sólo ve los movimientos de su propia caja.",
    ),
)


class Command(BaseCommand):
    help = "Informa los permisos de cada usuario y, con --aplicar, asigna la matriz de IPAC."

    def add_arguments(self, parser):
        parser.add_argument(
            "--aplicar",
            action="store_true",
            help="Asigna los roles de la matriz en lugar de sólo informar.",
        )
        parser.add_argument(
            "--sucursal",
            default="POS",
            help="Código de sucursal para los usuarios sin alcance global (por defecto POS).",
        )

    def handle(self, *args, **options):
        sucursal = self._sucursal(options["sucursal"])
        if options["aplicar"]:
            self._aplicar(sucursal)
        self._informe(sucursal)

    def _sucursal(self, codigo):
        try:
            return Sucursal.objects.get(codigo=codigo)
        except Sucursal.DoesNotExist:
            raise CommandError(
                f"No existe la sucursal {codigo!r}. "
                f"Disponibles: {', '.join(Sucursal.objects.values_list('codigo', flat=True)) or 'ninguna'}."
            ) from None

    @transaction.atomic
    def _aplicar(self, sucursal):
        for entrada in MATRIZ:
            perfil = self._perfil_de(entrada)
            if perfil is None:
                continue
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

    def _informe(self, sucursal):
        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING("Matriz de permisos de IPAC (07/10/2026)"))
        self.stdout.write("")
        encabezado = f"{'usuario':<12} {'rol':<16} {'sucursal':<10} {'alcance':<18} estado"
        self.stdout.write(encabezado)
        self.stdout.write("-" * len(encabezado))

        faltantes = []
        for entrada in MATRIZ:
            perfil = self._perfil_de(entrada)
            if perfil is None:
                faltantes.append(entrada.username)
                self.stdout.write(f"{entrada.username:<12} {'-':<16} {'-':<10} {'-':<18} NO EXISTE")
                continue
            alcance = "todas las sedes" if perfil.puede_ver_todas_las_sucursales else "su sucursal"
            coincide = perfil.rol == entrada.rol and perfil.puede_ver_todas_las_sucursales == entrada.todas_las_sucursales
            estado = self.style.SUCCESS("coincide") if coincide else self.style.WARNING("DIFIERE de la matriz")
            self.stdout.write(
                f"{entrada.username:<12} {perfil.get_rol_display():<16} "
                f"{perfil.sucursal.codigo:<10} {alcance:<18} {estado}"
            )
            self.stdout.write(f"{'':<12} {entrada.definicion}")

        otros = self._usuarios_fuera_de_la_matriz(sucursal)
        if otros:
            self.stdout.write("")
            self.stdout.write(self.style.MIGRATE_HEADING("Usuarios que no están en la matriz"))
            for perfil in otros:
                alcance = "todas" if perfil.puede_ver_todas_las_sucursales else perfil.sucursal.codigo
                self.stdout.write(f"  {perfil.user.username:<12} {perfil.get_rol_display():<16} {alcance}")
            self.stdout.write("")
            self.stdout.write(
                "  `admin` es la cuenta de arranque que crea el seed. Necesita superadmin porque\n"
                "  sólo un superadmin puede dar de alta a otro superadmin: sin ella no hay por\n"
                "  dónde empezar. Los demás que aparezcan acá hay que mirarlos antes de tocarles\n"
                "  el rol."
            )

        if faltantes:
            self.stdout.write("")
            raise CommandError(
                "Faltan usuarios de la matriz: "
                + ", ".join(faltantes)
                + ". Crealos desde Usuarios y permisos y volvé a correr el comando."
            )

    def _perfil_de(self, entrada):
        try:
            return PerfilUsuario.objects.select_related("sucursal").get(
                user__username=entrada.username
            )
        except PerfilUsuario.DoesNotExist:
            return None

    def _usuarios_fuera_de_la_matriz(self, sucursal):
        """Todo perfil que no es de la matriz, sin excepciones.

        `admin` se muestra a propósito: quedó con superadmin para poder dar de
        alta a los dos directivos, y esconderlo haría que el informe dijera que
        no hay nadie más cuando sí lo hay.
        """
        nombres = {entrada.username for entrada in MATRIZ}
        return list(
            PerfilUsuario.objects.select_related("user", "sucursal")
            .exclude(user__username__in=nombres)
            .order_by("user__username")
        )