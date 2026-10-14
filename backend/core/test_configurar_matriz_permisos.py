"""Tests del comando `configurar_matriz_permisos`.

El comando no tenía ni un test. Eso es lo que dejó pasar dos cosas:

1. Los usernames quedaron escritos en el `.py`, tomados de un entorno de
   prueba, y en la instalación real el comando falló entero sin tocar nada
   ("NO EXISTE" para los cinco).
2. Aplicaba los permisos que encontraba, comiteaba ese `transaction.atomic`, y
   recién después el informe tiraba el `CommandError`: matriz a medias y salida
   con código de error.

Estos tests fijan las dos cosas. La matriz vive en `config/matriz_permisos.json`
así que acá se exercise con JSON temporales, no con el archivo real: si el
archivo real cambia (aparece una persona nueva), los tests de abajo tienen que
seguir significando algo.
"""

import json
import tempfile
from pathlib import Path

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, TestCase

from core.management.commands.configurar_matriz_permisos import (
    RUTA_POR_DEFECTO,
    cargar_matriz,
)
from core.models import PerfilUsuario, Sucursal

MATRIZ_EJEMPLO = {
    "sucursal_por_defecto": "POS",
    "usuarios": [
        {
            "username": "direccion",
            "rol": "superadmin",
            "alcance": "global",
            "definicion": "Directivo.",
        },
        {
            "username": "administracion",
            "rol": "administracion",
            "alcance": "sucursal",
            "definicion": "Administración.",
        },
        {
            "username": "cajero",
            "rol": "caja",
            "alcance": "sucursal",
            "definicion": "Caja.",
        },
    ],
}


def escribir_matriz(datos):
    """Devuelve la ruta de un JSON temporal con la matriz."""
    directorio = tempfile.mkdtemp(prefix="matriz-")
    ruta = Path(directorio) / "matriz_permisos.json"
    ruta.write_text(json.dumps(datos, ensure_ascii=False), encoding="utf-8")
    return ruta


class ArchivoDeMatrizShippeadoTests(SimpleTestCase):
    """El archivo que va en el repo tiene que ser válido y estar completo."""

    def test_se_lee_sin_argumentos(self):
        matriz = cargar_matriz(RUTA_POR_DEFECTO)
        self.assertTrue(matriz.entradas)
        self.assertEqual(matriz.sucursal_por_defecto, "POS")

    def test_las_cinco_personas_del_acuerdo_estan_con_su_rol(self):
        matriz = cargar_matriz(RUTA_POR_DEFECTO)
        self.assertEqual(
            {entrada.username: (entrada.rol, entrada.alcance) for entrada in matriz.entradas},
            {
                "claudio.rodriguez": ("superadmin", "global"),
                "mario.osten": ("superadmin", "global"),
                "zulma.rodriguez": ("administracion", "sucursal"),
                "laura.acosta": ("administracion", "sucursal"),
                "gerardo.casco": ("caja", "sucursal"),
            },
        )

    def test_gerardo_es_caja_y_no_superadmin(self):
        """La persona con menos permisos es la que más fácil se deja como admin."""
        matriz = cargar_matriz(RUTA_POR_DEFECTO)
        gerardo = next(e for e in matriz.entradas if e.username == "gerardo.casco")
        self.assertEqual(gerardo.rol, PerfilUsuario.Rol.CAJA)
        self.assertFalse(gerardo.todas_las_sucursales)

    def test_los_dos_directivos_ven_ambas_sedes(self):
        """Claudio y Mario Rubén Ostén son los dos directivos del acuerdo."""
        matriz = cargar_matriz(RUTA_POR_DEFECTO)
        directivos = {
            entrada.username for entrada in matriz.entradas if entrada.todas_las_sucursales
        }
        self.assertEqual(directivos, {"claudio.rodriguez", "mario.osten"})


