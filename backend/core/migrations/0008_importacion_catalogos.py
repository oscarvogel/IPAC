from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0007_alter_perfilusuario_rol"),
    ]

    operations = [
        migrations.AddField(
            model_name="alumno",
            name="cuil",
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name="alumno",
            name="domicilio",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="alumno",
            name="fecha_nacimiento",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="alumno",
            name="dni",
            field=models.CharField(blank=True, max_length=20, null=True, unique=True),
        ),
        migrations.AddField(
            model_name="carreracurso",
            name="cuota_convenio_15",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name="carreracurso",
            name="cuota_convenio_20",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name="carreracurso",
            name="cuota_extraprogramatica",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name="carreracurso",
            name="cuota_programatica",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name="carreracurso",
            name="cuota_total",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name="carreracurso",
            name="duracion",
            field=models.CharField(blank=True, max_length=80),
        ),
        migrations.AddField(
            model_name="carreracurso",
            name="importe_matricula",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name="carreracurso",
            name="plan_cuotas",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="carreracurso",
            name="tipo",
            field=models.CharField(choices=[("carrera", "Carrera"), ("curso", "Curso")], default="carrera", max_length=20),
        ),
    ]
