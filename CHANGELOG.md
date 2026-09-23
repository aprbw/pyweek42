# Changelog

All notable changes to **Grain of Doubt** (PyWeek 42 entry) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
