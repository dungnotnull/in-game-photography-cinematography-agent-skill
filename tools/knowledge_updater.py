"""knowledge_updater.py — Skill 209: in-game-photography-cinematography

Production-grade crawl pipeline for the living knowledge base
(``SECOND-KNOWLEDGE-BRAIN.md``). It fetches candidate references from
Semantic Scholar, ArXiv, and RSS feeds, deduplicates them by a SHA256 of
their DOI/URL/ISBN, scores them on a 0–10 composite, and appends the
highest-scoring new entries to the knowledge base.

The module is import-safe: every optional dependency is loaded lazily so the
unit tests can run without network access.

Usage:
    python tools/knowledge_updater.py [--dry-run] [--news-only] [--keywords KEY ...]

Exit codes:
    0 — pipeline ran (entries appended or none new)
    1 — fatal misconfiguration / filesystem error
"""
from __future__ import annotations

import argparse
import hashlib
import logging
import math
import re
import sys
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set

# Make config importable whether run as a script or a module.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import BRAIN_PATH, KNOWLEDGE_CONFIG, KnowledgeConfig, LOG_DIR, LOG_PATH  # noqa: E402

try:
    import requests
except ImportError:  # pragma: no cover - optional at import time
    requests = None  # type: ignore[assignment]

try:
    import feedparser
except ImportError:  # pragma: no cover - optional at import time
    feedparser = None  # type: ignore[assignment]

try:
    from dateutil import parser as date_parser
except ImportError:  # pragma: no cover
    date_parser = None  # type: ignore[assignment]


# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
def _build_logger() -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("knowledge_updater")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

    file_handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(fmt)
    logger.addHandler(stream_handler)

    return logger


LOG = _build_logger()


# --------------------------------------------------------------------------- #
# Data model
# --------------------------------------------------------------------------- #
@dataclass
class Candidate:
    """A normalized reference candidate from any source."""

    title: str
    authors: List[str]
    year: int
    venue: str
    doi_or_url: str
    abstract: str
    published_date: Optional[datetime]
    citation_count: int
    source: str
    score: float = 0.0

    def key(self) -> str:
        """Stable dedup key (DOI/URL/ISBN, normalized)."""

        return self.doi_or_url.strip().lower()


# --------------------------------------------------------------------------- #
# Core helpers
# --------------------------------------------------------------------------- #
def compute_hash(identifier: str) -> str:
    """SHA256 of a normalized identifier for deduplication."""

    return hashlib.sha256(identifier.strip().lower().encode("utf-8")).hexdigest()


def load_existing_hashes(brain_path: Path = BRAIN_PATH) -> Set[str]:
    """Return SHA256 hashes of every DOI/URL/ISBN already in the brain."""

    if not brain_path.exists():
        return set()
    hashes: Set[str] = set()
    text = brain_path.read_text(encoding="utf-8")
    for pattern in (
        r"10\.\d{4,9}/[^\s|)]+",
        r"https?://\S+",
        r"ISBN\s*[: ]\s*[\d\-X]+",
    ):
        for match in re.finditer(pattern, text):
            hashes.add(compute_hash(match.group(0)))
    return hashes


def score_entry(
    entry: Dict[str, Any],
    keywords: Sequence[str],
    now: datetime,
    weights: Optional[Any] = None,
) -> float:
    """Composite 0–10 score: recency + keyword relevance + citation count."""

    if weights is None:
        weights = KNOWLEDGE_CONFIG.scoring_weights

    pub = entry.get("published_date")
    recency = 0.0
    if pub is not None:
        try:
            recency = max(0.0, 1.0 - (now - pub).days / 730.0)
        except (TypeError, ValueError):
            recency = 0.0

    text = (
        (entry.get("title") or "") + " " + (entry.get("abstract") or "")
    ).lower()
    hits = sum(1 for kw in keywords if kw.lower() in text)
    relevance = min(hits / max(len(keywords), 1), 1.0)

    cit = float(entry.get("citation_count", 0) or 0)
    cit_score = min(math.log1p(cit) / math.log1p(1000.0), 1.0)

    raw = (
        recency * weights.recency
        + relevance * weights.keyword_relevance
        + cit_score * weights.citation_count
    )
    return round(raw * 10.0, 2)


# --------------------------------------------------------------------------- #
# Network
# --------------------------------------------------------------------------- #
def fetch_with_retry(
    url: str,
    params: Optional[Dict[str, Any]] = None,
    config: KnowledgeConfig = KNOWLEDGE_CONFIG,
) -> Optional["requests.Response"]:
    """GET with retry/backoff and explicit handling of 429/5xx."""

    if requests is None:
        LOG.warning("requests not installed; skipping %s", url)
        return None

    last_error: Optional[str] = None
    for attempt in range(config.max_retries):
        if attempt > 0:
            time.sleep(config.base_retry_delay_seconds * (2 ** attempt))
        try:
            resp = requests.get(
                url, params=params or {}, timeout=config.request_timeout_seconds
            )
            if resp.status_code == 429:
                LOG.warning("429 rate-limited on %s (attempt %d)", url, attempt + 1)
                continue
            if resp.status_code >= 500:
                LOG.warning("server %d on %s (attempt %d)", resp.status_code, url, attempt + 1)
                continue
            resp.raise_for_status()
            return resp
        except requests.exceptions.RequestException as exc:
            last_error = str(exc)
            LOG.warning("request failed on %s (attempt %d): %s", url, attempt + 1, exc)
    LOG.error("exhausted retries for %s: %s", url, last_error)
    return None


