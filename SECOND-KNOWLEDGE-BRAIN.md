# SECOND-KNOWLEDGE-BRAIN.md — Skill 209: in-game-photography-cinematography

> **Living Knowledge Base** — updated by `tools/knowledge_updater.py` on a weekly
> schedule. All entries are date-stamped; new entries are appended under
> Section 7. Evidence hierarchy: Systematic Review > Meta-Analysis >
> Guideline/RCT > Cohort > Expert Consensus > News.

---

## 1. Core Concepts & Frameworks

### 1.1 Virtual Photography & Game Cinematography — Foundational Methods

**Composition**
Rule of thirds, golden ratio (Phi grid), golden triangle, leading lines,
framing within the frame, depth (foreground / midground / background), negative
space, balance & visual weight, symmetry/reflection, headroom, eye-line, and
the 180° line / screen direction for continuity.

**Camera**
Angles: eye-level, low-angle (empower/threat), high-angle (vulnerability),
dutch/canted tilt (unease), over-the-shoulder (intimacy), bird's-eye (pattern),
worm's-eye (awe). Shot types: ECU → CU → MCU → MS → MLS → LS/wide → ELS
(establishing), plus insert/cutaway.

**Focal length / FOV (the under-used control)**
Wide (24–35 mm eq.) expands depth and exaggerates perspective; normal (~50 mm
eq.) is honest/neutral; tele (85–200 mm eq.) compresses depth and isolates
subject. FOV choice changes composition more than framing does.

**Lighting & exposure**
Three-point (key/fill/back/kicker), high-key (low contrast, bright) vs low-key
(high contrast, dramatic), rim/back light for subject separation, motivated vs
unmotivated light. Exposure triangle analogues: aperture→DOF, shutter→motion
blur, ISO→noise. HDR for high-dynamic-range scenes; golden/blue hour.

**Color grading & mood**
Warm (amber/gold) → nostalgia/intimacy/safety; cool (teal/blue) →
isolation/cold/tech; complementary teal-orange → cinematic pop & subject
separation; desaturated/monochrome → grit/period/memory. LUTs and HSL deltas
encode the intent (Itten color theory underpins mood association).