class ValidacionDelArchivoTests(SimpleTestCase):
    """Un JSON mal editado tiene que decir qué está mal, no aceptarlo en silencio."""

    def _con(self, **cambios):
        datos = json.loads(json.dumps(MATRIZ_EJEMPLO))
        datos.update(cambios)
        return escribir_matriz(datos)

    def test_archivo_inexistente(self):
        with self.assertRaisesMessage(CommandError, "No existe el archivo de matriz"):
            cargar_matriz(Path("config/no-existe-esta.json"))

    def test_json_invalido(self):
        ruta = Path(tempfile.mkdtemp()) / "roto.json"
        ruta.write_text("{esto no es json", encoding="utf-8")
        with self.assertRaisesMessage(CommandError, "no es JSON válido"):
            cargar_matriz(ruta)

    def test_falta_la_lista_de_usuarios(self):
        with self.assertRaisesMessage(CommandError, "falta la lista 'usuarios'"):
            cargar_matriz(self._con(usuarios="todos"))

    def test_falta_sucursal_por_defecto(self):
        with self.assertRaisesMessage(CommandError, "falta 'sucursal_por_defecto'"):
            cargar_matriz(self._con(sucursal_por_defecto=""))

    def test_rol_inexistente(self):
        datos = json.loads(json.dumps(MATRIZ_EJEMPLO))
        datos["usuarios"][0]["rol"] = "jefe"
        with self.assertRaisesMessage(CommandError, "que no existe"):
            cargar_matriz(escribir_matriz(datos))

    def test_alcance_inexistente(self):
        datos = json.loads(json.dumps(MATRIZ_EJEMPLO))
        datos["usuarios"][2]["alcance"] = "todo"
        with self.assertRaisesMessage(CommandError, "alcance 'todo'"):
            cargar_matriz(escribir_matriz(datos))

    def test_username_vacio(self):
        datos = json.loads(json.dumps(MATRIZ_EJEMPLO))
        datos["usuarios"][0]["username"] = "  "
        with self.assertRaisesMessage(CommandError, "no tiene 'username'"):
            cargar_matriz(escribir_matriz(datos))

    def test_username_duplicado(self):
        datos = json.loads(json.dumps(MATRIZ_EJEMPLO))
        datos["usuarios"].append(dict(datos["usuarios"][0]))
        with self.assertRaisesMessage(CommandError, "repite el username"):
            cargar_matriz(escribir_matriz(datos))


class BaseAplicacion(TestCase):
    def setUp(self):
        self.posadas = Sucursal.objects.create(codigo="POS", nombre="Posadas")
        self.eldorado = Sucursal.objects.create(codigo="ELD", nombre="Eldorado")

    def _usuario(self, username, rol=PerfilUsuario.Rol.CONSULTA, sucursal=None, todas=False):
        user = User.objects.create_user(username, password="clave123")
        perfil = PerfilUsuario.objects.create(
            user=user,
            rol=rol,
            sucursal=sucursal or self.posadas,
            puede_ver_todas_las_sucursales=todas,
        )
        return perfil


class AplicarMatrizTests(BaseAplicacion):
    def test_asigna_rol_y_alcance(self):
        self._usuario("direccion")
        admin = self._usuario("administracion", sucursal=self.eldorado)
        cajero = self._usuario("cajero", todas=True)

        call_command("configurar_matriz_permisos", "--aplicar", "--matriz", escribir_matriz(MATRIZ_EJEMPLO))

        admin.refresh_from_db()
        cajero.refresh_from_db()
        self.assertEqual(admin.rol, PerfilUsuario.Rol.ADMINISTRACION)
        self.assertFalse(admin.puede_ver_todas_las_sucursales)
        self.assertEqual(admin.sucursal_id, self.posadas.id)
        self.assertEqual(cajero.rol, PerfilUsuario.Rol.CAJA)
        self.assertFalse(cajero.puede_ver_todas_las_sucursales)

    def test_el_directivo_conserva_el_alcance_global(self):
        self._usuario("direccion", sucursal=self.eldorado)
        self._usuario("administracion")
        self._usuario("cajero")
        call_command(
            "configurar_matriz_permisos",
            "--aplicar",
            "--matriz",
            escribir_matriz(MATRIZ_EJEMPLO),
        )
        self.assertEqual(
            PerfilUsuario.objects.get(user__username="direccion").puede_ver_todas_las_sucursales,
            True,
        )

    def test_es_idempotente(self):
        self._usuario("direccion")
        self._usuario("administracion")
        self._usuario("cajero")
        ruta = escribir_matriz(MATRIZ_EJEMPLO)

        call_command("configurar_matriz_permisos", "--aplicar", "--matriz", ruta)
        antes = list(PerfilUsuario.objects.values_list("user__username", "rol", "sucursal_id"))

        call_command("configurar_matriz_permisos", "--aplicar", "--matriz", ruta)
        despues = list(PerfilUsuario.objects.values_list("user__username", "rol", "sucursal_id"))

        self.assertEqual(antes, despues)

    def test_sin_aplicar_no_toca_nada(self):
        cajero = self._usuario("cajero", todas=True)
        self._usuario("direccion")
        self._usuario("administracion", PerfilUsuario.Rol.SUPERADMIN, todas=True)
        call_command(
            "configurar_matriz_permisos",
            "--matriz",
            escribir_matriz(MATRIZ_EJEMPLO),
        )
        cajero.refresh_from_db()
        self.assertEqual(cajero.rol, PerfilUsuario.Rol.CONSULTA)
        self.assertTrue(cajero.puede_ver_todas_las_sucursales)


