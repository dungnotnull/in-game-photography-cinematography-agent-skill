# test-scenarios.md — Skill 209: in-game-photography-cinematography

Six concrete end-to-end scenarios. Each lists inputs, expected steps, the
verdict target, and the applicable quality gates. The scenarios exercise all
universal gates U1–U6 and the domain gates G1–G4, plus all four verdict
categories. They also exercise every degradation level (0–4) of the harness.

---

## Scenario 1 — Standard analysis (object in scope, all sources reachable)
- **Input:** A Ghost of Tsushima landscape scene with a lone samurai on a
  ridge at dusk; full inputs (screenshot + photo-mode control list +
  platform). Degradation Level 0.
- **Expected:** Step 1 requirements → Step 2 evidence (photo-mode docs +
  cinematography refs) → Step 3 core analysis (rule of thirds + leading
  lines + low-angle + golden-hour grade + DOF/FOV settings) → Step 4
  knowledge citations → Step 5 advisor synthesis → Step 6 quality gate.
- **Gates:** U1–U6 + G1, G2, G3, G4.
- **Verdict target:** Strong Composition.

## Scenario 2 — Minimal-input analysis (defaults)
- **Input:** "Phân tích cảnh đêm trong game horror" — terse request, no
  screenshot, game unnamed. Language = Vietnamese (Pre-Flight).
- **Expected:** Defaults applied with explicit assumptions; the missing
  screenshot degrades to Level 3 (DATA UNAVAILABLE for image); never
  fabricate a scene. Recommend the user provide a screenshot or fuller
  description; give general low-key lighting + dutch-angle guidance.
- **Gates:** U2, U4 (Vietnamese output), U5, G1, G2, G3, G4.
- **Verdict target:** Inconclusive (decisive input missing).

## Scenario 3 — Comparison scenario (two framings)
- **Input:** Compare a wide-FOV establishing shot vs. a telephoto portrait
  of the same character in Cyberpunk 2077. Full inputs.
- **Expected:** Side-by-side scorecard (depth effect, subject isolation,
  color grade fit) with an evidence-based winner; sub-core-analysis applied
  to both framings.
- **Gates:** U3 (evidence hierarchy per source), U6, G1, G2, G3, G4.
- **Verdict target:** Conditional (reframe) — name the better framing and
  the concrete setting deltas.

## Scenario 4 — Risk / feasibility or conflict scenario
- **Input:** Assess a borderline boss-arena shot where low-key light clashes
  with the engine's ambient occlusion; conflicting guidance: dramatic
  (low-key) vs. readable (lift shadows).
- **Expected:** Multi-scenario (Best/Base/Worst) risk output; stated
  precedence (narrative beat > readability for a cinematic capture);
  ≥3 key risks with probability & impact; mandatory disclosure first.
- **Gates:** U2 (disclosure), G1, G2, G3, G4.
- **Verdict target:** Conditional (reframe).

## Scenario 5 — Degraded-mode scenario (primary sources unreachable)
- **Input:** Game photo-mode docs unreachable (timeout) and the knowledge
  base misses the specific patch-changed control. Degradation Level 2.
- **Expected:** Fallback chain (live → secondary → knowledge base →
  flag) with a LIMITATION notice; no fabricated values; the missing
  control queued as a crawl query for sub-knowledge-updater.
- **Gates:** U2, graceful-degradation Level 2, G1, G2, G3, G4.
- **Verdict target:** Inconclusive (or Conditional if KB gives enough).

## Scenario 6 — Weak-composition critique scenario
- **Input:** A default-FOV, center-locked, flat-lit screenshot the user
  thinks "looks good". Full inputs.
- **Expected:** Sub-core-analysis identifies the failure modes (flat
  depth, unmotivated fill, no leading lines, no color intent) and
  provides a concrete reframing plan with photo-mode setting deltas;
  ≥3 risks.
- **Gates:** U2, G1, G2, G3, G4.
- **Verdict target:** Weak Composition.

### Gate coverage matrix

| Gate | S1 | S2 | S3 | S4 | S5 | S6 |
|------|----|----|----|----|----|----|
| G1 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| G2 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| G3 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| G4 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| U1–U6 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

### Verdict coverage
Strong Composition (S1) · Conditional (reframe) (S3, S4, S5) ·
Weak Composition (S6) · Inconclusive (S2, S5).

### Degradation-level coverage
Level 0 (S1) · Level 2 (S5) · Level 3 (S2) · Level 4 is exercised when all
sources and the knowledge base fail (documented fallback notice).