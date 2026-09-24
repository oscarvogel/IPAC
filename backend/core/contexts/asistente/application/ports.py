from typing import Protocol

from ..domain.models import Classification, KnowledgeArticleData


class AIIntentClassifier(Protocol):
    def classify(
        self,
        *,
        question: str,
        history: list[dict],
        tool_names: tuple[str, ...],
        role_context: str,
    ) -> Classification:
        ...


class KnowledgeRepository(Protocol):
    def find_match(self, message: str, role: str) -> KnowledgeArticleData | None:
        ...

    def prompt_context(self, role: str) -> str:
        ...


class AssistantRepository(Protocol):
    def register_unresolved(
        self,
        *,
        user,
        question: str,
        category: str,
        response: str,
        conversation=None,
        user_message=None,
        intent: str = "",
        tool: str = "",
        metadata: dict | None = None,
    ):
        ...


class AssistantNotifier(Protocol):
    def notify_immediate(self, event_id: int) -> bool:
        ...
