from __future__ import annotations

import csv
import io
import posixpath
import re
import zipfile
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from xml.etree import ElementTree as ET


MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PACKAGE_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
NS = {"m": MAIN_NS, "r": REL_NS, "p": PACKAGE_REL_NS}


def _column_index(cell_reference: str) -> int:
    letters = re.match(r"[A-Z]+", cell_reference.upper())
    if not letters:
        return 0
    result = 0
    for letter in letters.group(0):
        result = result * 26 + ord(letter) - ord("A") + 1
    return result - 1


def _serial_to_date(value: str) -> str:
    try:
        serial = Decimal(value)
        return (datetime(1899, 12, 30) + timedelta(days=float(serial))).date().isoformat()
    except (InvalidOperation, ValueError, OverflowError):
        return value


class SpreadsheetReader:
    """Read the small XLSX/CSV surface needed by the import use case.

    It deliberately returns plain strings and matrices so the application layer
    does not depend on Excel, Django or an ORM-specific workbook abstraction.
    """

    date_format_ids = {14, 15, 16, 17, 22}

    def read(self, source, filename: str | None = None) -> dict[str, list[list[str]]]:
        filename = filename or getattr(source, "name", "") or "archivo.xlsx"
        data = source.read() if hasattr(source, "read") else source
        if hasattr(source, "seek"):
            source.seek(0)
        if filename.lower().endswith(".csv"):
            text = data.decode("utf-8-sig")
            try:
                dialect = csv.Sniffer().sniff(text[:4096], delimiters=";,\t")
            except csv.Error:
                dialect = csv.excel
            return {"Alumnos": list(csv.reader(io.StringIO(text), dialect))}
        return self._read_xlsx(data)

    def _read_xlsx(self, data: bytes) -> dict[str, list[list[str]]]:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            names = set(archive.namelist())
            shared_strings = self._read_shared_strings(archive) if "xl/sharedStrings.xml" in names else []
            style_dates = self._read_date_styles(archive) if "xl/styles.xml" in names else set()
            workbook = ET.fromstring(archive.read("xl/workbook.xml"))
            relationships = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
            rel_targets = {
                rel.attrib["Id"]: self._resolve_relationship(rel.attrib["Target"])
                for rel in relationships.findall("p:Relationship", NS)
            }
            result = {}
            for sheet in workbook.findall("m:sheets/m:sheet", NS):
                name = sheet.attrib["name"]
                target = rel_targets[sheet.attrib[f"{{{REL_NS}}}id"]]
                result[name] = self._read_sheet(archive, target, shared_strings, style_dates)
            return result

    @staticmethod
    def _resolve_relationship(target: str) -> str:
        target = target.lstrip("/")
        if not target.startswith("xl/"):
            target = posixpath.join("xl", target)
        return posixpath.normpath(target)

    @staticmethod
    def _read_shared_strings(archive: zipfile.ZipFile) -> list[str]:
        root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
        return [
            "".join(text.text or "" for text in item.findall(".//m:t", NS))
            for item in root.findall("m:si", NS)
        ]

    def _read_date_styles(self, archive: zipfile.ZipFile) -> set[int]:
        root = ET.fromstring(archive.read("xl/styles.xml"))
        custom_formats = {
            int(item.attrib["numFmtId"]): item.attrib.get("formatCode", "")
            for item in root.findall("m:numFmts/m:numFmt", NS)
        }
        date_styles = set()
        cell_xfs = root.findall("m:cellXfs/m:xf", NS)
        for index, xf in enumerate(cell_xfs):
            num_fmt_id = int(xf.attrib.get("numFmtId", "0"))
            code = custom_formats.get(num_fmt_id, "")
            if num_fmt_id in self.date_format_ids or re.search(r"(^|[^A-Z])[dmy]{1,4}([^A-Z]|$)", code, re.I):
                date_styles.add(index)
        return date_styles

    def _read_sheet(self, archive, target, shared_strings, date_styles):
        root = ET.fromstring(archive.read(target))
        rows = {}
        max_row = 0
        max_col = 0
        for row in root.findall("m:sheetData/m:row", NS):
            row_index = int(row.attrib.get("r", "1")) - 1
            max_row = max(max_row, row_index)
            values = {}
            for cell in row.findall("m:c", NS):
                col_index = _column_index(cell.attrib.get("r", "A1"))
                max_col = max(max_col, col_index)
                values[col_index] = self._cell_value(cell, shared_strings, date_styles)
            rows[row_index] = values
        matrix = []
        for row_index in range(max_row + 1):
            row = [""] * (max_col + 1)
            for col_index, value in rows.get(row_index, {}).items():
                row[col_index] = value
            matrix.append(row)
        return matrix

    @staticmethod
    def _cell_value(cell, shared_strings, date_styles) -> str:
        cell_type = cell.attrib.get("t")
        value_node = cell.find("m:v", NS)
        inline_node = cell.find("m:is", NS)
        if cell_type == "inlineStr" and inline_node is not None:
            return "".join(text.text or "" for text in inline_node.findall(".//m:t", NS))
        if value_node is None or value_node.text is None:
            return ""
        raw = value_node.text
        if cell_type == "s":
            try:
                return shared_strings[int(raw)]
            except (IndexError, ValueError):
                return raw
        if cell_type == "b":
            return "Sí" if raw == "1" else "No"
        if cell.attrib.get("s") and int(cell.attrib["s"]) in date_styles:
            return _serial_to_date(raw)
        return raw
