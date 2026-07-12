from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from .models import Alumno, CajaDiaria, CarreraCurso, ConceptoCobrable, Cuota, Matricula, MovimientoCaja, Pago, PerfilUsuario, Sucursal


class SucursalSeedTests(TestCase):
    def test_seed_creates_posadas_and_eldorado(self):
        call_command("seed_initial_data", verbosity=0)

        self.assertTrue(Sucursal.objects.filter(codigo="POS", nombre="Posadas").exists())
        self.assertTrue(Sucursal.objects.filter(codigo="ELD", nombre="Eldorado").exists())

    def test_seed_creates_initial_admin_with_profile(self):
        call_command("seed_initial_data", verbosity=0)

        admin = User.objects.get(username="admin")

        self.assertTrue(admin.is_staff)
        self.assertEqual(admin.perfil.rol, PerfilUsuario.Rol.ADMINISTRACION)
        self.assertTrue(admin.perfil.puede_ver_todas_las_sucursales)

    def test_seed_creates_demo_catalogs_and_students(self):
        call_command("seed_initial_data", verbosity=0)

        self.assertGreaterEqual(CarreraCurso.objects.count(), 2)
        self.assertGreaterEqual(ConceptoCobrable.objects.count(), 2)
        self.assertGreaterEqual(Alumno.objects.count(), 3)


class ModeloBaseTests(TestCase):
    def test_alumno_belongs_to_sucursal_and_has_estado(self):
        sucursal = Sucursal.objects.create(codigo="POS", nombre="Posadas")
        alumno = Alumno.objects.create(
            legajo="A-001",
            nombre="Ana",
            apellido="Gomez",
            dni="30111222",
            email="ana@example.com",
            telefono="3764000000",
            sucursal=sucursal,
        )

        self.assertEqual(str(alumno), "Gomez, Ana")
        self.assertEqual(alumno.estado, Alumno.Estado.ACTIVO)

    def test_concepto_can_be_limited_to_carrera(self):
        sucursal = Sucursal.objects.create(codigo="ELD", nombre="Eldorado")
        carrera = CarreraCurso.objects.create(nombre="Auxiliar administrativo", sucursal=sucursal)
        concepto = ConceptoCobrable.objects.create(
            nombre="Matricula 2026",
            tipo=ConceptoCobrable.Tipo.MATRICULA,
            importe=50000,
            sucursal=sucursal,
            carrera=carrera,
        )

        self.assertEqual(str(concepto), "Matricula 2026")
        self.assertEqual(concepto.carrera, carrera)


