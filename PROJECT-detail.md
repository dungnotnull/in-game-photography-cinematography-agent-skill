# PROJECT-detail.md — Skill 209: in-game-photography-cinematography

## Executive Summary

`in-game-photography-cinematography` is a professional-grade harness for Claude
Code targeting the **Virtual Photography & Game Cinematography** domain. It
transforms Claude into a domain-expert that delivers structured,
evidence-backed outputs by combining real-time data aggregation, recognized
domain methods (composition → angle → FOV → lighting → color → photo-mode),
and academic research into a single orchestrated workflow ending in a
risk/limitation-disclosed recommendation guarded by 10 quality gates.

---

## Problem Statement

Practitioners in this domain face three structural gaps:
1. **Data fragmentation** — authoritative data scattered across game docs,
   cinematography books, and academic papers.
2. **Methodology gaps** — most advice lacks systematic, evidence-graded
   methods (it defaults to "rule of thirds and looks nice").
3. **No self-improvement** — static tools don't learn from new research.

This skill addresses all three via real-time aggregation, professional
frameworks, and a continuously-updated knowledge crawl pipeline.

---

## Target Users & Use Cases

| User | Trigger Example | Skill Response |
|------|-----------------|----------------|
| Practitioner | "Analyze this Ghost of Tsushima ridge shot" | Full evidenced report with photo-mode settings |
| Researcher | "What composition methods apply to virtual photography?" | Method-grounded guidance with citations |
| Decision-maker | "Assess risk of a borderline boss-arena shot" | Risk-disclosed assessment with scenarios |
| Learner | "Explain low-key lighting for in-game scenes" | Educational framing with evidence |

---

## Harness Architecture

```
USER INPUT
    │
    ▼
[main.md — in-game-photography-cinematography]
    │  Pre-Flight: language detection (vi/en) → store LANG
    │
    ├─► sub-gather-requirements.md  → confirm object, scope, inputs before any fetch
    ├─► sub-evidence-collector.md  → authoritative current + reference data, tiered
    ├─► sub-core-analysis.md       → composition · angle/shot · FOV · lighting · color · photo-mode · scenarios
    ├─► sub-knowledge-updater.md  → tiered KB citations + crawl-gap queue
    ├─► sub-advisor.md            → risk-disclosed synthesis + evidence chain

    └─► [QUALITY GATE — main.md]
            ✓ U1 ≥3 sources, ≥1 academic (Tier 1–2)
            ✓ U2 disclosure before recommendation
            ✓ U3 tier label per source
            ✓ U4 language matches user
            ✓ U5 declared template, all sections
            ✓ U6 every claim traceable or flagged
            ✓ G1 composition/angle/lighting grounded in theory
            ✓ G2 photo-mode settings explicit (DOF/FOV/filters/resolution)
            ✓ G3 color grading for mood, named target
            ✓ G4 Best/Base/Worst scenarios
```

---

## Full Sub-Skill Catalog

### 1. `sub-gather-requirements.md`
- **Purpose:** Confirm the object, scope, timeframe, available inputs, target
  audience, and language before any data fetching.
- **Role:** Intake specialist.
- **Inputs:** Raw user message + any provided materials/inputs.
- **Outputs:** Structured requirements `{object, scope, timeframe, available_inputs, target_audience, language, analysis_type}`.
- **Tools:** Conversation only (no external tools).
- **Quality Gate:** At least one object of analysis confirmed before proceeding.

### 2. `sub-evidence-collector.md`
- **Purpose:** Fetch authoritative current + reference data (game/photo-mode
  capabilities, standards, recent developments, cached benchmarks), each
  tagged with source + date + tier.
- **Role:** Data librarian.
- **Inputs:** Requirements object from Step 1.
- **Outputs:** Evidence bundle `{current_data, authoritative_docs, recent_news, reference_benchmarks}` with source + date + tier per item.
- **Tools:** WebSearch, WebFetch (domain + academic sources); Read (SECOND-KNOWLEDGE-BRAIN.md).
- **Quality Gate:** At least current data + 1 authoritative document retrieved, or a limitation flag.

### 3. `sub-core-analysis.md`
- **Purpose:** Analyze in-game scenes and propose camera angles, composition,
  and lighting for high-quality virtual photography, grounded in
  cinematography and composition theory.
