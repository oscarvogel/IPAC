from decimal import Decimal

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import serializers

from .models import AplicacionPago, Alumno, CajaDiaria, CarreraCurso, ConceptoCobrable, Cuota, EventoAuditoria, Matricula, MovimientoCaja, Pago, PerfilUsuario, ReglaRecargo, Sucursal, TipoDescuento
from .permissions import can_manage_user
from .contexts.caja.application.validar_caja import CajaCerradaError, asegurar_caja_abierta
from .contexts.alumnos.application.gestionar_matricula import GestionarMatricula, MatriculaError
from .contexts.cobranzas.application.registrar_pago import actualizar_saldo_pendiente_posterior


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
    deuda_total = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True, default=0)
    saldo_a_favor = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True, default=0)

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
            "deuda_total",
            "saldo_a_favor",
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


class TipoDescuentoSerializer(serializers.ModelSerializer):
    sucursal_nombre = serializers.CharField(source="sucursal.nombre", read_only=True)

    class Meta:
        model = TipoDescuento
        fields = ["id", "nombre", "modalidad", "valor", "sucursal", "sucursal_nombre", "vigencia_desde", "vigencia_hasta", "activo"]

    def validate(self, attrs):
        if attrs.get("valor", getattr(self.instance, "valor", 0)) < 0:
            raise serializers.ValidationError("El valor del descuento no puede ser negativo.")
        return attrs


class ReglaRecargoSerializer(serializers.ModelSerializer):
    sucursal_nombre = serializers.CharField(source="sucursal.nombre", read_only=True)
    concepto_nombre = serializers.CharField(source="concepto.nombre", read_only=True)

    class Meta:
        model = ReglaRecargo
        fields = ["id", "nombre", "sucursal", "sucursal_nombre", "concepto", "concepto_nombre", "modalidad", "valor", "dias_tolerancia", "vigencia_desde", "activo"]

    def validate(self, attrs):
        sucursal = attrs.get("sucursal") or getattr(self.instance, "sucursal", None)
        concepto = attrs.get("concepto") or getattr(self.instance, "concepto", None)
        if concepto and sucursal and concepto.sucursal_id != sucursal.id:
            raise serializers.ValidationError("El concepto y la regla deben pertenecer a la misma sucursal.")
        if attrs.get("valor", getattr(self.instance, "valor", 0)) < 0:
            raise serializers.ValidationError("El valor del recargo no puede ser negativo.")
        return attrs


class MatriculaSerializer(serializers.ModelSerializer):
    alumno_nombre = serializers.CharField(source="alumno.__str__", read_only=True)
    carrera_nombre = serializers.CharField(source="carrera.nombre", read_only=True)
    sucursal_nombre = serializers.CharField(source="sucursal.nombre", read_only=True)
    sucursal = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Matricula
        fields = ["id", "alumno", "alumno_nombre", "carrera", "carrera_nombre", "sucursal", "sucursal_nombre", "fecha_inicio", "fecha_fin", "estado", "observacion"]
        read_only_fields = ["fecha_fin", "estado"]

    def validate(self, attrs):
        alumno = attrs.get("alumno") or getattr(self.instance, "alumno", None)
        carrera = attrs.get("carrera") or getattr(self.instance, "carrera", None)
        if self.instance and "carrera" in attrs and attrs["carrera"].pk != self.instance.carrera_id:
            raise serializers.ValidationError("Utilice la acción Cambiar carrera para conservar el historial.")
        if alumno and carrera and alumno.sucursal_id != carrera.sucursal_id:
            raise serializers.ValidationError("El alumno y la carrera deben pertenecer a la misma sucursal.")
        estado = attrs.get("estado", getattr(self.instance, "estado", Matricula.Estado.ACTIVA))
        if estado == Matricula.Estado.ACTIVA and alumno and carrera:
            active = Matricula.objects.filter(alumno=alumno, estado=Matricula.Estado.ACTIVA)
            if self.instance:
                active = active.exclude(pk=self.instance.pk)
            if active.exists():
                raise serializers.ValidationError("El alumno ya tiene una matrícula activa. Finalícela o utilice Cambiar carrera.")
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
        fields = ["id", "alumno", "alumno_nombre", "matricula", "concepto", "concepto_nombre", "sucursal", "periodo", "fecha_emision", "fecha_vencimiento", "importe", "descuento", "tipo_descuento", "motivo_descuento", "descuento_registrado_por", "recargo", "regla_recargo", "recargo_calculado_en", "total", "total_pagado", "saldo", "estado"]
        read_only_fields = ["estado", "descuento_registrado_por", "regla_recargo", "recargo_calculado_en"]

    def validate(self, attrs):
        alumno = attrs.get("alumno") or getattr(self.instance, "alumno", None)
        concepto = attrs.get("concepto") or getattr(self.instance, "concepto", None)
        matricula = attrs.get("matricula") or getattr(self.instance, "matricula", None)
        if alumno and concepto and alumno.sucursal_id != concepto.sucursal_id:
            raise serializers.ValidationError("El concepto debe pertenecer a la sucursal del alumno.")
        if alumno and matricula and matricula.alumno_id != alumno.id:
            raise serializers.ValidationError("La matricula no pertenece al alumno.")
        tipo = attrs.get("tipo_descuento") or getattr(self.instance, "tipo_descuento", None)
        descuento = attrs.get("descuento", getattr(self.instance, "descuento", 0))
        importe = attrs.get("importe", getattr(self.instance, "importe", 0))
        if tipo:
            if alumno and tipo.sucursal_id != alumno.sucursal_id:
                raise serializers.ValidationError("El tipo de descuento no pertenece a la sucursal del alumno.")
            if not tipo.activo:
                raise serializers.ValidationError("El tipo de descuento seleccionado está inactivo.")
            if tipo.valor > 0:
                descuento = tipo.calcular(importe)
                attrs["descuento"] = descuento
        if descuento < 0 or descuento > importe:
            raise serializers.ValidationError("El descuento no puede superar el importe de la cuota.")
        return attrs

    def create(self, validated_data):
        validated_data["sucursal"] = validated_data["alumno"].sucursal
        if validated_data.get("descuento", 0) > 0 and not validated_data.get("tipo_descuento"):
            validated_data["tipo_descuento"], _ = TipoDescuento.objects.get_or_create(
                nombre="Excepción manual",
                sucursal=validated_data["sucursal"],
                defaults={"modalidad": TipoDescuento.Modalidad.IMPORTE, "valor": 0},
            )
            validated_data["motivo_descuento"] = validated_data.get("motivo_descuento") or "Ajuste manual"
        request = self.context.get("request")
        if validated_data.get("descuento", 0) > 0 and request:
            validated_data["descuento_registrado_por"] = request.user
        return super().create(validated_data)


