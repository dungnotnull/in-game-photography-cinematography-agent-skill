# RAG Prompt Templates — Reference

These templates provide structured prompts for RAG (Retrieval-Augmented Generation)
context grounding when analyzing scenes and making recommendations.

---

## Template 1: Scene Analysis with Domain Context

```markdown
You are analyzing a {scene_type} scene from {game_title} for virtual photography
recommendations. Use the following domain context to ground your analysis:

### Domain Context
{composition_principles}

### Camera Terminology
{camera_terminology}

### Color Theory
{color_theory}

### Photo Mode Capabilities
{photo_mode_specs}

### Scene Description
{scene_description}

### Analysis Framework
1. Read the scene: subject, geometry, light, depth, mood
2. Apply at least two composition principles from domain context
3. Choose angle + shot type justified by mood
4. Set focal length/FOV for desired depth effect
5. Set exposure/lighting and color grade for mood
6. Specify concrete photo-mode settings

### Output Format
Use the standard report format with all required sections.
```

---

## Template 2: Evidence-Based Recommendation

```markdown
You are providing evidence-backed recommendations for {specific_task}.
Base your recommendations on the following authoritative sources:

### Academic Evidence
{academic_citations}

### Industry Standards
{industry_standards}

### Professional References
{professional_references}

### Task Context
{task_description}

### Requirements
1. Cite at least 3 sources, including 1 academic/authoritative (Tier 1-2)
2. Explicitly state evidence tier per source
3. Disclose limitations before recommendations
4. Make claims traceable to cited sources
5. Flag any claims based on agent judgment

### Output Structure
- Executive Summary
- Evidence Collected (with tiers)
- Analysis
- Recommendations
- Key Risks
- Evidence Chain
- Disclosure/Limitations
```

---

## Template 3: Knowledge Base Query

```markdown
Query the knowledge base for evidence related to: {topic_keywords}

### Search Strategy
1. Check SECOND-KNOWLEDGE-BRAIN.md for direct matches
2. Look for Tier 1-2 sources (systematic review, meta-analysis, peer-reviewed)
3. Prioritize recent research (last 5 years) for current practices
4. Flag gaps for crawl pipeline

### Output Format
For each relevant entry:
- Title, authors, year, venue
- DOI/ISBN/URL
- Tier label (1-4)
- Key finding relevant to query
- Relevance score (0-10)

### Coverage Assessment
- Number of academic sources found: {count}
- Number of professional sources found: {count}
- Coverage rating: [Comprehensive/Adequate/Limited/None]
- Gaps identified: {list}
```

---

## Template 4: Photo Mode Configuration

```markdown
Based on scene analysis, recommend specific photo mode settings for {game_title}.

### Scene Characteristics
- Subject: {subject}
- Mood: {mood}
- Lighting: {lighting_description}
- Depth requirements: {depth_needs}

### Available Controls
{available_controls}

### Configuration Protocol
1. **Composition Settings**
   - FOV: {value} mm equivalent / {value}°
   - Focal distance: {value}m
   - DOF: {value}% (aperture equivalent)

2. **Exposure Settings**
   - Exposure: {value} stops
   - Time of day: {value}
   - HDR: {enabled/disabled}

3. **Color Settings**
   - Saturation: {value}%
   - Color temperature: {warm/cool/neutral}
   - Contrast: {value}%
   - Split tone: {shadows color}, {highlights color}

4. **Output Settings**
   - Resolution: {value}
   - Format: {PNG/TIFF} (lossless)
   - Aspect ratio: {ratio}

### Justification
Each setting tied to composition principle or technical requirement.

### Safety Limits
- Maximum exposure before clipping
- Maximum FOV before distortion
- Maximum saturation before skin tone issues
```

---

## Template 5: Multi-Scenario Comparison

