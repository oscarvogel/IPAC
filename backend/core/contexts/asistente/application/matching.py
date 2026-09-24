import re
import unicodedata
from difflib import SequenceMatcher

from ..domain.models import KnowledgeArticleData


STOPWORDS = {
    "a", "al", "como", "de", "del", "el", "en", "la", "las", "lo", "los",
    "me", "para", "por", "que", "se", "un", "una", "y",
}


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFD", (value or "").lower())
    value = "".join(char for char in value if unicodedata.category(char) != "Mn")
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _meaningful_tokens(value: str) -> list[str]:
    return [
        token
        for token in normalize_text(value).split()
        if token not in STOPWORDS and len(token) > 2
    ]


def _token_match_score(message: str, alias: str) -> float:
    message_tokens = _meaningful_tokens(message)
    alias_tokens = _meaningful_tokens(alias)
    if not alias_tokens:
        return 0.0

    hits = 0
    for expected in alias_tokens:
        if any(
            expected == actual
            or SequenceMatcher(None, expected, actual).ratio() >= 0.78
            for actual in message_tokens
        ):
            hits += 1
    return hits / len(alias_tokens)


def best_article_match(
    message: str,
    articles: list[KnowledgeArticleData],
) -> KnowledgeArticleData | None:
    normalized = normalize_text(message)
    if not normalized:
        return None

    best = None
    best_score = 0.0
    for article in articles:
        for alias in article.aliases:
            normalized_alias = normalize_text(alias)
            if normalized_alias and normalized_alias in normalized:
                return article
            score = max(
                SequenceMatcher(None, normalized, normalized_alias).ratio(),
                _token_match_score(normalized, normalized_alias),
            )
            if score > best_score:
                best = article
                best_score = score
    return best if best_score >= 0.72 else None


def format_article(article: KnowledgeArticleData) -> str:
    lines = [article.title, ""]
    lines.extend(f"{index}. {step}" for index, step in enumerate(article.steps, start=1))
    if article.notes:
        lines.extend(["", "A tener en cuenta:"])
        lines.extend(f"- {note}" for note in article.notes)
    return "\n".join(lines)


def format_articles_for_prompt(articles: list[KnowledgeArticleData]) -> str:
    blocks = []
    for article in articles:
        block = [article.title]
        block.extend(f"- {step}" for step in article.steps)
        block.extend(f"- Nota: {note}" for note in article.notes)
        if article.route:
            block.append(f"- Ruta: {article.route}")
        blocks.append("\n".join(block))
    return "\n\n".join(blocks)
