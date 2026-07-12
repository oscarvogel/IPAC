from django.contrib.auth import authenticate
from rest_framework import serializers

from .models import AplicacionPago, Alumno, CajaDiaria, CarreraCurso, ConceptoCobrable, Cuota, Matricula, MovimientoCaja, Pago, PerfilUsuario, Sucursal


class SucursalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sucursal
        fields = ["id", "codigo", "nombre", "activa"]


class PerfilUsuarioSerializer(serializers.ModelSerializer):
    sucursal = SucursalSerializer(read_only=True)

    class Meta:
        model = PerfilUsuario
        fields = ["rol", "sucursal", "puede_ver_todas_las_sucursales"]


class CurrentUserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.EmailField()
    perfil = PerfilUsuarioSerializer()


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(trim_whitespace=False, write_only=True)

    def validate(self, attrs):
        user = authenticate(
            request=self.context.get("request"),
            username=attrs["username"],
            password=attrs["password"],
        )
        if not user:
            raise serializers.ValidationError("Usuario o clave invalidos.")
        if not user.is_active:
            raise serializers.ValidationError("El usuario esta inactivo.")
        attrs["user"] = user
        return attrs


class CarreraCursoSerializer(serializers.ModelSerializer):
    sucursal_nombre = serializers.CharField(source="sucursal.nombre", read_only=True)

    class Meta:
        model = CarreraCurso
        fields = ["id", "nombre", "descripcion", "sucursal", "sucursal_nombre", "activa"]


class AlumnoSerializer(serializers.ModelSerializer):
    sucursal_nombre = serializers.CharField(source="sucursal.nombre", read_only=True)
    carrera_nombre = serializers.CharField(source="carrera.nombre", read_only=True)

    class Meta:
        model = Alumno
        fields = [
            "id",
            "legajo",
            "nombre",
            "apellido",
            "dni",
            "email",
            "telefono",
            "estado",
            "sucursal",
            "sucursal_nombre",
            "carrera",
            "carrera_nombre",
        ]


class ConceptoCobrableSerializer(serializers.ModelSerializer):
    sucursal_nombre = serializers.CharField(source="sucursal.nombre", read_only=True)
    carrera_nombre = serializers.CharField(source="carrera.nombre", read_only=True)

    class Meta:
        model = ConceptoCobrable
        fields = [
            "id",
            "nombre",
            "tipo",
            "importe",
            "sucursal",
            "sucursal_nombre",
            "carrera",
            "carrera_nombre",
            "activo",
        ]


class MatriculaSerializer(serializers.ModelSerializer):
    alumno_nombre = serializers.CharField(source="alumno.__str__", read_only=True)
    carrera_nombre = serializers.CharField(source="carrera.nombre", read_only=True)
    sucursal = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Matricula
        fields = ["id", "alumno", "alumno_nombre", "carrera", "carrera_nombre", "sucursal", "fecha_inicio", "fecha_fin", "estado", "observacion"]

    def validate(self, attrs):
        alumno = attrs.get("alumno") or getattr(self.instance, "alumno", None)
        carrera = attrs.get("carrera") or getattr(self.instance, "carrera", None)
        if alumno and carrera and alumno.sucursal_id != carrera.sucursal_id:
            raise serializers.ValidationError("El alumno y la carrera deben pertenecer a la misma sucursal.")
        return attrs

    def create(self, validated_data):
        validated_data["sucursal"] = validated_data["alumno"].sucursal
        return super().create(validated_data)


class CuotaSerializer(serializers.ModelSerializer):
    alumno_nombre = serializers.CharField(source="alumno.__str__", read_only=True)
    concepto_nombre = serializers.CharField(source="concepto.nombre", read_only=True)
    sucursal = serializers.PrimaryKeyRelatedField(read_only=True)
    total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_pagado = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    saldo = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Cuota
        fields = ["id", "alumno", "alumno_nombre", "matricula", "concepto", "concepto_nombre", "sucursal", "periodo", "fecha_emision", "fecha_vencimiento", "importe", "descuento", "recargo", "total", "total_pagado", "saldo", "estado"]
        read_only_fields = ["estado"]

    def validate(self, attrs):
        alumno = attrs.get("alumno") or getattr(self.instance, "alumno", None)
        concepto = attrs.get("concepto") or getattr(self.instance, "concepto", None)
        matricula = attrs.get("matricula") or getattr(self.instance, "matricula", None)
        if alumno and concepto and alumno.sucursal_id != concepto.sucursal_id:
            raise serializers.ValidationError("El concepto debe pertenecer a la sucursal del alumno.")
        if alumno and matricula and matricula.alumno_id != alumno.id:
            raise serializers.ValidationError("La matricula no pertenece al alumno.")
        return attrs

    def create(self, validated_data):
        validated_data["sucursal"] = validated_data["alumno"].sucursal
        return super().create(validated_data)


