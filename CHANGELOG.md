# Changelog

All notable changes to **Grain of Doubt** (PyWeek 42 entry) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
