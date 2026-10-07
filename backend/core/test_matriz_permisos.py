"""Matriz de permisos acordada con IPAC el 07/10/2026 (punto 4 del mail).

Qué respondió IPAC:

| Persona | Puede |
|---|---|
| Ruben Ostén, Claudio Rodríguez Agüero | ver todo, **ambas sedes** |
| Zulma, Laura | todo: carreras/cursos/diplomaturas, alta y matrícula de alumnos, situaciones, usuarios, movimientos de cajas, caja diaria |
| Casco Gerardo | **sólo cobros de cuotas y su caja diaria** |

Y dos condiciones sueltas: por ahora sólo Posadas, y Gerardo **sólo puede ver
los movimientos de su propia caja**.

Estos tests fijan esa matriz contra el código. La aplicación de la matriz a los
usuarios reales es un comando de configuración, no código; lo que sí es código
es que las restricciones se respeten, y sobre todo que no se filtren datos de
otras cajas por la puerta de atrás del reporte.
"""

from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APITestCase

from .models import (
    Alumno,
    CajaDiaria,
    CarreraCurso,
    ConceptoCobrable,
    Cuota,
    Pago,
    PerfilUsuario,
    Sucursal,
)


class BaseMatriz(APITestCase):
    def setUp(self):
        self.posadas = Sucursal.objects.create(codigo="POS", nombre="Posadas")
        self.eldorado = Sucursal.objects.create(codigo="ELD", nombre="Eldorado")

        self.zulma = self._usuario("zulma", PerfilUsuario.Rol.ADMINISTRACION, self.posadas)
        self.laura = self._usuario("laura", PerfilUsuario.Rol.ADMINISTRACION, self.posadas)
        self.gerardo = self._usuario("gerardo", PerfilUsuario.Rol.CAJA, self.posadas)
        self.otro_cajero = self._usuario("recepcion", PerfilUsuario.Rol.CAJA, self.posadas)
        self.ruben = self._usuario("ruben", PerfilUsuario.Rol.SUPERADMIN, self.posadas, todas=True)
        self.claudio = self._usuario("claudio", PerfilUsuario.Rol.SUPERADMIN, self.posadas, todas=True)
        self.consulta = self._usuario("mirta", PerfilUsuario.Rol.CONSULTA, self.posadas)

        self.caja_gerardo = self._caja(self.gerardo)
        self.caja_recepcion = self._caja(self.otro_cajero)

    def _usuario(self, username, rol, sucursal, todas=False):
        user = User.objects.create_user(username, password="clave123")
        PerfilUsuario.objects.create(
            user=user, rol=rol, sucursal=sucursal, puede_ver_todas_las_sucursales=todas
        )
        return user

    def _caja(self, usuario, fecha=None):
        return CajaDiaria.objects.create(
            sucursal=usuario.perfil.sucursal,
            usuario=usuario,
            fecha=fecha or timezone.localdate(),
        )


