# CLAUDE.md — Skill 209: in-game-photography-cinematography

## Skill Identity
- **Skill Name:** `in-game-photography-cinematography`
- **Tagline:** In-Game Photography & Cinematography (Camera Angles, Composition) — Virtual Photography & Game Cinematography analysis & decision-support harness.
- **Current Phase:** Phase 6 — v2.0.0 Production Upgrade (PRODUCTION READY v2.0.0)
- **Folder:** `D:\972026\209-in-game-photography-cinematography\`

---

## Problem This Skill Solves

This skill provides a structured, evidence-backed analytical workflow for
**Virtual Photography & Game Cinematography**. It gathers authoritative
real-time and reference data, applies recognized domain methods
(composition → angle → FOV → lighting → color → photo-mode), cross-references
academic research, and delivers actionable outputs that are fully evidenced,
risk/limitation-disclosed, and traceable to authoritative sources —
continuously self-improving through an automated knowledge crawl pipeline.

---

## Harness Flow Summary

```
/in-game-photography-cinematography invoked
│  Pre-Flight: detect language (vi / en / other→en) → store LANG
│
├─ Step 1: sub-gather-requirements  → confirm object & inputs before any fetch
├─ Step 2: sub-evidence-collector   → authoritative current + reference data (tiered)
├─ Step 3: sub-core-analysis        → composition · angle/shot · FOV · lighting · color · photo-mode · scenarios
├─ Step 4: sub-knowledge-updater    → tiered KB citations + crawl-gap queue
├─ Step 5: sub-advisor             → risk-disclosed synthesis + evidence chain
└─ Step 6: main (quality gate)     → verify U1–U6 + G1–G4, auto-fix, deliver
```

---

## Sub-Skills

| File | Step | Role |
|------|------|------|
| `skills/sub-gather-requirements.md` | 1 | Intake specialist — confirm object & inputs before any fetch |
| `skills/sub-evidence-collector.md` | 2 | Data librarian — authoritative current + reference data, tiered |
| `skills/sub-core-analysis.md` | 3 | Cinematography advisor — scene decomposition, composition, angle, FOV, lighting, color, photo-mode, scenarios |
| `skills/sub-knowledge-updater.md` | 4 | Research librarian — tiered KB citations + crawl-gap queue |
| `skills/sub-advisor.md` | 5 | Senior advisor — risk-disclosed synthesis + evidence chain |

---

## Tools Required

- **WebSearch** — live game/photo-mode docs, cinematography references, recent developments
- **WebFetch** — scrape authoritative sources
- **Read / Write** — read SECOND-KNOWLEDGE-BRAIN.md; append knowledge entries
- **Bash** — run `tools/knowledge_updater.py` for periodic crawl
- **Skill** — invoke sub-skills sequentially through the harness

---

## Knowledge Sources

### Domain authoritative sources
- Game photo-mode documentation (NVIDIA Ansel, AMD Radeon ReLive, and built-in
  photo modes for God of War, Ghost of Tsushima, Red Dead Redemption 2,
  Horizon, Marvel's Spider-Man).
- Cinematography references (Bordwell & Thompson *Film Art*; ASC Manual;
  Bruce Block *The Visual Story*; Peter Ward *Picture Composition*).
- Photography composition references (Freeman *The Photographer's Eye*; Itten
  *The Elements of Color*).
- Virtual photography communities (Steam screenshot art, galleries).
- Engine & rendering references (RTX/path tracing, Unreal/Unity post-process).
- Color grading references (LUT libraries, HSL color theory).

### Academic & research sources
- Proceedings of CHI PLAY (ACM)
- Game Studies — gamestudies.org
- Entertainment Computing — Elsevier
- Computers in Human Behavior — Elsevier
- Leonardo (MIT Press)
- ACM Transactions on Graphics (SIGGRAPH)

### Academic crawl targets
- Semantic Scholar / Google Scholar for "virtual photography" /
  "game cinematography" / "virtual cinematography" keyword clusters
- ArXiv (cs.GR, cs.AI, cs.HC) where applicable
- Standards bodies and professional associations (ASC, NVIDIA, AMD docs)

---

## Supporting Python Tools

| File | Purpose |
|------|---------|
| `tools/config.py` | Central, validated configuration (keywords, sources, scoring weights) |
| `tools/knowledge_updater.py` | Crawl pipeline: Semantic Scholar + ArXiv + RSS → SHA256 dedup → composite score → append to SECOND-KNOWLEDGE-BRAIN.md |
| `tools/test_knowledge_updater.py` | Offline unit tests for the pipeline (hash, score, format, dedup, config invariant) |
| `tools/run_test_scenarios.py` | Production-grade structural & content validator (~140 checks) |
| `tools/validate_project.py` | Lightweight 8-File Contract validator for CI |

---

## Automated Knowledge Update Schedule

```cron
# Weekly academic update (Mondays 08:00)
0 8 * * 1 python D:/972026/209-in-game-photography-cinematography/tools/knowledge_updater.py >> logs/knowledge_update.log 2>&1

# Daily news/RSS update (Daily 07:00)
0 7 * * * python D:/972026/209-in-game-photography-cinematography/tools/knowledge_updater.py --news-only >> logs/knowledge_news.log 2>&1
```

Manual:
```bash
python tools/knowledge_updater.py --dry-run
python tools/knowledge_updater.py --news-only
python tools/knowledge_updater.py --keywords "in-game photography" "color grading"
```

---

## Quality Gates (summary)

Universal gates **U1–U6** (sources, disclosure, tier, language, template,
traceability) plus domain gates **G1–G4** (theory-grounding, photo-mode
settings, color-grade intent, scenarios). Auto-fix + 2-retry-max enforcement
with explicit limitation notices. Full table in `skills/main.md`.

---

## Active Development Tasks

- [x] Phase 0: Architecture & source map (this file, PROJECT-detail.md, PDPT.md)
- [x] Phase 1: Core sub-skills (production-grade, domain-deep)
- [x] Phase 2: Main harness + 10 quality gates + 5-level degradation + error table
- [x] Phase 3: Knowledge pipeline (config + crawl + tests + cron)
- [x] Phase 4: Testing & validation (6 scenarios, ~140 checks, all green)
- [x] Phase 5: Integration & polish (PRODUCTION READY v1.0.0)
- [x] Phase 6: v2.0.0 Production Upgrade (PRODUCTION READY v2.0.0)

---

## References

- `PROJECT-detail.md` — full technical specification
- `PROJECT-DEVELOPMENT-PHASE-TRACKING.md` — build roadmap (all phases 100%)
- `SECOND-KNOWLEDGE-BRAIN.md` — self-improving knowledge base
- `tests/test-scenarios.md` — end-to-end scenario coverage
- `D:\972026\SKILL-STANDARD.md` — library-wide standard