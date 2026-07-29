# Camera Terminology — Domain Reference

## Shot Sizes (from closest to farthest)

| Shot Type | Abbreviation | Frame | Typical Use |
|-----------|-------------|-------|-------------|
| Extreme Close-Up | ECU | Single feature (eyes, mouth) | Intimacy, emphasis |
| Close-Up | CU | Head & shoulders | Expression, emotion |
| Medium Close-Up | MCU | Chest up | Conversation, detail |
| Medium Shot | MS | Waist up | Action, interaction |
| Medium Long Shot | MLS | Knees up | Context + detail |
| Long Shot / Wide | LS | Full figure | Environment, scale |
| Extreme Long Shot | ELS | Landscape / establishing | Setting, scope |

**Other shot types:**
- **Insert:** Detail shot of object or action (props, UI elements)
- **Cutaway:** Separate shot to bridge edits or provide context

---

## Camera Angles

| Angle | Effect | Typical Use |
|-------|--------|-------------|
| **Eye-level** | Neutral, realistic | Standard dialogue, observation |
| **Low-angle** | Empowers subject, suggests dominance | Heroes, villains, authority figures |
| **High-angle** | Diminishes subject, suggests vulnerability | Victims, losses, overview |
| **Bird's-eye** | God-like view, reveals patterns | Maps, battlefields, cityscapes |
| **Worm's-eye** | Awe, monumental scale | Skyscrapers, massive structures |
| **Dutch/canted** | Unease, disorientation | Horror, tension, psychological distress |
| **Over-the-shoulder (OTS)** | Intimacy, POV | Conversations, confrontations |

---

## Focal Length / Field of View

### 35mm-equivalent focal lengths and their effects:

| Focal Length | Classification | Effect | Typical Use |
|--------------|----------------|--------|-------------|
| 14-24mm | Ultra-wide | Extreme depth expansion, distortion | Architecture, interiors, establishing shots |
| 24-35mm | Wide | Expanded depth, exaggerated perspective | Environmental portraits, context |
| 35-50mm | Normal-wide | Natural perspective, slight expansion | Documentary, street photography |
| 50mm | Normal | Human-eye perspective, minimal distortion | Standard, reference view |
| 85-135mm | Short telephoto | Compressed depth, flattering portraits | Character portraits, subject isolation |
| 135-200mm | Telephoto | Significant depth compression | Sports, wildlife, distant subjects |
| 200mm+ | Long telephoto | Extreme compression, background blur | Extreme subject isolation |

### FOV equivalents (for games with FOV settings rather than focal length):

| Focal Length (35mm eq.) | Horizontal FOV | Usage Notes |
|------------------------|----------------|-------------|
| 24mm | ~84° | Wide environmental shots |
| 35mm | ~63° | Standard wide view |
| 50mm | ~47° | Normal perspective |
| 85mm | ~28° | Portraiture |
| 135mm | ~15° | Tight portraits |

**In-game application:**
- Adjust FOV slider in photo mode to approximate desired focal length
- Lower FOV = telephoto effect (compression, background blur)
- Higher FOV = wide effect (depth, perspective exaggeration)

---

## Aperture & Depth of Field

| Aperture (f-stop) | Depth of Field | Typical Use |
|-------------------|----------------|-------------|
| f/1.4 - f/2.8 | Shallow | Portraits, subject isolation |
| f/4 - f/5.6 | Moderate | General purpose, street |
| f/8 - f/11 | Deep | Landscape, architecture |
| f/16 - f/22 | Very deep | Macro, maximum sharpness |

**In-game equivalents:**
- DOF slider in photo mode (often 0-100%)
- Higher DOF = more of frame in focus (f/8-f/11 equivalent)
- Lower DOF = subject isolation (f/1.4-f/2.8 equivalent)
- Focal distance: Where the plane of sharp focus falls

---

## Shutter Speed & Motion

| Shutter Speed | Motion Rendering | Typical Use |
|---------------|------------------|-------------|
| 1/4000+ | Frozen motion | Sports, action |
| 1/500-1/1000 | Sharp, slight motion blur | Street, general action |
| 1/125-1/250 | Natural motion | Everyday scenes |
| 1/30-1/60 | Motion blur | Intentional motion, panning |
| 1/15 or slower | Significant blur | Long exposure, light trails |

**In-game equivalents:**
- Motion blur slider or shutter angle control
- Time-of-day freeze can affect apparent motion blur
- Some games allow path tracing for natural motion rendering

---

## Exposure & ISO

| ISO Setting | Noise Level | Light Sensitivity | Typical Use |
|-------------|-------------|-------------------|-------------|
| 100-200 | Minimal | Low (bright conditions) | Daylight, tripod |
| 400-800 | Low | Moderate | Indoor, overcast |
| 1600-3200 | Moderate | High | Low light, events |
| 6400+ | High | Very high | Extreme low light |

