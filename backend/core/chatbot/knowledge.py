import re
import unicodedata
from difflib import SequenceMatcher


QUICK_SUGGESTIONS = [
    "¿Cómo doy de alta un alumno?",
    "¿Cómo genero cuotas?",
    "¿Cómo registro un pago?",
    "¿Cómo cierro la caja?",
]


PROCEDURES = {
    "alta_alumno": {
        "title": "Dar de alta un alumno",
        "aliases": [
            "dar de alta un alumno",
            "alta alumno",
            "nuevo alumno",
            "crear alumno",
            "cargar alumno",
            "agregar alumno",
        ],
        "route": "/alumnos?accion=nuevo",
        "action_label": "Abrir Nuevo alumno",
        "permission": "Administración o Superadmin.",
        "steps": [
            "Entrá a Alumnos.",
            "Presioná Nuevo alumno.",
            "Completá como mínimo legajo, nombre, apellido y sucursal. Podés agregar DNI, CUIL, fecha de nacimiento, contacto, domicilio y carrera cuando correspondan.",
            "Guardá el alumno.",
            "Después seleccioná el alumno en el directorio para completar matrícula, cuotas, pagos o consultar su estado de cuenta.",
        ],
        "notes": [
            "El legajo debe ser único. Si cargás DNI, también debe ser único.",
            "Si el botón Nuevo alumno no aparece, revisá el rol del usuario.",
        ],
    },
    "matricular_alumno": {
        "title": "Matricular un alumno",
        "aliases": [
            "matricular alumno",
            "crear matricula",
            "dar de alta matricula",
            "asignar carrera alumno",
            "inscribir alumno carrera",
        ],
        "route": "/alumnos",
        "action_label": "Abrir Alumnos",
        "permission": "Administración o Superadmin.",
        "steps": [
            "Entrá a Alumnos y buscá al alumno por nombre, apellido, DNI o legajo.",
            "Seleccioná el alumno para abrir su ficha.",
            "En el panel de matrículas, elegí la carrera o curso y la fecha de inicio.",
            "Guardá la matrícula.",
            "Verificá que la matrícula activa quede asociada a la carrera correcta antes de generar cuotas.",
        ],
        "notes": [
            "El sistema admite una sola matrícula activa por alumno.",
        ],
    },
    "generar_cuotas": {
        "title": "Generar cuotas",
        "aliases": [
            "generar cuotas",
            "generar cuota",
            "crear cuotas",
            "crear cuota",
            "cargar cuotas",
            "cuotas masivas",
        ],
        "route": "/alumnos?accion=cuotas-masivas",
        "action_label": "Abrir generación de cuotas",
        "permission": "Superadmin, Administración o Tesorería.",
        "steps": [
            "Para una cuota individual: entrá a Alumnos, seleccioná el alumno y usá Generar cuota en su ficha.",
            "Elegí el concepto cobrable, período, fechas e importe. Si corresponde, aplicá el tipo de descuento disponible.",
            "Para varias cuotas: en Alumnos usá Generar cuotas masivas.",
            "En la generación masiva filtrá la sucursal/carrera que corresponda y revisá concepto, período, vencimiento e importe antes de confirmar.",
            "Al finalizar, controlá el estado de cuenta del alumno o una muestra de alumnos para verificar los cargos generados.",
        ],
        "notes": [
            "No generes dos veces el mismo concepto/período para el mismo alumno: el backend protege esa combinación.",
            "La carrera/matrícula debe estar correctamente asignada para evitar cuotas en alumnos equivocados.",
        ],
    },
    "registrar_pago": {
        "title": "Registrar un pago",
        "aliases": [
            "registrar pago",
            "cobrar alumno",
            "cargar pago",
            "cobrar cuota",
            "ingresar pago",
            "recibir pago",
        ],
        "route": "/alumnos",
        "action_label": "Abrir Alumnos",
        "permission": "Superadmin, Administración, Tesorería o Caja.",
        "steps": [
            "Entrá a Alumnos, buscá al alumno y seleccioná su ficha.",
            "Presioná Registrar pago.",
            "Elegí el modo de aplicación: automático para imputar a deuda pendiente, manual para seleccionar cuotas, o a cuenta cuando no querés imputar a una cuota.",
            "Indicá importe, medio de pago y observación si hace falta.",
            "Confirmá el pago y verificá el recibo/estado de cuenta.",
        ],
        "notes": [
            "Si el importe supera la deuda objetivo, el sistema pide confirmar el saldo a favor.",
            "Los pagos impactan en la caja del usuario/sucursal según el circuito vigente.",
        ],
    },
    "estado_cuenta": {
        "title": "Consultar el estado de cuenta de un alumno",
        "aliases": [
            "estado de cuenta",
            "cuenta corriente alumno",
            "deuda alumno",
            "ver cuotas alumno",
            "saldo alumno",
        ],
        "route": "/alumnos",
        "action_label": "Abrir Alumnos",
        "permission": "Disponible para usuarios autenticados con acceso al alumno.",
        "steps": [
            "Entrá a Alumnos y buscá al alumno.",
            "Seleccioná su ficha.",
            "Usá Estado de cuenta para ver cuotas, pagos aplicados, saldo pendiente y saldo a favor.",
            "Revisá especialmente cuotas vencidas o parcialmente pagadas antes de registrar un nuevo cobro.",
        ],
        "notes": [],
    },
    "cerrar_caja": {
        "title": "Cerrar la caja del día",
        "aliases": [
            "cerrar caja",
            "cierre de caja",
            "cerrar la caja",
            "como cierro caja",
            "finalizar caja",
        ],
        "route": "/caja?accion=cerrar",
        "action_label": "Abrir cierre de caja",
        "permission": "Superadmin, Administración, Tesorería o Caja.",
        "steps": [
            "Entrá a Caja y revisá los movimientos del día y el efectivo esperado.",
            "Presioná Cerrar caja.",
            "Ingresá el Total contado físicamente.",
            "Definí cuánto efectivo se retira y cuánto se deja como saldo para la próxima apertura.",
            "El importe retirado más el saldo arrastrable debe coincidir con el total contado.",
            "Revisá la diferencia contra el efectivo esperado y confirmá el cierre.",
        ],
        "notes": [
            "Si existe diferencia entre lo esperado y lo contado, el sistema la muestra y la registra en el cierre.",
            "Transferencias, tarjetas, Mercado Pago y otros medios no forman parte del efectivo físico esperado.",
        ],
    },
    "saldo_anterior_caja": {
        "title": "Usar saldo del cierre anterior",
        "aliases": [
            "saldo anterior caja",
            "saldo inicial caja",
            "usar saldo anterior",
            "arrastrar saldo caja",
        ],
        "route": "/caja",
        "action_label": "Abrir Caja",
        "permission": "Superadmin, Administración, Tesorería o Caja.",
        "steps": [
            "Entrá a Caja.",
            "Si hay un saldo disponible del cierre anterior, aparece una franja con el importe y su origen.",
            "Presioná Usar como saldo inicial.",
            "Verificá que el saldo inicial de la caja actual se actualice antes de seguir operando.",
        ],
        "notes": [],
    },
    "anular_pago": {
        "title": "Anular un pago",
        "aliases": [
            "anular pago",
            "cancelar pago",
            "revertir pago",
            "borrar pago",
        ],
        "route": "/alumnos",
        "action_label": "Abrir Alumnos",
        "permission": "Superadmin o Tesorería.",
        "steps": [
            "Ubicá al alumno y abrí su estado de cuenta.",
            "Identificá el pago correcto antes de anularlo.",
            "Usá la acción de anulación e indicá el motivo cuando el sistema lo solicite.",
            "Confirmá y luego verificá que las cuotas afectadas recuperen el saldo correspondiente y que la reversa quede auditada.",
        ],
        "notes": [
            "No se elimina físicamente el pago: se conserva la trazabilidad de la anulación.",
        ],
    },
    "importar_datos": {
        "title": "Importar alumnos, carreras y cursos",
        "aliases": [
            "importar datos",
            "importar excel",
            "cargar excel",
            "importar alumnos",
            "cargar alumnos desde excel",
        ],
        "route": "/importaciones",
        "action_label": "Abrir Importar datos",
        "permission": "Administración o Superadmin.",
        "steps": [
            "Entrá a Configuración → Importar datos.",
            "Descargá o revisá las plantillas disponibles si necesitás validar columnas.",
            "Seleccioná el archivo CSV o XLSX y ejecutá primero la previsualización.",
            "Corregí las advertencias o inconsistencias relevantes.",
            "Confirmá la importación y luego controlá una muestra de alumnos/carreras importados.",
        ],
        "notes": [
            "La importación está diseñada para ser idempotente y deduplicar alumnos por DNI o legajo.",
        ],
    },
}


