from unittest import TestCase as UnitTestCase
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from core.models import PerfilUsuario, Sucursal
from core.contexts.identidad.application.consultas_favoritas import ConsultasFavoritas
from core.contexts.identidad.domain.consulta_favorita import FavoritaInvalida, FavoritaNoEncontrada


def caja_config():
    return {"tipo": "pago", "medio": "efectivo", "ordenamiento": "recent"}


def reporte_config(**kwargs):
    return {"seccion": "caja", "periodo": "mes", "desde": "", "hasta": "", "sucursal": None, "medio": "", "usuario": None, **kwargs}


class FakeRepository:
    def __init__(self):
        self.items = {}

    def listar(self, owner, pantalla=None):
        return [item for item in self.items.values() if item.propietario_id == owner and (not pantalla or item.pantalla == pantalla)]

    def obtener(self, owner, id):
        item = self.items.get(id)
        return item if item and item.propietario_id == owner else None

    def guardar(self, item):
        from dataclasses import replace
        if any(other.id != item.id and other.propietario_id == item.propietario_id and other.pantalla == item.pantalla and other.nombre.lower() == item.nombre.lower() for other in self.items.values()):
            raise FavoritaInvalida("Duplicado")
        item = replace(item, id=item.id or len(self.items) + 1)
        self.items[item.id] = item
        return item

    def eliminar(self, owner, id):
        del self.items[id]


class FakeScope:
    available = True

    def validar(self, *args):
        if not self.available:
            raise FavoritaInvalida("Alcance cambió")


class FavoritasApplicationTests(UnitTestCase):
    def setUp(self):
        self.repo, self.scope = FakeRepository(), FakeScope()
        self.caso = ConsultasFavoritas(self.repo, self.scope)

    def test_crud_and_owner_isolation(self):
        item = self.caso.guardar(actor_id=1, datos={"nombre": "  Efectivo  ", "pantalla": "caja", "configuracion": caja_config()})
        self.assertEqual(item.nombre, "Efectivo")
        self.assertEqual(self.caso.listar(actor_id=2), [])
        with self.assertRaises(FavoritaNoEncontrada):
            self.caso.obtener(actor_id=2, id=item.id)
        self.caso.guardar(actor_id=1, id=item.id, datos={"nombre": "Pagos"})
        self.assertEqual(self.caso.obtener(actor_id=1, id=item.id).nombre, "Pagos")
        self.caso.eliminar(actor_id=1, id=item.id)
        self.assertEqual(self.caso.listar(actor_id=1), [])

    def test_invalid_config_owner_and_stale_scope(self):
        for config in [{**caja_config(), "busqueda": "privada"}, {**caja_config(), "tipo": []}]:
            with self.assertRaises(FavoritaInvalida):
                self.caso.guardar(actor_id=1, datos={"nombre": "X", "pantalla": "caja", "configuracion": config})
        with self.assertRaises(FavoritaInvalida):
            self.caso.guardar(actor_id=1, datos={"propietario": 2})
        item = self.caso.guardar(actor_id=1, datos={"nombre": "X", "pantalla": "caja", "configuracion": caja_config()})
        self.scope.available = False
        self.assertEqual(len(self.caso.listar(actor_id=1)), 1)
        with self.assertRaises(FavoritaInvalida):
            self.caso.obtener(actor_id=1, id=item.id)
        self.caso.eliminar(actor_id=1, id=item.id)


class FavoritasAPITests(TestCase):
    def setUp(self):
        self.branch = Sucursal.objects.create(codigo="FAV1", nombre="Favoritas uno")
        self.other_branch = Sucursal.objects.create(codigo="FAV2", nombre="Favoritas dos")
        self.user = self.make_user("favoritas", "administracion", self.branch)
        self.other = self.make_user("otra", "caja", self.branch)
        self.outside = self.make_user("externa", "caja", self.other_branch)
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.url = "/api/consultas-favoritas/"

    def make_user(self, name, role, branch):
        user = User.objects.create_user(name)
        PerfilUsuario.objects.create(user=user, rol=role, sucursal=branch)
        return user

    def create(self, **overrides):
        return self.client.post(self.url, {"nombre": "Mi consulta", "pantalla": "reportes", "configuracion": reporte_config(), **overrides}, format="json")

    def test_crud_persistence_duplicate_and_cross_account(self):
        response = self.create()
        self.assertEqual(response.status_code, 201)
        url = f'{self.url}{response.data["id"]}/'
        fresh = APIClient()
        fresh.force_authenticate(self.user)
        self.assertEqual(len(fresh.get(self.url).data), 1)
        self.assertEqual(self.create(nombre="mi consulta").status_code, 400)
        self.assertEqual(self.client.patch(url, {"nombre": "Renombrada"}, format="json").status_code, 200)
        self.assertEqual(self.client.patch(url, {"propietario": self.other.id}, format="json").status_code, 400)
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(self.url).data, [])
        self.assertEqual(self.create(nombre="Renombrada").status_code, 201)
        for response in [self.client.get(url), self.client.patch(url, {"nombre": "Ajena"}, format="json"), self.client.delete(url)]:
            self.assertEqual(response.status_code, 404)
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.delete(url).status_code, 204)

    def test_scope_changes_block_apply_allow_edit_and_delete(self):
        self.assertEqual(self.create(configuracion=reporte_config(sucursal=self.other_branch.id)).status_code, 400)
        self.assertEqual(self.create(configuracion=reporte_config(usuario=self.outside.id)).status_code, 400)
        response = self.create(configuracion=reporte_config(sucursal=self.branch.id, usuario=self.other.id))
        self.assertEqual(response.status_code, 201)
        url = f'{self.url}{response.data["id"]}/'
        self.other.perfil.sucursal = self.other_branch
        self.other.perfil.save()
        self.assertEqual(self.client.get(url).status_code, 400)
        self.assertEqual(len(self.client.get(self.url).data), 1)
        self.assertEqual(self.client.patch(url, {"configuracion": reporte_config()}, format="json").status_code, 200)
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_role_and_invalid_configuration(self):
        for role in ["superadmin", "administracion", "tesoreria", "caja", "consulta"]:
            self.user.perfil.rol = role
            self.user.perfil.save()
            self.assertEqual(self.create(nombre=role).status_code, 201)
            expected = 201 if role != "consulta" else 400
            self.assertEqual(self.create(nombre=role, pantalla="caja", configuracion=caja_config()).status_code, expected)
            expected = 201 if role in {"superadmin", "administracion", "tesoreria"} else 400
            self.assertEqual(self.create(nombre=role + " cajero", configuracion=reporte_config(usuario=self.other.id)).status_code, expected)
        for config in [reporte_config(periodo="personalizado", desde="2026-09-30", hasta="2026-09-01"), reporte_config(medio="inexistente"), reporte_config(seccion="alumnos", usuario=self.other.id)]:
            self.assertEqual(self.create(configuracion=config).status_code, 400)
        self.assertEqual(self.create(nombre=" ").status_code, 400)

    def test_unauthenticated_and_invalid_payloads(self):
        self.assertEqual(self.client.get(self.url + 'abc/').status_code, 404)
        self.assertEqual(self.client.post(self.url, [], format='json').status_code, 400)
        self.client.force_authenticate(None)
        self.assertIn(self.client.get(self.url).status_code, (401, 403))