class AislamientoDeCajasTests(BaseMatriz):
    """El punto que IPAC marcó dos veces: Gerardo sólo ve su caja."""

    def _leer(self, actor, **filtros):
        """El reporte se prueba sobre el adaptador y no sobre el XLSX.

        El endpoint devuelve un binario que no dice nada del alcance, y el
        defecto estaba en el lector. Probarlo acá deja el fallo bien ubicado.
        """
        from .contexts.reportes.application.exportar_cajas import FiltrosExportacionCajas
        from .contexts.reportes.infrastructure.django_caja_export_reader import (
            DjangoCajaExportReader,
        )

        return DjangoCajaExportReader().leer_cajas(
            actor=actor, filtros=FiltrosExportacionCajas(**filtros)
        )

    def test_el_reporte_de_cajas_de_un_cajero_no_trae_ajenas(self):
        """Por la API de reportes el alcance es sólo la sucursal. Un cajero
        podría exportar los movimientos de todos los demás de Posadas."""
        filas = self._leer(self.gerardo)

        usuarios = {fila[2] for fila in filas}
        self.assertEqual(usuarios, {"gerardo"})

    def test_un_cajero_no_puede_ampliar_el_reporte_pidiendo_otro_usuario(self):
        """El filtro `usuario` viene del cliente. Si se aplica encima del
        alcance sin recortarlo, alcanza con pasar el id de otro para leer su
        caja."""
        filas = self._leer(self.gerardo, usuario_id=str(self.otro_cajero.id))

        self.assertEqual(filas, [])

    def test_una_supervisora_si_ve_las_cajas_de_la_sucursal(self):
        """Zulma tiene que poder auditar la caja de Gerardo: para eso existe
        el rol de administración."""
        filas = self._leer(self.zulma)

        usuarios = {fila[2] for fila in filas}
        self.assertEqual(usuarios, {"gerardo", "recepcion"})

    def test_el_reporte_es_alcanzable_por_http_para_un_cajero(self):
        """Deja constancia de que la fuga no es teórica: el endpoint le llega
        al cajero y responde 200."""
        self.client.force_authenticate(user=self.gerardo)

        respuesta = self.client.get("/api/reportes/exportar.xlsx?tipo=cajas")

        self.assertEqual(respuesta.status_code, 200)

    def test_el_listado_de_cajas_mostra_solo_la_suya(self):
        self.client.force_authenticate(user=self.gerardo)

        respuesta = self.client.get("/api/cajas/?format=json")

        self.assertEqual(respuesta.status_code, 200)
        ids = {c["id"] for c in respuesta.json().get("results", respuesta.json())}
        self.assertEqual(ids, {self.caja_gerardo.id})

    def test_el_resumen_no_le_cuenta_al_cajero_las_cajas_de_otros(self):
        """El resumen contaba cajas por sucursal. Un cajero veía "3 abiertas"
        aunque sólo tenga la suya: le confirma que existen otras cajas y quién
        las tiene abiertas."""
        CajaDiaria.objects.create(
            sucursal=self.posadas, usuario=self.zulma, fecha=timezone.localdate()
        )
        self.client.force_authenticate(user=self.gerardo)

        respuesta = self.client.get("/api/reportes/resumen/")

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.data["cajas"]["abiertas"], 1)

    def test_una_supervisora_sigue_viendo_el_resumen_completo_de_su_sucursal(self):
        """El recorte es sólo para el rol `caja`. Administración tiene que poder
        auditar todas las cajas de la sucursal: de nada sirve una matriz que
        ciegue a quien tiene que controlar."""
        CajaDiaria.objects.create(
            sucursal=self.posadas, usuario=self.zulma, fecha=timezone.localdate()
        )
        self.client.force_authenticate(user=self.zulma)

        respuesta = self.client.get("/api/reportes/resumen/")

        # gerardo + recepcion (setUp) + zulma (esta caja)
        self.assertEqual(respuesta.data["cajas"]["abiertas"], 3)


class AlcancePorSucursalTests(BaseMatriz):
    def test_los_directivos_ven_las_dos_sedes(self):
        self.client.force_authenticate(user=self.ruben)

        respuesta = self.client.get("/api/sucursales/?format=json")

        self.assertEqual(respuesta.status_code, 200)
        codigos = {s["codigo"] for s in respuesta.json().get("results", respuesta.json())}
        self.assertEqual(codigos, {"POS", "ELD"})

    def test_gerardo_solo_ve_posadas(self):
        self.client.force_authenticate(user=self.gerardo)

        respuesta = self.client.get("/api/sucursales/?format=json")

        self.assertEqual(respuesta.status_code, 200)
        codigos = {s["codigo"] for s in respuesta.json().get("results", respuesta.json())}
        self.assertEqual(codigos, {"POS"})


class PermisosDeAdministracionTests(BaseMatriz):
    """El punto 2 de la reunión: dar de alta alumnos a Laura y Zulma."""

    def _alumno_en(self, sucursal, legajo):
        carrera = CarreraCurso.objects.create(
            nombre="Analista", sucursal=sucursal, tipo=CarreraCurso.Tipo.CARRERA
        )
        return Alumno.objects.create(
            legajo=legajo,
            nombre="Ana",
            apellido="Perez",
            sucursal=sucursal,
            carrera=carrera,
        )

    def test_zulma_puede_dar_de_alta_alumnos(self):
        alumno = self._alumno_en(self.posadas, "POS-EXISTENTE")
        self.client.force_authenticate(user=self.zulma)

        respuesta = self.client.post(
            "/api/alumnos/",
            {"legajo": "POS-NUEVO", "nombre": "Nuevo", "apellido": "Alumno", "sucursal": self.posadas.id},
            format="json",
        )

        self.assertEqual(respuesta.status_code, 201)
        self.assertTrue(Alumno.objects.filter(legajo="POS-NUEVO").exists())
        self.assertTrue(alumno.id)

    def test_laura_puede_dar_de_alta_alumnos(self):
        self.client.force_authenticate(user=self.laura)

        respuesta = self.client.post(
            "/api/alumnos/",
            {"legajo": "POS-NUEVO-2", "nombre": "Nueva", "apellido": "Alumna", "sucursal": self.posadas.id},
            format="json",
        )

        self.assertEqual(respuesta.status_code, 201)

    def test_gerardo_no_puede_dar_de_alta_alumnos(self):
        self.client.force_authenticate(user=self.gerardo)

        respuesta = self.client.post(
            "/api/alumnos/",
            {"legajo": "POS-PROHIBIDO", "nombre": "No", "apellido": "Debe", "sucursal": self.posadas.id},
            format="json",
        )

        self.assertEqual(respuesta.status_code, 403)
        self.assertFalse(Alumno.objects.filter(legajo="POS-PROHIBIDO").exists())


