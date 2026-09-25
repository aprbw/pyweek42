# Changelog

All notable changes to **Grain of Doubt** (PyWeek 42 entry) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [v1.1.4] - 2026-09-25
### Changed
- **E-Reader Mode Telemetry Alignment**:
  - Moved gameplay telemetry to the 3rd scriptural paragraph (between Ecclesiastes 3:9-13 and 3:14-15).
  - Formatted with `start_y=24`, `line_h=19`, `para_gap=10` so all 3 initial paragraphs fit comfortably on-screen at scroll `prog=0.0`.
- **Lore & Learn Page 1 Refinements**:
  - Competition context featured 1st: Built for PyWeek 42 (September 2026), Theme: Borrowed Time.
  - Placed `"by www.arianprabowo.com"` on its own dedicated line.
  - Refined sand grains description by removing `"only"`.
- **Lore & Scriptures Sin Paraphrases (Pages 3 & 4)**:
  - Envy: *"you want everything you see, so you don't deserve to see as much"*
  - Wrath: *"you use great force to push all dangers away, but you also push all the good things away too"*
  - Sloth: *"you push all dangers to a later time, so you don't have to do anything now"*
- **Developer Mode Bottom Box Dedicated Lines**:
  - Strictly enforced 1 key per line across all 7 lines in `[key] NAME: STATS` format without pipe character cramming.
  - Standardized box geometry ($h=148$, $w=560$) across both Title Screen and in-game translucent debug overlay.
- **Wrath Mechanics Overhaul**:
  - Rebalanced blast radius: Glass shards = 1600px; Sand grains = 3200px.
  - Eliminated zero-yield score penalty completely (`wrath_zero_yield_timer == 0`). The massive 3200px blast scattering all golden sand grains into the deep void serves as the con.
- **Sloth Mechanics Overhaul**:
  - Rebalanced area of effect to 1600px (Left, Right, Down) providing ~2.0s of hazard-free safe descent.
  - Shards within AOE are hurled downward; sand grains within AOE move linearly toward horizontal center ($x=300$) and remain locked in the middle once centered (`stay_in_middle = True`).
- **Documentation & Packaging**:
  - `README.md`: Reordered sections so the 10 Themes list appears after Controls and Seven Deadly Faustian Bargains. Updated Wrath and Sloth pact descriptions. Bumped version to `v1.1.4`.
  - `build.sh`: Updated distribution zip target to `grain-of-doubt-1.1.4.zip`.

## [v1.1.3] - 2026-09-25
### Changed
- **Home Screen Presentation & Controls Layout**:
  - Formatted all keys consistently in square brackets `[...]`.
  - Split controls across dedicated lines to clearly present all hardware and mobile touch options (`[A] / [D] : KEYBOARD`, `[LEFT] / [RIGHT] ARROWS : KEYBOARD`, `[D-PAD] / [THUMBSTICK] : CONTROLLER`, `[LEFT] / [RIGHT] ON-SCREEN : TOUCH`).
  - Simplified Themes section header to `SELECT THEMES` (removed "10" and removed "ACTIVE"), formatting count as normal parentheses `(X/10) <NAME>`.
  - Arranged shortcuts strictly one key per line (`[L] LORE & LEARN TO PLAY` and `[X] QUIT GAME`).
  - Updated Photosensitivity Warning to clarify that Pro Mode is a high-contrast clinical view (not monochrome).
- **Themes Polish**:
  - **Sumi-e (Theme 8)**: Made completely Black & White (BnW) by replacing the red seal stamp (`color 8`) with black (`color 0`), eliminating color 8 from the Kairos palette, and ensuring sand and hourglass rendering use pure monochrome grays and blacks.
  - **Pastel Sakura (Theme 9)**: Updated falling sand to leaf green (`body=11, border=3`) to evoke cherry blossom leaves drifting alongside pink petals.
  - **HUD Faustian Pacts Contrast**: Enhanced `is_light` theme detection to support Pastel Sakura, Sumi-e, and light modes with pure black text (`0`) on white boxes, and crisp white text (`7`) on dark themes, ensuring effortless readability across all 10 themes.