**In-game equivalents:**
- Exposure slider: Overall brightness
- ISO simulation: Some photo modes add grain at higher "ISO"
- HDR mode: Capture high dynamic range scenes (bright sky + dark shadows)

---

## White Balance & Color Temperature

| White Balance | Color Cast | Typical Conditions |
|---------------|------------|-------------------|
| Daylight | Neutral | Bright sunlight (5500K) |
| Cloudy | Slight warm | Overcast (6500K) |
| Shade | Warm | Open shade (7000K) |
| Tungsten | Blue | Incandescent (3200K) |
| Fluorescent | Green | Fluorescent lights (4000K) |

**Color temperature scale:**
- 2000K: Candlelight (very warm)
- 3000K: Tungsten (warm)
- 5000K: Daylight (neutral)
- 7000K: Overcast (cool)
- 10000K: Heavy shade (very cool)

**In-game application:**
- Time of day affects color temperature
- Color grade in post to adjust mood (warm/cool)
- Some photo modes include white balance presets

---

## Lighting Patterns

### Three-Point Lighting

1. **Key Light:** Primary light source, establishes shape and dimension
   - Position: 45° from camera, 45° above subject
   - Quality: Can be hard (direct) or soft (diffused)

2. **Fill Light:** Softens shadows created by key light
   - Position: Opposite side of key light, lower intensity
   - Ratio: Typically 2:1 to 4:1 (key:fill)

3. **Back Light (Rim Light):** Separates subject from background
   - Position: Behind subject, above and to side
   - Purpose: Creates outline/rim for subject separation

### High-Key vs Low-Key Lighting

| Type | Contrast Ratio | Mood | Typical Use |
|------|----------------|------|-------------|
| **High-key** | Low (< 2:1) | Bright, optimistic | Comedy, romance, commercial |
| **Low-key** | High (> 8:1) | Dramatic, mysterious | Thriller, horror, drama |

### Motivated vs Unmotivated Light

- **Motivated:** Light source visible in scene (sun, lamp, window)
- **Unmotivated:** Light source implied but not visible (fill, rim)

---

## Focus Techniques

| Technique | Description | Effect |
|-----------|-------------|--------|
| **Deep focus** | Foreground and background both sharp | Realism, allows simultaneous action |
| **Shallow focus** | Only one plane sharp, others blurred | Subject isolation, emphasis |
| **Rack focus** | Change focus plane during shot | Direct attention, reveal information |
| **Pull focus** | Follow moving subject with focus | Maintain sharpness on moving target |
| **Split diopter** | Half of frame close focus, half far | Simultaneous near/far subjects (rare) |

**In-game equivalents:**
- Manual focus distance setting in photo mode
- Auto-focus vs. manual focus options
- Some games allow focusing on specific objects

---

## Movement & Stabilization

| Technique | Description | Effect |
|-----------|-------------|--------|
| **Static** | Fixed camera, no movement | Stability, observation |
| **Pan** | Horizontal rotation | Following action, reveal |
| **Tilt** | Vertical rotation | Revealing height, power dynamics |
| **Dolly** | Camera moves through space | Entering scene, following subject |
| **Tracking** | Follows subject laterally | Parallel movement with subject |
| **Crane** | Vertical camera movement | Sweeping overview, dramatic reveal |
| **Handheld** | Camera shake/movement | Realism, immediacy, tension |
| **Steadicam** | Smooth movement without tracks | Fluid motion, gliding feel |

**In-game equivalents:**
- Free camera movement in photo mode
- Some games support cinematic camera paths
- Smooth camera tools for recording

---

## Format & Resolution

| Resolution | Aspect Ratio | Typical Use |
|------------|--------------|-------------|
| 1920×1080 | 16:9 | Standard HD, displays |
| 2560×1440 | 16:9 | QHD, high-end PC |
| 3840×2160 | 16:9 | 4K UHD, high-fidelity |
| 2560×1080 | 21:9 | Ultrawide, cinematic |
| 4096×2160 | 17:9 | DCI 4K, cinema standard |

**In-game considerations:**
- Super-resolution upscale for higher final output
- PNG/TIFF for lossless compression (avoid JPEG artifacts)
- Aspect ratio affects composition (wider = more environmental context)

---

## Sources

- Bordwell, D., & Thompson, K. (2017). Film Art: An Introduction (11th ed.). McGraw-Hill. ISBN 978-1259544627 (Tier 2)
- Block, B. (2008). The Visual Story: Creating the Visual Structure of Film, TV and Digital Media (3rd ed.). Focal Press. ISBN 978-0240807799 (Tier 2)
- Freeman, M. (2007). The Photographer's Eye: Composition and Design for Better Digital Photos. Focal Press. ISBN 978-0240809342 (Tier 2)
- Ward, P. (2003). Picture Composition for Film and Television (2nd ed.). Focal Press. ISBN 978-0240516813 (Tier 2)