class AplicacionPagoSerializer(serializers.ModelSerializer):
    class Meta:
        model = AplicacionPago
        fields = ["id", "pago", "cuota", "importe", "activa", "anulada_en", "creado"]
        read_only_fields = ["activa", "anulada_en", "creado"]

    def validate(self, attrs):
        pago, cuota, importe = attrs["pago"], attrs["cuota"], attrs["importe"]
        if pago.estado == Pago.Estado.ANULADO:
            raise serializers.ValidationError("No se puede aplicar un pago anulado.")
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
        actualizar_saldo_pendiente_posterior(aplicacion.pago)
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
    cuotas = serializers.PrimaryKeyRelatedField(
        queryset=Cuota.objects.all(), many=True, write_only=True, required=False
    )
    aplicacion_automatica = serializers.BooleanField(write_only=True, required=False, default=False)
    registrado_por_nombre = serializers.CharField(source="registrado_por.username", read_only=True)
    usuario_nombre = serializers.CharField(source="registrado_por.username", read_only=True)
    anulado_por_nombre = serializers.CharField(source="anulado_por.username", read_only=True)
    importe_aplicado = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    saldo_a_favor = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    aplicaciones = AplicacionPagoSerializer(many=True, read_only=True)

    class Meta:
        model = Pago
        fields = [
            "id",
            "alumno",
            "alumno_nombre",
            "alumno_legajo",
            "concepto",
            "cuota",
            "cuotas",
            "aplicacion_automatica",
            "concepto_nombre",
            "sucursal",
            "sucursal_nombre",
            "fecha",
            "importe",
            "medio",
            "observacion",
            "numero_recibo",
            "registrado_por_nombre",
            "usuario_nombre",
            "estado",
            "motivo_anulacion",
            "anulado_en",
            "anulado_por_nombre",
            "importe_aplicado",
            "saldo_a_favor",
            "saldo_pendiente_posterior",
            "aplicaciones",
        ]
        read_only_fields = [
            "numero_recibo",
            "registrado_por_nombre",
            "estado",
            "motivo_anulacion",
            "anulado_en",
            "anulado_por_nombre",
            "saldo_pendiente_posterior",
        ]

    def validate(self, attrs):
        alumno = attrs.get("alumno") or getattr(self.instance, "alumno", None)
        concepto = attrs.get("concepto") or getattr(self.instance, "concepto", None)
        importe = attrs.get("importe")
        cuota = attrs.get("cuota")
        cuotas = attrs.get("cuotas", [])
        aplicacion_automatica = attrs.get("aplicacion_automatica", False)
        request = self.context.get("request")
        perfil = getattr(getattr(request, "user", None), "perfil", None)
        if importe is not None and importe <= 0:
            raise serializers.ValidationError("El importe del pago debe ser mayor que cero.")
        if alumno and perfil and not perfil.puede_ver_todas_las_sucursales and alumno.sucursal_id != perfil.sucursal_id:
            raise serializers.ValidationError("No puede registrar pagos de otra sucursal.")
        if alumno and concepto and alumno.sucursal_id != concepto.sucursal_id:
            raise serializers.ValidationError("El concepto debe pertenecer a la misma sucursal del alumno.")
        cuotas_seleccionadas = ([cuota] if cuota else []) + list(cuotas)
        if aplicacion_automatica and cuotas_seleccionadas:
            raise serializers.ValidationError("No puede combinar aplicación automática con cuotas seleccionadas.")
        for cuota_item in cuotas_seleccionadas:
            if cuota_item.alumno_id != alumno.id:
                raise serializers.ValidationError("Todas las cuotas deben pertenecer al alumno seleccionado.")
            if cuota_item.sucursal_id != alumno.sucursal_id:
                raise serializers.ValidationError("Todas las cuotas deben pertenecer a la misma sucursal del alumno.")
            if cuota_item.estado == Cuota.Estado.ANULADA or cuota_item.saldo <= 0:
                raise serializers.ValidationError("Una de las cuotas seleccionadas no tiene saldo pendiente.")
        if cuota and concepto and concepto.id != cuota.concepto_id:
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
    dias_mora = serializers.SerializerMethodField()
    segmento_morosidad = serializers.SerializerMethodField()

    class Meta:
        model = Alumno
        fields = [
            "id", "alumno", "nombre", "apellido", "dni", "legajo", "telefono", "email",
            "sucursal", "sucursal_nombre", "carrera", "carrera_nombre", "deuda_total",
            "cuotas_pendientes", "cuotas_vencidas", "cuota_vencida_mas_antigua", "fecha_ultimo_pago",
            "dias_mora", "segmento_morosidad",
        ]

    def get_dias_mora(self, obj):
        if not obj.cuota_vencida_mas_antigua:
            return 0
        return max((timezone.localdate() - obj.cuota_vencida_mas_antigua).days, 0)

    def get_segmento_morosidad(self, obj):
        cantidad = obj.cuotas_vencidas or 0
        if cantidad >= 3:
            return "3 o más cuotas"
        if cantidad == 2:
            return "2 cuotas"
        if cantidad == 1:
            return "1 cuota"
        return "Sin cuotas vencidas"

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
    usuario_nombre = serializers.CharField(source="caja.usuario.username", read_only=True)
    pago_numero_recibo = serializers.CharField(source="pago.numero_recibo", read_only=True)

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
            "pago_numero_recibo",
            "movimiento_origen",
            "usuario_nombre",
            "creado",
        ]
        read_only_fields = ["pago", "movimiento_origen"]

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


