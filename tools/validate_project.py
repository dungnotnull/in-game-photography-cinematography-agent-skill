"""validate_project.py — Skill 209: in-game-photography-cinematography

Lightweight 8-File Contract validator used by CI and the Phase 5 gate. It
checks that the mandatory deliverables exist and that each carries the
required structural anchors. For the deep domain + scenario coverage checks
use ``run_test_scenarios.py``.

Exit code 0 = pass.

Run:
    python tools/validate_project.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CONTRACT = {
    "CLAUDE.md": ["Skill Identity", "Harness Flow", "Sub-Skills"],
    "PROJECT-detail.md": ["Harness Architecture", "Idea (Vietnamese)"],
    "PROJECT-DEVELOPMENT-PHASE-TRACKING.md": ["100%", "Phase 5"],
    "README.md": ["Usage", "Installation"],
    "SECOND-KNOWLEDGE-BRAIN.md": ["Tier 1", "Tier 4", "## 7. Knowledge Update Log"],
    "skills/main.md": ["Harness Execution Protocol", "Quality Gates",
                       "Graceful Degradation"],
    "skills/sub-gather-requirements.md": ["Role & Persona", "Workflow"],
    "skills/sub-evidence-collector.md": ["Role & Persona", "Workflow"],
    "skills/sub-core-analysis.md": ["Role & Persona", "Workflow"],
    "skills/sub-knowledge-updater.md": ["Role & Persona", "Workflow"],
    "skills/sub-advisor.md": ["Role & Persona", "Workflow"],
    "tools/knowledge_updater.py": ["KNOWLEDGE_CONFIG", "compute_hash", "score_entry"],
    "tools/test_knowledge_updater.py": ["def test_hash", "def main"],
    "tools/run_test_scenarios.py": ["def run", "def main"],
}


def validate() -> int:
    failures: list[str] = []
    for rel, anchors in CONTRACT.items():
        path = ROOT / rel
        if not path.exists():
            failures.append(f"missing file: {rel}")
            continue
        text = path.read_text(encoding="utf-8")
        for anchor in anchors:
            if anchor not in text:
                failures.append(f"{rel}: missing anchor '{anchor}'")
    if failures:
        print(f"[validate_project] {len(failures)} failure(s):")
        for f in failures:
            print(f"  - {f}")
        return 1
    print(f"[validate_project] {len(CONTRACT)} files validated — 8-File Contract PASS")
    return 0


if __name__ == "__main__":
    sys.exit(validate())