from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0014_cuota_descuento_registrado_por_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="perfilusuario",
            name="debe_cambiar_clave",
            field=models.BooleanField(default=False),
        ),
    ]
