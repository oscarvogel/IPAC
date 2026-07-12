from django.db import migrations


def assign_receipt_numbers(apps, schema_editor):
    Pago = apps.get_model("core", "Pago")
    for pago in Pago.objects.filter(numero_recibo__isnull=True).order_by("id"):
        pago.numero_recibo = f"REC-{pago.id:08d}"
        pago.save(update_fields=["numero_recibo"])


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0005_pago_numero_recibo"),
    ]

    operations = [
        migrations.RunPython(assign_receipt_numbers, migrations.RunPython.noop),
    ]
