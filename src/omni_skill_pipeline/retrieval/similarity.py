from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Iterable, Protocol, Sequence, runtime_checkable

from omni_skill_pipeline.models import SkillDocument

_TOKEN_PATTERN = re.compile(r'[a-z0-9]+')


def _tokenize(text: str) -> set[str]:
    return set(_TOKEN_PATTERN.findall(str(text).lower()))


def _normalize_tags(tags: Sequence[str]) -> tuple[str, ...]:
    normalized = []
    seen: set[str] = set()
    for item in tags:
        value = str(item).strip().lower()
        if not value or value in seen:
            continue
        seen.add(value)
        normalized.append(value)
    return tuple(normalized)


def _clamp_score(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


@dataclass(frozen=True, slots=True)
class SkillSearchDocument:
    skill_id: str
    name: str
    summary: str = ''
    domain: str = 'general'
    tags: tuple[str, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_skill_document(
        cls,
        skill: SkillDocument,
        *,
        domain: str = 'general',
        metadata: dict[str, Any] | None = None,
    ) -> 'SkillSearchDocument':
        return cls(
            skill_id=skill.skill_id,
            name=skill.name,
            summary=skill.summary,
            domain=domain.strip() or 'general',
            tags=_normalize_tags(skill.tags),
            metadata=dict(metadata or {}),
        )

    def tokenized_text(self) -> set[str]:
        return _tokenize('%s %s' % (self.name, self.summary))


@dataclass(frozen=True, slots=True)
class SimilarityQuery:
    text: str
    top_k: int = 5
    domain: str = ''
    tags: tuple[str, ...] = field(default_factory=tuple)

    def normalized_tags(self) -> tuple[str, ...]:
        return _normalize_tags(self.tags)

    def validate(self) -> None:
        if self.top_k < 1:
            raise ValueError('SimilarityQuery.top_k must be >= 1.')
        if not self.text.strip() and not self.domain.strip() and not self.tags:
            raise ValueError('SimilarityQuery requires text, domain, or tags.')


@dataclass(frozen=True, slots=True)
class SimilarityResult:
    skill_id: str
    score: float
    backend: str
    metadata: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class SimilarityBackend(Protocol):
    backend_name: str

    def index(self, documents: Sequence[SkillSearchDocument]) -> None:
        ...

    def search(self, query: SimilarityQuery) -> list[SimilarityResult]:
        ...


class BackendNotReadyError(RuntimeError):
    pass


class InMemorySimilarityBackend(SimilarityBackend):
    backend_name = 'inmemory'

    def __init__(
        self,
        *,
        domain_bonus: float = 0.15,
        tag_bonus: float = 0.1,
    ) -> None:
        self.domain_bonus = float(domain_bonus)
        self.tag_bonus = float(tag_bonus)
        self._indexed: list[tuple[SkillSearchDocument, set[str]]] = []

    def index(self, documents: Sequence[SkillSearchDocument]) -> None:
        self._indexed = [(item, item.tokenized_text()) for item in documents]

    def search(self, query: SimilarityQuery) -> list[SimilarityResult]:
        query.validate()
        if not self._indexed:
            return []

        query_tokens = _tokenize(query.text)
        query_domain = query.domain.strip().lower()
        query_tags = set(query.normalized_tags())
        ranked: list[SimilarityResult] = []

        for document, document_tokens in self._indexed:
            base_score = self._jaccard(query_tokens, document_tokens)
            domain_score = self._domain_score(query_domain, document.domain)
            tag_score, matched_tags = self._tag_score(query_tags, document.tags)
            total_score = _clamp_score(base_score + domain_score + tag_score)
            if total_score <= 0:
                continue
            ranked.append(
                SimilarityResult(
                    skill_id=document.skill_id,
                    score=total_score,
                    backend=self.backend_name,
                    metadata={
                        'name': document.name,
                        'domain': document.domain,
                        'tags': list(document.tags),
                        'base_score': round(base_score, 4),
                        'domain_score': round(domain_score, 4),
                        'tag_score': round(tag_score, 4),
                        'matched_tags': matched_tags,
                    },
                )
            )

        ranked.sort(key=lambda item: (-item.score, item.skill_id))
        return ranked[: query.top_k]

    def _jaccard(self, query_tokens: set[str], document_tokens: set[str]) -> float:
        if not query_tokens or not document_tokens:
            return 0.0
        union = query_tokens | document_tokens
        if not union:
            return 0.0
        intersection = query_tokens & document_tokens
        return float(len(intersection)) / float(len(union))

    def _domain_score(self, query_domain: str, document_domain: str) -> float:
        if not query_domain:
            return 0.0
        return self.domain_bonus if query_domain == document_domain.strip().lower() else 0.0

    def _tag_score(self, query_tags: set[str], document_tags: Sequence[str]) -> tuple[float, list[str]]:
        if not query_tags:
            return 0.0, []
        normalized_document_tags = set(_normalize_tags(document_tags))
        overlap = sorted(query_tags & normalized_document_tags)
        if not overlap:
            return 0.0, []
        ratio = float(len(overlap)) / float(len(query_tags))
        return self.tag_bonus * ratio, overlap


class _UnavailableSimilarityBackend(SimilarityBackend):
    def __init__(self, backend_name: str, reason: str) -> None:
        self.backend_name = backend_name
        self._reason = reason

    def index(self, documents: Sequence[SkillSearchDocument]) -> None:
        raise BackendNotReadyError('%s backend not ready: %s' % (self.backend_name, self._reason))

    def search(self, query: SimilarityQuery) -> list[SimilarityResult]:
        raise BackendNotReadyError('%s backend not ready: %s' % (self.backend_name, self._reason))


class PgVectorSimilarityBackend(_UnavailableSimilarityBackend):
    def __init__(self, *, dsn: str = '') -> None:
        reason = 'requires pgvector DDL/indexing pipeline wiring (dsn=%s).' % (dsn.strip() or '<empty>')
        super().__init__('pgvector', reason=reason)


class QdrantSimilarityBackend(_UnavailableSimilarityBackend):
    def __init__(self, *, url: str = '') -> None:
        reason = 'requires Qdrant collection/index sync wiring (url=%s).' % (url.strip() or '<empty>')
        super().__init__('qdrant', reason=reason)


def build_similarity_backend(
    backend: str = 'inmemory',
    *,
    pgvector_dsn: str = '',
    qdrant_url: str = '',
) -> SimilarityBackend:
    normalized = backend.strip().lower()
    if normalized in {'inmemory', 'memory', 'default'}:
        return InMemorySimilarityBackend()
    if normalized in {'pgvector', 'postgres', 'postgresql'}:
        return PgVectorSimilarityBackend(dsn=pgvector_dsn)
    if normalized == 'qdrant':
        return QdrantSimilarityBackend(url=qdrant_url)
    raise ValueError('Unknown similarity backend: %s' % backend)


class SimilarityRetriever(object):
    def __init__(self, backend: SimilarityBackend | None = None) -> None:
        self.backend = backend or InMemorySimilarityBackend()

    def index(self, documents: Sequence[SkillSearchDocument]) -> None:
        self.backend.index(documents)

    def index_skill_documents(
        self,
        skills: Sequence[SkillDocument],
        *,
        domain: str = 'general',
        metadata: dict[str, Any] | None = None,
    ) -> None:
        records = [
            SkillSearchDocument.from_skill_document(skill, domain=domain, metadata=metadata)
            for skill in skills
        ]
        self.index(records)

    def search(
        self,
        *,
        text: str,
        top_k: int = 5,
        domain: str = '',
        tags: Iterable[str] = (),
    ) -> list[SimilarityResult]:
        query = SimilarityQuery(
            text=text,
            top_k=top_k,
            domain=domain,
            tags=tuple(tags),
        )
        return self.backend.search(query)