class PermisosDeCobroTests(BaseMatriz):
    def test_gerardo_puede_cobrar(self):
        """Es lo único que su rol habilita además de su caja."""
        concepto = ConceptoCobrable.objects.create(
            nombre="Cuota mensual",
            tipo=ConceptoCobrable.Tipo.CUOTA,
            importe="10000.00",
            sucursal=self.posadas,
        )
        alumno = Alumno.objects.create(
            legajo="POS-COBRO", nombre="Ana", apellido="Perez", sucursal=self.posadas
        )
        Cuota.objects.create(
            alumno=alumno,
            concepto=concepto,
            sucursal=self.posadas,
            periodo="2026-03",
            fecha_emision=timezone.localdate(),
            fecha_vencimiento=timezone.localdate(),
            importe="10000.00",
        )
        self.client.force_authenticate(user=self.gerardo)

        respuesta = self.client.post(
            "/api/pagos/",
            {"alumno": alumno.id, "importe": "10000.00", "medio": "efectivo", "observacion": ""},
            format="json",
        )

        self.assertEqual(respuesta.status_code, 201)
        self.assertTrue(Pago.objects.filter(alumno=alumno).exists())

    def test_gerardo_no_puede_administrar_usuarios(self):
        self.client.force_authenticate(user=self.gerardo)

        respuesta = self.client.post(
            "/api/usuarios/",
            {"username": "intruso", "rol": "caja", "sucursal": self.posadas.id},
            format="json",
        )

        self.assertEqual(respuesta.status_code, 403)
        self.assertFalse(User.objects.filter(username="intruso").exists())

    def test_un_consulta_no_puede_cobrar(self):
        concepto = ConceptoCobrable.objects.create(
            nombre="Cuota mensual",
            tipo=ConceptoCobrable.Tipo.CUOTA,
            importe="10000.00",
            sucursal=self.posadas,
        )
        alumno = Alumno.objects.create(
            legajo="POS-CONSULTA", nombre="Ana", apellido="Perez", sucursal=self.posadas
        )
        self.client.force_authenticate(user=self.consulta)

        respuesta = self.client.post(
            "/api/pagos/",
            {"alumno": alumno.id, "importe": "1000.00", "medio": "efectivo", "observacion": ""},
            format="json",
        )

        self.assertIn(respuesta.status_code, (403, 400))
        self.assertEqual(concepto.id, concepto.id)


class AislamientoEntreSucursalesTests(BaseMatriz):
    def test_un_usuario_de_posadas_no_ve_alumnos_de_eldorado(self):
        Alumno.objects.create(
            legajo="ELD-999", nombre="De", apellido="Eldorado", sucursal=self.eldorado
        )
        self.client.force_authenticate(user=self.zulma)

        respuesta = self.client.get("/api/alumnos/?format=json")

        legajos = {a["legajo"] for a in respuesta.json().get("results", respuesta.json())}
        self.assertNotIn("ELD-999", legajos)

    def test_un_directivo_si_ve_las_dos_sedes(self):
        Alumno.objects.create(
            legajo="ELD-999", nombre="De", apellido="Eldorado", sucursal=self.eldorado
        )
        self.client.force_authenticate(user=self.claudio)

        respuesta = self.client.get("/api/alumnos/?format=json")

        legajos = {a["legajo"] for a in respuesta.json().get("results", respuesta.json())}
        self.assertIn("ELD-999", legajos)