from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ScopeKind(StrEnum):
    IPAC = "ipac"
    OUT_OF_SCOPE = "out_of_scope"
    UNCERTAIN = "uncertain"


class IntentKind(StrEnum):
    KNOWLEDGE = "knowledge"
    READ_TOOL = "read_tool"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class Classification:
    scope: ScopeKind
    intent: IntentKind
    tool: str | None = None
    arguments: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class KnowledgeArticleData:
    id: int
    key: str
    title: str
    module: str
    aliases: tuple[str, ...]
    description: str
    steps: tuple[str, ...]
    route: str
    action_label: str
    permission_roles: tuple[str, ...]
    notes: tuple[str, ...]


@dataclass(frozen=True)
class ToolContext:
    user_id: int
    role: str
    sucursal_id: int
    global_access: bool


@dataclass(frozen=True)
class ToolResult:
    status: str
    data: dict[str, Any]
    scope_label: str
    as_of: str


@dataclass(frozen=True)
class AssistantResponse:
    content: str
    source: str
    procedure: str | None = None
    action: dict[str, str] | None = None
    clarification: dict[str, Any] | None = None
    tokens_used: int | None = None
