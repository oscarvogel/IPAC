from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from django.db import transaction

from core.models import Alumno, CarreraCurso, ConceptoCobrable, Cuota, Pago, Sucursal

from ..infrastructure.xlsx_reader import SpreadsheetReader


MONTHS = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "setiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}


def normalize_text(value) -> str:
    value = "" if value is None else str(value)
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", value).strip().upper()


def clean_identifier(value) -> str:
    value = "" if value is None else str(value).strip()
    if not value:
        return ""
    value = value.replace(",", ".")
    try:
        if re.fullmatch(r"[+-]?\d+(?:\.\d+)?[Ee][+-]?\d+", value):
            value = format(Decimal(value), "f")
        elif re.fullmatch(r"[+-]?\d+\.0+", value):
            value = value.split(".", 1)[0]
    except InvalidOperation:
        pass
    return re.sub(r"\D", "", value)


def parse_decimal(value) -> Decimal | None:
    value = "" if value is None else str(value).strip()
    if not value:
        return None
    value = re.sub(r"[^0-9,.-]", "", value)
    if "," in value and "." in value:
        value = value.replace(".", "").replace(",", ".")
    elif "," in value:
        value = value.replace(",", ".")
    try:
        return Decimal(value)
    except InvalidOperation:
        return None


def parse_integer(value) -> int | None:
    parsed = parse_decimal(value)
    return int(parsed) if parsed is not None and parsed == int(parsed) else None


