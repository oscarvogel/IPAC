from django.contrib.auth.models import User
from rest_framework.test import APITestCase

from core.models import AsistenteConsultaNoResuelta, EventoAuditoria, PerfilUsuario, Sucursal


class AssistantAdminApiTests(APITestCase):
    def setUp(self):
        self.branch = Sucursal.objects.create(codigo="ADM-AI", nombre="Admin AI")
        self.admin = User.objects.create_user(username="ai-admin", password="secret")
        PerfilUsuario.objects.create(
            user=self.admin,
            rol=PerfilUsuario.Rol.ADMINISTRACION,
            sucursal=self.branch,
        )
        self.superadmin = User.objects.create_user(username="ai-super", password="secret")
        PerfilUsuario.objects.create(
            user=self.superadmin,
            rol=PerfilUsuario.Rol.SUPERADMIN,
            sucursal=self.branch,
            puede_ver_todas_las_sucursales=True,
        )
        self.tesoreria = User.objects.create_user(username="ai-tes", password="secret")
        PerfilUsuario.objects.create(
            user=self.tesoreria,
            rol=PerfilUsuario.Rol.TESORERIA,
            sucursal=self.branch,
        )

    def test_admin_can_create_knowledge_article(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            "/api/asistente/conocimiento/",
            {
                "clave": "refinanciar",
                "titulo": "Refinanciar cuotas",
                "modulo": "cobranzas",
                "preguntas_equivalentes": ["como refinancio"],
                "pasos": ["Abrí el estado de cuenta."],
                "roles_permitidos": ["administracion"],
                "activo": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            EventoAuditoria.objects.filter(
                modulo="asistente",
                accion="alta",
            ).exists()
        )

    def test_tesoreria_cannot_manage_knowledge(self):
        self.client.force_authenticate(self.tesoreria)
        response = self.client.get("/api/asistente/conocimiento/")
        self.assertEqual(response.status_code, 403)

    def test_admin_can_read_but_not_patch_notification_config(self):
        self.client.force_authenticate(self.admin)
        self.assertEqual(
            self.client.get("/api/asistente/configuracion/").status_code,
            200,
        )
        self.assertEqual(
            self.client.patch(
                "/api/asistente/configuracion/",
                {"email_habilitado": True},
                format="json",
            ).status_code,
            403,
        )

    def test_superadmin_can_patch_notification_config(self):
        self.client.force_authenticate(self.superadmin)
        response = self.client.patch(
            "/api/asistente/configuracion/",
            {
                "email_habilitado": True,
                "modo_email": "diario",
                "destinatarios": ["oscar@example.com"],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["email_habilitado"])

    def test_restricted_admin_only_sees_unresolved_from_own_branch(self):
        other_branch = Sucursal.objects.create(codigo="OTR-AI", nombre="Otra sede AI")
        AsistenteConsultaNoResuelta.objects.create(
            usuario=self.admin,
            sucursal=self.branch,
            pregunta="Pregunta propia",
            pregunta_normalizada="pregunta propia",
            categoria=AsistenteConsultaNoResuelta.Categoria.NO_DOCUMENTADA,
        )
        AsistenteConsultaNoResuelta.objects.create(
            usuario=self.superadmin,
            sucursal=other_branch,
            pregunta="Pregunta de otra sede",
            pregunta_normalizada="pregunta de otra sede",
            categoria=AsistenteConsultaNoResuelta.Categoria.NO_DOCUMENTADA,
        )

        self.client.force_authenticate(self.admin)
        response = self.client.get("/api/asistente/no-resueltas/")

        self.assertEqual(response.status_code, 200)
        rows = response.data["results"]
        self.assertEqual([row["pregunta"] for row in rows], ["Pregunta propia"])

    def test_rejects_external_knowledge_route(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            "/api/asistente/conocimiento/",
            {
                "clave": "malicioso",
                "titulo": "Malicioso",
                "modulo": "otro",
                "preguntas_equivalentes": ["x"],
                "pasos": ["x"],
                "roles_permitidos": ["administracion"],
                "ruta": "javascript:alert(1)",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
