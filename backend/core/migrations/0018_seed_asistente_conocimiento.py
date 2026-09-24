from django.db import migrations


ARTICLES = [
    {
        "clave": "alta_alumno",
        "titulo": "Dar de alta un alumno",
        "modulo": "alumnos",
        "preguntas_equivalentes": ["dar de alta un alumno", "alta alumno", "nuevo alumno", "crear alumno", "cargar alumno", "agregar alumno"],
        "pasos": [
            "Entrá a Alumnos.",
            "Presioná Nuevo alumno.",
            "Completá como mínimo legajo, nombre, apellido y sucursal. Podés agregar DNI, CUIL, fecha de nacimiento, contacto, domicilio y carrera cuando correspondan.",
            "Guardá el alumno.",
            "Después seleccioná el alumno en el directorio para completar matrícula, cuotas, pagos o consultar su estado de cuenta.",
        ],
        "ruta": "/alumnos?accion=nuevo",
        "action_label": "Abrir Nuevo alumno",
        "roles_permitidos": ["superadmin", "administracion"],
        "notas": ["El legajo debe ser único. Si cargás DNI, también debe ser único.", "Si el botón Nuevo alumno no aparece, revisá el rol del usuario."],
        "orden": 10,
    },
    {
        "clave": "matricular_alumno",
        "titulo": "Matricular un alumno",
        "modulo": "alumnos",
        "preguntas_equivalentes": ["matricular alumno", "crear matricula", "dar de alta matricula", "asignar carrera alumno", "inscribir alumno carrera"],
        "pasos": [
            "Entrá a Alumnos y buscá al alumno por nombre, apellido, DNI o legajo.",
            "Seleccioná el alumno para abrir su ficha.",
            "En el panel de matrículas, elegí la carrera o curso y la fecha de inicio.",
            "Guardá la matrícula.",
            "Verificá que la matrícula activa quede asociada a la carrera correcta antes de generar cuotas.",
        ],
        "ruta": "/alumnos",
        "action_label": "Abrir Alumnos",
        "roles_permitidos": ["superadmin", "administracion"],
        "notas": ["El sistema admite una sola matrícula activa por alumno."],
        "orden": 20,
    },
    {
        "clave": "generar_cuotas",
        "titulo": "Generar cuotas",
        "modulo": "cuotas",
        "preguntas_equivalentes": ["generar cuotas", "generar cuota", "crear cuotas", "crear cuota", "cargar cuotas", "cuotas masivas"],
        "pasos": [
            "Para una cuota individual: entrá a Alumnos, seleccioná el alumno y usá Generar cuota en su ficha.",
            "Elegí el concepto cobrable, período, fechas e importe. Si corresponde, aplicá el tipo de descuento disponible.",
            "Para varias cuotas: en Alumnos usá Generar cuotas masivas.",
            "En la generación masiva filtrá la sucursal/carrera que corresponda y revisá concepto, período, vencimiento e importe antes de confirmar.",
            "Al finalizar, controlá el estado de cuenta del alumno o una muestra de alumnos para verificar los cargos generados.",
        ],
        "ruta": "/alumnos?accion=cuotas-masivas",
        "action_label": "Abrir generación de cuotas",
        "roles_permitidos": ["superadmin", "administracion", "tesoreria"],
        "notas": ["No generes dos veces el mismo concepto/período para el mismo alumno: el backend protege esa combinación.", "La carrera/matrícula debe estar correctamente asignada para evitar cuotas en alumnos equivocados."],
        "orden": 30,
    },
    {
        "clave": "registrar_pago",
        "titulo": "Registrar un pago",
        "modulo": "cobranzas",
        "preguntas_equivalentes": ["registrar pago", "cobrar alumno", "cargar pago", "cobrar cuota", "ingresar pago", "recibir pago"],
        "pasos": [
            "Entrá a Alumnos, buscá al alumno y seleccioná su ficha.",
            "Presioná Registrar pago.",
            "Elegí el modo de aplicación: automático para imputar a deuda pendiente, manual para seleccionar cuotas, o a cuenta cuando no querés imputar a una cuota.",
            "Indicá importe, medio de pago y observación si hace falta.",
            "Confirmá el pago y verificá el recibo/estado de cuenta.",
        ],
        "ruta": "/alumnos",
        "action_label": "Abrir Alumnos",
        "roles_permitidos": ["superadmin", "administracion", "tesoreria", "caja"],
        "notas": ["Si el importe supera la deuda objetivo, el sistema pide confirmar el saldo a favor.", "Los pagos impactan en la caja del usuario/sucursal según el circuito vigente."],
        "orden": 40,
    },
    {
        "clave": "estado_cuenta",
        "titulo": "Consultar el estado de cuenta de un alumno",
        "modulo": "cobranzas",
        "preguntas_equivalentes": ["estado de cuenta", "cuenta corriente alumno", "deuda alumno", "ver cuotas alumno", "saldo alumno"],
        "pasos": [
            "Entrá a Alumnos y buscá al alumno.",
            "Seleccioná su ficha.",
            "Usá Estado de cuenta para ver cuotas, pagos aplicados, saldo pendiente y saldo a favor.",
            "Revisá especialmente cuotas vencidas o parcialmente pagadas antes de registrar un nuevo cobro.",
        ],
        "ruta": "/alumnos",
        "action_label": "Abrir Alumnos",
        "roles_permitidos": ["superadmin", "administracion", "tesoreria", "caja", "consulta"],
        "notas": [],
        "orden": 50,
    },
    {
        "clave": "cerrar_caja",
        "titulo": "Cerrar la caja del día",
        "modulo": "caja",
        "preguntas_equivalentes": ["cerrar caja", "cierre de caja", "cerrar la caja", "como cierro caja", "finalizar caja"],
        "pasos": [
            "Entrá a Caja y revisá los movimientos del día y el efectivo esperado.",
            "Presioná Cerrar caja.",
            "Ingresá el Total contado físicamente.",
            "Definí cuánto efectivo se retira y cuánto se deja como saldo para la próxima apertura.",
            "El importe retirado más el saldo arrastrable debe coincidir con el total contado.",
            "Revisá la diferencia contra el efectivo esperado y confirmá el cierre.",
        ],
        "ruta": "/caja?accion=cerrar",
        "action_label": "Abrir cierre de caja",
        "roles_permitidos": ["superadmin", "administracion", "tesoreria", "caja"],
        "notas": ["Si existe diferencia entre lo esperado y lo contado, el sistema la muestra y la registra en el cierre.", "Transferencias, tarjetas, Mercado Pago y otros medios no forman parte del efectivo físico esperado."],
        "orden": 60,
    },
    {
        "clave": "saldo_anterior_caja",
        "titulo": "Usar saldo del cierre anterior",
        "modulo": "caja",
        "preguntas_equivalentes": ["saldo anterior caja", "saldo inicial caja", "usar saldo anterior", "arrastrar saldo caja"],
        "pasos": ["Entrá a Caja.", "Si hay un saldo disponible del cierre anterior, aparece una franja con el importe y su origen.", "Presioná Usar como saldo inicial.", "Verificá que el saldo inicial de la caja actual se actualice antes de seguir operando."],
        "ruta": "/caja",
        "action_label": "Abrir Caja",
        "roles_permitidos": ["superadmin", "administracion", "tesoreria", "caja"],
        "notas": [],
        "orden": 70,
    },
    {
        "clave": "anular_pago",
        "titulo": "Anular un pago",
        "modulo": "cobranzas",
        "preguntas_equivalentes": ["anular pago", "cancelar pago", "revertir pago", "borrar pago"],
        "pasos": ["Ubicá al alumno y abrí su estado de cuenta.", "Identificá el pago correcto antes de anularlo.", "Usá la acción de anulación e indicá el motivo cuando el sistema lo solicite.", "Confirmá y luego verificá que las cuotas afectadas recuperen el saldo correspondiente y que la reversa quede auditada."],
        "ruta": "/alumnos",
        "action_label": "Abrir Alumnos",
        "roles_permitidos": ["superadmin", "tesoreria"],
        "notas": ["No se elimina físicamente el pago: se conserva la trazabilidad de la anulación."],
        "orden": 80,
    },
    {
        "clave": "importar_datos",
        "titulo": "Importar alumnos, carreras y cursos",
        "modulo": "importacion",
        "preguntas_equivalentes": ["importar datos", "importar excel", "cargar excel", "importar alumnos", "cargar alumnos desde excel"],
        "pasos": ["Entrá a Configuración → Importar datos.", "Descargá o revisá las plantillas disponibles si necesitás validar columnas.", "Seleccioná el archivo CSV o XLSX y ejecutá primero la previsualización.", "Corregí las advertencias o inconsistencias relevantes.", "Confirmá la importación y luego controlá una muestra de alumnos/carreras importados."],
        "ruta": "/importaciones",
        "action_label": "Abrir Importar datos",
        "roles_permitidos": ["superadmin", "administracion"],
        "notas": ["La importación está diseñada para ser idempotente y deduplicar alumnos por DNI o legajo."],
        "orden": 90,
    },
]


def seed_knowledge(apps, schema_editor):
    Article = apps.get_model("core", "AsistenteKnowledgeArticle")
    for data in ARTICLES:
        Article.objects.update_or_create(clave=data["clave"], defaults=data)


def unseed_knowledge(apps, schema_editor):
    Article = apps.get_model("core", "AsistenteKnowledgeArticle")
    Article.objects.filter(clave__in=[item["clave"] for item in ARTICLES]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0017_asistente_fase2_schema"),
    ]

    operations = [
        migrations.RunPython(seed_knowledge, reverse_code=unseed_knowledge),
    ]