- **Role:** Virtual-photography & game-cinematography advisor.
- **Inputs:** Scene screenshot/description, photo-mode options, language.
- **Outputs:** Scene decomposition + composition (≥2 named rules) + angle/shot
  pair + FOV + lighting/exposure + color grade + explicit photo-mode settings
  + Best/Base/Worst scenarios.
- **Tools:** Image analysis (vision); Read (SECOND-KNOWLEDGE-BRAIN.md); reasoning.
- **Quality Gate:** Composition, angle, lighting each tied to named theory; photo-mode settings specified (G1, G2, G3, G4).

### 4. `sub-knowledge-updater.md`
- **Purpose:** Query SECOND-KNOWLEDGE-BRAIN.md for tiered academic/professional
  evidence; surface citations with tier labels and flag gaps for the crawl
  pipeline.
- **Role:** Research librarian.
- **Inputs:** Topic keywords from the current analysis.
- **Outputs:** 3–5 knowledge-base citations with tier labels + flagged gaps + coverage rating.
- **Tools:** Read (SECOND-KNOWLEDGE-BRAIN.md); WebSearch (gap-fill, max 2 queries).
- **Quality Gate:** At least 1 academic/authoritative source surfaced; coverage rating provided.

### 5. `sub-advisor.md`
- **Purpose:** Synthesize all prior analysis into a risk-disclosed conclusion
  with a full evidence chain and recommended actions.
- **Role:** Senior in-game-photography & game-cinematography advisor.
- **Inputs:** Core analysis scorecard + evidence bundle + knowledge-base evidence.
- **Outputs:** Conclusion (one of four declared categories) + scenarios + key risks (≥3) + evidence chain + remediation + mandatory disclosure.
- **Tools:** Reasoning/synthesis; `Skill("sub-knowledge-updater")` optional.
- **Quality Gate:** Conclusion is exactly one of: Strong Composition / Conditional (reframe) / Weak Composition / Inconclusive; disclosure appears before the conclusion.

---

## Skill File Format Specification

```markdown
---
name: {skill-name}
description: {one-line summary}
---
## Role & Persona
## Workflow
## Tools
## Output Format
## Quality Gates
```

---

## E2E Execution Flow

```
1. User invokes /in-game-photography-cinematography [query]
2. Pre-Flight language detection → LANG
3. main.md → sub-gather-requirements → structured requirements
4. sub-evidence-collector → tiered data bundle
5. sub-core-analysis → scorecard + photo-mode settings + scenarios
6. sub-knowledge-updater → academic evidence entries + gaps
7. sub-advisor → final draft with disclosure-first conclusion
8. main.md Quality Gate → verify U1–U6 + G1–G4, auto-fix, deliver
```

**Error handling:** primary sources fail → fallback chain → knowledge base →
explicit limitation flag; never silently proceed with stale data.

---

## SECOND-KNOWLEDGE-BRAIN Integration

- **Sources crawled:** Semantic Scholar, ArXiv (cs.GR/AI/HC), RSS feeds for
  game-development and cinematography news.
- **Crawl config:** `KNOWLEDGE_CONFIG` in `tools/config.py`.
- **Dedup:** SHA256 of DOI/URL/ISBN (case/whitespace-insensitive).
- **Scoring:** composite 0–10 = recency (0.4) + keyword_relevance (0.4) + citation_count (0.2).

---

## Quality Gates Definition

Universal gates U1–U6 plus domain gates G1–G4 defined in `skills/main.md`.

---

## Test Scenarios

See `tests/test-scenarios.md` for six concrete scenario tests covering all
verdicts, all gates, and all degradation levels.

---

## Key Design Decisions

1. Domain sub-skills kept separate (distinct methods/data).
2. Authoritative domain sources as primary; global fallback secondary.
3. Disclosure enforced at the quality-gate level, not optional.
4. SECOND-KNOWLEDGE-BRAIN as living memory updated by crawl pipeline.
5. Graceful degradation to knowledge base with explicit limitation flags.
6. FOV/focal length treated as a first-class composition control, not an afterthought.

---

## Idea (Vietnamese)

> Tạo skill phân tích và đề xuất góc máy, kỹ thuật quay phim trong game
> (In-game Photography), việc đánh giá và đưa đề xuất phải dựa trên các
> phương pháp đánh giá uy tín trên thế giới và đưa ra các đề xuất, giải pháp
> cải tiến, không ngừng đi crawl data từ các nguyên lý nhiếp ảnh điện ảnh
> thực tế hoặc document uy tín liên quan để cập nhật kiến thức cho skill ngày
> càng tốt hơn, xu hướng hơn.