class CajaResumenSerializer(serializers.Serializer):
    saldo_inicial = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    cobranzas_efectivo = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    otros_ingresos_efectivo = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    egresos_efectivo = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    retiros_efectivo = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    efectivo_esperado = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_ingresos = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_egresos = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_cobrado = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    efectivo = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    transferencia = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    mercado_pago = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    tarjeta = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    otro = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)


class CajaDiariaSerializer(serializers.ModelSerializer):
    sucursal_nombre = serializers.CharField(source="sucursal.nombre", read_only=True)
    usuario_nombre = serializers.CharField(source="usuario.username", read_only=True)
    movimientos = MovimientoCajaSerializer(many=True, read_only=True)
    total_esperado = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    diferencia = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    resumen = CajaResumenSerializer(read_only=True)
    saldo_final_fisico = serializers.SerializerMethodField()

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
            "saldo_inicial",
            "total_contado",
            "total_esperado",
            "diferencia",
            "importe_retirado",
            "saldo_arrastrable",
            "saldo_final_fisico",
            "resumen",
            "cerrada_en",
            "movimientos",
        ]
        read_only_fields = [
            "usuario",
            "estado",
            "saldo_inicial",
            "total_contado",
            "importe_retirado",
            "saldo_arrastrable",
            "cerrada_en",
        ]

    def get_saldo_final_fisico(self, obj):
        if obj.estado == CajaDiaria.Estado.CERRADA:
            return obj.total_contado
        return obj.total_esperado


class EventoAuditoriaSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.CharField(source="usuario.username", read_only=True)
    sucursal_nombre = serializers.CharField(source="sucursal.nombre", read_only=True)

    class Meta:
        model = EventoAuditoria
        fields = [
            "id", "creado", "usuario", "usuario_nombre", "sucursal", "sucursal_nombre",
            "modulo", "accion", "entidad", "entidad_id", "descripcion",
            "valores_anteriores", "valores_nuevos", "metadata",
        ]
        read_only_fields = fields