def parse_date_value(value) -> date | None:
    value = "" if value is None else str(value).strip().lower()
    if not value or value in {"f.n", "n/a", "-"}:
        return None
    value = value.replace("_", "/").replace("-", "/")
    for fmt in ("%Y/%m/%d", "%d/%m/%Y", "%d/%m/%y", "%m/%d/%Y", "%m/%d/%y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            pass
    match = re.search(r"(\d{1,2})\s+de?\s+([a-z]+)(?:\s+del?)?\s+(\d{4})", value)
    if match:
        month = MONTHS.get(match.group(2))
        if month:
            try:
                return date(int(match.group(3)), month, int(match.group(1)))
            except ValueError:
                return None
    return None


def split_full_name(value: str) -> tuple[str, str]:
    value = re.sub(r"\([^)]*\)", "", value or "")
    value = re.sub(r"\s+", " ", value).strip()
    if not value:
        return "", ""
    if "," in value:
        surname, given = value.split(",", 1)
        return surname.strip(), given.strip()
    tokens = value.split()
    if len(tokens) == 1:
        return tokens[0], ""
    if all(token.upper() == token for token in tokens if re.search(r"[A-Za-zÁÉÍÓÚÜÑ]", token)):
        return tokens[0], " ".join(tokens[1:])
    surname_tokens = []
    for token in tokens:
        if token.upper() == token and re.search(r"[A-Za-zÁÉÍÓÚÜÑ]", token):
            surname_tokens.append(token)
        else:
            break
    if surname_tokens:
        return " ".join(surname_tokens), " ".join(tokens[len(surname_tokens):])
    return tokens[0], " ".join(tokens[1:])


@dataclass
class ImportCounters:
    created: int = 0
    updated: int = 0
    skipped: int = 0
    found: int = 0


@dataclass
class ImportResult:
    filename: str
    careers: ImportCounters = field(default_factory=ImportCounters)
    students: ImportCounters = field(default_factory=ImportCounters)
    concepts: ImportCounters = field(default_factory=ImportCounters)
    opening_balances: ImportCounters = field(default_factory=ImportCounters)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def warn(self, message: str):
        if len(self.warnings) < 200:
            self.warnings.append(message)

    def error(self, message: str):
        if len(self.errors) < 200:
            self.errors.append(message)

    def as_dict(self):
        return {
            "archivo": self.filename,
            "carreras": self.careers.__dict__,
            "alumnos": self.students.__dict__,
            "conceptos": self.concepts.__dict__,
            "saldos_iniciales": self.opening_balances.__dict__,
            "advertencias": self.warnings,
            "total_advertencias": len(self.warnings),
            "errores": self.errors,
            "total_errores": len(self.errors),
        }


class IPACWorkbookImporter:
    """Application service for the import use case.

    Spreadsheet parsing is isolated in an infrastructure adapter. This class
    coordinates catalog and student aggregates and keeps the operation atomic.
    """

    def __init__(self, reader=None):
        self.reader = reader or SpreadsheetReader()

    @transaction.atomic
    def import_file(self, source, filename: str, default_branch_code="POS", default_career_name="", allowed_branch_codes=None, persist=True):
        self.allowed_branch_codes = set(allowed_branch_codes or []) or None
        sheets = self.reader.read(source, filename)
        result = ImportResult(filename=filename)
        catalog = self._extract_catalog(sheets)
        if catalog:
            self._import_catalog(catalog, default_branch_code, result, persist=persist)
        students = self._extract_students(sheets)
        if students:
            self._import_students(students, default_branch_code, default_career_name, result, persist=persist)
        concepts = self._extract_concepts(sheets)
        if concepts:
            self._import_concepts(concepts, default_branch_code, result, persist=persist)
        opening_balances = self._extract_opening_balances(sheets)
        if opening_balances:
            self._import_opening_balances(opening_balances, default_branch_code, result, persist=persist)
        if not catalog and not students and not concepts and not opening_balances:
            result.warn("No se encontraron hojas reconocibles de alumnos, carreras, conceptos o saldos iniciales.")
        return result

    def preview_file(self, source, filename: str, default_branch_code="POS", default_career_name="", allowed_branch_codes=None):
        """Analyze using the exact import use case and roll back every write.

        The importer remains the single source of truth for parsing, matching,
        validation and idempotent counters. Its explicit non-persistent mode
        skips all create, save and update operations.
        """
        result = self.import_file(
            source,
            filename,
            default_branch_code=default_branch_code,
            default_career_name=default_career_name,
            allowed_branch_codes=allowed_branch_codes,
            persist=False,
        )
        self._classify_preview_errors(result)
        return result

    @staticmethod
    def _classify_preview_errors(result):
        critical_fragments = (
            "no tiene permiso para cargar",
            "no existe la sucursal",
            "no se encontraron hojas reconocibles",
        )
        for warning in result.warnings:
            if any(fragment in warning.lower() for fragment in critical_fragments):
                result.error(warning)

    def _extract_catalog(self, sheets):
        rows = []
        fees = {}
        for name, matrix in sheets.items():
            normalized = normalize_text(name)
            if "MONTO" in normalized or any("CUOTA PROGRAMATICA" in normalize_text(cell) for row in matrix[:12] for cell in row):
                fees.update(self._extract_fee_rows(matrix))
            elif "CARRERA" in normalized or any("CARRERAS" in normalize_text(cell) for row in matrix[:12] for cell in row):
                rows.extend(self._extract_catalog_rows(matrix))
        for row in rows:
            fee = fees.get(normalize_text(row["nombre"]), {})
            row.update(fee)
        return rows

    def _extract_catalog_rows(self, matrix):
        header_index = next((index for index, row in enumerate(matrix) if "CARRERAS" in {normalize_text(cell) for cell in row} and "CURSOS" in {normalize_text(cell) for cell in row}), None)
        if header_index is None:
            return self._extract_canonical_catalog_rows(matrix)
        result = []
        for values, kind, offset in ((matrix[header_index + 1 :], "carrera", 0), (matrix[header_index + 1 :], "curso", 5)):
            for row in values:
                name = row[offset].strip() if len(row) > offset else ""
                if not name or normalize_text(name) in {"CARRERAS", "CURSOS"}:
                    continue
                result.append({
                    "nombre": name,
                    "tipo": kind,
                    "duracion": row[offset + 1].strip() if len(row) > offset + 1 else "",
                    "plan_cuotas": parse_integer(row[offset + 2]) if len(row) > offset + 2 else None,
                    "importe_matricula": parse_decimal(row[offset + 3]) if len(row) > offset + 3 else None,
                })
        return result

    def _extract_canonical_catalog_rows(self, matrix):
        header_index, headers = self._find_header(matrix, {"NOMBRE"})
        if header_index is None:
            header_index, headers = self._find_header(matrix, {"CARRERA"})
        if header_index is None:
            return []
        result = []
        for row in matrix[header_index + 1 :]:
            item = self._row_dict(headers, row)
            name = item.get("nombre") or item.get("nombre de carrera") or item.get("carrera")
            if not name.strip():
                continue
            result.append({
                "nombre": name.strip(),
                "tipo": normalize_text(item.get("tipo", "carrera")).lower() or "carrera",
                "sucursal_codigo": item.get("sucursal_codigo", "").strip(),
                "duracion": item.get("duracion", "").strip(),
                "plan_cuotas": parse_integer(item.get("plan_cuotas")),
                "importe_matricula": parse_decimal(item.get("importe_matricula")),
                "cuota_programatica": parse_decimal(item.get("cuota_programatica")),
                "cuota_extraprogramatica": parse_decimal(item.get("cuota_extraprogramatica")),
                "cuota_total": parse_decimal(item.get("cuota_total")),
                "cuota_convenio_20": parse_decimal(item.get("cuota_convenio_20")),
                "cuota_convenio_15": parse_decimal(item.get("cuota_convenio_15")),
                "descripcion": item.get("descripcion", "").strip(),
            })
        return result

    def _extract_fee_rows(self, matrix):
        header_index, headers = self._find_header(matrix, {"CARRERAS", "CUOTA PROGRAMATICA"})
        if header_index is None:
            return {}
        result = {}
        for row in matrix[header_index + 1 :]:
            item = self._row_dict(headers, row)
            name = item.get("carreras", "").strip()
            if not name:
                continue
            result[normalize_text(name)] = {
                "cuota_programatica": parse_decimal(item.get("cuota programatica")),
                "cuota_extraprogramatica": parse_decimal(item.get("cuota extraprogramatica")),
                "cuota_total": parse_decimal(item.get("total a pagar x alumno")),
                "cuota_convenio_20": parse_decimal(item.get("total a pagar x alumno 20")),
                "cuota_convenio_15": parse_decimal(item.get("total a pagar por alumno 15")),
            }
        return result

    def _extract_students(self, sheets):
        for name, matrix in sheets.items():
            header_index, headers = self._find_header(matrix, {"APELLIDO Y NOMBRES", "DNI/USUARIO"})
            if header_index is None:
                header_index, headers = self._find_header(matrix, {"APELLIDO", "NOMBRE", "DNI"})
            if header_index is not None:
                default_career = ""
                for row in matrix[:header_index]:
                    text = " ".join(cell.strip() for cell in row if cell.strip())
                    match = re.search(r"(.+?)\s*-\s*ALUMNOS", text, re.I)
                    if match:
                        default_career = match.group(1).strip()
                return {"headers": headers, "rows": matrix[header_index + 1 :], "default_career": default_career}
        return None

    def _extract_concepts(self, sheets):
        result = []
        for name, matrix in sheets.items():
            if "CONCEPTO" not in normalize_text(name):
                continue
            header_index, headers = self._find_header(matrix, {"NOMBRE", "TIPO", "IMPORTE"})
            if header_index is None:
                continue
            for row in matrix[header_index + 1 :]:
                item = self._row_dict(headers, row)
                if item.get("nombre", "").strip():
                    result.append(item)
        return result

    def _extract_opening_balances(self, sheets):
        result = []
        for name, matrix in sheets.items():
            normalized_name = normalize_text(name)
            if "SALDO" not in normalized_name:
                continue
            header_index, headers = self._find_header(matrix, {"TIPO", "IMPORTE"})
            if header_index is None or not any(key in headers for key in {"DNI", "LEGAJO"}):
                continue
            for row in matrix[header_index + 1 :]:
                item = self._row_dict(headers, row)
                if item.get("dni", "").strip() or item.get("legajo", "").strip():
                    result.append(item)
        return result

    @staticmethod
    def _find_header(matrix, required):
        for index, row in enumerate(matrix):
            headers = {normalize_text(cell): column for column, cell in enumerate(row) if str(cell).strip()}
            if all(any(token in header for header in headers) for token in required):
                return index, headers
        return None, {}

    @staticmethod
    def _row_dict(headers, row):
        result = {}
        for header, column in headers.items():
            result[header.lower()] = row[column].strip() if column < len(row) else ""
        return result

    def _import_catalog(self, rows, default_branch_code, result, persist=True):
        for item in rows:
            branch_code = self._branch_code(item.get("sucursal_codigo") or default_branch_code)
            if self.allowed_branch_codes and branch_code not in self.allowed_branch_codes:
                result.warn(f"Carrera omitida: no tiene permiso para cargar la sucursal {branch_code} ({item['nombre']}).")
                result.careers.skipped += 1
                continue
            try:
                branch = Sucursal.objects.get(codigo=branch_code)
            except Sucursal.DoesNotExist:
                result.warn(f"Carrera omitida: no existe la sucursal {branch_code} ({item['nombre']}).")
                result.careers.skipped += 1
                continue
            kind = item.get("tipo", "carrera").lower()
            kind = "curso" if "curso" in kind else "carrera"
            defaults = {
                "descripcion": item.get("descripcion", ""),
                "tipo": kind,
                "duracion": item.get("duracion", ""),
                "plan_cuotas": item.get("plan_cuotas"),
                "importe_matricula": item.get("importe_matricula"),
                "cuota_programatica": item.get("cuota_programatica"),
                "cuota_extraprogramatica": item.get("cuota_extraprogramatica"),
                "cuota_total": item.get("cuota_total"),
                "cuota_convenio_20": item.get("cuota_convenio_20"),
                "cuota_convenio_15": item.get("cuota_convenio_15"),
                "activa": True,
            }
            career = CarreraCurso.objects.filter(nombre=item["nombre"].strip(), sucursal=branch).first()
            created = career is None
            if persist:
                career, created = CarreraCurso.objects.update_or_create(
                    nombre=item["nombre"].strip(), sucursal=branch, defaults=defaults
                )
            if created:
                result.careers.created += 1
            else:
                result.careers.updated += 1
            ciclo = date.today().year
            if persist and career.importe_matricula is not None:
                ConceptoCobrable.objects.update_or_create(
                    nombre=f"Matrícula {ciclo}",
                    sucursal=branch,
                    carrera=career,
                    defaults={"tipo": ConceptoCobrable.Tipo.MATRICULA, "importe": career.importe_matricula, "activo": True},
                )
            if persist and career.cuota_total is not None:
                ConceptoCobrable.objects.update_or_create(
                    nombre=f"Cuota mensual {ciclo}",
                    sucursal=branch,
                    carrera=career,
                    defaults={"tipo": ConceptoCobrable.Tipo.CUOTA, "importe": career.cuota_total, "activo": True},
                )

    def _import_students(self, data, default_branch_code, default_career_name, result, persist=True):
        headers = data["headers"]
        inferred_career = default_career_name or data.get("default_career", "")
        sequence = 0
        seen_keys = set()
        for source_row, row in enumerate(data["rows"], start=1):
            item = self._row_dict(headers, row)
            full_name = item.get("apellido y nombres", "") or item.get("nombre completo", "")
            separate_name = item.get("apellido", "") or item.get("nombre", "")
            if (not full_name.strip() and not separate_name.strip()) or normalize_text(full_name) in {"APELLIDO Y NOMBRES", "NOMBRE"}:
                continue
            sequence += 1
            result.students.found += 1
            branch_code = self._branch_code(item.get("sucursal_codigo", "") or default_branch_code)
            if self.allowed_branch_codes and branch_code not in self.allowed_branch_codes:
                result.warn(f"Alumno omitido en fila {source_row}: no tiene permiso para la sucursal {branch_code}.")
                result.students.skipped += 1
                continue
            try:
                branch = Sucursal.objects.get(codigo=branch_code)
            except Sucursal.DoesNotExist:
                result.warn(f"Alumno omitido en fila {source_row}: no existe la sucursal {branch_code}.")
                result.students.skipped += 1
                continue
            if item.get("apellido") or item.get("nombre"):
                surname = item.get("apellido", "").strip()
                given = item.get("nombre", "").strip()
            else:
                surname, given = split_full_name(full_name)
            dni = clean_identifier(item.get("dni/usuario") or item.get("dni")) or None
            cuil = clean_identifier(item.get("cuil"))
            identity = (dni or f"row:{source_row}", branch_code)
            if identity in seen_keys:
                result.warn(f"Fila {source_row}: registro duplicado en el archivo; se consolidó con el anterior.")
            seen_keys.add(identity)
            birth_raw = item.get("fecha nacim.") or item.get("fecha_nacimiento") or item.get("fecha de nacimiento")
            birth = parse_date_value(birth_raw)
            if (birth_raw or "").strip() and birth is None:
                result.warn(f"Fila {source_row}: no se pudo interpretar la fecha de nacimiento {birth_raw!r}.")
            career_name = item.get("carrera", "").strip() or inferred_career.strip()
            career = self._find_career(career_name, branch) if career_name else None
            if career_name and career is None:
                result.warn(f"Fila {source_row}: no se encontró la carrera/curso {career_name!r}; se importó sin carrera.")
            legajo = item.get("legajo", "").strip() or f"{branch_code}-IMPORT-{sequence:04d}"
            existing = None
            matched_by_dni = False
            if dni:
                existing = Alumno.objects.filter(dni=dni).first()
                matched_by_dni = existing is not None
            if existing is None:
                existing = Alumno.objects.filter(legajo=legajo).first()

            target_branch = branch
            target_career = career
            if existing and matched_by_dni and existing.sucursal_id != branch.id:
                result.warn(
                    f"Fila {source_row}: DNI {dni} ya pertenece a la sucursal {existing.sucursal.codigo}; "
                    f"se conservó esa sucursal. Los traslados deben realizarse explícitamente."
                )
                target_branch = existing.sucursal
                target_career = existing.carrera

            values = {
                "legajo": existing.legajo if existing else legajo,
                "nombre": given or (existing.nombre if existing else "Sin nombre"),
                "apellido": surname or (existing.apellido if existing else "Sin apellido"),
                "dni": dni if dni is not None else (existing.dni if existing else None),
                "cuil": cuil or (existing.cuil if existing else ""),
                "fecha_nacimiento": birth or (existing.fecha_nacimiento if existing else None),
                "email": item.get("direccion de correo") or item.get("email") or (existing.email if existing else ""),
                "telefono": clean_identifier(item.get("whatsapp") or item.get("telefono")) or (existing.telefono if existing else ""),
                "domicilio": item.get("domicilio/chacra/barrio") or item.get("domicilio") or (existing.domicilio if existing else ""),
                "sucursal": target_branch,
                "carrera": target_career or (existing.carrera if existing else None),
                "estado": Alumno.Estado.ACTIVO,
            }
            if existing and dni and existing.dni == dni and any([existing.email and values["email"] and existing.email != values["email"], existing.cuil and values["cuil"] and existing.cuil != values["cuil"]]):
                result.warn(f"Fila {source_row}: DNI {dni} ya existía con datos diferentes; se conservaron los datos más recientes no vacíos.")
            if existing:
                if persist:
                    for field_name, value in values.items():
                        setattr(existing, field_name, value)
                    existing.save()
                result.students.updated += 1
            else:
                if persist:
                    Alumno.objects.create(**values)
                result.students.created += 1

    def _import_concepts(self, rows, default_branch_code, result, persist=True):
        type_map = {
            "MATRICULA": ConceptoCobrable.Tipo.MATRICULA,
            "CUOTA": ConceptoCobrable.Tipo.CUOTA,
            "MATERIAL": ConceptoCobrable.Tipo.MATERIAL,
            "OTRO": ConceptoCobrable.Tipo.OTRO,
        }
        for source_row, item in enumerate(rows, start=2):
            result.concepts.found += 1
            branch_code = self._branch_code(item.get("sucursal_codigo") or default_branch_code)
            if self.allowed_branch_codes and branch_code not in self.allowed_branch_codes:
                result.warn(f"Concepto omitido en fila {source_row}: no tiene permiso para la sucursal {branch_code}.")
                result.concepts.skipped += 1
                continue
            branch = Sucursal.objects.filter(codigo=branch_code).first()
            amount = parse_decimal(item.get("importe"))
            concept_type = type_map.get(normalize_text(item.get("tipo")))
            if not branch or amount is None or amount < 0 or concept_type is None:
                result.warn(f"Concepto omitido en fila {source_row}: revisá sucursal, tipo e importe.")
                result.concepts.skipped += 1
                continue
            career_name = item.get("carrera", "").strip()
            career = self._find_career(career_name, branch) if career_name else None
            if career_name and not career:
                result.warn(f"Concepto omitido en fila {source_row}: no existe la carrera {career_name!r} en {branch.nombre}.")
                result.concepts.skipped += 1
                continue
            lookup = {"nombre": item["nombre"].strip(), "sucursal": branch, "carrera": career}
            existing = ConceptoCobrable.objects.filter(**lookup).first()
            if persist:
                ConceptoCobrable.objects.update_or_create(
                    **lookup,
                    defaults={"tipo": concept_type, "importe": amount, "activo": True},
                )
            if existing:
                result.concepts.updated += 1
            else:
                result.concepts.created += 1

    def _import_opening_balances(self, rows, default_branch_code, result, persist=True):
        for source_row, item in enumerate(rows, start=2):
            result.opening_balances.found += 1
            branch_code = self._branch_code(item.get("sucursal_codigo") or default_branch_code)
            if self.allowed_branch_codes and branch_code not in self.allowed_branch_codes:
                result.warn(f"Saldo inicial omitido en fila {source_row}: no tiene permiso para la sucursal {branch_code}.")
                result.opening_balances.skipped += 1
                continue
            branch = Sucursal.objects.filter(codigo=branch_code).first()
            dni = clean_identifier(item.get("dni"))
            legajo = item.get("legajo", "").strip()
            alumno_query = Alumno.objects.filter(sucursal=branch) if branch else Alumno.objects.none()
            alumno = alumno_query.filter(dni=dni).first() if dni else None
            alumno = alumno or (alumno_query.filter(legajo=legajo).first() if legajo else None)
            amount = parse_decimal(item.get("importe"))
            balance_type = normalize_text(item.get("tipo")).replace(" ", "_")
            balance_date = parse_date_value(item.get("fecha")) or date.today()
            valid_types = {"DEUDA", "SALDO_A_FAVOR", "CREDITO", "CRÉDITO"}
            if not alumno or amount is None or amount <= 0 or balance_type not in valid_types:
                result.warn(f"Saldo inicial omitido en fila {source_row}: revisá alumno, tipo e importe.")
                result.opening_balances.skipped += 1
                continue

            marker = f"SALDO-INICIAL:{balance_date.isoformat()}"
            if balance_type == "DEUDA":
                concept = ConceptoCobrable.objects.filter(
                    nombre="Saldo inicial", sucursal=branch, carrera__isnull=True
                ).first()
                period = f"SALDO-{balance_date:%Y%m%d}"
                existing = bool(concept and Cuota.objects.filter(
                    alumno=alumno, concepto=concept, periodo=period
                ).exists())
                if persist and not existing:
                    concept, _ = ConceptoCobrable.objects.get_or_create(
                        nombre="Saldo inicial", sucursal=branch, carrera=None,
                        defaults={"tipo": ConceptoCobrable.Tipo.OTRO, "importe": Decimal("0"), "activo": True},
                    )
                    Cuota.objects.create(
                        alumno=alumno, concepto=concept, sucursal=branch, periodo=period,
                        fecha_emision=balance_date, fecha_vencimiento=balance_date, importe=amount,
                    )
            else:
                existing = Pago.objects.filter(
                    alumno=alumno, sucursal=branch, medio=Pago.Medio.OTRO,
                    importe=amount, observacion=marker,
                ).exists()
                if persist and not existing:
                    payment = Pago.objects.create(
                        alumno=alumno, sucursal=branch, importe=amount,
                        medio=Pago.Medio.OTRO, observacion=marker,
                    )
                    Pago.objects.filter(pk=payment.pk).update(fecha=balance_date)
            if existing:
                result.opening_balances.updated += 1
            else:
                result.opening_balances.created += 1

    @staticmethod
    def _find_career(name, branch):
        normalized = normalize_text(name)
        return next((career for career in CarreraCurso.objects.filter(sucursal=branch, activa=True) if normalize_text(career.nombre) == normalized), None)

    @staticmethod
    def _branch_code(value):
        normalized = normalize_text(value)
        return {"POSADAS": "POS", "POS": "POS", "ELDORADO": "ELD", "ELD": "ELD"}.get(normalized, str(value).strip().upper() or "POS")
