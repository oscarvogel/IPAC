from core.models import AsistenteKnowledgeArticle

from ..application.matching import best_article_match, format_articles_for_prompt
from ..domain.models import KnowledgeArticleData


def _to_data(article: AsistenteKnowledgeArticle) -> KnowledgeArticleData:
    return KnowledgeArticleData(
        id=article.id,
        key=article.clave,
        title=article.titulo,
        module=article.modulo,
        aliases=tuple(str(item) for item in (article.preguntas_equivalentes or [])),
        description=article.descripcion,
        steps=tuple(str(item) for item in (article.pasos or [])),
        route=article.ruta,
        action_label=article.action_label,
        permission_roles=tuple(str(item) for item in (article.roles_permitidos or [])),
        notes=tuple(str(item) for item in (article.notas or [])),
    )


class DjangoKnowledgeRepository:
    def active_for_role(self, role: str) -> list[KnowledgeArticleData]:
        articles = AsistenteKnowledgeArticle.objects.filter(activo=True).order_by(
            "orden", "titulo", "id"
        )
        return [
            _to_data(article)
            for article in articles
            if not article.roles_permitidos or role in article.roles_permitidos
        ]

    def find_match(self, message: str, role: str) -> KnowledgeArticleData | None:
        return best_article_match(message, self.active_for_role(role))

    def prompt_context(self, role: str) -> str:
        return format_articles_for_prompt(self.active_for_role(role))