class ApiInicialTests(APITestCase):
    def setUp(self):
        self.posadas = Sucursal.objects.create(codigo="POS", nombre="Posadas")
        self.eldorado = Sucursal.objects.create(codigo="ELD", nombre="Eldorado")
        self.admin = User.objects.create_user("admin", password="admin123")
        PerfilUsuario.objects.create(
            user=self.admin,
            rol=PerfilUsuario.Rol.ADMINISTRACION,
            sucursal=self.posadas,
            puede_ver_todas_las_sucursales=True,
        )
        self.cajero = User.objects.create_user("cajero", password="cajero123")
        PerfilUsuario.objects.create(
            user=self.cajero,
            rol=PerfilUsuario.Rol.CAJA,
            sucursal=self.posadas,
        )
        Alumno.objects.create(
            legajo="P-001",
            nombre="Pedro",
            apellido="Perez",
            dni="22111222",
            sucursal=self.posadas,
        )
        Alumno.objects.create(
            legajo="E-001",
            nombre="Elena",
            apellido="Silva",
            dni="23111222",
            sucursal=self.eldorado,
        )
        CarreraCurso.objects.create(nombre="Secretariado", sucursal=self.posadas)
        ConceptoCobrable.objects.create(
            nombre="Cuota mensual",
            tipo=ConceptoCobrable.Tipo.CUOTA,
            importe=25000,
            sucursal=self.posadas,
        )

    def test_login_and_current_user(self):
        client = APIClient()

        response = client.post("/api/auth/login/", {"username": "admin", "password": "admin123"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("key", response.data)

        client.credentials(HTTP_AUTHORIZATION=f"Token {response.data['key']}")
        me = client.get("/api/auth/me/")

        self.assertEqual(me.status_code, status.HTTP_200_OK)
        self.assertEqual(me.data["username"], "admin")
        self.assertEqual(me.data["perfil"]["rol"], PerfilUsuario.Rol.ADMINISTRACION)

    def test_unauthenticated_api_requests_are_rejected(self):
        response = self.client.get("/api/alumnos/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_without_global_access_only_sees_own_sucursal_students(self):
        self.client.force_authenticate(user=self.cajero)

        response = self.client.get("/api/alumnos/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["legajo"] for item in response.data["results"]], ["P-001"])

    def test_admin_can_list_initial_catalogs(self):
        self.client.force_authenticate(user=self.admin)

        sucursales = self.client.get("/api/sucursales/")
        carreras = self.client.get("/api/carreras/")
        conceptos = self.client.get("/api/conceptos/")

        self.assertEqual(sucursales.status_code, status.HTTP_200_OK)
        self.assertEqual(carreras.status_code, status.HTTP_200_OK)
        self.assertEqual(conceptos.status_code, status.HTTP_200_OK)
        self.assertEqual(sucursales.data["count"], 2)
        self.assertEqual(carreras.data["count"], 1)
        self.assertEqual(conceptos.data["count"], 1)

    def test_authenticated_user_can_update_student(self):
        self.client.force_authenticate(user=self.admin)
        alumno = Alumno.objects.get(legajo="P-001")

        response = self.client.patch(
            f"/api/alumnos/{alumno.id}/",
            {"telefono": "3764555010", "email": "pedro.actualizado@example.com"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        alumno.refresh_from_db()
        self.assertEqual(alumno.telefono, "3764555010")
        self.assertEqual(alumno.email, "pedro.actualizado@example.com")

    def test_authenticated_user_can_register_payment_for_student(self):
        self.client.force_authenticate(user=self.admin)
        alumno = Alumno.objects.get(legajo="P-001")
        concepto = ConceptoCobrable.objects.get(nombre="Cuota mensual", sucursal=self.posadas)

        response = self.client.post(
            "/api/pagos/",
            {
                "alumno": alumno.id,
                "concepto": concepto.id,
                "importe": "25000.00",
                "medio": Pago.Medio.EFECTIVO,
                "observacion": "Pago de prueba",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Pago.objects.count(), 1)
        self.assertEqual(response.data["alumno_nombre"], "Perez, Pedro")

    def test_payment_list_can_be_filtered_by_student(self):
        self.client.force_authenticate(user=self.admin)
        pedro = Alumno.objects.get(legajo="P-001")
        elena = Alumno.objects.get(legajo="E-001")
        concepto = ConceptoCobrable.objects.get(nombre="Cuota mensual", sucursal=self.posadas)
        Pago.objects.create(
            alumno=pedro,
            concepto=concepto,
            sucursal=self.posadas,
            importe=25000,
            medio=Pago.Medio.EFECTIVO,
        )
        Pago.objects.create(
            alumno=elena,
            sucursal=self.eldorado,
            importe=12000,
            medio=Pago.Medio.TRANSFERENCIA,
        )

        response = self.client.get(f"/api/pagos/?alumno={pedro.id}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["alumno"], pedro.id)

    def test_get_today_cashbox_creates_open_cashbox(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.get(f"/api/cajas/hoy/?sucursal={self.posadas.id}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["estado"], CajaDiaria.Estado.ABIERTA)
        self.assertEqual(response.data["sucursal"], self.posadas.id)
        self.assertEqual(CajaDiaria.objects.count(), 1)

    def test_payment_creates_cash_movement(self):
        self.client.force_authenticate(user=self.admin)
        alumno = Alumno.objects.get(legajo="P-001")
        concepto = ConceptoCobrable.objects.get(nombre="Cuota mensual", sucursal=self.posadas)

        response = self.client.post(
            "/api/pagos/",
            {
                "alumno": alumno.id,
                "concepto": concepto.id,
                "importe": "25000.00",
                "medio": Pago.Medio.EFECTIVO,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        movimiento = MovimientoCaja.objects.get(pago_id=response.data["id"])
        self.assertEqual(movimiento.tipo, MovimientoCaja.Tipo.PAGO)
        self.assertEqual(movimiento.importe, Pago.objects.get(id=response.data["id"]).importe)
        self.assertEqual(movimiento.caja.sucursal, self.posadas)

    def test_can_register_manual_cashbox_movement_and_close_cashbox(self):
        self.client.force_authenticate(user=self.admin)
        caja = self.client.get(f"/api/cajas/hoy/?sucursal={self.posadas.id}").data

        movimiento = self.client.post(
            "/api/movimientos-caja/",
            {
                "caja": caja["id"],
                "tipo": MovimientoCaja.Tipo.EGRESO,
                "medio": Pago.Medio.EFECTIVO,
                "importe": "5000.00",
                "descripcion": "Compra de insumos",
            },
            format="json",
        )
        self.assertEqual(movimiento.status_code, status.HTTP_201_CREATED)

        cierre = self.client.post(
            f"/api/cajas/{caja['id']}/cerrar/",
            {"total_contado": "10000.00"},
            format="json",
        )

        self.assertEqual(cierre.status_code, status.HTTP_200_OK)
        self.assertEqual(cierre.data["estado"], CajaDiaria.Estado.CERRADA)
        self.assertEqual(cierre.data["total_contado"], "10000.00")
        self.assertEqual(cierre.data["total_esperado"], "-5000.00")
        self.assertEqual(cierre.data["diferencia"], "15000.00")

    def test_branch_user_cannot_register_payment_for_other_branch_student(self):
        self.client.force_authenticate(user=self.cajero)
        elena = Alumno.objects.get(legajo="E-001")

        response = self.client.post(
            "/api/pagos/",
            {
                "alumno": elena.id,
                "importe": "12000.00",
                "medio": Pago.Medio.EFECTIVO,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Pago.objects.count(), 0)

    def test_branch_user_cannot_register_movement_in_another_users_cashbox(self):
        self.client.force_authenticate(user=self.admin)
        admin_cashbox = self.client.get(f"/api/cajas/hoy/?sucursal={self.posadas.id}").data

        self.client.force_authenticate(user=self.cajero)
        response = self.client.post(
            "/api/movimientos-caja/",
            {
                "caja": admin_cashbox["id"],
                "tipo": MovimientoCaja.Tipo.EGRESO,
                "medio": Pago.Medio.EFECTIVO,
                "importe": "1000.00",
                "descripcion": "Intento no permitido",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(MovimientoCaja.objects.count(), 0)

    def test_can_enroll_student_and_create_fee(self):
        self.client.force_authenticate(user=self.admin)
        alumno = Alumno.objects.get(legajo="P-001")
        carrera = CarreraCurso.objects.get(nombre="Secretariado")
        concepto = ConceptoCobrable.objects.get(nombre="Cuota mensual")
        hoy = timezone.localdate()

        matricula = self.client.post("/api/matriculas/", {"alumno": alumno.id, "carrera": carrera.id, "fecha_inicio": hoy}, format="json")
        self.assertEqual(matricula.status_code, status.HTTP_201_CREATED)

        cuota = self.client.post("/api/cuotas/", {"alumno": alumno.id, "matricula": matricula.data["id"], "concepto": concepto.id, "periodo": "2026-07", "fecha_emision": hoy, "fecha_vencimiento": hoy, "importe": "25000.00", "descuento": "2000.00", "recargo": "500.00"}, format="json")
        self.assertEqual(cuota.status_code, status.HTTP_201_CREATED)
        self.assertEqual(cuota.data["total"], "23500.00")
        self.assertEqual(cuota.data["saldo"], "23500.00")

    def test_partial_payment_updates_fee_and_keeps_credit_balance(self):
        self.client.force_authenticate(user=self.admin)
        alumno = Alumno.objects.get(legajo="P-001")
        concepto = ConceptoCobrable.objects.get(nombre="Cuota mensual")
        hoy = timezone.localdate()
        cuota = Cuota.objects.create(alumno=alumno, concepto=concepto, sucursal=self.posadas, periodo="2026-07", fecha_emision=hoy, fecha_vencimiento=hoy, importe=25000)

        pago = self.client.post("/api/pagos/", {"alumno": alumno.id, "importe": "30000.00", "medio": Pago.Medio.EFECTIVO}, format="json")
        aplicacion = self.client.post("/api/aplicaciones-pago/", {"pago": pago.data["id"], "cuota": cuota.id, "importe": "10000.00"}, format="json")

        self.assertEqual(aplicacion.status_code, status.HTTP_201_CREATED)
        cuota.refresh_from_db()
        self.assertEqual(cuota.estado, Cuota.Estado.PARCIAL)
        detalle_pago = self.client.get(f"/api/pagos/{pago.data['id']}/")
        self.assertEqual(detalle_pago.data["importe_aplicado"], "10000.00")
        self.assertEqual(detalle_pago.data["saldo_a_favor"], "20000.00")

    def test_payment_receipt_has_stable_number_and_details(self):
        self.client.force_authenticate(user=self.admin)
        alumno = Alumno.objects.get(legajo="P-001")

        pago = self.client.post(
            "/api/pagos/",
            {"alumno": alumno.id, "importe": "12500.00", "medio": Pago.Medio.TRANSFERENCIA},
            format="json",
        )

        self.assertEqual(pago.status_code, status.HTTP_201_CREATED)
        self.assertTrue(pago.data["numero_recibo"].startswith("REC-"))
        recibo = self.client.get(f"/api/pagos/{pago.data['id']}/recibo/")
        self.assertEqual(recibo.status_code, status.HTTP_200_OK)
        self.assertEqual(recibo.data["numero"], pago.data["numero_recibo"])
        self.assertEqual(recibo.data["pago"]["alumno_nombre"], "Perez, Pedro")

    def test_account_statement_returns_real_fees_and_credit(self):
        self.client.force_authenticate(user=self.admin)
        alumno = Alumno.objects.get(legajo="P-001")
        concepto = ConceptoCobrable.objects.get(nombre="Cuota mensual")
        hoy = timezone.localdate()
        cuota = Cuota.objects.create(
            alumno=alumno,
            concepto=concepto,
            sucursal=self.posadas,
            periodo="2026-08",
            fecha_emision=hoy,
            fecha_vencimiento=hoy,
            importe="25000.00",
        )
        pago = Pago.objects.create(
            alumno=alumno,
            sucursal=self.posadas,
            importe="30000.00",
            medio=Pago.Medio.TRANSFERENCIA,
        )
        aplicacion = self.client.post(
            "/api/aplicaciones-pago/",
            {"pago": pago.id, "cuota": cuota.id, "importe": "10000.00"},
            format="json",
        )
        self.assertEqual(aplicacion.status_code, status.HTTP_201_CREATED)

        estado = self.client.get(f"/api/alumnos/{alumno.id}/estado-cuenta/")
        self.assertEqual(estado.status_code, status.HTTP_200_OK)
        self.assertEqual(str(estado.data["resumen"]["saldo_pendiente"]), "15000.00")
        self.assertEqual(str(estado.data["resumen"]["saldo_a_favor"]), "20000.00")
        self.assertEqual(str(estado.data["resumen"]["saldo_neto"]), "-5000.00")

    def test_can_generate_fees_for_multiple_students_once(self):
        self.client.force_authenticate(user=self.admin)
        concepto = ConceptoCobrable.objects.get(nombre="Cuota mensual")
        pedro = Alumno.objects.get(legajo="P-001")
        ana = Alumno.objects.create(
            legajo="P-003",
            nombre="Ana",
            apellido="Lopez",
            dni="24111222",
            sucursal=self.posadas,
        )
        hoy = timezone.localdate()
        payload = {
            "alumnos": [pedro.id, ana.id],
            "concepto": concepto.id,
            "periodo": "2026-09",
            "fecha_emision": hoy,
            "fecha_vencimiento": hoy,
            "importe": "26000.00",
        }

        response = self.client.post("/api/cuotas/generar/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(Cuota.objects.filter(periodo="2026-09").count(), 2)

        repetida = self.client.post("/api/cuotas/generar/", payload, format="json")
        self.assertEqual(repetida.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Cuota.objects.filter(periodo="2026-09").count(), 2)

    def test_operational_report_respects_branch_and_date_range(self):
        self.client.force_authenticate(user=self.admin)
        alumno = Alumno.objects.get(legajo="P-001")
        Pago.objects.create(alumno=alumno, sucursal=self.posadas, importe="12500.00", medio=Pago.Medio.EFECTIVO)

        reporte = self.client.get(
            f"/api/reportes/resumen/?desde={timezone.localdate()}&hasta={timezone.localdate()}&sucursal={self.posadas.id}"
        )
        self.assertEqual(reporte.status_code, status.HTTP_200_OK)
        self.assertEqual(reporte.data["cobranzas"]["cantidad_pagos"], 1)
        self.assertEqual(str(reporte.data["cobranzas"]["total"]), "12500")
        self.assertEqual(str(reporte.data["cobranzas"]["por_medio"][Pago.Medio.EFECTIVO]), "12500")

# Create your tests here.