- **End Game / Game Over Screen Overhaul**:
  - Centered `"HOURGLASS SHATTERED"` title mathematically at $x=130$ ($(600 - 339) // 2 = 130$).
  - Removed `"BY ARIAN PRABOWO"` from the game over screen.
  - Split bottom prompts into multiple centered lines for clean readability (`PRESS ANY KEY TO RESTART` / `[X] RETURN TO MENU` / bot countdown).
- **Lore & Learn Screen Overhaul (5 Pages)**:
  - Expanded manual to 5 balanced pages (`MAX_LORE_PAGES = 5`) with strict word wrap ($\le 41$ chars per line):
    - **Page 1**: Interprets Borrowed Time first before grains of doubt; sand grains serve as time units only within an hourglass; defines grain of doubt as natural hesitation.
    - **Page 2**: Explains Lore and Predatory Debt before mechanics; details Chronos (10s continuous flow) and Kairos (10s crossroads); summarizes kinematic controls.
    - **Page 3 (Pacts Part 1)**: Pride, Greed, Lust, Envy with large `scale=2` PRO/CON typography, color swatches, and narrative meaning.
    - **Page 4 (Pacts Part 2)**: Gluttony, Wrath, Sloth with large `scale=2` PRO/CON typography, color swatches, and compounding decay formulas.
    - **Page 5**: 10 Themes, Pro Mode clinical telemetry, E-Reader Stealth Mode (*PhD Comics emergency button tribute*), and loving Sakura dedication (*"lovingly dedicated to my twin sister, girlfriend, and wife—who happen to be the exact same person!"*).
  - Bottom navigation: Removed `[X]` from the arrow line, separating into `[A / LEFT] PREV | [D / RIGHT] NEXT` and a prominent `[X] RETURN TO MENU` prompt.
- **Developer Mode Refinements**:
  - Mapped God Mode toggle to `[G]` key (`pyxel.KEY_G`, with `[I]` fallback).
  - Standardized all dev mode lines across title screen and in-game overlay to `[key] NAME: STATS` format.
  - Removed redundant theme cycling line from dev mode boxes (already accessible on main menu).
- **Packaging**:
  - Updated `build.sh` to package `grain-of-doubt-1.1.3.zip`.

## [v1.1.2] - 2026-09-24
### Changed
- **Homepage Polish & Visual Hierarchy**:
  - Removed redundant `[L] LORE & LEARN TO PLAY` plaque previously situated above the main box (already featured cleanly in Shortcuts).
  - Changed subtitle prompt to `COLLECT GOLDEN SAND FOR POINTS` (emphasizing score acquisition over mere survival).
  - Unified section header color harmony: `SHORTCUTS` is Yellow (`Color 10`), matching `CONTROLS` and `10 THEMES`. Active theme remains Amber/Gold (`Color 9`).
  - Photosensitivity warning overhaul: `"PHOTOSENSITIVITY WARNING"` is rendered huge at `scale=2`, explanatory body text is standard `scale=1`, and redundant theme-cycling shortcut line was removed.
- **Lore & Learn Screen Overhaul (`GameState.LORE`)**:
  - Renamed title to `GRAIN OF DOUBT : LORE & LEARN [PAGE X/4]` (eliminated all "CODEX" terminology).
  - Expanded and rebalanced manual across 4 dedicated pages utilizing spacious `scale=2` typography filling the 552px wide, 768px tall frame without asymmetric empty space:
    - **Page 1 (1/4)**: Hourglass-ception narrative, unstoppable downward descent, why "Grain of Doubt", and PyWeek 42 theme context. (Strictly zero mentions of Ecclesiastes).
    - **Page 2 (2/4)**: Chronos (10.0s relentless descent) and Kairos (10.0s circuit breaker freeze), predatory debt structure, and core kinematic steering.
    - **Page 3 (3/4)**: Faustian Pacts breakdown for all 7 sins (Pride, Greed, Lust, Envy, Gluttony, Wrath, Sloth), compounding boon/curse equations, and tactical survival tips.
    - **Page 4 (4/4)**: 10 Themes, High-Contrast Pro Mode, and E-Reader Stealth Mode (*"Pretend you are reading serious literature and not playing a game at work or school, inspired by the classic PhD Comics emergency button!"*).
  - Refined bottom navigation: `[A / LEFT] PREV   |   [D / RIGHT] NEXT   |   [X] RETURN` (no duplicate page counters at footer).
  - Input protection: `Escape` and `Space` do **NOT** exit Lore! Only `[X]`, `[RETURN]`, `[L]`, `[H]`, touch tap, or Right arrow on the final page exits back to Title.
- **Font Recalculations & Layout Bounds Containment**:
  - **Kairos Modal**:
    - Scaled card titles using exact 5x7 font formula `(len(name) * 6 - 1) * title_scale`. Gluttony tamed to `scale=4` (188px wide within bulging frame, no longer overlapping neighbor card); other sins `scale=3`.
    - Pro/Con feature titles rendered at `scale=2` (e.g. "Tidal Pull", "Fat Grains") with detailed stats at `scale=1`, strictly containing all text within the 196px card printable area.
    - Compounding note centered at `scale=1`.
    - E-Reader Mode: KJV paragraph rendered at `scale=1` with `line_spacing=14`, fitting comfortably within $col\_h = 530$px without crowding the bottom button.
  - **Faustian Pacts HUD Board**:
    - Widened HUD board from 180px to 205px ($x=385$..$590$, clean 10px screen margin).
    - Capitalized sin names (`sin.name.capitalize()`) so "Pride" begins with a capital "P".
    - Right-aligned count numbers (`k`) strictly inside the box.
  - **E-Reader Mode Text Formatting**:
    - Recalculated `render_reader_mode_text` in `engine/themes.py` using exact 5x7 font metrics at `scale=2` (`char_w = 12`, word widths `len(w) * 12`, space = 12), justifying cleanly between margins without bleeding off-screen.
- **Performance & Framerate Optimization**:
  - Verified memory footprint is rock-solid flat at ~151KB across 10,000 continuous simulation frames (zero memory leak).
  - Implemented viewport/frustum culling in `draw()` (`main.py`) for all falling sand grains and glass shards, eliminating ~90% of off-screen trigonometric calculations and polygon draw calls.
  - Set `step_x = 3` in `sand_dunes_landscape.py`, reducing background CPU workload in Theme 0 by 33%.
- **Packaging Pipeline**:
  - Updated `build.sh` to package `grain-of-doubt-1.1.2.zip`.

## [v1.1.1] - 2026-09-24
### Added
- **Multi-Page Lore Codex (`GameState.LORE`)**:
  - Expanded the in-game manual into an interactive 3-page codex derived from `p02.md` Section 2:
    - **Page 1 (1/3)**: Narrative Premise (*Hourglass-ception* — a fragile hourglass falling through the cosmic neck of a shattered colossal hourglass), Unstoppable Downward Descent (SkiFree-style zero-stopping collapse), Why the title "Grain of Doubt" (physical sand units of time + English idiom for paralyzing hesitation during Faustian deals), and PyWeek 42 (September 2026, theme "Borrowed Time") competition context. (Strictly no mentions of Ecclesiastes).
    - **Page 2 (2/3)**: Temporal Duality (Chronos 8.0s relentless kinematic flow vs. Kairos 2.0s circuit-breaker panic freeze), Borrowed Time as Predatory Debt (mandatory Faustian bargains trading future survival for immediate reprieve), and Kinematic Controls summary.
    - **Page 3 (3/3)**: The Seven Faustian Covenants in Catholic canonical order (Pride, Greed, Lust, Envy, Gluttony, Wrath, Sloth) with color plaques and Boon vs. Curse breakdowns, Compounding Decay equations ($Boon \times 0.75^k$, $Curse \times 1.50^k$), and 10 Themes & Pro Mode accessibility tips.
  - **Intuitive Page Navigation**:
    - Press `[A]` or `[LEFT ARROW]` to turn to the previous page.
    - Press `[D]` or `[RIGHT ARROW]` to turn to the next page.
    - Pressing `[RIGHT]` / `[D]` on the last page (Page 3) exits directly back to the Title Screen.
    - Pressing `[X]`, `[ESC]`, `[SPACE]`, `[RETURN]`, `[L]`, `[H]`, or touch screen returns to the Title Screen.
- **Theme 5 Replacement: Glacial Crevasse (`engine/themes.py`)**:
  - Replaced Monochrome Blueprint (which overlapped aesthetically with Pro Mode) with **Glacial Crevasse**: deep blue abyss with sheer meltwater streams, firn ice shelves, and crystalline frost motes.
- **Theme 9 Replacement: Pastel Sakura (`engine/themes.py`)**:
  - Replaced Liminal Vaporwave with **Pastel Sakura**: a cute, girly aesthetic with blossom pink canvas (`Color 14`), drifting cherry blossom petals swaying with organic sinusoidal drift, soft peach clouds, and twinkling fairy dust stars.
- **Dedicated Dev Mode Plaque**:
  - Separated Dev Mode controls into their own dedicated box at the bottom of the Title screen when active (`self.dev_mode = True`), keeping standard controls clean.

### Changed
- **Homepage Centering & Geometric Typography**:
  - Mathematically aligned all Title screen headings using exact 5x7 font metrics formula $(len(s) \times 6 - 1) \times scale$:
    - `"GRAIN OF DOUBT"` ($scale=4$, 332px wide $\to x=134$).
    - `"PYWEEK 42 : BORROWED TIME"` ($scale=2$, 310px wide $\to x=145$).
    - `"BY ARIAN PRABOWO"` ($scale=2$, 190px wide $\to x=205$).
    - Gameplay subtitles and `[L] LORE & LEARN TO PLAY` button ($scale=2$, 286px wide $\to x=157$).
- **Homepage 10 Themes & Controls Box Overhaul**:
  - Header simplified to `"10 THEMES"` (removed "divergent", "pro", and "reader mode").
  - Added clean 1-line vertical gap before the 10 Themes section.
  - Streamlined theme controls to `[,] PREV   |   [.] NEXT` (removed `[0-9] SELECT` and counter from the top line).
  - Consolidated theme indicator onto the active line: `ACTIVE [X/10]: <NAME>`.
  - Added generous 1-line vertical gap before `"SHORTCUTS"`.
  - Cleaned shortcut line: `[L] LORE & LEARN TO PLAY   |   [X] QUIT` (removed `[SPACE] START`).
  - Tightened box height to $222$px ($Y=238..460$), eliminating bottom dead space.
  - Relocated the Photosensitivity Warning & Pro Mode suggestion plaque directly above the blinking start prompt.
- **Theme Names Simplified**:
  - Theme 0: `DUNES IN THE COSMIC HOURGLASS` (was `DESERT DUNES`).
  - Theme 1: `PRO MODE LIGHT` (removed "HIGH CONTRAST").
  - Theme 2: `PRO MODE DARK` (removed "HIGH CONTRAST").
  - Theme 3: `E-READER LIGHT` (was `READER MODE (E-READER LIGHT)`).
  - Theme 4: `E-READER DARK` (was `READER MODE (E-READER DARK)`).
- **Packaging Pipeline**:
  - Updated `build.sh` to assemble `grain-of-doubt-1.1.1.zip`.

## [v1.1.0] - 2026-09-24
### Added
- **Custom 5x7 Typography Engine (`engine/font5x7.py`)**:
  - Implemented spacious 5-pixel character width font covering all 95 printable ASCII glyphs (32..126).
  - Characters 'W' and 'w' feature full 5-pixel wide glyphs and are never squished.
  - High-performance direct pixel rendering via `pyxel.pset` / `pyxel.rect` with zero buffer limitations and 100% cross-platform compatibility across Desktop and WebAssembly.
- **Pro Mode 3-Line Kairos Cards**:
  - Redesigned Kairos Dilemma cards in Pro Mode into a high-density, ultra-clean 3-line format:
    - Line 1: 2-letter sin abbreviation (1st capitalized, 2nd lowercase, e.g. `Pd` for Pride, `Gd` for Greed, `Lt` for Lust, `Ey` for Envy, `Gy` for Gluttony, `Wh` for Wrath, `Sh` for Sloth) in 3x huge font (`scale=6`).
    - Line 2: Full sin name written in standard font (`scale=2`).
    - Line 3: Level number alone without the word "level" in 3x huge font (`scale=6`).
  - **Wrath Card Contrast Fix**: Font color rendered in crisp white (`Color 7`) against red background (`Color 8`) for WCAG AAA contrast compliance.
- **Reader Mode Justified KJV Kairos Dilemmas**:
  - In Reader Mode, cards display the covenant title like usual, followed by an authentic King James Version narrative paragraph describing boon and curse with justified text alignment without bullet points.
- **Lore & How to Play Codex Screen (`GameState.LORE`)**:
  - Added dedicated sub-screen accessible from the Title screen via `[L]` or `[H]` keys.
  - Documents the narrative premise (Ecclesiastes 3), Chronos vs Kairos architecture, the Seven Faustian Covenants, and accessibility tips.
- **Photosensitivity / Epilepsy Warning Plaque**:
  - Added high-contrast warning plaque on Title screen directing players to Pro Mode (Themes 2 & 3) for calm monochrome blueprint graphics.

### Changed
- **Relative Background Kinematics (Pro Mode)**:
  - Background grid scrolls upward at $1.6\times$ scroll speed (`dist_bg = int(dist * 1.6)`).
  - Hazards and sand grains moving at $1.0\times$ speed visually travel downward relative to the grid ($0.6\times$ speed) while the player falls downward even faster ($1.6\times$ speed), keeping screen-space gameplay and mechanics 100% identical.
- **Pro Mode Shard Drop Shadow Suppression**:
  - Shard drop shadows are strictly suppressed in Pro Mode Light and Dark for clean monochrome blueprint aesthetics.
- **Pro Mode Dark Pact Board Text Color**:
  - Unselected pact text ($k=0$) drawn in bright Cyan (`Color 12`) so text never blends into dark background grid lines.
- **HUD Box Alignment & Clutter Elimination**:
  - Eliminated overlap between Time container (`x=225, w=150`) and Score container (`x=390, w=200`), removing the vertical border line dividing score text.
  - Removed cluttering HUD badges (`WRATH: ZERO YIELD` and `TIDAL PULL`).
- **Hardware Dither Transparency (`pyxel.dither`)**:
  - Applied `pyxel.dither(0.70)` to Developer Overlay, Pact Sealed banner, and Theme banner.
  - Applied `pyxel.dither(0.60)` to Mobile touch arcade buttons.
- **Firefox on Android Mobile Viewport Optimization**:
  - Added `-moz-text-size-adjust: 100% !important;` to disable automatic text-size inflation.
  - Removed canvas `object-fit: contain` to eliminate Firefox Android canvas cropping bugs.
  - Dynamically clamped `fitScreen()` against `visualViewport`, client width, and high `devicePixelRatio`.

## [v1.0.0] - 2026-09-24
### Added
- **Curated 10 Maximally Divergent Themes (`0..9`)**:
  - Streamlined the theme catalog into a curated roster of 10 maximally divergent, high-contrast themes mapped directly to keyboard number keys `0` through `9` as well as `,` / `.`:
    - `0: Desert Dunes` (Continuous procedural sand dunes landscape with perspective inverse Z-depth motion, intra-layer shadow mapping, and atmospheric scattering; formerly SkiFree Sandfall).
    - `1: Pro Mode Light` (Clinical white engineering grid, static major/minor blueprint grid, dual vertical margin countdown bars, extreme contrast).
    - `2: Pro Mode Dark` (Pitch-black background, static major/minor blueprint grid, dual vertical margin countdown bars, WCAG AAA compliant contrast).
    - `3: Reader Mode Light` (Warm parchment digital e-reader displaying Ecclesiastes 3 KJV with justified typography and disguised scripture telemetry).
    - `4: Reader Mode Dark` (Midnight slate digital e-reader displaying Ecclesiastes 3 KJV with justified typography and disguised scripture telemetry).
    - `5: Monochrome Blueprint` (Navy architectural drafting blueprint with precision coordinate grids and measurement callouts).
    - `6: Magma Caldera` (Volcanic obsidian crags, molten basalt flumes, glowing embers, and fiery core).
    - `7: Retro Terminal Matrix` (Monochrome green CRT phosphor terminal with digital glyph matrix rain and scanlines).
    - `8: Zen Ink Wash (Sumi-e)` (Minimalist Japanese washi parchment, black ink calligraphy brush strokes, and red artisan seal).
    - `9: Liminal Vaporwave` (Dreamlike pink, periwinkle, and cyan wireframe grid with synthwave retro aesthetic).
- **Direct Number Key Theme Shortcuts**:
  - Keys `0` through `9` instantly select the corresponding curated theme from anywhere in gameplay or the title screen.
- **Ecclesiastes 3 KJV Prose Telemetry**:
  - Formatted telemetry as authentic 17th-century King James Bible prose strictly avoiding modern parentheses or brackets (e.g., *"and three faustian covenants have been made, to wit, two of Pride, and one of Sloth."*).
  - Embedded as the second paragraph between Ecclesiastes 3:1-8 and 3:9-13.
- **Dune Horizon Kairos Warning Temporal Glitch**:
  - In Theme 0 (Desert Dunes), imminent Kairos triggers a cosmic temporal rupture: dune layers rapidly blink across randomized desert palette tones and the vertical perspective gap dynamically shifts, destroying the spatial depth illusion.

### Changed
- **Chronos & Kairos 10.0-Second Cycle Rhythm**:
  - Chronos active sandfall descent duration set to `10.0` seconds (300 frames).
  - Kairos dilemma choice duration set to `10.0` seconds (300 frames).
- **Kairos Input Safety Lockout**:
  - Added a `1.0`-second input lockout upon entering Kairos time, preventing accidental card triggers from held steering inputs or immediate panic reactions.
- **Autonomous Bot Deliberation Delay**:
  - AI playtesting bot now incorporates a deliberate `2.0`-second evaluation pause before choosing Faustian bargains, reflecting human cognitive processing.
- **Reader Mode Translucent Watermark Tuning**:
  - Glass shards rendered at `0.30` alpha (`pyxel.dither(0.30)`).
  - Sand grains and player hourglass rendered at `0.60` alpha (`pyxel.dither(0.60)`).
  - Cleanly restores full opacity (`1.0`) after entity drawing.
- **Pro Mode Blueprint Grid**:
  - Both minor grid ($10 \times 10$ px) and major grid ($50 \times 50$ px) remain static on screen as a stationary drafting blueprint across player movement.
- **Theme-Harmonized Kairos Modal Styling**:
  - Modal body and border colors dynamically harmonize with each active theme's custom palette tokens.
- **Greed Pact Borrowed Time Mechanics**:
  - Enhanced sand simulation during Borrowed Time so Gluttony sand clusters cleanly multiply score potential.
- **Typography & Polishing**:
  - Fixed Game Over screen typo ("Debt Collected").
  - Fixed Gluttony oversized triangle rendering to use the exact theme shard facet palette.
  - Bumped engine release version to `v1.0.0`.

## [v0.19.0] - 2026-09-24
### Added
- **Continuous 2D Procedural Sand Dunes Landscape (`sand_dunes_landscape.py` & Theme 0)**:
  - **Topology Engine**: Layered procedural wave polygons rendered back-to-front. Prohibits explicit stroke outlines—defining dune boundaries entirely through negative space between sequential procedural waveforms.
  - **Perspective Inverse Z-Depth Velocity**: Projects simulated depth to 2D screen coordinates converging toward a supra-canvas horizon point ($Y_H = -140$). Translation velocity and wave amplitude are modulated inversely against Z-depth ($\frac{dY}{dt} \propto (Y - Y_H)^2$). Proximal dunes at the bottom rush upwards at $>10\times$ the velocity of distal dunes near the top, which experience asymptotic stalling near the horizon.
  - **Intra-Layer Shadow Mapping**: Binds localized vertical linear color gradients within wave geometry—rendering darker crest coordinates transitioning into luminous dune bases to simulate realistic directional self-shadowing.
  - **Atmospheric Scattering**: Overrides localized gradients with a global luminosity scalar linked to Z-depth, desaturating and optically bleaching distant ridges into the ambient desert haze threshold.
  - **Standalone Executable Script**: Created `sand_dunes_landscape.py` with interactive keyboard controls (`A`/`D` pan, `W`/`S` scroll speed, `U`/`J` horizon altitude, `P` haze toggle, `C` screenshot, and `--headless` automated test flags).
- **Reader Mode (E-Reader Dark & Light, Themes 13 & 14)**:
  - Replaced legacy stealth specifications with an authentic digital e-reader interface.
  - **Genuine Scripture Text**: Embedded complete **Ecclesiastes 3:1-22 (King James Version)** ("To every thing there is a season, and a time to every purpose under the heaven...").
  - **Double-Sized E-Reader Typography**: Double font size (`scale=2`, $8 \times 12$ px characters) formatted as continuous, un-indented wrapped prose.
  - **100% Floating HUD Suppression**: Removed all floating arcade UI containers (hearts, score, chronos timer bar, and pact list).
  - **Disguised Line 2 Telemetry**: Formats vital game state seamlessly into the second line of the prose (`Hearts: X/5 | Score: Y | Time: Z.Zs | Pacts: None / List`).
  - **30% Alpha Translucent Gameplay Elements**: Applies `pyxel.dither(0.30)` to the player hourglass, falling triangle glass shards, and cascading sand grains, transforming fast-paced arcade action into subtle watermarks beneath the prose.
- **20 Divergent Aesthetic Themes**: Introduced 20 completely unique, cohesive aesthetic themes accessible in real time:
    1. *SkiFree Sandfall (Dune Horizon)*: Continuous 2D procedural sand dune landscape, perspective Z-depth scaling, and atmospheric scattering.
    2. *Cosmic Chronometer*: Deep midnight space, concentric planetary orbits, astrolabe celestial ticks.
    3. *Abyssal Hourglass*: Pitch black void, bioluminescent indigo trails, and crystalline glints.
    4. *Shattered Mirror Chasm*: Iridescent violet prism corridors, silver quartz dust, and fractured facets.
    5. *Magma Caldera*: Volcanic obsidian crags, molten basalt flumes, glowing embers, and fiery core.
    6. *Cartographer's Scroll*: Aged sepia parchment, nautical rhumb lines, and compass bearings.
    7. *Pro Mode (High Contrast Dark)*: High-contrast pure black background, static major/minor grid lines fixed to screen background, dual vertical Chronos countdown progress bars at extreme left/right margins, and color-blind safe palettes (WCAG AAA).
    8. *Pro Mode (High Contrast Light)*: Clinical white engineering drafting grid, static major/minor grid lines fixed to screen background, dual vertical Chronos countdown progress bars at extreme left/right margins, pitch-black obsidian shards, amber sand, and extreme luminance delta.
    9. *Copper & Verdigris*: Oxidized green patinas, hammered bronze gears, and industrial copper rivets.
    10. *Solar Flare*: Blinding orange and yellow coronal mass ejections and solar prominence arches.
    11. *Monochrome Blueprint*: Navy architectural technical blueprint with white drafting grid lines and measurement callouts.
    12. *Glacial Crevasse*: Sub-zero ice shelf, vertical fissure crevasses, and permafrost ice needles.
    13. *Retro Terminal Matrix*: Monochrome green CRT phosphor terminal, falling digital glyph matrix rain, and scanlines.
    14. *Reader Mode (E-Reader Dark)*: Digital e-reader displaying Ecclesiastes 3 KJV in double-sized font, 100% suppressed floating HUD, disguised Line 2 telemetry, and 30% alpha translucent watermarks.
    15. *Reader Mode (E-Reader Light)*: Warm parchment e-reader displaying Ecclesiastes 3 KJV, disguised Line 2 telemetry, and 30% alpha gameplay watermarks.
    16. *Neon Noir Megacity*: Rain-slicked cyber metropolis, neon signage, and vertical skyscraper silhouettes.
    17. *Liminal Vaporwave*: Dreamlike pink and periwinkle wireframe grid with neon aesthetic.
    18. *Chalkboard Theory*: Dark slate academic chalkboard with sketched physical equations and calculus integrals.
    19. *Blood Moon Eclipse*: Crimson lunar halo, eclipse corona rays, and dark sanguine dunes.
    20. *Zen Ink Wash (Sumi-e)*: Minimalist Japanese parchment, black ink wash brush strokes, and red artisan seal.
- **Universal Theme Switching & Home Page Integration**:
  - Theme selection using `,` (previous) and `.` (next) is now accessible to all players at any time, decoupled completely from Dev Mode.
  - Title Screen (Home Page) features a dedicated "20 DIVERGENT THEMES (PRO & READER MODES)" guide showcasing key shortcuts and live-updating active theme indicator.

- **Pro Mode Dual Vertical Countdown Progress Bars**:
  - Pinned to the extreme left (`x = 0..6`) and extreme right (`x = 594..600`) margins of the screen.
  - Progresses downwards from top to bottom during Chronos descent, providing intuitive peripheral vision countdown until Kairos strikes.
  - Features imminent urgency pulsing (Crimson Red / Amber) during the final 1.5 seconds.
- **Eliminated UI Checkerboard Noise for 100% Typography Readability**:
  - Replaced dithered transparency on all UI text containers (Hearts, Elapsed Time, Score, Faustian Pacts HUD, Kairos modal body, Game Over stats, theme banner, dev overlay, and mobile buttons) with solid opaque backgrounds and crisp borders.
  - Background dimming behind modals now uses a clean full-screen ambient backdrop, ensuring zero checkered dot artifacts interfere with text across all 20 themes.
- **Harmonious Entity & Palettes System**:
  - Each theme defines bespoke palettes for sand grains (body, outline, center glint, drop shadow, fat grain styling), glass shards (translucent facet, outline, specular glint, drop shadow, fat shard styling), and player hourglass (caps, cap highlights, rivets, glass walls, waist neck, and dual-tone bulb sands).
- **Dedicated Theme Engine Architecture (`engine/themes.py`)**:
  - Modularized theme definitions and procedural background math into dedicated dataclasses (`Theme`, `SandPalette`, `ShardPalette`, `HourglassPalette`) with infinite horizontal rendering and high 60 FPS performance.
- **Mobile Browser Zoom Prevention & Touch Hardening**:
  - Implemented multi-layered defense to completely disable browser zoom gestures on mobile devices while maintaining responsive Pyxel canvas controls:
    - Viewport metadata configured with `user-scalable=no, maximum-scale=1.0, viewport-fit=cover`.
    - CSS touch restrictions: `touch-action: none !important`, `overscroll-behavior: none !important`, `-webkit-touch-callout: none !important`, and `-webkit-user-select: none !important`.
    - Active JavaScript listeners preventing Safari gesture events (`gesturestart`, `gesturechange`, `gestureend`).
    - Multi-touch pinch zoom prevention for `touchstart` and `touchmove` (`e.touches.length > 1`).
    - Double-tap zoom debounce suppression window ($\le 300$ms).
    - Trackpad and Ctrl-wheel zoom prevention (`wheel` with `ctrlKey`).

---

## [v0.18.0] - 2026-09-23
### Added
- **Complete Visual Decluttering (Zero Particles)**: Removed all screen-space particle clutter, including sand collection sparks, hazard explosion bursts, and hourglass drip trails, ensuring players maintain unobstructed focus on essential sand grains and lethal glass shards.
- **Hourglass Interior Scoring Feedback**: Replaced distracting particle popups with localized sprite feedback: upon collecting sand grains, the hourglass bulbs and waist neck flash in radiant gold/amber glints (`player_score_flash_timer = 8`).
- **Braided Sandfall / Landslide Terrain (Fluid Sand River)**: Replaced static terrain with a dynamic, rushing golden sand river:
  - *Cascading Flumes & Streamlines*: Striated vertical flow lines streaming through channels with distinct speed multipliers (1.18x to 1.50x), creating genuine fluid velocity shearing and the visceral sensation of an active landslide pouring downhill.
  - *Braided Sandbar Banks & Weaving Channels*: Sinuous, undulating sandbar ridges with sunlit white rims (`7`) and amber slope shadows (`9`/`4`), breached by deep channel chutes where sand rushes through.
  - *Granular Froth & Shoal Pebbles*: Procedural spray motes (`10`/`7`) dancing at chute breaches, miniature sand ripple arcs, and sandstone pebbles on calm shoals.
  - *Greed Blood-River Mode*: When Greed triggers ("Borrowed Time"), the golden river transforms into a subterranean torrent of blood and magma (`2`/`4` base, `8` crimson flumes, `14` pink foam).
- **High-Contrast Entity & Shadow Rendering**:
  - *Sand Grains*: Cast warm drop shadows on the sand and feature rich amber-brown outlines (`4`) around sparkling golden bodies (`10`/`9`) and white facet glints (`7`).
  - *Glass Shards*: Cast distinct drop shadows on the slope (`4`) and have razor-sharp black perimeter outlines (`0`) around translucent icy cyan facets (`6`) with specular glints (`7`).
  - *Player Hourglass*: Casts an oval drop shadow onto the sand slope beneath it, physically anchoring the player to the desert.
- **Gluttony Bent Frame UI**: In the Kairos modal, the card frame borders now visibly bend and bulge outward by 22 pixels around the oversized `GLUTTONY` title, making its massive width look completely intentional, humorous, and thematic.
- **Hourglass Player Silky Gliding Physics**: Rebalanced air friction damping from aggressive `0.85` down to a gentle `0.94` (`air_friction = 0.06`, `base_accel = 2.4`), allowing the player hourglass to glide smoothly and preserve momentum naturally when controls are released.
- **Obtuse Glass Shard Geometry**: Shards now procedurally generate as obtuse triangles (one angle $> 90^\circ$, verified by negative vector dot product $< -8.0$) as well as acute/scalene triangles, while maintaining strict exclusion of right-angled shapes.
- **Aerodynamic Shard Rotation**: Shard angular velocity is now proportional to horizontal airspeed $V_x = \text{base\_vx} + v_x$, realistically simulating aerodynamic torque as glass shards flutter through the air.
- **Gluttony Fat Entities Rework**: Completely redesigned Gluttony progression:
  - At Gluttony level $N$: Probability of fat entities is $1.0 - 0.9^N$ (Level 0: 0% fat, 100% normal).
  - **Fat Sand Grains**: $\sim 3\times$ radius / length-wise ($10\times$ area), awarding $3\times$ score ($3$ points per grain).
  - **Fat Glass Shards**: $\sim 2.8\times$ linear dimensions ($10\times$ area), creating massive, menacing obstacles.
- **Double Danger Sloth Overlap**: When Sloth hurls shards downward, new hazards are seeded at the bottom horizon ($y \in [1050, 1450]$ px). The hurled shards catch up and overlap with oncoming hazards, creating a doubly dangerous wall of glass that returns when descent resumes.
- **UI & HUD Polish**:
  - Spaced time display: Added clear whitespace before units (`TIME: 24.5 s`).
  - Faustian Pacts board: Widened the top-right HUD box to 180px with full title `FAUSTIAN PACTS`.

### Changed
- **Envy Starting Point Recalibration**: Recalibrated Envy dual-radius progression so Envy 1 equals previous Envy 3:
  - Exponent mapped to $k_{\text{eff}} = k + 2$.
  - Envy 1: Outer radius $= 1200 \times 0.8^3 = 614.4$ px; Inner radius $= 1000 \times 0.8^4 = 409.6$ px.
- **Wrath Pure Kinetic Shockwave**: Removed all particle debris from Wrath explosion; radial blast acceleration and screen shake are preserved with pristine visual clarity.

---

## [v0.17.0] - 2026-09-23
### Added
- **Multi-Frame Burst Acceleration Curve**: Replaced single-frame extreme impulse spikes in Sloth and Wrath with smooth, multi-frame acceleration curves distributed across 10–12 frames.
- **Pride Spatial Hazard Density Preservation**: Scaled wave spawn accumulation directly with `speed_multiplier`. When descent speed is increased (e.g. by Pride pacts), the spawn rate scales proportionally so spatial density (entities per 100 vertical pixels fallen) remains constant, preventing the world from diluting or becoming easier at high speeds.

---

## [v0.16.0] - 2026-09-23
### Added
- **Dynamic Glass Shard Geometry**: Replaced uniform right-angled triangles with procedurally randomized non-right-angled (acute/scalene) triangles verified by vector dot products ($|A \cdot B| > 0.05$).
- **Continuous Glass Shard Tumbling**: Shards now spin continuously with individual randomized float angular velocity ($\text{spin\_speed} \in [-0.18, -0.04] \cup [0.04, 0.18]$ rad/frame).
- **Deep World Simulation (10 Seconds Down)**: Extended entity active simulation and despawn boundary down to $y \le 6000.0$ px (~10–12 seconds of scroll time) so downward-hurled and blasted hazards persist and catch up to the player.
- **Wrath Shockwave Particles**: Dual-ring debris bursts, 24-particle central shockwave, and 2.5× shard spin burst upon detonating Wrath explosion.

### Changed
- **Wrath Rework (1200px Radial Kinetic Explosion)**: Replaced instant screen hazard wipe with an instant 1200px radial explosion blasting both golden sands and glass shards outward away from the player with high acceleration ($\text{impulse} \le 46.0$ px/frame). Screen shakes for 20 frames at 12px intensity. 10.0s zero-yield curse remains active.
- **Lust Rebalance**: Reduced base magnetic attraction radius from 180px down to 100px, scaling by +50px per subsequent pact ($r_{\text{lust}} = 100.0 + k \times 50.0$ px) symmetrically for both sand motes and glass shards.
- **Terminal Velocity Clamp**: Increased shard and sand terminal velocity clamp from 22.0 px/frame to 50.0 px/frame to accommodate explosion and downward hurl physics.
- **Strict Naming Consistency**: Completely eradicated all references to "razor" regarding shards and hazards across the repository; all hazard entities are consistently named **glass shards**.

---

## [v0.15.0] - 2026-09-23
### Added
- **Sloth Lazy Reprieve (Lazy = Doing Nothing)**: In a single high-acceleration impulse frame, all glass shards below the player within 3 screens wide are hurled downward toward the bottom horizon ($v_y \ge 38$ px/frame, $y \ge y_p + 520$ px).
- **Safe Void Window**: Clears the descent space directly below the player for ~2.0 to 2.5 seconds, allowing the player to do literally nothing and survive.
- **Bottom Clumped Wave**: Hurled shards condense into a dense, dangerous wave near the bottom horizon that later scrolls back upward.

### Changed
- **Envy Terminology Alignment**: Standardized terminology to **Tidal Pull** across the HUD, Kairos cards, engine summaries, and documentation.
- **LaTeX Math Sanitization**: Cleaned all mathematical delimiters and percent escapes across the documentation for universal compatibility with GitHub Flavored Markdown and KaTeX.

---

## [v0.14.0] - 2026-09-23
### Added
- **Second-Order Newtonian Momentum Physics**: Replaced discrete positional translation with proper acceleration, velocity, and momentum physics ($\mathbf{a} \to \mathbf{v} \to \mathbf{x}$) for Lust and Envy.
- **Viscous Momentum Gliding**: Grains and glass shards carry momentum and smoothly decelerate with viscous damping ($0.94$ drag) when magnetic attraction ends.
- **GOFAI Dynamic Momentum Perception**: Autonomous bot kinematics upgraded to project future hazard trajectories using active momentum vectors.

---

## [v0.13.0] - 2026-09-23
### Changed
- **Kairos Card Typography Overhaul**: Increased card title font size significantly (scale 7, +133% larger than former scale 3).
- **Horizontal Box-Filling Titles**: Calibrated font scaling to fill nearly the entire card box horizontally based on the longest sin name (`GLUTTONY`), leaving clean 5–6px margins.
- **Center-Justified Layout**: Titles and level indicators are justified center horizontally within each card for instant split-second legibility during the 2.0-second Kairos circuit breaker.

---

## [v0.12.0] - 2026-09-23
### Added
- **Envy Tidal Pull Boon**: Reworked Envy boon into temporary Tidal Pull: for 2.0 seconds (60 frames), all sand grains within 2× the current vignette pixel radius (1920px at Pact 1) are strongly drawn into the hourglass.
- **Tilt-Proportional Sand Physics**: Direction and flow velocity of falling sand (both internal neck flow, dynamic bulb sand redistribution, and external dripping cascade) are directly proportional to the hourglass tilt angle.
- **GOFAI Bot Envy Handicap**: Constrained autonomous bot perception to the visible circular vignette mask, making dark void hazards invisible to AI pathfinding.

### Changed
- **Score Space Formatting**: Removed leading zeros across HUD and Game Over screen; scores format with single space thousands separators (e.g. `SCORE: 1 234`).

---

## [v0.11.0] - 2026-09-23
### Added
- **Bot Mode Restart Delay**: Autonomous bot waits 6.0 seconds (180 frames) with live countdown before restarting, allowing review of final run statistics.

### Changed
- **Difficulty Rebalance (Halved Initial Spawn Rate)**: Reduced base entity spawn accumulator from 0.45 to 0.225 per frame, halving the initial amount of sand grains and glass shards at the start for a smoother learning curve.
- **Envy Vignette Progression (Dual-Radius)**:
  - Outermost circle (zero vision beyond): $\text{radius} = 1200 \times 0.8^k$ px.
  - Innermost circle (full clear vision): $\text{radius} = 1000 \times 0.8^{k+1}$ px.
  - 5 graduated dither transparency tiers interpolated between inner and outer radii.

---

## [v0.10.0] - 2026-09-23
### Added
- **X Key Dual-Behaviour**: In gameplay (Chronos / Kairos / Game Over), pressing `X` returns to the Title Menu without quitting. On the Title Menu, `X` exits the application (graceful no-op in browser).
- **Numbered Top-Right Pact Menu**: Replaced the `(7)` header with a clean, canonically ordered numbered list (`1. pride 0`, `2. greed 0`, etc.).

### Changed
- **Envy Documentation**: Documented mathematical progression for inner and outer vignette radii.
- **Version Normalization**: Normalized version sequence from v0.9.0 to v0.10.0.

---

## [v0.9.0] - 2026-09-23
### Added
- **Dev Mode Pact Reduction Shortcuts**: Keys `Q`, `W`, `E`, `R`, `T`, `Y`, `U` in Dev Mode decrement corresponding pact levels in canonical order and dynamically relax active modifiers.
- **Lethal Borrowed Time (Greed Overhaul)**: Greed timer countdown displayed in Dev Mode overlay; when Borrowed Time expires, the debt is collected and the player instantly dies with dedicated cause of death.
- **Dev Mode Title Screen Version Display**: Displays version number on the main title screen header when Dev Mode is active.

### Changed
- **Universal PC & Mobile Viewport 3:4 Containment**: Implemented pure CSS responsive containment (`--target-w: min(var(--avail-w), calc(var(--avail-h) * 0.75))`) with continuous JS visual viewport observation to eliminate canvas cropping.
- **Remapped Quit Shortcut**: Changed quit key from `Q` to `X` (`pyxel.KEY_X`), preventing accidental quits while inspecting pact reduction shortcuts.

---

## [v0.8.0] - 2026-09-23
### Added
- **Kairos Input Re-press Protection**: Prevents accidental pact selection upon entering Kairos if holding lateral steering keys; requires fresh button release and re-press.
- **Pride Organic Cluster Randomization**: Sand clusters spawn with randomized relative non-overlapping offsets ($r \in [14, 36]$ px) while preserving shared velocity and trajectory.

### Changed
- **Mobile Viewport Optimization**: Implemented `100svh`, safe area insets, and active visual viewport centering cushion.
- **Clean Game Over Screen**: Simplified pact count display, removed redundant debug labels, and added debounced restart lockout.

---

## [v0.7.0] - 2026-09-23
### Added
- **Dev-Only Bot & Video Toggles**: Restricted bot mode (`B`) and video recording (`V`) activation exclusively to Dev Mode.
- **Greed 110% Score Multiplier**: Each sand grain collected during Borrowed Time multiplies the current score by 110% (`floor(score * 1.10)`).
- **Envy Screen Sand Reap**: Granted instant screen-wide sand harvest upon sealing Envy pact.
- **Mathematical Calibrations**: Added exact compounding formulas ($k \ge 0$) to design documentation.

---

## [v0.6.0] - 2026-09-23
### Added
- **Mobile Responsive 3:4 Letterbox**: Responsive web layout maintaining strict 3:4 portrait aspect ratio.
- **Transparent Touch Controls**: Semi-transparent on-screen `< LEFT` and `RIGHT >` touch steering buttons for mobile viewports.
- **±4.5 Screen Spawn Horizon**: Procedural entity generation margin expanding 2700px on each lateral side to support unrestricted horizontal exploration.
- **Game Over 2.0s Debounce Lockout**: Enforced 60-frame lockout preventing accidental restart inputs.
- **Canonical 7 Sins Vertical List**: Arranged Faustian Bargain deck in strict Gregorian Catholic order (SALIGIA).

---

## [v0.5.0] - 2026-09-23
### Added
- **1-Point Golden Sand Standard**: Normalized scoring to 1 point per grain.
- **Pride Sand Clusters**: Pride spawns multiple sand motes in clustered formations.
- **Bottom Alpha Dev Overlay**: Semi-transparent HUD toggled via backtick (`` ` ``) with telemetry and `1`–`7` instant pact injection keys.
- **Enlarged Typography**: Upgraded retro text scale for enhanced readability.

---

## [v0.4.0] - 2026-09-22
### Added
- **SkiFree Infinite Horizontal Arena**: Removed lateral boundary walls; player and hazards navigate an infinite horizontal expanse with smooth camera tracking.
- **Lossless FFmpeg Video Recorder**: Real-time canvas MP4 video export with unique timestamped filenames.
- **Elapsed Time HUD**: Survival timer and descent stopwatch displayed on screen.

---

## [v0.3.0] - 2026-09-22
### Added
- **Dual-Tier Concentric Vignette**: Circular darkness mask with clear central core and 50% dithered boundary ring.
- **5-Heart Life System**: Fragile hourglass vessel with 5 hearts, invulnerability flash, and impact screen shake.
- **Background Temporal Stimuli**: Animated falling cosmic sand streams and parallax dust motes.
- **Dual-Clock Engine (Chronos & Kairos)**: 8-second Chronos descent followed by 2-second Kairos circuit breaker with 2-card Faustian Bargain selection.
- **Lateral Drift Physics**: Dynamic X-axis velocity variance and sinusoidal flutter oscillation for falling entities.

---

## [v0.2.0] - 2026-09-22
### Added
- **Resolution Upscale to 600 × 800**: High-definition retro portrait resolution (3:4 aspect ratio).
- **Kinematic Steering**: Lateral movement with viscous damping coefficient ($0.82$).
- **Tilting Hourglass Sprite**: Physical hourglass tilt proportional to horizontal velocity.
- **GOFAI Autonomous Playtesting Bot**: Heuristic AI agent with spacetime trajectory projection for headless evaluation and balance benchmarks.

---

## [v0.1.0] - 2026-09-22
### Added
- **Initial PyWeek 42 Prototype ("Borrowed Time")**:
  - Endless downhill retro falling-hourglass arcade runner concept ("Hourglass-ception").
  - Basic sand collection and glass hazard evasion mechanics.
  - Pyxel retro game engine loop, state manager, and initial asset framework.
