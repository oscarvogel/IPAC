from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from core.contexts.auditoria.application.registrar_evento import RegistrarEventoAuditoria
from core.contexts.auditoria.infrastructure.django_auditoria_repository import DjangoAuditoriaRepository
from core.models import (
    AsistenteConfig,
    AsistenteConsultaNoResuelta,
    AsistenteKnowledgeArticle,
)
from core.permissions import AssistantConfigPermission, AssistantKnowledgePermission

from ..application.no_resueltas import resolver_consulta
from .serializers import (
    AsistenteConfigSerializer,
    AsistenteConsultaNoResueltaSerializer,
    AsistenteKnowledgeArticleSerializer,
)


def _audit(request, *, action_name, instance, description="", metadata=None):
    profile = getattr(request.user, "perfil", None)
    RegistrarEventoAuditoria(DjangoAuditoriaRepository()).execute(
        usuario=request.user,
        sucursal=getattr(profile, "sucursal", None),
        modulo="asistente",
        accion=action_name,
        entidad=f"{instance._meta.app_label}.{instance.__class__.__name__}",
        entidad_id=instance.pk,
        descripcion=description,
        metadata=metadata or {},
    )


class AsistenteKnowledgeViewSet(viewsets.ModelViewSet):
    serializer_class = AsistenteKnowledgeArticleSerializer
    permission_classes = [AssistantKnowledgePermission]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        qs = AsistenteKnowledgeArticle.objects.select_related(
            "creado_por", "actualizado_por"
        ).all()
        if module := self.request.query_params.get("modulo"):
            qs = qs.filter(modulo=module)
        if active := self.request.query_params.get("activo"):
            if active.lower() in {"1", "true", "si", "sí"}:
                qs = qs.filter(activo=True)
            elif active.lower() in {"0", "false", "no"}:
                qs = qs.filter(activo=False)
        if search := self.request.query_params.get("search", "").strip():
            qs = qs.filter(
                Q(titulo__icontains=search)
                | Q(clave__icontains=search)
                | Q(descripcion__icontains=search)
            )
        return qs

    def perform_create(self, serializer):
        article = serializer.save(
            creado_por=self.request.user,
            actualizado_por=self.request.user,
        )
        _audit(
            self.request,
            action_name="alta",
            instance=article,
            description=f"Artículo de conocimiento creado: {article.titulo}",
        )

    def perform_update(self, serializer):
        article = serializer.save(actualizado_por=self.request.user)
        _audit(
            self.request,
            action_name="modificacion",
            instance=article,
            description=f"Artículo de conocimiento actualizado: {article.titulo}",
        )

    @action(detail=True, methods=["post"])
    def activar(self, request, pk=None):
        article = self.get_object()
        article.activo = True
        article.actualizado_por = request.user
        article.save(update_fields=["activo", "actualizado_por", "actualizado"])
        _audit(request, action_name="activacion", instance=article)
        return Response(self.get_serializer(article).data)

    @action(detail=True, methods=["post"])
    def desactivar(self, request, pk=None):
        article = self.get_object()
        article.activo = False
        article.actualizado_por = request.user
        article.save(update_fields=["activo", "actualizado_por", "actualizado"])
        _audit(request, action_name="desactivacion", instance=article)
        return Response(self.get_serializer(article).data)


class AsistenteConsultaNoResueltaViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AsistenteConsultaNoResueltaSerializer
    permission_classes = [AssistantKnowledgePermission]

    def get_queryset(self):
        qs = AsistenteConsultaNoResuelta.objects.select_related(
            "usuario",
            "sucursal",
            "articulo",
            "resuelto_por",
        )
        if state := self.request.query_params.get("estado"):
            qs = qs.filter(estado=state)
        if category := self.request.query_params.get("categoria"):
            qs = qs.filter(categoria=category)
        if branch := self.request.query_params.get("sucursal"):
            qs = qs.filter(sucursal_id=branch)
        if user := self.request.query_params.get("usuario"):
            qs = qs.filter(usuario_id=user)
        if search := self.request.query_params.get("search", "").strip():
            qs = qs.filter(pregunta__icontains=search)
        return qs

    @action(detail=True, methods=["post"])
    def resolver(self, request, pk=None):
        event = self.get_object()
        resolver_consulta(event, user=request.user)
        _audit(request, action_name="resolucion", instance=event)
        return Response(self.get_serializer(event).data)

    @action(detail=True, methods=["post"])
    def ignorar(self, request, pk=None):
        event = self.get_object()
        resolver_consulta(event, user=request.user, ignored=True)
        _audit(request, action_name="ignorar", instance=event)
        return Response(self.get_serializer(event).data)

    @action(detail=True, methods=["post"], url_path="crear-articulo")
    def crear_articulo(self, request, pk=None):
        event = self.get_object()
        payload = request.data.copy()
        aliases = list(payload.get("preguntas_equivalentes") or [])
        if event.pregunta not in aliases:
            aliases.insert(0, event.pregunta)
        payload["preguntas_equivalentes"] = aliases
        serializer = AsistenteKnowledgeArticleSerializer(
            data=payload,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        article = serializer.save(
            creado_por=request.user,
            actualizado_por=request.user,
        )
        resolver_consulta(event, user=request.user, article=article)
        _audit(
            request,
            action_name="alta",
            instance=article,
            description=f"Artículo creado desde consulta no resuelta #{event.id}",
        )
        _audit(
            request,
            action_name="resolucion",
            instance=event,
            description=f"Resuelta con artículo #{article.id}",
        )
        return Response(
            AsistenteKnowledgeArticleSerializer(article).data,
            status=status.HTTP_201_CREATED,
        )


class AsistenteConfigView(APIView):
    permission_classes = [AssistantConfigPermission]

    def get(self, request):
        config = AsistenteConfig.get_solo()
        return Response(AsistenteConfigSerializer(config).data)

    def patch(self, request):
        config = AsistenteConfig.get_solo()
        serializer = AsistenteConfigSerializer(
            config,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        config = serializer.save(actualizado_por=request.user)
        _audit(
            request,
            action_name="configuracion",
            instance=config,
            description="Configuración de notificaciones del asistente actualizada",
        )
        return Response(AsistenteConfigSerializer(config).data)