# --------------------------------------------------------------------------- #
# Source fetchers — each returns a list[dict] of candidate entries
# --------------------------------------------------------------------------- #
def fetch_arxiv(keywords: Sequence[str], config: KnowledgeConfig = KNOWLEDGE_CONFIG) -> List[Dict[str, Any]]:
    if requests is None or not config.arxiv_categories:
        LOG.info("arxiv: skipped (no client or no categories)")
        return []

    cats = config.arxiv_categories
    kw_query = " AND ".join('all:"%s"' % k for k in keywords[:5])
    q = "(%s) AND (%s)" % (
        " OR ".join("cat:%s" % c for c in cats),
        kw_query,
    )
    resp = fetch_with_retry(
        config.arxiv_base,
        {
            "search_query": q,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
            "max_results": config.max_results_per_source,
        },
        config,
    )
    if resp is None:
        return []

    ns = {"atom": "http://www.w3.org/2005/Atom"}
    try:
        root = ET.fromstring(resp.content)
    except ET.ParseError as exc:
        LOG.error("arxiv XML parse failed: %s", exc)
        return []

    out: List[Dict[str, Any]] = []
    for entry in root.findall("atom:entry", ns):
        title_el = entry.find("atom:title", ns)
        id_el = entry.find("atom:id", ns)
        published_el = entry.find("atom:published", ns)
        summary_el = entry.find("atom:summary", ns)

        title = (title_el.text or "").strip().replace("\n", " ") if title_el is not None else ""
        url = (id_el.text or "").strip() if id_el is not None else ""
        if not title or not url:
            continue

        pub: Optional[datetime] = None
        if published_el is not None and published_el.text and date_parser is not None:
            try:
                pub = date_parser.parse(published_el.text).replace(tzinfo=None)
            except (TypeError, ValueError):
                pub = None

        authors: List[str] = []
        for author in entry.findall("atom:author", ns):
            name_el = author.find("atom:name", ns)
            if name_el is not None and name_el.text:
                authors.append(name_el.text)

        out.append(
            {
                "title": title,
                "authors": authors[:3],
                "year": pub.year if pub else datetime.now().year,
                "venue": "ArXiv",
                "doi_or_url": url,
                "abstract": (summary_el.text or "")[:300] if summary_el is not None else "",
                "published_date": pub,
                "citation_count": 0,
                "source": "arxiv",
            }
        )
    LOG.info("arxiv: %d candidates", len(out))
    return out


def fetch_semantic_scholar(
    keywords: Sequence[str], config: KnowledgeConfig = KNOWLEDGE_CONFIG
) -> List[Dict[str, Any]]:
    if requests is None:
        LOG.info("semantic scholar: skipped (no client)")
        return []

    resp = fetch_with_retry(
        config.semantic_scholar_base,
        {
            "query": " ".join(keywords[:4]),
            "fields": "title,authors,year,venue,externalIds,abstract,citationCount",
            "limit": config.max_results_per_source,
        },
        config,
    )
    if resp is None:
        return []
    try:
        data = resp.json()
    except ValueError as exc:
        LOG.error("semantic scholar JSON parse failed: %s", exc)
        return []

    out: List[Dict[str, Any]] = []
    for paper in data.get("data", []):
        title = paper.get("title", "")
        if not title:
            continue
        year = paper.get("year") or datetime.now().year
        ext = paper.get("externalIds", {}) or {}
        doi = ext.get("DOI") or (
            "https://arxiv.org/abs/%s" % ext["ArXiv"] if ext.get("ArXiv") else ""
        )
        if not doi:
            doi = "https://www.semanticscholar.org/paper/%s" % paper.get("paperId", "")
        pub_date: Optional[datetime] = None
        try:
            pub_date = datetime(int(year), 1, 1)
        except (TypeError, ValueError):
            pub_date = None
        out.append(
            {
                "title": title,
                "authors": [a.get("name", "") for a in (paper.get("authors", []) or [])[:3]],
                "year": year,
                "venue": paper.get("venue") or "Unknown",
                "doi_or_url": doi,
                "abstract": (paper.get("abstract") or "")[:300],
                "published_date": pub_date,
                "citation_count": paper.get("citationCount", 0) or 0,
                "source": "semantic_scholar",
            }
        )
    LOG.info("semantic scholar: %d candidates", len(out))
    return out


