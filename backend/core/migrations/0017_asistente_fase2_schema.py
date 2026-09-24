import datetime

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0016_chatbotconversation_chatbotmessage"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AsistenteKnowledgeArticle",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("creado", models.DateTimeField(auto_now_add=True)),
                ("actualizado", models.DateTimeField(auto_now=True)),
                ("clave", models.SlugField(max_length=120, unique=True)),
                ("titulo", models.CharField(max_length=180)),
                ("modulo", models.CharField(max_length=80)),
                ("preguntas_equivalentes", models.JSONField(blank=True, default=list)),
                ("descripcion", models.TextField(blank=True)),
                ("pasos", models.JSONField(blank=True, default=list)),
                ("ruta", models.CharField(blank=True, max_length=255)),
                ("action_label", models.CharField(blank=True, max_length=120)),
                ("roles_permitidos", models.JSONField(blank=True, default=list)),
                ("notas", models.JSONField(blank=True, default=list)),
                ("activo", models.BooleanField(default=True)),
                ("orden", models.IntegerField(default=0)),
                ("actualizado_por", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="articulos_asistente_actualizados", to=settings.AUTH_USER_MODEL)),
                ("creado_por", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="articulos_asistente_creados", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "artículo de conocimiento del asistente",
                "verbose_name_plural": "artículos de conocimiento del asistente",
                "ordering": ["orden", "titulo", "id"],
            },
        ),
        migrations.CreateModel(
            name="AsistenteConfig",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("creado", models.DateTimeField(auto_now_add=True)),
                ("actualizado", models.DateTimeField(auto_now=True)),
                ("email_habilitado", models.BooleanField(default=False)),
                ("modo_email", models.CharField(choices=[("desactivado", "Desactivado"), ("inmediato", "Inmediato"), ("diario", "Resumen diario")], default="desactivado", max_length=20)),
                ("destinatarios", models.JSONField(blank=True, default=list)),
                ("incluir_fuera_de_alcance", models.BooleanField(default=False)),
                ("hora_resumen_diario", models.TimeField(default=datetime.time(18, 0))),
                ("ultimo_resumen_exitoso_en", models.DateTimeField(blank=True, null=True)),
                ("actualizado_por", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="config_asistente_actualizadas", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "configuración del asistente",
                "verbose_name_plural": "configuración del asistente",
            },
        ),
        migrations.CreateModel(
            name="AsistenteConsultaNoResuelta",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("creado", models.DateTimeField(auto_now_add=True)),
                ("actualizado", models.DateTimeField(auto_now=True)),
                ("pregunta", models.TextField()),
                ("pregunta_normalizada", models.TextField()),
                ("categoria", models.CharField(choices=[("no_documentada", "No documentada"), ("sin_datos", "Sin datos"), ("sin_permiso", "Sin permiso"), ("fuera_de_alcance", "Fuera de alcance"), ("error_ia", "Error IA"), ("error_herramienta", "Error de herramienta")], max_length=40)),
                ("intencion", models.CharField(blank=True, max_length=80)),
                ("herramienta", models.CharField(blank=True, max_length=80)),
                ("respuesta", models.TextField(blank=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("estado", models.CharField(choices=[("pendiente", "Pendiente"), ("resuelta", "Resuelta"), ("ignorada", "Ignorada")], default="pendiente", max_length=20)),
                ("resuelto_en", models.DateTimeField(blank=True, null=True)),
                ("notificado_en", models.DateTimeField(blank=True, null=True)),
                ("articulo", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="consultas_resueltas", to="core.asistenteknowledgearticle")),
                ("conversacion", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="consultas_no_resueltas", to="core.chatbotconversation")),
                ("mensaje", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="consultas_no_resueltas", to="core.chatbotmessage")),
                ("resuelto_por", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="consultas_asistente_resueltas", to=settings.AUTH_USER_MODEL)),
                ("sucursal", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="consultas_asistente_no_resueltas", to="core.sucursal")),
                ("usuario", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="consultas_asistente_no_resueltas", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "consulta no resuelta del asistente",
                "verbose_name_plural": "consultas no resueltas del asistente",
                "ordering": ["-creado", "-id"],
            },
        ),
        migrations.AddIndex(
            model_name="asistenteknowledgearticle",
            index=models.Index(fields=["activo", "modulo"], name="core_asiste_activo_f514c8_idx"),
        ),
        migrations.AddIndex(
            model_name="asistenteknowledgearticle",
            index=models.Index(fields=["clave"], name="core_asiste_clave_335cd9_idx"),
        ),
        migrations.AddIndex(
            model_name="asistenteconsultanoresuelta",
            index=models.Index(fields=["estado", "creado"], name="core_asiste_estado_b2b403_idx"),
        ),
        migrations.AddIndex(
            model_name="asistenteconsultanoresuelta",
            index=models.Index(fields=["categoria", "creado"], name="core_asiste_categor_312a62_idx"),
        ),
        migrations.AddIndex(
            model_name="asistenteconsultanoresuelta",
            index=models.Index(fields=["usuario", "creado"], name="core_asiste_usuario_debf82_idx"),
        ),
        migrations.AddIndex(
            model_name="asistenteconsultanoresuelta",
            index=models.Index(fields=["sucursal", "creado"], name="core_asiste_sucursa_ea6f34_idx"),
        ),
        migrations.AddIndex(
            model_name="asistenteconsultanoresuelta",
            index=models.Index(fields=["pregunta_normalizada"], name="core_asiste_pregunt_3f419c_idx"),
        ),
    ]