class UsuarioFaltanteTests(BaseAplicacion):
    """El caso que rompió en producción.

    Faltan usuarios de la matriz. La versión anterior aplicaba los que
    encontraba, comiteaba, y después tiraba el error. Ahora no se aplica nada.
    """

    def setUp(self):
        super().setUp()
        self._usuario("direccion")
        self._usuario("cajero", todas=True)
        # "administracion" no existe a propósito.

    def test_falla_con_el_nombre_de_los_faltantes(self):
        with self.assertRaisesMessage(CommandError, "Faltan usuarios de la matriz: administracion"):
            call_command("configurar_matriz_permisos", "--aplicar", "--matriz", escribir_matriz(MATRIZ_EJEMPLO))

    def test_no_aplica_nada_a_partir_de_uno_que_falta(self):
        """El que sí existe tiene que seguir como estaba, no a medias."""
        with self.assertRaises(CommandError):
            call_command(
                "configurar_matriz_permisos",
                "--aplicar",
                "--matriz",
                escribir_matriz(MATRIZ_EJEMPLO),
            )

        direccion = PerfilUsuario.objects.get(user__username="direccion")
        cajero = PerfilUsuario.objects.get(user__username="cajero")
        self.assertEqual(direccion.rol, PerfilUsuario.Rol.CONSULTA)
        self.assertFalse(direccion.puede_ver_todas_las_sucursales)
        self.assertEqual(cajero.rol, PerfilUsuario.Rol.CONSULTA)
        self.assertTrue(cajero.puede_ver_todas_las_sucursales)

    def test_el_error_dice_que_no_se_aplico_nada(self):
        with self.assertRaisesMessage(CommandError, "No se aplicó nada"):
            call_command("configurar_matriz_permisos", "--aplicar", "--matriz", escribir_matriz(MATRIZ_EJEMPLO))


class InformeTests(BaseAplicacion):
    def test_lista_a_los_usuarios_que_no_estan_en_la_matriz(self):
        self._usuario("direccion")
        self._usuario("administracion")
        self._usuario("cajero")
        self._usuario("admin")
        self._usuario("otro.superadmin", PerfilUsuario.Rol.SUPERADMIN, todas=True)

        salida = self._correr()
        fuera = salida.split("Usuarios que no están en la matriz")[1]
        self.assertIn("admin", fuera)
        self.assertIn("otro.superadmin", fuera)
        # Los de la matriz ya salen arriba; repetirlos acá confunde el informe.
        self.assertNotIn("direccion", fuera)
        self.assertNotIn("cajero", fuera)

    def test_marca_cuando_un_rol_no_coincide(self):
        self._usuario("direccion")
        self._usuario("administracion")
        self._usuario("cajero")

        salida = self._correr()
        self.assertIn("DIFIERE de la matriz", salida)

    def test_muestra_los_pendientes_de_la_matriz(self):
        datos = json.loads(json.dumps(MATRIZ_EJEMPLO))
        datos["pendientes"] = ["Falta definir el segundo directivo."]
        for username in ("direccion", "administracion", "cajero"):
            self._usuario(username)

        salida = self._correr(escribir_matriz(datos))
        self.assertIn("Pendientes de la matriz", salida)
        self.assertIn("Falta definir el segundo directivo.", salida)

    def _correr(self, ruta=None):
        from io import StringIO

        salida = StringIO()
        call_command(
            "configurar_matriz_permisos",
            "--matriz", ruta or escribir_matriz(MATRIZ_EJEMPLO),
            stdout=salida,
        )
        return salida.getvalue()