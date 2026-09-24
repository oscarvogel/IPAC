import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0015_perfilusuario_debe_cambiar_clave"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ChatbotConversation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("creado", models.DateTimeField(auto_now_add=True)),
                ("actualizado", models.DateTimeField(auto_now=True)),
                ("titulo", models.CharField(default="Asistente IPAC", max_length=160)),
                (
                    "sucursal",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="conversaciones_chatbot",
                        to="core.sucursal",
                    ),
                ),
                (
                    "usuario",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="conversaciones_chatbot",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-actualizado", "-id"],
                "verbose_name": "conversación del asistente",
                "verbose_name_plural": "conversaciones del asistente",
            },
        ),
        migrations.CreateModel(
            name="ChatbotMessage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("creado", models.DateTimeField(auto_now_add=True)),
                ("actualizado", models.DateTimeField(auto_now=True)),
                (
                    "role",
                    models.CharField(
                        choices=[("user", "Usuario"), ("assistant", "Asistente")],
                        max_length=20,
                    ),
                ),
                ("content", models.TextField()),
                ("tokens_used", models.PositiveIntegerField(blank=True, null=True)),
                (
                    "conversacion",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="mensajes",
                        to="core.chatbotconversation",
                    ),
                ),
            ],
            options={
                "ordering": ["creado", "id"],
                "verbose_name": "mensaje del asistente",
                "verbose_name_plural": "mensajes del asistente",
            },
        ),
    ]
