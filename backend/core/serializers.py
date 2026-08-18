from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import serializers

from .models import AplicacionPago, Alumno, CajaDiaria, CarreraCurso, ConceptoCobrable, Cuota, Matricula, MovimientoCaja, Pago, PerfilUsuario, Sucursal
from .permissions import can_manage_user
from .contexts.caja.application.validar_caja import CajaCerradaError, asegurar_caja_abierta
from .contexts.alumnos.application.gestionar_matricula import GestionarMatricula, MatriculaError


class UserSerializer(serializers.ModelSerializer):
    rol = serializers.ChoiceField(choices=PerfilUsuario.Rol.choices, write_only=True)
    sucursal = serializers.PrimaryKeyRelatedField(
        queryset=Sucursal.objects.all(), write_only=True,
    )
    puede_ver_todas_las_sucursales = serializers.BooleanField(
        write_only=True, required=False, default=False,
    )
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    perfil = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "username", "password",
            "first_name", "last_name", "email", "is_active",
            "rol", "sucursal", "puede_ver_todas_las_sucursales", "perfil",
        ]

    def get_perfil(self, obj):
        perfil = getattr(obj, "perfil", None)
        if not perfil:
            return None
        from .serializers import PerfilUsuarioSerializer
        return PerfilUsuarioSerializer(perfil).data

    def validate_username(self, value):
        qs = User.objects.filter(username=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("El nombre de usuario ya existe.")
        return value

    def validate(self, attrs):
        request = self.context.get("request")
        actor = getattr(request, "user", None)
        actor_profile = getattr(actor, "perfil", None)
        proposed_role = attrs.get("rol")
        global_access = attrs.get("puede_ver_todas_las_sucursales")
        allowed, message = can_manage_user(
            actor,
            target=self.instance,
            proposed_role=proposed_role,
            global_access=global_access,
        )
        if not allowed:
            raise serializers.ValidationError(message)
        if (
            actor_profile
            and actor_profile.rol == PerfilUsuario.Rol.ADMINISTRACION
            and not actor_profile.puede_ver_todas_las_sucursales
        ):
            target_profile = getattr(self.instance, "perfil", None)
            target_branch = attrs.get("sucursal") or getattr(target_profile, "sucursal", None)
            if target_branch and target_branch.id != actor_profile.sucursal_id:
                raise serializers.ValidationError("Sólo puede administrar usuarios de su sucursal.")
        if self.instance and self.instance.pk == getattr(actor, "pk", None) and attrs.get("is_active") is False:
            raise serializers.ValidationError("No puede desactivar su propio usuario.")
        return attrs

    def create(self, validated_data):
        rol = validated_data.pop("rol")
        sucursal = validated_data.pop("sucursal")
        puede_ver_todas = validated_data.pop("puede_ver_todas_las_sucursales", False)
        password = validated_data.pop("password", None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        PerfilUsuario.objects.create(
            user=user, rol=rol, sucursal=sucursal,
            puede_ver_todas_las_sucursales=puede_ver_todas,
        )
        return user

    def update(self, instance, validated_data):
        rol = validated_data.pop("rol", None)
        sucursal = validated_data.pop("sucursal", None)
        puede_ver_todas = validated_data.pop("puede_ver_todas_las_sucursales", None)
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        if rol is not None or sucursal is not None or puede_ver_todas is not None:
            perfil, _ = PerfilUsuario.objects.get_or_create(user=instance)
            if rol is not None:
                perfil.rol = rol
            if sucursal is not None:
                perfil.sucursal = sucursal
            if puede_ver_todas is not None:
                perfil.puede_ver_todas_las_sucursales = puede_ver_todas
            perfil.save()
        return instance


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
        fields = [
            "id", "nombre", "descripcion", "sucursal", "sucursal_nombre", "tipo", "duracion",
            "plan_cuotas", "importe_matricula", "cuota_programatica", "cuota_extraprogramatica",
            "cuota_total", "cuota_convenio_20", "cuota_convenio_15", "activa",
        ]


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
            "cuil",
            "fecha_nacimiento",
            "email",
            "telefono",
            "domicilio",
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
    sucursal_nombre = serializers.CharField(source="sucursal.nombre", read_only=True)
    sucursal = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Matricula
        fields = ["id", "alumno", "alumno_nombre", "carrera", "carrera_nombre", "sucursal", "sucursal_nombre", "fecha_inicio", "fecha_fin", "estado", "observacion"]

    def validate(self, attrs):
        alumno = attrs.get("alumno") or getattr(self.instance, "alumno", None)
        carrera = attrs.get("carrera") or getattr(self.instance, "carrera", None)
        if alumno and carrera and alumno.sucursal_id != carrera.sucursal_id:
            raise serializers.ValidationError("El alumno y la carrera deben pertenecer a la misma sucursal.")
        estado = attrs.get("estado", getattr(self.instance, "estado", Matricula.Estado.ACTIVA))
        if estado == Matricula.Estado.ACTIVA and alumno and carrera:
            active = Matricula.objects.filter(alumno=alumno, carrera=carrera, estado=Matricula.Estado.ACTIVA)
            if self.instance:
                active = active.exclude(pk=self.instance.pk)
            if active.exists():
                raise serializers.ValidationError("El alumno ya tiene una matrícula activa para esta carrera.")
        return attrs

    def create(self, validated_data):
        try:
            return GestionarMatricula().crear(**validated_data)
        except MatriculaError as exc:
            raise serializers.ValidationError(str(exc)) from exc

    def update(self, instance, validated_data):
        try:
            return GestionarMatricula().actualizar(instance, **validated_data)
        except MatriculaError as exc:
            raise serializers.ValidationError(str(exc)) from exc


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
    alumno_legajo = serializers.CharField(source="alumno.legajo", read_only=True)
    concepto_nombre = serializers.CharField(source="concepto.nombre", read_only=True)
    sucursal_nombre = serializers.CharField(source="sucursal.nombre", read_only=True)
    sucursal = serializers.PrimaryKeyRelatedField(read_only=True)
    cuota = serializers.PrimaryKeyRelatedField(
        queryset=Cuota.objects.all(), write_only=True, required=False, allow_null=True
    )
    importe_aplicado = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    saldo_a_favor = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Pago
        fields = [
            "id",
            "alumno",
            "alumno_nombre",
            "alumno_legajo",
            "concepto",
            "cuota",
            "concepto_nombre",
            "sucursal",
            "sucursal_nombre",
            "fecha",
            "importe",
            "medio",
            "observacion",
            "numero_recibo",
            "importe_aplicado",
            "saldo_a_favor",
        ]
        read_only_fields = ["numero_recibo"]

    def validate(self, attrs):
        alumno = attrs.get("alumno") or getattr(self.instance, "alumno", None)
        concepto = attrs.get("concepto") or getattr(self.instance, "concepto", None)
        cuota = attrs.get("cuota")
        request = self.context.get("request")
        perfil = getattr(getattr(request, "user", None), "perfil", None)
        if alumno and perfil and not perfil.puede_ver_todas_las_sucursales and alumno.sucursal_id != perfil.sucursal_id:
            raise serializers.ValidationError("No puede registrar pagos de otra sucursal.")
        if alumno and concepto and alumno.sucursal_id != concepto.sucursal_id:
            raise serializers.ValidationError("El concepto debe pertenecer a la misma sucursal del alumno.")
        if cuota:
            if cuota.alumno_id != alumno.id:
                raise serializers.ValidationError("La cuota no pertenece al alumno seleccionado.")
            if cuota.sucursal_id != alumno.sucursal_id:
                raise serializers.ValidationError("La cuota debe pertenecer a la misma sucursal del alumno.")
            if cuota.estado == Cuota.Estado.ANULADA or cuota.saldo <= 0:
                raise serializers.ValidationError("La cuota seleccionada no tiene saldo pendiente.")
            if concepto and concepto.id != cuota.concepto_id:
                raise serializers.ValidationError("El concepto debe coincidir con el de la cuota.")
        return attrs


class DeudorSerializer(serializers.ModelSerializer):
    alumno = serializers.SerializerMethodField()
    sucursal_nombre = serializers.CharField(source="sucursal.nombre", read_only=True)
    carrera_nombre = serializers.CharField(source="carrera.nombre", read_only=True, allow_null=True)
    deuda_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    cuotas_pendientes = serializers.IntegerField(read_only=True)
    cuotas_vencidas = serializers.IntegerField(read_only=True)
    cuota_vencida_mas_antigua = serializers.DateField(read_only=True, allow_null=True)
    fecha_ultimo_pago = serializers.DateField(read_only=True, allow_null=True)

    class Meta:
        model = Alumno
        fields = [
            "id", "alumno", "nombre", "apellido", "dni", "legajo", "telefono", "email",
            "sucursal", "sucursal_nombre", "carrera", "carrera_nombre", "deuda_total",
            "cuotas_pendientes", "cuotas_vencidas", "cuota_vencida_mas_antigua", "fecha_ultimo_pago",
        ]

    def get_alumno(self, obj):
        return {
            "id": obj.id,
            "nombre": obj.nombre,
            "apellido": obj.apellido,
            "dni": obj.dni,
            "legajo": obj.legajo,
        }

    def create(self, validated_data):
        validated_data.pop("cuota", None)
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
        if caja:
            try:
                asegurar_caja_abierta(caja)
            except CajaCerradaError as exc:
                raise serializers.ValidationError({"caja": str(exc)}) from exc
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
