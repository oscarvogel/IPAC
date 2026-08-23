from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0008_importacion_catalogos"),
    ]

    operations = [
        migrations.AddField(
            model_name="pago",
            name="saldo_pendiente_posterior",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                editable=False,
                max_digits=12,
                null=True,
            ),
        ),
    ]