**Photo mode**
DOF/aperture, focal length/FOV, focal distance, roll/tilt, exposure, filters,
time-of-day freeze, free camera, high-resolution/super-resolution upscale.
Tools: NVIDIA Ansel, AMD Radeon ReLive, and built-in photo modes (God of War,
Ghost of Tsushima, Red Dead Redemption 2, Horizon, Marvel's Spider-Man).
Compression-free capture (PNG/TIFF) is preferred over lossy JPEG.

**Knowledge categories covered**
Composition · Camera angles & shot types · Focal length/FOV · Lighting &
exposure · Color grading & mood · Subject & storytelling · Photo-mode tools &
resolution · Engine rendering (RTX/path tracing for photography).

### 1.2 Evidence Hierarchy (this domain)
- **Tier 1** — Systematic review / meta-analysis / official standard (ISO, ASC,
  engine specification).
- **Tier 2** — Peer-reviewed paper / RCT / academic book.
- **Tier 3** — Industry report / professional association guideline / official
  game documentation.
- **Tier 4** — News / blog / vendor marketing / community post.

---

## 2. Key Research Papers & Standards

| Title | Authors | Year | Venue | DOI / URL / ISBN | Tier |
|------|---------|------|-------|------------------|------|
| Does gamification work? A literature review of empirical studies | Hamari, Koivisto, Sarsa | 2014 | Computers in Human Behavior | 10.1016/j.chb.2014.03.006 | 2 |
| Film Art: An Introduction (11th ed.) | Bordwell & Thompson | 2017 | McGraw-Hill | ISBN 978-1259544627 | 2 |
| The Visual Story: Creating the Visual Structure of Film, TV and Digital Media (3rd ed.) | Block, B. | 2008 | Focal Press | ISBN 978-0240807799 | 2 |
| The Photographer's Eye: Composition and Design for Better Digital Photos | Freeman, M. | 2007 | Focal Press | ISBN 978-0240809342 | 2 |
| The Elements of Color | Itten, J. | 1970 | Van Nostrand Reinhold | ISBN 978-0471289278 | 2 |
| Picture Composition for Film and Television (2nd ed.) | Ward, P. | 2003 | Focal Press | ISBN 978-0240516813 | 2 |
| NVIDIA Ansel — Developer Documentation | NVIDIA Corporation | 2023 | NVIDIA Developer | https://developer.nvidia.com/ansel | 3 |
| AMD Radeon ReLive — User Guide | AMD | 2023 | AMD Support | https://www.amd.com/en/support | 3 |
| in-game photography (online article) | various | 2020 | Game Studies | https://gamestudies.org | 4 |

**Authoritative sources registered**
Proceedings of CHI PLAY (ACM) · Game Studies (gamestudies.org) · Entertainment
Computing (Elsevier) · Computers in Human Behavior (Elsevier) · Leonardo
(MIT Press) · ACM Transactions on Graphics (for real-time rendering/cinematography).

---

## 3. State-of-the-Art Methods & Tools

State of the art (as of the last update): AI-assisted composition suggestion,
real-time path-traced rendering for virtual photography, automated
virtual-camera cinematography, color-grade LUT pipelines, super-resolution
upscale, and virtual-photography galleries/communities.

Crawl targets for ongoing SOTA: CHI PLAY, Game Studies, Entertainment
Computing, Leonardo, ACM Transactions on Graphics, and SIGGRAPH/SIGGRAPH
Asia proceedings.

---

## 4. Authoritative Data Sources

### 4.1 Domain authoritative sources
- Game photo-mode documentation (NVIDIA Ansel, AMD Radeon ReLive, and built-in
  photo modes for God of War, Ghost of Tsushima, Red Dead Redemption 2, Horizon,
  Marvel's Spider-Man).
- Cinematography references (Bordwell & Thompson; ASC Manual; Bruce Block;
  Peter Ward).
- Photography composition references (Freeman; Itten).
- Virtual photography communities (Steam screenshot art, in-game photography
  galleries).
- Engine & rendering references (RTX/path tracing, Unreal/Unity post-process).
- Color grading references (LUT libraries, HSL color theory).

### 4.2 Academic & research sources
- Proceedings of CHI PLAY (ACM)
- Game Studies — gamestudies.org
- Entertainment Computing — Elsevier
- Computers in Human Behavior — Elsevier
- Leonardo (MIT Press)
- ACM Transactions on Graphics (SIGGRAPH)

---

## 5. Analytical Frameworks

Knowledge categories covered: Composition · Camera angles & shot types ·
Focal length/FOV · Lighting & exposure · Color grading & mood · Subject &
storytelling · Photo-mode tools & resolution.

Cross-reference the sub-skill workflows in `skills/*.md` for the domain methods
applied at each step. The fixed bookends (requirements → evidence →
knowledge → synthesis → quality gate) are mandatory; the core-analysis
sub-skill implements the domain-specific methods.

**Composition decision order (this skill's framework):**
1. Read the scene (subject, geometry, light, depth, mood).
2. Pick composition principle(s) — at least two complementary rules.
3. Choose angle + shot type as a pair, justified by mood.
4. Set focal length / FOV for the desired depth effect.
5. Set exposure/lighting and color grade for mood.
6. Emit explicit photo-mode settings; build Best/Base/Worst scenarios.

---

## 6. Self-Update Protocol

- **Crawl pipeline:** `tools/knowledge_updater.py` (config in `tools/config.py`).
- **Schedule:** weekly academic (Mondays 08:00) + daily news (07:00); documented
  in `CLAUDE.md`.
- **Dedup:** SHA256 of DOI/URL/ISBN (case- and whitespace-insensitive).
- **Scoring:** composite 0–10 = recency (0.4) + keyword_relevance (0.4) +
  citation_count (0.2).
- **Crawl targets:** Semantic Scholar keyword clusters; ArXiv (cs.AI, cs.GR,
  cs.HC where applicable); RSS feeds for game-development and
  cinematography news.
- **Gap-fill:** `sub-knowledge-updater` flags missing topics as crawl queries.
- **Append rule:** new entries appended under Section 7 with a date stamp and a
  relevance score.

---

## 7. Knowledge Update Log

_(Appended automatically by the crawl pipeline. Baseline seeded with the
references in Section 2. Each new entry: title, authors, year, venue, DOI/URL,
relevance score, key finding.)_