def fetch_rss(config: KnowledgeConfig = KNOWLEDGE_CONFIG) -> List[Dict[str, Any]]:
    if feedparser is None or not config.rss_feeds:
        LOG.info("rss: skipped (no client or no feeds)")
        return []

    out: List[Dict[str, Any]] = []
    for url in config.rss_feeds:
        try:
            feed = feedparser.parse(url)
        except Exception as exc:  # pragma: no cover - feedparser edge cases
            LOG.warning("rss %s failed: %s", url, exc)
            continue
        for item in getattr(feed, "entries", [])[:10]:
            title = item.get("title", "")
            link = item.get("link", "")
            if not title or not link:
                continue
            pp = item.get("published_parsed")
            pub = datetime(*pp[:6]) if pp else datetime.now()
            out.append(
                {
                    "title": title,
                    "authors": ["Editorial"],
                    "year": pub.year,
                    "venue": "RSS",
                    "doi_or_url": link,
                    "abstract": (item.get("summary", ""))[:200],
                    "published_date": pub,
                    "citation_count": 0,
                    "source": "rss",
                }
            )
    LOG.info("rss: %d candidates", len(out))
    return out


# --------------------------------------------------------------------------- #
# Formatting & append
# --------------------------------------------------------------------------- #
def format_entry(entry: Dict[str, Any], score: float) -> str:
    stamp = datetime.now().strftime("%Y-%m-%d")
    authors = ", ".join(entry.get("authors", [])) or "Unknown"
    return (
        "\n### %s — %s\n"
        "- **Authors:** %s\n"
        "- **Year:** %s\n"
        "- **Venue:** %s\n"
        "- **DOI/URL:** %s\n"
        "- **Relevance Score:** %.2f/10\n"
        "- **Key Finding:** %s\n"
    ) % (
        stamp,
        entry.get("title", "Untitled"),
        authors,
        entry.get("year", ""),
        entry.get("venue", "Unknown"),
        entry.get("doi_or_url", ""),
        score,
        entry.get("abstract", "No abstract available."),
    )


def append_to_brain(
    entries: Iterable[Dict[str, Any]],
    config: KnowledgeConfig = KNOWLEDGE_CONFIG,
    dry_run: bool = False,
    brain_path: Path = BRAIN_PATH,
) -> int:
    if not brain_path.exists():
        LOG.error("brain not found: %s", brain_path)
        return 0

    existing = load_existing_hashes(brain_path)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    new: List[Dict[str, Any]] = []

    for entry in entries:
        doi = entry.get("doi_or_url", "")
        if not doi:
            continue
        h = compute_hash(doi)
        if h in existing:
            continue
        existing.add(h)
        entry["_score"] = score_entry(entry, config.keywords, now, config.scoring_weights)
        new.append(entry)

    if not new:
        LOG.info("no new entries to append")
        return 0

    new.sort(key=lambda e: e["_score"], reverse=True)
    new = new[: config.max_new_entries_per_run]
    text = "".join(format_entry(e, e["_score"]) for e in new)

    if dry_run:
        LOG.info("[DRY-RUN] would append %d entries", len(new))
        return len(new)

    content = brain_path.read_text(encoding="utf-8")
    if "## 7. Knowledge Update Log" in content:
        content += text
    else:
        content += "\n## 7. Knowledge Update Log\n" + text
    brain_path.write_text(content, encoding="utf-8")
    LOG.info("appended %d entries to %s", len(new), brain_path)
    return len(new)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Crawl pipeline for the in-game-photography-cinematography knowledge base.",
    )
    parser.add_argument("--dry-run", action="store_true", help="score candidates but do not write")
    parser.add_argument(
        "--news-only",
        action="store_true",
        help="only fetch RSS news (skip academic sources)",
    )
    parser.add_argument(
        "--keywords",
        nargs="+",
        default=list(KNOWLEDGE_CONFIG.keywords),
        help="override crawl keywords",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    KNOWLEDGE_CONFIG.validate()
    LOG.info("start dry=%s news=%s", args.dry_run, args.news_only)

    candidates: List[Dict[str, Any]] = []
    if not args.news_only:
        candidates += fetch_arxiv(args.keywords, KNOWLEDGE_CONFIG)
        time.sleep(KNOWLEDGE_CONFIG.inter_source_delay_seconds)
        candidates += fetch_semantic_scholar(args.keywords, KNOWLEDGE_CONFIG)
        time.sleep(KNOWLEDGE_CONFIG.inter_source_delay_seconds)
    candidates += fetch_rss(KNOWLEDGE_CONFIG)

    LOG.info("total candidates: %d", len(candidates))
    appended = append_to_brain(candidates, KNOWLEDGE_CONFIG, args.dry_run)
    LOG.info("done; appended %d", appended)
    return 0


if __name__ == "__main__":
    sys.exit(main())