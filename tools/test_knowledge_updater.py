"""test_knowledge_updater.py — Skill 209: in-game-photography-cinematography

Unit tests for the knowledge crawl pipeline. These run offline (no network)
and validate hashing/dedup, the composite score, entry formatting, dedup
filtering on append, and the config invariant.

Run:
    python tools/test_knowledge_updater.py
"""
from __future__ import annotations

import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import knowledge_updater as ku  # noqa: E402
from config import KnowledgeConfig, ScoringWeights  # noqa: E402


def test_hash_stable() -> None:
    a = ku.compute_hash("https://x.com/1")
    b = ku.compute_hash("https://x.com/1")
    c = ku.compute_hash("  HTTPS://X.COM/1  ")
    assert a == b, "identical identifiers must hash equal"
    assert a == c, "hash must be case/whitespace-insensitive"
    assert ku.compute_hash("https://x.com/2") != a, "different identifiers differ"
    print("[OK] dedup hash stable + normalized")


def test_score_bounds() -> None:
    kw = ku.KNOWLEDGE_CONFIG.keywords
    now = datetime.datetime.now()
    entry = {
        "title": ku.KNOWLEDGE_CONFIG.domain,
        "abstract": ku.KNOWLEDGE_CONFIG.domain,
        "published_date": now,
        "citation_count": 10,
    }
    s = ku.score_entry(entry, kw, now)
    assert 0.0 <= s <= 10.0, f"score out of range: {s}"
    assert isinstance(s, float)
    print(f"[OK] score={s} within [0,10]")


def test_score_recency_decays() -> None:
    kw = ["test"]
    now = datetime.datetime.now()
    fresh = ku.score_entry(
        {"title": "test", "abstract": "test", "published_date": now, "citation_count": 0},
        kw, now,
    )
    old = ku.score_entry(
        {
            "title": "test",
            "abstract": "test",
            "published_date": now - datetime.timedelta(days=720),
            "citation_count": 0,
        },
        kw, now,
    )
    assert fresh >= old, "fresh entries should score >= stale entries"
    print(f"[OK] recency decay fresh={fresh} >= old={old}")


def test_format_entry() -> None:
    txt = ku.format_entry(
        {
            "title": "T",
            "authors": ["A"],
            "year": 2026,
            "venue": "V",
            "doi_or_url": "https://x",
            "abstract": "ab",
        },
        5.0,
    )
    assert "DOI/URL:" in txt
    assert "Relevance Score:" in txt
    assert "5.00/10" in txt
    assert "Authors:** A" in txt
    print("[OK] format_entry")


def test_append_dedup(tmp_path: Path) -> None:
    brain = tmp_path / "brain.md"
    brain.write_text(
        "## 2. Key\n| T | A | 2026 | V | https://already |\n## 7. Knowledge Update Log\n",
        encoding="utf-8",
    )
    existing_before = ku.load_existing_hashes(brain)
    assert any(
        ku.compute_hash("https://already") == h for h in existing_before
    ), "existing URL must be loaded"

    entries = [
        {"title": "New", "authors": ["A"], "year": 2026, "venue": "V",
         "doi_or_url": "https://new-1", "abstract": "ab",
         "published_date": datetime.datetime.now(), "citation_count": 0},
        {"title": "Dup", "authors": ["A"], "year": 2026, "venue": "V",
         "doi_or_url": "https://already", "abstract": "ab",
         "published_date": datetime.datetime.now(), "citation_count": 0},
    ]
    n = ku.append_to_brain(entries, ku.KNOWLEDGE_CONFIG, dry_run=True, brain_path=brain)
    assert n == 1, f"expected 1 new after dedup, got {n}"
    print("[OK] append dedup skips existing")


def test_config_invariant() -> None:
    cfg = KnowledgeConfig()
    cfg.validate()  # should not raise
    assert abs(cfg.scoring_weights.total() - 1.0) < 1e-6
    bad = KnowledgeConfig(scoring_weights=ScoringWeights(0.1, 0.1, 0.1))
    raised = False
    try:
        bad.validate()
    except ValueError:
        raised = True
    assert raised, "weights not summing to 1.0 must raise"
    print("[OK] config invariant enforced")


def test_candidate_dataclass() -> None:
    c = ku.Candidate(
        title="T", authors=["A"], year=2026, venue="V", doi_or_url="https://x/1",
        abstract="ab", published_date=None, citation_count=0, source="test",
    )
    assert c.key() == "https://x/1"
    assert c.score == 0.0
    print("[OK] Candidate dataclass")


def main() -> int:
    tests = [
        test_hash_stable,
        test_score_bounds,
        test_score_recency_decays,
        test_format_entry,
        test_append_dedup,
        test_config_invariant,
        test_candidate_dataclass,
    ]
    for t in tests:
        # Give the append test a temp dir.
        if t is test_append_dedup:
            import tempfile
            with tempfile.TemporaryDirectory() as d:
                t(Path(d))
        else:
            t()
    print(f"\n[{len(tests)}/{len(tests)}] all knowledge_updater tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())