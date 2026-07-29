"""Central configuration for the in-game-photography-cinematography knowledge
crawl pipeline.

Keeping the configuration in one module makes the crawl targets, scoring
weights, and source lists auditable and easy to tune without touching the
pipeline logic. Every constant here is consumed by ``knowledge_updater.py``
and validated by ``test_knowledge_updater.py``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
BRAIN_PATH: Path = PROJECT_ROOT / "SECOND-KNOWLEDGE-BRAIN.md"
LOG_DIR: Path = PROJECT_ROOT / "logs"
LOG_PATH: Path = LOG_DIR / "knowledge_update.log"


@dataclass(frozen=True)
class ScoringWeights:
    """Composite-score weights (must sum to 1.0)."""

    recency: float = 0.4
    keyword_relevance: float = 0.4
    citation_count: float = 0.2

    def total(self) -> float:
        return self.recency + self.keyword_relevance + self.citation_count


@dataclass(frozen=True)
class KnowledgeConfig:
    """All tunable parameters for the crawl pipeline."""

    domain: str = "Virtual Photography & Game Cinematography"
    keywords: List[str] = field(
        default_factory=lambda: [
            "in-game photography composition",
            "virtual photography rule of thirds",
            "game cinematography camera angle",
            "photo mode game engine",
            "color grading screenshot",
            "leading lines framing virtual",
            "real-time path tracing photography",
            "virtual cinematography",
        ]
    )
    arxiv_categories: List[str] = field(
        default_factory=lambda: ["cs.GR", "cs.AI", "cs.HC"]
    )
    arxiv_base: str = "https://export.arxiv.org/api/query"
    semantic_scholar_base: str = "https://api.semanticscholar.org/graph/v1/paper/search"
    rss_feeds: List[str] = field(
        default_factory=lambda: [
            "https://www.gamedeveloper.com/rss",
            "https://www.unrealengine.com/en-US/rss",
            "https://80.lv/rss",
        ]
    )
    authoritative_docs: List[str] = field(
        default_factory=lambda: [
            "Proceedings of CHI PLAY (ACM)",
            "Game Studies (gamestudies.org)",
            "Entertainment Computing (Elsevier)",
            "Computers in Human Behavior (Elsevier)",
            "Leonardo (MIT Press)",
            "ACM Transactions on Graphics (SIGGRAPH)",
        ]
    )
    scoring_weights: ScoringWeights = field(default_factory=ScoringWeights)
    max_results_per_source: int = 10
    max_new_entries_per_run: int = 20
    request_timeout_seconds: int = 30
    max_retries: int = 3
    base_retry_delay_seconds: float = 2.0
    inter_source_delay_seconds: float = 1.0

    def validate(self) -> None:
        """Fail fast on a misconfigured config so the pipeline never silently
        produces garbage scores."""
        total = self.scoring_weights.total()
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"scoring weights must sum to 1.0, got {total}")
        if self.max_results_per_source <= 0:
            raise ValueError("max_results_per_source must be positive")
        if self.max_new_entries_per_run <= 0:
            raise ValueError("max_new_entries_per_run must be positive")


KNOWLEDGE_CONFIG = KnowledgeConfig()
KNOWLEDGE_CONFIG.validate()


def get_config() -> KnowledgeConfig:
    """Return the validated singleton config (importable by tests)."""

    return KNOWLEDGE_CONFIG