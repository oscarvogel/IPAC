from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import ChatbotConversation, ChatbotMessage

from .knowledge import QUICK_SUGGESTIONS
from .service import answer_message


GREETING = (
    "Hola, soy el Asistente IPAC. Puedo explicarte cómo usar el sistema: "
    "alta de alumnos, matrículas, cuotas, pagos, estado de cuenta y caja."
)


def _conversation_for_user(user, conversation_id):
    return get_object_or_404(
        ChatbotConversation.objects.select_related("usuario", "sucursal"),
        pk=conversation_id,
        usuario=user,
    )


def _serialize_message(message):
    return {
        "id": message.id,
        "role": message.role,
        "content": message.content,
        "created_at": message.creado,
    }


class ChatbotBriefingView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            {
                "title": "Asistente IPAC",
                "headline": "¿Qué necesitás hacer?",
                "suggestions": QUICK_SUGGESTIONS,
            }
        )


class ChatbotConversationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        profile = getattr(request.user, "perfil", None)
        if profile is None:
            return Response(
                {"detail": "El usuario no tiene un perfil operativo configurado."},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        conversation = ChatbotConversation.objects.create(
            usuario=request.user,
            sucursal=profile.sucursal,
            titulo=(request.data.get("title") or "Asistente IPAC")[:160],
        )
        greeting = ChatbotMessage.objects.create(
            conversacion=conversation,
            role=ChatbotMessage.Role.ASSISTANT,
            content=GREETING,
        )
        return Response(
            {
                "conversation": {
                    "id": conversation.id,
                    "title": conversation.titulo,
                    "created_at": conversation.creado,
                },
                "messages": [_serialize_message(greeting)],
            },
            status=status.HTTP_201_CREATED,
        )


class ChatbotHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        conversation_id = request.query_params.get("conversation_id")
        if not conversation_id:
            return Response(
                {"detail": "conversation_id es obligatorio."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        conversation = _conversation_for_user(request.user, conversation_id)
        messages = list(conversation.mensajes.order_by("creado", "id")[:50])
        return Response(
            {
                "conversation": {
                    "id": conversation.id,
                    "title": conversation.titulo,
                },
                "messages": [_serialize_message(message) for message in messages],
            }
        )


class ChatbotMessageView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        conversation_id = request.data.get("conversation_id")
        content = str(request.data.get("content") or "").strip()

        if not conversation_id:
            return Response(
                {"detail": "conversation_id es obligatorio."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not content:
            return Response(
                {"detail": "El mensaje no puede estar vacío."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if len(content) > 4000:
            return Response(
                {"detail": "El mensaje es demasiado largo."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        conversation = _conversation_for_user(request.user, conversation_id)
        user_message = ChatbotMessage.objects.create(
            conversacion=conversation,
            role=ChatbotMessage.Role.USER,
            content=content,
        )

        history = list(
            conversation.mensajes.exclude(pk=user_message.pk)
            .order_by("-creado", "-id")
            .values("role", "content")[:12]
        )
        history.reverse()

        result = answer_message(request.user, content, history)
        assistant_message = ChatbotMessage.objects.create(
            conversacion=conversation,
            role=ChatbotMessage.Role.ASSISTANT,
            content=result["content"],
            tokens_used=result["tokens_used"],
        )

        conversation.save(update_fields=["actualizado"])

        return Response(
            {
                "messages": [
                    _serialize_message(user_message),
                    _serialize_message(assistant_message),
                ],
                "source": result["source"],
                "procedure": result["procedure"],
                "action": result["action"],
            }
        )
