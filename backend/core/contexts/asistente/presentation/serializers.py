from django.core.validators import validate_email
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from core.models import (
    AsistenteConfig,
    AsistenteConsultaNoResuelta,
    AsistenteKnowledgeArticle,
    PerfilUsuario,
)


def _string_list(value, field_name):
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise serializers.ValidationError(f"{field_name} debe ser una lista de textos.")
    return [item.strip() for item in value if item.strip()]


class AsistenteKnowledgeArticleSerializer(serializers.ModelSerializer):
    creado_por_username = serializers.CharField(source="creado_por.username", read_only=True)
    actualizado_por_username = serializers.CharField(source="actualizado_por.username", read_only=True)

    class Meta:
        model = AsistenteKnowledgeArticle
        fields = [
            "id",
            "clave",
            "titulo",
            "modulo",
            "preguntas_equivalentes",
            "descripcion",
            "pasos",
            "ruta",
            "action_label",
            "roles_permitidos",
            "notas",
            "activo",
            "orden",
            "creado_por_username",
            "actualizado_por_username",
            "creado",
            "actualizado",
        ]
        read_only_fields = [
            "id",
            "creado_por_username",
            "actualizado_por_username",
            "creado",
            "actualizado",
        ]

    def validate_preguntas_equivalentes(self, value):
        return _string_list(value, "preguntas_equivalentes")

    def validate_pasos(self, value):
        return _string_list(value, "pasos")

    def validate_notas(self, value):
        return _string_list(value, "notas")

    def validate_roles_permitidos(self, value):
        values = _string_list(value, "roles_permitidos")
        valid = set(PerfilUsuario.Rol.values)
        invalid = set(values) - valid
        if invalid:
            raise serializers.ValidationError(
                f"Roles no válidos: {', '.join(sorted(invalid))}."
            )
        return values

    def validate_ruta(self, value):
        value = (value or "").strip()
        if not value:
            return ""
        lowered = value.lower()
        if not value.startswith("/") or lowered.startswith(("//", "http:", "https:", "javascript:")):
            raise serializers.ValidationError("La ruta debe ser una ruta interna de IPAC.")
        return value


class AsistenteConsultaNoResueltaSerializer(serializers.ModelSerializer):
    usuario = serializers.CharField(source="usuario.username", read_only=True)
    sucursal = serializers.CharField(source="sucursal.nombre", read_only=True)
    articulo_titulo = serializers.CharField(source="articulo.titulo", read_only=True)

    class Meta:
        model = AsistenteConsultaNoResuelta
        fields = [
            "id",
            "conversacion_id",
            "mensaje_id",
            "usuario",
            "sucursal",
            "pregunta",
            "categoria",
            "intencion",
            "herramienta",
            "respuesta",
            "metadata",
            "estado",
            "articulo_id",
            "articulo_titulo",
            "resuelto_por_id",
            "resuelto_en",
            "notificado_en",
            "creado",
        ]
        read_only_fields = fields


class AsistenteConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = AsistenteConfig
        fields = [
            "email_habilitado",
            "modo_email",
            "destinatarios",
            "incluir_fuera_de_alcance",
            "hora_resumen_diario",
            "ultimo_resumen_exitoso_en",
            "actualizado",
        ]
        read_only_fields = ["ultimo_resumen_exitoso_en", "actualizado"]

    def validate_destinatarios(self, value):
        values = _string_list(value, "destinatarios")
        for email in values:
            try:
                validate_email(email)
            except DjangoValidationError as exc:
                raise serializers.ValidationError(f"Email inválido: {email}.") from exc
        return values