```markdown
Generate three capture scenarios for {scene}: Best, Base, and Worst.

### Scene Context
{scene_description}

### Scenario Definitions
- **Best:** Optimal conditions, ideal lighting, perfect composition
- **Base:** Acceptable conditions, practical constraints
- **Worst:** Challenging conditions, significant limitations

### Analysis Per Scenario
1. **Composition Assessment**
   - Applied principles
   - Strengths and weaknesses
   - Overall score (1-10)

2. **Technical Settings**
   - Photo mode configuration
   - Rationale for choices

3. **Likelihood & Impact**
   - Probability of achieving this result
   - Visual impact rating
   - Technical challenges

4. **Risks & Limitations**
   - What could go wrong
   - Mitigation strategies

### Comparative Summary
Table comparing key metrics across scenarios.

### Recommendation
Which scenario to target and why.
```

---

## Template 6: Error Recovery & Fallback

```markdown
Primary data source {source_name} failed. Activate fallback protocol.

### Error Details
- Source: {failed_source}
- Error type: {error_type}
- Timestamp: {timestamp}

### Fallback Chain
1. **Try alternate source:** {alternate_source}
2. **Use cached data:** {cache_status}
3. **Query knowledge base:** {kb_query}
4. **Use default values:** {defaults}
5. **Explicit limitation:** Flag limitation

### Degradation Level
{current_level} (0-4)

### Limitation Notice
Generate appropriate notice for user:
```
---
⚠️ LIMITATION NOTICE
This output was generated with reduced data availability (Level {level}).
Cross-check with current data before acting on it. Substituted/missing sources are flagged inline.
---
```

### Recovery Actions
- {action_taken}
- {source_used}
- {reliability_assessment}

### Continue Analysis
Proceed with available data, explicitly flagging all limitations.
```

---

## Template 7: Language-Specific Output

```markdown
Generate analysis in {language} (Vietnamese/English).

### Translation Table
{translation_table}

### Requirements
1. Use all section headings from translation table
2. Maintain technical accuracy in translations
3. Preserve source citations in original language
4. Use appropriate domain terminology

### Special Handling for Vietnamese
- Technical terms: Keep in English with Vietnamese explanation in parentheses
- Example: "Depth of Field (Độ sâu trường ảnh)"
- Citations: Keep in English, translate title in brackets

### Output Format
Use standard report structure with translated section headers.
```

---

## Template 8: Quality Gate Verification

```markdown
Verify output passes all quality gates before delivery.

### Universal Gates (U1-U6)
- [ ] U1: ≥3 sources cited, ≥1 academic/authoritative
- [ ] U2: Disclosure/limitations before recommendation
- [ ] U3: Evidence hierarchy per source
- [ ] U4: Language matches user preference
- [ ] U5: Declared template, all sections present
- [ ] U6: Every claim traceable or flagged

### Domain Gates (G1-G4)
- [ ] G1: Composition/angle/lighting grounded in theory
- [ ] G2: Photo-mode settings explicit
- [ ] G3: Color grading for mood with named target
- [ ] G4: Best/Base/Worst scenarios present

### Auto-Fix Actions
{fix_history}

### Final Verification
- All gates passed: {yes/no}
- Limitations present: {yes/no}
- Degradation level: {0-4}

### Delivery Decision
✓ Approved for delivery
✗ Requires revision (specify gate failures)
```

---

## Usage Notes

1. **Template Selection:** Choose appropriate template based on task type
2. **Variable Substitution:** Replace {variables} with actual content
3. **Context Injection:** Load domain references before template use
4. **Validation:** Verify output follows template structure
5. **Fallback:** Use error recovery template if sources fail

---

## Template Metadata

| Template | Purpose | Required Context | Output Structure |
|----------|---------|------------------|------------------|
| 1 | Scene analysis | Composition, camera, color, photo mode | Full analysis report |
| 2 | Evidence-based recommendation | Academic, industry, professional sources | Structured recommendation |
| 3 | Knowledge base query | SECOND-KNOWLEDGE-BRAIN.md | Citation list with coverage |
| 4 | Photo mode configuration | Scene characteristics, available controls | Concrete settings |
| 5 | Multi-scenario comparison | Scene description | Three scenario comparison |
| 6 | Error recovery | Error details, fallback chain | Degraded analysis |
| 7 | Language-specific | Translation table | Localized report |
| 8 | Quality gate verification | Output content, gate definitions | Pass/fail report |