STOPWORDS = {
    "a", "al", "como", "de", "del", "el", "en", "la", "las", "lo", "los",
    "me", "para", "por", "que", "se", "un", "una", "y",
}


def normalize_text(value):
    value = unicodedata.normalize("NFD", (value or "").lower())
    value = "".join(char for char in value if unicodedata.category(char) != "Mn")
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _meaningful_tokens(value):
    return [token for token in normalize_text(value).split() if token not in STOPWORDS and len(token) > 2]


def _token_match_score(message, alias):
    message_tokens = _meaningful_tokens(message)
    alias_tokens = _meaningful_tokens(alias)
    if not alias_tokens:
        return 0.0

    hits = 0
    for expected in alias_tokens:
        if any(
            expected == actual or SequenceMatcher(None, expected, actual).ratio() >= 0.78
            for actual in message_tokens
        ):
            hits += 1
    return hits / len(alias_tokens)


def match_procedure(message):
    normalized = normalize_text(message)
    if not normalized:
        return None

    best = None
    best_score = 0.0

    for key, procedure in PROCEDURES.items():
        for alias in procedure["aliases"]:
            normalized_alias = normalize_text(alias)
            if normalized_alias in normalized:
                return key, procedure

            sequence_score = SequenceMatcher(None, normalized, normalized_alias).ratio()
            token_score = _token_match_score(normalized, normalized_alias)
            score = max(sequence_score, token_score)

            if score > best_score:
                best = (key, procedure)
                best_score = score

    return best if best_score >= 0.72 else None


def format_procedure(procedure):
    lines = [procedure["title"], ""]
    for index, step in enumerate(procedure["steps"], start=1):
        lines.append(f"{index}. {step}")

    permission = procedure.get("permission")
    if permission:
        lines.extend(["", f"Permisos: {permission}"])

    notes = procedure.get("notes") or []
    if notes:
        lines.extend(["", "A tener en cuenta:"])
        lines.extend(f"- {note}" for note in notes)

    return "\n".join(lines)


def knowledge_for_prompt():
    blocks = []
    for procedure in PROCEDURES.values():
        block = [procedure["title"]]
        block.extend(f"- {step}" for step in procedure["steps"])
        if procedure.get("notes"):
            block.extend(f"- Nota: {note}" for note in procedure["notes"])
        block.append(f"- Ruta: {procedure['route']}")
        block.append(f"- Permisos: {procedure['permission']}")
        blocks.append("\n".join(block))
    return "\n\n".join(blocks)
