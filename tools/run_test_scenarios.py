"""run_test_scenarios.py — Skill 209: in-game-photography-cinematography

Production-grade structural & content validator. It enforces the project's
"8-File Contract" plus deep domain checks: sub-skill depth, quality-gate
coverage, evidence tiering in the knowledge base, the scenario coverage
matrix, and the crawl-pipeline contract.

Exit code 0 = all checks pass; non-zero = failures. Output is JSON-friendly
and human-readable.

Run:
    python tools/run_test_scenarios.py
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"

DOMAIN_GATES = ["G1", "G2", "G3", "G4"]
UNIVERSAL_GATES = ["U1", "U2", "U3", "U4", "U5", "U6"]
ALL_GATES = UNIVERSAL_GATES + DOMAIN_GATES
VERDICTS = [
    "Strong Composition",
    "Conditional (reframe)",
    "Weak Composition",
    "Inconclusive",
]


@dataclass
class Result:
    name: str
    passed: bool
    detail: str = ""

    def render(self) -> str:
        mark = "PASS" if self.passed else "FAIL"
        suffix = f" — {self.detail}" if self.detail else ""
        return f"  [{mark}] {self.name}{suffix}"


@dataclass
class Suite:
    results: List[Result] = field(default_factory=list)

    def add(self, cond: bool, name: str, detail: str = "") -> None:
        self.results.append(Result(name, bool(cond), detail))

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if not r.passed)


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8") if p.exists() else ""


FRONTMATTER = re.compile(r"^---\s*\n(.*?\n)---", re.S)


def run() -> Suite:
    suite = Suite()

    # ---- 1. Required files (8-File Contract) ----
    required = [
        "CLAUDE.md", "PROJECT-detail.md", "PROJECT-DEVELOPMENT-PHASE-TRACKING.md",
        "README.md", "SECOND-KNOWLEDGE-BRAIN.md", "skills/main.md",
        "tools/knowledge_updater.py", "tools/test_knowledge_updater.py",
        "tools/run_test_scenarios.py", "tools/validate_project.py",
        "tools/config.py", "tests/test-scenarios.md", "tests/TEST_RESULTS.md",
        "LICENSE", "pyproject.toml", "progression.json",
    ]
    for f in required:
        suite.add((ROOT / f).exists(), f"file present: {f}")

    subs = sorted(SKILLS.glob("sub-*.md"))
    expected_subs = {
        "sub-gather-requirements", "sub-evidence-collector", "sub-core-analysis",
        "sub-knowledge-updater", "sub-advisor",
    }
    got_subs = {s.stem for s in subs}
    suite.add(len(subs) >= 5, "at least 5 sub-skills", f"found {len(subs)}")
    suite.add(got_subs == expected_subs, "sub-skill set exact", f"got {got_subs}")

    # ---- 2. Sub-skill structure & depth ----
    for s in subs:
        txt = read(s)
        m = FRONTMATTER.search(txt)
        suite.add(bool(m), f"{s.name}: frontmatter")
        if m:
            suite.add("name:" in m.group(1) and "description:" in m.group(1),
                      f"{s.name}: name+description in frontmatter")
        for sec in ["Role & Persona", "Workflow", "Output Format", "Quality Gates"]:
            suite.add(sec in txt, f"{s.name}: section {sec}")
        suite.add(len(txt) >= 1200, f"{s.name}: depth (>=1200 chars)",
                  f"len={len(txt)}")

    # ---- 3. main.md harness ----
    main_txt = read(ROOT / "skills/main.md")
    for sec in ["Role & Persona", "Quality Gates", "Graceful Degradation",
                "Harness Execution Protocol", "Pre-Flight", "Sub-skills Available",
                "Output Format", "Tools"]:
        suite.add(sec in main_txt, f"main.md: section {sec}")
    suite.add("limitation" in main_txt.lower(), "main.md: limitation banner")
    suite.add(all(g in main_txt for g in ALL_GATES), "main.md: all gates U1-U6,G1-G4 present")

    # ---- 4. Domain depth checks (real cinematography content) ----
    core = read(ROOT / "skills/sub-core-analysis.md")
    for term in ["rule of thirds", "leading lines", "low-angle", "dutch",
                 "over-the-shoulder", "focal length", "golden ratio", "high-key",
                 "low-key", "teal-orange", "DOF", "FOV", "Bordwell", "Block",
                 "Freeman", "Itten"]:
        suite.add(term.lower() in core.lower(),
                  f"sub-core-analysis: domain term '{term}'")

    # ---- 5. Verdict coverage ----
    advisor = read(ROOT / "skills/sub-advisor.md")
    for v in VERDICTS:
        suite.add(v in advisor or v in main_txt, f"verdict '{v}' present")

    # ---- 6. Knowledge base ----
    brain = read(ROOT / "SECOND-KNOWLEDGE-BRAIN.md")
    suite.add("Tier 1" in brain and "Tier 4" in brain, "brain: evidence tiers 1 & 4")
    dois = re.findall(r"10\.\d{4,9}/[^\s|)]+", brain)
    suite.add(len(dois) >= 1, "brain: >=1 DOI-cited reference", f"found {len(dois)}")
    isbns = re.findall(r"ISBN\s*[: ]\s*[\d\-X]+", brain)
    suite.add(len(isbns) >= 3, "brain: >=3 ISBN-cited books", f"found {len(isbns)}")
    for sec in ["## 1. Core Concepts", "## 2. Key Research", "## 3. State-of-the-Art",
                "## 4. Authoritative Data Sources", "## 5. Analytical Frameworks",
                "## 6. Self-Update Protocol", "## 7. Knowledge Update Log"]:
        suite.add(sec in brain, f"brain: section {sec}")

    # ---- 7. Test scenarios ----
    sc = read(ROOT / "tests/test-scenarios.md")
    suite.add(sc.count("Scenario") >= 5, "scenarios: >=5", f"found {sc.count('Scenario')}")
    suite.add("degraded" in sc.lower(), "scenarios: degraded case")
    suite.add("comparison" in sc.lower() or "compare" in sc.lower(),
              "scenarios: comparison case")
    suite.add("conflict" in sc.lower() or "risk" in sc.lower(),
              "scenarios: risk/conflict case")
    for g in DOMAIN_GATES:
        suite.add(g in sc, f"scenarios: gate {g} referenced")

    # ---- 8. Knowledge pipeline contract ----
    ku_txt = read(ROOT / "tools/knowledge_updater.py")
    for token in ["KNOWLEDGE_CONFIG", "compute_hash", "score_entry",
                  "append_to_brain", "fetch_arxiv", "fetch_semantic_scholar",
                  "fetch_rss", "--dry-run", "--news-only", "Candidate",
                  "logging", "validate("]:
        suite.add(token in ku_txt, f"knowledge_updater: {token}")

    cfg_txt = read(ROOT / "tools/config.py")
    for token in ["KnowledgeConfig", "ScoringWeights", "BRAIN_PATH",
                  "arxiv_categories", "rss_feeds", "validate"]:
        suite.add(token in cfg_txt, f"config: {token}")

    # ---- 9. Docs ----
    pdpt = read(ROOT / "PROJECT-DEVELOPMENT-PHASE-TRACKING.md")
    suite.add("100%" in pdpt, "PDPT: 100% markers")
    suite.add("Phase 5" in pdpt, "PDPT: Phase 5")
    for phase in ["Phase 0", "Phase 1", "Phase 2", "Phase 3", "Phase 4", "Phase 5"]:
        suite.add(phase in pdpt, f"PDPT: {phase}")
    readme = read(ROOT / "README.md")
    suite.add("Usage" in readme and "Installation" in readme, "README: usage+install")
    pd = read(ROOT / "PROJECT-detail.md")
    suite.add("Idea (Vietnamese)" in pd, "PROJECT-detail: Idea (Vietnamese)")
    suite.add("Harness Architecture" in pd, "PROJECT-detail: harness architecture")

    # ---- 10. License & packaging ----
    license_txt = read(ROOT / "LICENSE")
    suite.add("MIT" in license_txt, "LICENSE: MIT")
    pyproject = read(ROOT / "pyproject.toml")
    suite.add("in-game-photography-cinematography" in pyproject
              or "knowledge_updater" in pyproject, "pyproject: project name")
    prog = read(ROOT / "progression.json")
    suite.add('"209"' in prog or "209" in prog, "progression.json: skill 209 entry")

    return suite


def render_report(suite: Suite) -> None:
    total = len(suite.results)
    print(f"[run_test_scenarios] {suite.passed}/{total} checks passed")
    for r in suite.results:
        if not r.passed:
            print(r.render())
    if suite.failed:
        print(f"\n{suite.failed} FAILURE(S)")
    else:
        print("\n[OK] all checks passed")


def main() -> int:
    suite = run()
    render_report(suite)
    return 1 if suite.failed else 0


if __name__ == "__main__":
    sys.exit(main())