class AplicacionPagoSerializer(serializers.ModelSerializer):
    class Meta:
        model = AplicacionPago
        fields = ["id", "pago", "cuota", "importe", "creado"]
        read_only_fields = ["creado"]

    def validate(self, attrs):
        pago, cuota, importe = attrs["pago"], attrs["cuota"], attrs["importe"]
        if pago.alumno_id != cuota.alumno_id:
            raise serializers.ValidationError("El pago y la cuota deben pertenecer al mismo alumno.")
        if cuota.estado == Cuota.Estado.ANULADA:
            raise serializers.ValidationError("No se puede aplicar un pago a una cuota anulada.")
        if importe <= 0 or importe > pago.saldo_a_favor:
            raise serializers.ValidationError("El importe supera el saldo disponible del pago o no es valido.")
        if importe > cuota.saldo:
            raise serializers.ValidationError("El importe supera el saldo de la cuota.")
        return attrs

    def create(self, validated_data):
        aplicacion = super().create(validated_data)
        aplicacion.cuota.actualizar_estado()
        return aplicacion


class PagoSerializer(serializers.ModelSerializer):
    alumno_nombre = serializers.CharField(source="alumno.__str__", read_only=True)
    concepto_nombre = serializers.CharField(source="concepto.nombre", read_only=True)
    sucursal_nombre = serializers.CharField(source="sucursal.nombre", read_only=True)
    sucursal = serializers.PrimaryKeyRelatedField(read_only=True)
    importe_aplicado = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    saldo_a_favor = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Pago
        fields = [
            "id",
            "alumno",
            "alumno_nombre",
            "concepto",
            "concepto_nombre",
            "sucursal",
            "sucursal_nombre",
            "fecha",
            "importe",
            "medio",
            "observacion",
            "importe_aplicado",
            "saldo_a_favor",
        ]

    def validate(self, attrs):
        alumno = attrs.get("alumno") or getattr(self.instance, "alumno", None)
        concepto = attrs.get("concepto") or getattr(self.instance, "concepto", None)
        request = self.context.get("request")
        perfil = getattr(getattr(request, "user", None), "perfil", None)
        if alumno and perfil and not perfil.puede_ver_todas_las_sucursales and alumno.sucursal_id != perfil.sucursal_id:
            raise serializers.ValidationError("No puede registrar pagos de otra sucursal.")
        if alumno and concepto and alumno.sucursal_id != concepto.sucursal_id:
            raise serializers.ValidationError("El concepto debe pertenecer a la misma sucursal del alumno.")
        return attrs

    def create(self, validated_data):
        validated_data["sucursal"] = validated_data["alumno"].sucursal
        return super().create(validated_data)


class MovimientoCajaSerializer(serializers.ModelSerializer):
    tipo_label = serializers.CharField(source="get_tipo_display", read_only=True)

    class Meta:
        model = MovimientoCaja
        fields = [
            "id",
            "caja",
            "tipo",
            "tipo_label",
            "medio",
            "importe",
            "descripcion",
            "pago",
            "creado",
        ]
        read_only_fields = ["pago"]

    def validate(self, attrs):
        caja = attrs.get("caja") or getattr(self.instance, "caja", None)
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if caja and caja.estado == CajaDiaria.Estado.CERRADA:
            raise serializers.ValidationError("No se pueden registrar movimientos en una caja cerrada.")
        if caja and user and caja.usuario_id != user.id:
            raise serializers.ValidationError("No puede registrar movimientos en una caja de otro usuario.")
        return attrs


class CajaDiariaSerializer(serializers.ModelSerializer):
    sucursal_nombre = serializers.CharField(source="sucursal.nombre", read_only=True)
    usuario_nombre = serializers.CharField(source="usuario.username", read_only=True)
    movimientos = MovimientoCajaSerializer(many=True, read_only=True)
    total_esperado = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    diferencia = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = CajaDiaria
        fields = [
            "id",
            "fecha",
            "sucursal",
            "sucursal_nombre",
            "usuario",
            "usuario_nombre",
            "estado",
            "total_contado",
            "total_esperado",
            "diferencia",
            "cerrada_en",
            "movimientos",
        ]
        read_only_fields = ["usuario", "estado", "cerrada_en"]
