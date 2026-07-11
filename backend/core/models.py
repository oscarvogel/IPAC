from django.db import models
from django.contrib.auth.models import User


class TimeStampedModel(models.Model):
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Sucursal(TimeStampedModel):
    codigo = models.CharField(max_length=10, unique=True)
    nombre = models.CharField(max_length=100, unique=True)
    activa = models.BooleanField(default=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "sucursal"
        verbose_name_plural = "sucursales"

    def __str__(self):
        return self.nombre


class PerfilUsuario(TimeStampedModel):
    class Rol(models.TextChoices):
        ADMINISTRACION = "administracion", "Administracion"
        TESORERIA = "tesoreria", "Tesoreria"
        CAJA = "caja", "Caja"
        CONSULTA = "consulta", "Consulta"

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="perfil")
    rol = models.CharField(max_length=30, choices=Rol.choices, default=Rol.CONSULTA)
    sucursal = models.ForeignKey(Sucursal, on_delete=models.PROTECT, related_name="usuarios")
    puede_ver_todas_las_sucursales = models.BooleanField(default=False)

    class Meta:
        verbose_name = "perfil de usuario"
        verbose_name_plural = "perfiles de usuario"

    def __str__(self):
        return f"{self.user.username} ({self.get_rol_display()})"


class CarreraCurso(TimeStampedModel):
    nombre = models.CharField(max_length=160)
    descripcion = models.TextField(blank=True)
    sucursal = models.ForeignKey(Sucursal, on_delete=models.PROTECT, related_name="carreras")
    activa = models.BooleanField(default=True)

    class Meta:
        ordering = ["nombre"]
        unique_together = [("nombre", "sucursal")]
        verbose_name = "carrera o curso"
        verbose_name_plural = "carreras y cursos"

    def __str__(self):
        return self.nombre


class Alumno(TimeStampedModel):
    class Estado(models.TextChoices):
        ACTIVO = "activo", "Activo"
        INACTIVO = "inactivo", "Inactivo"
        BAJA = "baja", "Baja"

    legajo = models.CharField(max_length=40, unique=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    dni = models.CharField(max_length=20, unique=True)
    email = models.EmailField(blank=True)
    telefono = models.CharField(max_length=50, blank=True)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.ACTIVO)
    sucursal = models.ForeignKey(Sucursal, on_delete=models.PROTECT, related_name="alumnos")
    carrera = models.ForeignKey(
        CarreraCurso,
        on_delete=models.PROTECT,
        related_name="alumnos",
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ["apellido", "nombre"]
        verbose_name = "alumno"
        verbose_name_plural = "alumnos"

    def __str__(self):
        return f"{self.apellido}, {self.nombre}"


class ConceptoCobrable(TimeStampedModel):
    class Tipo(models.TextChoices):
        MATRICULA = "matricula", "Matricula"
        CUOTA = "cuota", "Cuota"
        MATERIAL = "material", "Material"
        OTRO = "otro", "Otro"

    nombre = models.CharField(max_length=160)
    tipo = models.CharField(max_length=30, choices=Tipo.choices)
    importe = models.DecimalField(max_digits=12, decimal_places=2)
    sucursal = models.ForeignKey(Sucursal, on_delete=models.PROTECT, related_name="conceptos")
    carrera = models.ForeignKey(
        CarreraCurso,
        on_delete=models.PROTECT,
        related_name="conceptos",
        blank=True,
        null=True,
    )
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ["nombre"]
        unique_together = [("nombre", "sucursal", "carrera")]
        verbose_name = "concepto cobrable"
        verbose_name_plural = "conceptos cobrables"

    def __str__(self):
        return self.nombre


class Pago(TimeStampedModel):
    class Medio(models.TextChoices):
        EFECTIVO = "efectivo", "Efectivo"
        TRANSFERENCIA = "transferencia", "Transferencia"
        TARJETA = "tarjeta", "Tarjeta"
        OTRO = "otro", "Otro"

    alumno = models.ForeignKey(Alumno, on_delete=models.PROTECT, related_name="pagos")
    concepto = models.ForeignKey(
        ConceptoCobrable,
        on_delete=models.PROTECT,
        related_name="pagos",
        blank=True,
        null=True,
    )
    sucursal = models.ForeignKey(Sucursal, on_delete=models.PROTECT, related_name="pagos")
    fecha = models.DateField(auto_now_add=True)
    importe = models.DecimalField(max_digits=12, decimal_places=2)
    medio = models.CharField(max_length=30, choices=Medio.choices, default=Medio.EFECTIVO)
    observacion = models.TextField(blank=True)

    class Meta:
        ordering = ["-fecha", "-id"]
        verbose_name = "pago"
        verbose_name_plural = "pagos"

    def save(self, *args, **kwargs):
        if not self.sucursal_id and self.alumno_id:
            self.sucursal = self.alumno.sucursal
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.alumno} - {self.importe}"


class CajaDiaria(TimeStampedModel):
    class Estado(models.TextChoices):
        ABIERTA = "abierta", "Abierta"
        CERRADA = "cerrada", "Cerrada"

    fecha = models.DateField()
    sucursal = models.ForeignKey(Sucursal, on_delete=models.PROTECT, related_name="cajas")
    usuario = models.ForeignKey(User, on_delete=models.PROTECT, related_name="cajas")
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.ABIERTA)
    total_contado = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cerrada_en = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-fecha", "-id"]
        unique_together = [("fecha", "sucursal", "usuario")]
        verbose_name = "caja diaria"
        verbose_name_plural = "cajas diarias"

    @property
    def total_esperado(self):
        total = sum(movimiento.signed_amount for movimiento in self.movimientos.all())
        return total

    @property
    def diferencia(self):
        return self.total_contado - self.total_esperado

    def __str__(self):
        return f"{self.fecha} - {self.sucursal} - {self.usuario}"


class MovimientoCaja(TimeStampedModel):
    class Tipo(models.TextChoices):
        PAGO = "pago", "Pago"
        INGRESO = "ingreso", "Ingreso"
        EGRESO = "egreso", "Egreso"
        RETIRO = "retiro", "Retiro"
        PASE = "pase", "Pase"

    caja = models.ForeignKey(CajaDiaria, on_delete=models.PROTECT, related_name="movimientos")
    tipo = models.CharField(max_length=30, choices=Tipo.choices)
    medio = models.CharField(max_length=30, choices=Pago.Medio.choices, default=Pago.Medio.EFECTIVO)
    importe = models.DecimalField(max_digits=12, decimal_places=2)
    descripcion = models.CharField(max_length=180, blank=True)
    pago = models.OneToOneField(
        Pago,
        on_delete=models.PROTECT,
        related_name="movimiento_caja",
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ["-creado", "-id"]
        verbose_name = "movimiento de caja"
        verbose_name_plural = "movimientos de caja"

    @property
    def signed_amount(self):
        if self.tipo in {self.Tipo.EGRESO, self.Tipo.RETIRO, self.Tipo.PASE}:
            return -self.importe
        return self.importe

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.importe}"
