# CHANGELOG

All notable changes to **in-game-photography-cinematography** are documented
here. The format follows [Keep a Changelog](https://keepachangelog.com/) and the
project adheres to [Semantic Versioning](https://semver.org/).

## [1.0.0] — 2026-07-11 — PRODUCTION READY
### Added
- 5 domain-deep sub-skills (`sub-gather-requirements`,
  `sub-evidence-collector`, `sub-core-analysis`, `sub-knowledge-updater`,
  `sub-advisor`) with named cinematography/composition theory, FOV/focal-length
  depth control, high-key/low-key lighting, teal-orange color grading, and
  reproducible photo-mode settings.
- `skills/main.md` harness: 6-step protocol, Pre-Flight VI/EN language
  detection, 10 quality gates (U1–U6 + G1–G4), 5-level graceful-degradation
  protocol, error-recovery table.
- `SECOND-KNOWLEDGE-BRAIN.md` living knowledge base with verifiable ISBN/DOI
  references (Bordwell & Thompson, Block, Freeman, Itten, Ward, Hamari et al.).
- `tools/config.py` validated central configuration.
- `tools/knowledge_updater.py` production crawl pipeline: Semantic Scholar +
  ArXiv + RSS, SHA256 dedup, composite 0–10 scoring, structured logging,
  typed dataclasses, `--dry-run` / `--news-only` / `--keywords` flags.
- `tools/test_knowledge_updater.py` offline unit tests (7/7).
- `tools/run_test_scenarios.py` ~140-check project validator.
- `tools/validate_project.py` 8-File Contract validator.
- `tests/test-scenarios.md` six end-to-end scenarios covering all verdicts,
  all gates, and all degradation levels.
- `LICENSE` (MIT), `pyproject.toml`, `progression.json`, `logs/.gitkeep`.

### Changed
- Rewrote all sub-skills from thin templates to production-grade domain content.
- Replaced fabricated DOIs with verifiable ISBN/DOI references.
- Centralized pipeline config and added config-invariant validation.
- Fixed encoding (UTF-8 no BOM, LF) across all files.

## [0.1.0] — 2026-07-10
- Initial scaffold of the harness, sub-skills, knowledge base, and pipeline.