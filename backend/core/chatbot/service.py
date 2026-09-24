from core.contexts.asistente.application.responder_consulta import ResponderConsulta
from core.contexts.asistente.application.tools import ReadToolRegistry
from core.contexts.asistente.infrastructure.django_assistant_repository import DjangoAssistantRepository
from core.contexts.asistente.infrastructure.django_knowledge_repository import DjangoKnowledgeRepository
from core.contexts.asistente.infrastructure.django_reporting_gateway import DjangoReportingGateway
from core.contexts.asistente.infrastructure.minimax_provider import MiniMaxIntentClassifier


def answer_message(
    user,
    content,
    history,
    conversation=None,
    user_message=None,
):
    responder = ResponderConsulta(
        knowledge_repository=DjangoKnowledgeRepository(),
        classifier=MiniMaxIntentClassifier(),
        tool_registry=ReadToolRegistry(DjangoReportingGateway()),
        assistant_repository=DjangoAssistantRepository(),
    )
    result = responder.execute(
        user,
        content,
        history,
        conversation,
        user_message,
    )
    return {
        "content": result.content,
        "tokens_used": result.tokens_used,
        "source": result.source,
        "procedure": result.procedure,
        "action": result.action,
        "clarification": result.clarification,
    }
