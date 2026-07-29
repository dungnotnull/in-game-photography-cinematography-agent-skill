# in-game-photography-cinematography

**In-Game Photography & Cinematography (Camera Angles, Composition)**

[![Claude Skill](https://img.shields.io/badge/Claude-Skill-blue)](https://claude.ai/claude-code)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Status: Production Ready v2.0.0](https://img.shields.io/badge/status-production_v2.0.0-brightgreen)](#)

A professional-grade Claude Code harness for **Virtual Photography & Game
Cinematography**. It gathers real-time authoritative data, applies recognized
domain methods (composition → camera angle → FOV → lighting → color grading →
photo-mode settings), integrates academic research, and delivers
evidence-backed, risk-disclosed outputs through a 5-sub-skill pipeline guarded
by 10 quality gates — continuously self-improving through an automated
knowledge crawl pipeline.

## Features
- **Domain-deep sub-skills**: scene decomposition, named composition theory
  (rule of thirds, golden ratio, leading lines, framing, depth, negative
  space), camera angle + shot type pairs, focal-length/FOV depth control,
  high-key/low-key lighting, teal-orange color grading, and reproducible
  photo-mode settings.
- **Flexible agent & skill architecture** with dynamic registry and chain-of-thought routing
- **Real-time data aggregation** from authoritative game/photo-mode docs,
  cinematography references, and recent developments.
- **Academic research integration** with an auto-updating knowledge base
  (`SECOND-KNOWLEDGE-BRAIN.md`) — Semantic Scholar + ArXiv + RSS, SHA256
  dedup, composite scoring.
- **Risk/limitation-disclosed outputs** with Best/Base/Worst scenarios.
- **10 quality gates** (U1–U6 universal + G1–G4 domain) with auto-fix and a
  5-level graceful-degradation protocol.
- **Vietnamese/English** Pre-Flight language detection with full label
  translation table.
- **Production-grade execution** with context window management, structured logging, and error classification
- **Schema-defined tool execution** with timeout, fallback, and validation
- **Lifecycle hooks** for monitoring, metrics collection, and cross-cutting concerns

## Installation
```bash
pip install -r requirements.txt
```
Install the skill files to `~/.claude/skills/` or use via the project `CLAUDE.md`.

## Usage
```bash
/in-game-photography-cinematography [your query]
```

Example:
```
/in-game-photography-cinematography Analyze this Ghost of Tsushima ridge-at-dusk shot and recommend camera + photo-mode settings
```

## Architecture
Harness flow: Pre-Flight language detection → requirements → evidence → core
analysis → knowledge → synthesis → quality gate. See `PROJECT-detail.md` for
the full architecture diagram and sub-skill catalog.

## Quality Gates
Universal gates **U1–U6** (sources, disclosure, tier, language, template,
traceability) plus domain gates **G1–G4** (theory-grounding, photo-mode
settings, color-grade intent, scenarios). Full table in `skills/main.md`.

## Data Sources
- Game photo-mode docs (NVIDIA Ansel, AMD Radeon ReLive, and built-in photo
  modes for God of War, Ghost of Tsushima, Red Dead Redemption 2, Horizon,
  Marvel's Spider-Man).
- Cinematography references (Bordwell & Thompson; ASC Manual; Bruce Block;
  Peter Ward).
- Photography composition references (Freeman; Itten).
- Engine & rendering references (RTX/path tracing, Unreal/Unity post-process).
- Academic: CHI PLAY, Game Studies, Entertainment Computing, Computers in
  Human Behavior, Leonardo, ACM Transactions on Graphics.

## Testing
```bash
python tools/test_knowledge_updater.py    # offline unit tests
python tools/validate_project.py          # 8-File Contract
python tools/run_test_scenarios.py        # full ~140-check validator
```

## Knowledge Base
`SECOND-KNOWLEDGE-BRAIN.md` is auto-updated weekly via `tools/knowledge_updater.py`.

```bash
python tools/knowledge_updater.py --dry-run           # preview candidates
python tools/knowledge_updater.py                    # academic + news crawl
python tools/knowledge_updater.py --news-only        # RSS news only
```

## Roadmap
- [x] Phase 0: Architecture
- [x] Phase 1: Core sub-skills (5)
- [x] Phase 2: Main harness + 10 gates + degradation
- [x] Phase 3: Knowledge pipeline + tests + cron
- [x] Phase 4: Testing & validation (6 scenarios)
- [x] Phase 5: Integration & polish — PRODUCTION READY v1.0.0
- [x] Phase 6: v2.0.0 Production Upgrade — PRODUCTION READY v2.0.0

## License
MIT — see [LICENSE](LICENSE).

## Citation
```bibtex
@software{in-game-photography-cinematography,
  title  = {in-game-photography-cinematography: In-Game Photography & Cinematography (Camera Angles, Composition)},
  year   = {2026},
  version = {2.0.0}
}
```

## Why This Skill

Virtual Photography & Game Cinematography practitioners face fragmented data,
inconsistent methodology, and tools that do not self-improve. This skill
unifies authoritative real-time data, recognized domain methods, and a
continuously-updated academic knowledge base into one evidence-backed,
risk-disclosed workflow.