class AplicacionCobroItemSerializer(serializers.Serializer):
    """Item de aplicacion dentro del payload de cobro.

    Acepta la cuota por id (`cuota_id`) o por objeto (`cuota`). El importe es
    obligatorio y debe ser positivo.
    """

    cuota_id = serializers.IntegerField(required=False)
    cuota = serializers.IntegerField(required=False)
    importe = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"))

    def validate(self, attrs):
        if attrs.get("cuota_id") is None and attrs.get("cuota") is None:
            raise serializers.ValidationError("Debe indicar la cuota a aplicar.")
        return attrs

    @property
    def cuota_pk(self):
        return self.validated_data.get("cuota_id") or self.validated_data.get("cuota")


class CobroSerializer(serializers.Serializer):
    """Input del endpoint `POST /api/pagos/cobrar/`.

    Crea un pago, lo aplica a las cuotas indicadas (o automatico a las mas
    antiguas) y registra el movimiento de caja del usuario, todo en una
    unica transaccion.

    Modos de aplicacion soportados:
    - ``aplicaciones`` ausente o lista vacia: pago a cuenta (sin aplicaciones).
    - ``aplicaciones = "auto"``: aplica a la cuota mas antigua primero hasta
      agotar el importe; el excedente queda como saldo a favor.
    - ``aplicaciones = [{cuota_id, importe}, ...]``: aplica exactamente esos
      importes a esas cuotas.
    """

    MODO_AUTOMATICO = "auto"

    alumno = serializers.PrimaryKeyRelatedField(queryset=Alumno.objects.all())
    importe = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"))
    medio = serializers.ChoiceField(choices=Pago.Medio.choices, default=Pago.Medio.EFECTIVO)
    observacion = serializers.CharField(required=False, allow_blank=True, default="")
    concepto = serializers.PrimaryKeyRelatedField(
        queryset=ConceptoCobrable.objects.all(),
        required=False,
        allow_null=True,
    )
    aplicaciones = serializers.ListField(
        child=AplicacionCobroItemSerializer(),
        required=False,
        allow_empty=True,
    )
    modo_automatico = serializers.BooleanField(required=False, default=False)

    def validate_aplicaciones(self, value):
        if not value:
            return value
        cuota_ids = []
        for item in value:
            if "cuota_id" in item and item["cuota_id"] is not None:
                cuota_ids.append(item["cuota_id"])
            elif "cuota" in item and item["cuota"] is not None:
                cuota_ids.append(item["cuota"])
        if len(cuota_ids) != len(set(cuota_ids)):
            raise serializers.ValidationError("No se puede aplicar mas de una vez a la misma cuota.")
        return value

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None) if request else None
        perfil = getattr(user, "perfil", None)
        alumno = attrs.get("alumno")
        concepto = attrs.get("concepto")

        if perfil and not perfil.puede_ver_todas_las_sucursales and alumno.sucursal_id != perfil.sucursal_id:
            raise serializers.ValidationError({"alumno": "No puede registrar cobros de otra sucursal."})
        if concepto and alumno.sucursal_id != concepto.sucursal_id:
            raise serializers.ValidationError(
                {"concepto": "El concepto debe pertenecer a la misma sucursal del alumno."}
            )

        # Validacion de importes contra saldo de cuotas cuando el modo es manual.
        aplicaciones = attrs.get("aplicaciones") or []
        if aplicaciones and not attrs.get("modo_automatico", False):
            cuota_ids = []
            importe_por_cuota = {}
            for item in aplicaciones:
                cid = item.get("cuota_id") or item.get("cuota")
                if cid is None:
                    continue
                cuota_ids.append(cid)
                importe_por_cuota[cid] = item["importe"]
            cuotas = {
                cuota.id: cuota
                for cuota in Cuota.objects.filter(id__in=cuota_ids, alumno=alumno)
            }
            faltantes = set(cuota_ids) - set(cuotas.keys())
            if faltantes:
                raise serializers.ValidationError(
                    {"aplicaciones": f"Cuotas inexistentes o de otro alumno: {sorted(faltantes)}."}
                )
            anuladas = [cuota_id for cuota_id, cuota in cuotas.items() if cuota.estado == Cuota.Estado.ANULADA]
            if anuladas:
                raise serializers.ValidationError(
                    {"aplicaciones": f"No se puede aplicar a cuotas anuladas: {anuladas}."}
                )
            suma = sum(importe_por_cuota.values(), Decimal("0"))
            if suma > attrs["importe"]:
                raise serializers.ValidationError(
                    {"aplicaciones": "La suma de aplicaciones supera el importe del pago."}
                )
            for cid, importe in importe_por_cuota.items():
                cuota = cuotas[cid]
                if importe > cuota.saldo:
                    raise serializers.ValidationError(
                        {
                            "aplicaciones": (
                                f"La aplicacion a la cuota {cuota.id} supera su saldo "
                                f"({importe} > {cuota.saldo})."
                            )
                        }
                    )
        return attrs
