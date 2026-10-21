# Recap: Grains of Doubt (PyWeek 42) — September & October 2026

**Project Scope:** *Grains of Doubt* (PyWeek 42 entry: "Borrowed Time")  
**Project Directory:** `/Users/z3540725/My Drive/personal/2026 09 22 PyWeek 42 Borrowed Time`  
**Time Range:** 2026-09-01 to 2026-10-21  
**Timezone Notes:** Converted from UTC timestamps recorded in session transcripts to the active local timezones:
* **2026-09-22 to 2026-09-24 (early afternoon):** AEST (`UTC+10:00`)
* **2026-09-24 (afternoon) to 2026-09-26:** WIB (`UTC+07:00`)
* **2026-09-28 to 2026-10-07:** WITA / SGT (`UTC+08:00`)

---

## Project Overview Summary

* **Total Active Time:** 20h 31m (approx. 20.5 hours) across 7 active days and 33 discrete work sessions.
* **Scope & Delivery:** Conceptualized, built, tested, and released *Grains of Doubt* from initial game design document (`p02.md`) to the competition-ready PyWeek 42 entry (`v1.2.5`), followed by post-jam polish releases (`v1.2.6` – `v1.2.8`). Work encompassed core Pyxel engine game loop architecture, heuristic playtesting bot implementation, custom 5x7 bitmap typography, procedural sound synthesis, dual Chronos/Kairos time-dilation and deadly sin bargain mechanics, mobile touch responsive UI, WebAssembly browser builds, and high-contrast accessibility themes.

---

## Daily Summary

* **2026-09-22 (3h 47m):** Authored the core game design document, scaffolded the Pyxel engine architecture, built an automated playtesting bot, and balanced initial survival mechanics.
* **2026-09-23 (4h 27m):** Implemented mobile responsive touch controls, integrated continuous momentum physics, streamlined visual clutter, and established automated versioned changelog tracking.
* **2026-09-24 (6h 56m):** Designed high-contrast Pro/Stealth themes, synthesized procedural audio effects, finalized KJV-styled lore, and launched official release `v1.0.0` through `v1.1.0`.
* **2026-09-25 (3h 51m):** Engineered custom 5x7 bitmap typography, optimized web distribution bundles, fixed mobile touch hitboxes, and purified the monochrome Sumi-e theme for `v1.2.2`.
* **2026-09-26 (0h 54m):** Designed and implemented directional motion streaks to visually communicate the inverted control mechanic during Wrath pacts (`v1.2.3` - `v1.2.4`).
* **2026-09-28 (0h 10m):** Completed pre-submission checklist verification and packaged official release `v1.2.5` as the final PyWeek 42 competition submission.
* **2026-10-07 (0h 26m):** Executed post-competition polish across releases `v1.2.6` to `v1.2.8`, adding scientific notation for million-plus scores and harmonizing E-Reader palette uniformity.

---

## Detailed Session Logs

### 2026-09-22

* [2026-09-22 01:15 - 02:32 UTC+10:00] **Game Design Document Specification & Architectural Framing:** Authored and iterated on the formal Game Design Document (GDD) in megaprompt format within [`p02.md`](file:///Users/z3540725/My%20Drive/personal/2026%2009%2022%20PyWeek%2042%20Borrowed%20Time/p02.md) based on the initial conceptual notes in [`p01.md`](file:///Users/z3540725/My%20Drive/personal/2026%2009%2022%20PyWeek%2042%20Borrowed%20Time/p01.md). Defined core Pyxel engine constraints, the duality of Chronos vs Kairos time, seven deadly sin bargains, hourglass UI visual hierarchy, and an autonomous execution loop for self-directed coding agents.

* [2026-09-22 03:18 - 04:09 UTC+10:00] **Visual Art Style Integration & Autonomous Foundation Build:** Incorporated visual aesthetic principles and color theory into [`p02.md`](file:///Users/z3540725/My%20Drive/personal/2026%2009%2022%20PyWeek%2042%20Borrowed%20Time/p02.md), then initiated an autonomous build loop. Implemented foundational modules including game state tracking in [`engine/state.py`](file:///Users/z3540725/My%20Drive/personal/2026%2009%2022%20PyWeek%2042%20Borrowed%20Time/engine/state.py), sand grain particle physics and glass shards in [`engine/entities.py`](file:///Users/z3540725/My%20Drive/personal/2026%2009%2022%20PyWeek%2042%20Borrowed%20Time/engine/entities.py), procedural sound synthesis in [`engine/audio.py`](file:///Users/z3540725/My%20Drive/personal/2026%2009%2022%20PyWeek%2042%20Borrowed%20Time/engine/audio.py), and packaging pipeline automation in [`build.sh`](file:///Users/z3540725/My%20Drive/personal/2026%2009%2022%20PyWeek%2042%20Borrowed%20Time/build.sh).

* [2026-09-22 13:54 - 14:22 UTC+10:00] **Heuristic Playtesting Bot Development:** Developed an autonomous playtesting bot in [`playtest_bot.py`](file:///Users/z3540725/My%20Drive/personal/2026%2009%2022%20PyWeek%2042%20Borrowed%20Time/playtest_bot.py) that reads entity vectors and computes optimal steering decisions using greedy distance and hazard risk minimization. Ran automated headless playtest simulations to measure average survival duration and difficulty curves.

* [2026-09-22 15:06 - 16:03 UTC+10:00] **Difficulty Rebalancing & Visual Polish:** Rebalanced game mechanics based on playtest feedback to achieve an target median survival time of ~1 minute. Increased starting player health from 2 to 5 hearts, adjusted shard spawn velocity, added a dual-circle vignette shader to emulate optical glass in [`grain_of_doubt.html`](file:///Users/z3540725/My%20Drive/personal/2026%2009%2022%20PyWeek%2042%20Borrowed%20Time/grain_of_doubt.html), and fixed UI text alignment on the score and loading screens.

* [2026-09-22 17:06 - 17:19 UTC+10:00] **Developer Console Toggle & Documentation Refinement:** Implemented a developer mode toggled via backtick (`` ` ``) to expose bot steering diagnostics, invulnerability toggles, and live frame rates in [`main.py`](file:///Users/z3540725/My%20Drive/personal/2026%2009%2022%20PyWeek%2042%20Borrowed%20Time/main.py). Purged deprecated mechanic descriptions ("scar tissues") from [`README.md`](file:///Users/z3540725/My%20Drive/personal/2026%2009%2022%20PyWeek%2042%20Borrowed%20Time/README.md) to accurately represent current steering and gravity mechanics.

---

### 2026-09-23

* [2026-09-23 00:35 - 01:13 UTC+10:00] **Mobile Touch Controls & Automatic SemVer Packaging:** Refactored touch controls in [`grain_of_doubt.html`](file:///Users/z3540725/My%20Drive/personal/2026%2009%2022%20PyWeek%2042%20Borrowed%20Time/grain_of_doubt.html) to hide on-screen directional buttons on desktop while ensuring responsive touch targets on mobile devices. Automated semantic version increments (`+0.1.0`) during release builds and hid dev mode key shortcuts from the title screen unless actively triggered.

* [2026-09-23 01:56 - 03:55 UTC+10:00] **Viewport Scaling, Multi-Layer Vignette & Mechanical Verification:** Fixed mobile viewport clipping bugs ensuring the top HUD and hourglass neck are never cropped on high-DPI screens. Implemented proper exponential radii calculations for Envy's concentric fog of war in [`engine/bargains.py`](file:///Users/z3540725/My%20Drive/personal/2026%2009%2022%20PyWeek%2042%20Borrowed%20Time/engine/bargains.py), added an invulnerability toggle in dev mode, and verified game logic across automated test suites in [`tests/test_mechanics.py`](file:///Users/z3540725/My%20Drive/personal/2026%2009%2022%20PyWeek%2042%20Borrowed%20Time/tests/test_mechanics.py).

* [2026-09-23 09:12 - 09:19 UTC+10:00] **Early-Game Spawn Calibration:** Halved initial hazard density by reducing starting sand grains and razor shards in [`engine/entities.py`](file:///Users/z3540725/My%20Drive/personal/2026%2009%2022%20PyWeek%2042%20Borrowed%20Time/engine/entities.py), and adjusted the mathematical decay coefficient for Envy's concentric viewing apertures.

* [2026-09-23 10:25 - 11:23 UTC+10:00] **Inertial Momentum Physics & Score Typography:** Formatted score display to use space thousand separators without leading zeros. Refactored Lust and Envy bargains in [`engine/bargains.py`](file:///Users/z3540725/My%20Drive/personal/2026%2009%2022%20PyWeek%2042%20Borrowed%20Time/engine/bargains.py) to apply continuous force acceleration and momentum decay rather than sudden velocity cutoffs, and enlarged Kairos pact headers to maximize legibility.

* [2026-09-23 12:07 - 12:15 UTC+10:00] **Changelog Infrastructure Synchronization:** Created [`CHANGELOG.md`](file:///Users/z3540725/My%20Drive/personal/2026%2009%2022%20PyWeek%2042%20Borrowed%20Time/CHANGELOG.md) to document version history across all releases (v0.1.0 through v0.16.0), synced version notes to [`README.md`](file:///Users/z3540725/My%20Drive/personal/2026%2009%2022%20PyWeek%2042%20Borrowed%20Time/README.md), and tagged the repository.

* [2026-09-23 14:43 - 14:52 UTC+10:00] **Acceleration Damping for Sloth & Wrath:** Dampened instantaneous impulse acceleration on Sloth and Wrath bargains in [`engine/bargains.py`](file:///Users/z3540725/My%20Drive/personal/2026%2009%2022%20PyWeek%2042%20Borrowed%20Time/engine/bargains.py), distributing force across several frames to prevent disorienting control jolts.

* [2026-09-23 22:43 - 23:08 UTC+10:00] **Visual Decluttering & Minimalist UI Overhaul:** Stripped distracting particle animations, hourglass trailing lines, and scoring confetti to emphasize minimalist game design. Replaced scoring flash effects with subtle chromatic text highlights in [`main.py`](file:///Users/z3540725/My%20Drive/personal/2026%2009%2022%20PyWeek%2042%20Borrowed%20Time/main.py) and diagnosed background render crashes.

---

### 2026-09-24

* [2026-09-24 02:36 - 03:42 UTC+10:00] **Kairos Pact UI Framing & Dunes Visual Design:** Redesigned the Kairos pact selection interface to intentionally allow the Gluttony card to overhang and break the UI frame boundary. Prototyped procedural sand dune and broken glass background motifs in [`sand_dunes_landscape.py`](file:///Users/z3540725/My%20Drive/personal/2026%2009%2022%20PyWeek%2042%20Borrowed%20Time/sand_dunes_landscape.py) to reinforce the hourglass theme.

* [2026-09-24 08:27 - 08:30 UTC+10:00] **Gameplay Recording Pipeline Verification:** Verified Pyxel video recorder mechanics in [`main.py`](file:///Users/z3540725/My%20Drive/personal/2026%2009%2022%20PyWeek%2042%20Borrowed%20Time/main.py) to prevent accidental file overwrites by appending ISO timestamp suffixes to output GIF recordings.

* [2026-09-24 12:17 - 14:51 UTC+10:00] **Pro & Stealth High-Contrast Color Themes:** Engineered four high-contrast functional color themes (Pro Mode Light/Dark and Stealth Mode Light/Dark) in [`engine/themes.py`](file:///Users/z3540725/My%20Drive/personal/2026%2009%2022%20PyWeek%2042%20Borrowed%20Time/engine/themes.py) tailored for color-blind accessibility and clean competitive play. Implemented fixed Cartesian major and minor grid lines reminiscent of blueprint paper.

* [2026-09-24 12:24 - 12:46 UTC+07:00] **Architectural Health Check & Kairos Input Delay:** Conducted a comprehensive codebase health diagnostic and verified engine modularity. Balanced pacing by setting both Chronos and Kairos phases to 10 seconds, added a 1-second input cooldown when entering Kairos to prevent accidental instant selections, and tuned bot reaction speed.

* [2026-09-24 13:12 - 14:29 UTC+07:00] **Blueprint Grid Pinning & KJV Reader Mode:** Anchored major and minor grid lines to absolute world coordinates in Pro Mode so background grids remain static. Rewrote game lore and narrative flavor text in [`p04.md`](file:///Users/z3540725/My%20Drive/personal/2026%2009%2022%20PyWeek%2042%20Borrowed%20Time/p04.md) into authentic King James Bible style prose. Packaged and tagged official release `v1.0.0`.

* [2026-09-24 22:36 - 2026-09-25 00:10 UTC+07:00] **Audio Synthesis & v1.1.0 Roadmap Execution:** Executed milestone items from [`2do.md`](file:///Users/z3540725/My%20Drive/personal/2026%2009%2022%20PyWeek%2042%20Borrowed%20Time/2do.md). Synthesized custom sound effects for sand collection, pact sealing, and hazard damage in [`engine/audio.py`](file:///Users/z3540725/My%20Drive/personal/2026%2009%2022%20PyWeek%2042%20Borrowed%20Time/engine/audio.py), resolved web audio initialization bugs, and released version `v1.1.0`.

---

### 2026-09-25

* [2026-09-25 10:57 - 11:00 UTC+07:00] **GitHub Pages Cache Invalidation:** Investigated web asset caching issues where GitHub Pages served stale `v1.1.1` assets. Added cache-busting timestamp query parameters to HTML scripts in [`index.html`](file:///Users/z3540725/My%20Drive/personal/2026%2009%2022%20PyWeek%2042%20Borrowed%20Time/index.html) and triggered a clean Pages deployment.

* [2026-09-25 11:43 - 12:00 UTC+07:00] **v1.1.2 Web Asset Packaging:** Executed build optimization passes via [`build.sh`](file:///Users/z3540725/My%20Drive/personal/2026%2009%2022%20PyWeek%2042%20Borrowed%20Time/build.sh), creating optimized standalone bundles for both offline distribution (`grain-of-doubt-1.1.2.zip`) and browser deployment.

* [2026-09-25 12:46 - 13:11 UTC+07:00] **v1.1.3 Autonomous Build & Verification:** Processed queued backlog items in [`2do.md`](file:///Users/z3540725/My%20Drive/personal/2026%2009%2022%20PyWeek%2042%20Borrowed%20Time/2do.md), executing automated unit and gameplay test suites across mechanics and UI states before publishing `v1.1.3`.

* [2026-09-25 13:45 - 13:50 UTC+07:00] **Keybinding Legend & Controls UI Standardisation:** Standardised keyboard navigation legends across all menu screens, grouping `[A] / [D]` alongside arrow keys, removing obsolete controller references, and scaling control typography for improved legibility.

* [2026-09-25 14:20 - 15:00 UTC+07:00] **Custom Bitmap Font & Typography Overhaul:** Replaced standard 3x5 font with custom 5x7 bitmap typography in [`engine/font5x7.py`](file:///Users/z3540725/My%20Drive/personal/2026%2009%2022%20PyWeek%2042%20Borrowed%20Time/engine/font5x7.py) to resolve glyph overlap and improve legibility across titles, scores, and pact descriptions in `v1.1.5`.

* [2026-09-25 16:30 - 17:05 UTC+07:00] **Pact Screen Polish & v1.1.6 Release:** Refined card layout geometry on the Kairos bargain screen to accommodate longer narrative text without clipping. Packaged release `v1.1.6` and verified automated deployment pipelines.

* [2026-09-25 17:31 - 18:13 UTC+07:00] **Web Assembly Build Pipeline & v1.1.8 Release:** Resolved Pyxel WebAssembly packaging bottlenecks, optimized canvas dimensions for high-DPI retina mobile screens, and synchronized updates across [`README.md`](file:///Users/z3540725/My%20Drive/personal/2026%2009%2022%20PyWeek%2042%20Borrowed%20Time/README.md) and [`CHANGELOG.md`](file:///Users/z3540725/My%20Drive/personal/2026%2009%2022%20PyWeek%2042%20Borrowed%20Time/CHANGELOG.md) for `v1.1.8`.

* [2026-09-25 19:03 - 19:22 UTC+07:00] **v1.1.9 Bug Fixes & Touch Collision Tuning:** Calibrated touch hitboxes on mobile browsers to prevent missed clicks during frantic pact selections, releasing patch `v1.1.9`.

* [2026-09-25 19:47 - 19:51 UTC+07:00] **Milestone Tagging v1.2.0:** Tagged official milestone `v1.2.0`, generating release archives and uploading standalone Pyxel web artifacts.

* [2026-09-25 20:40 - 21:20 UTC+07:00] **Sumi-e Monochrome Palette Purification:** Eliminated lingering blue color artifacts from the Japanese ink wash (*Sumi-e*) theme in [`engine/themes.py`](file:///Users/z3540725/My%20Drive/personal/2026%2009%2022%20PyWeek%2042%20Borrowed%20Time/engine/themes.py), ensuring a 100% pure grayscale aesthetic across all particle effects and HUD elements for `v1.2.2`.

---

### 2026-09-26

* [2026-09-26 10:06 - 10:13 UTC+07:00] **Wrath Visual Feedback Ideation:** Brainstormed visual indicator alternatives to screen-shake for the Wrath bargain (controls reversed), concluding on triple horizontal motion streak lines indicating forced directional inversion.

* [2026-09-26 10:44 - 11:19 UTC+07:00] **Inverted Control Motion Streaks Implementation:** Implemented dynamic motion streak lines rendered adjacent to player particles whenever Wrath reverses directional controls, packaging and deploying `v1.2.3`.

* [2026-09-26 13:05 - 13:17 UTC+07:00] **Automated Regression Testing & v1.2.4 Release:** Updated test runners in [`tests/test_mechanics.py`](file:///Users/z3540725/My%20Drive/personal/2026%2009%2022%20PyWeek%2042%20Borrowed%20Time/tests/test_mechanics.py) to assert motion streak frame counters and control reversal invariants, publishing `v1.2.4`.

---

### 2026-09-28

* [2026-09-28 23:55 - 2026-09-29 00:05 UTC+08:00] **PyWeek 42 Final Polish & v1.2.5 Packaging:** Conducted pre-submission checklist verification in [`2do.md`](file:///Users/z3540725/My%20Drive/personal/2026%2009%2022%20PyWeek%2042%20Borrowed%20Time/2do.md), verified standalone `.pyxapp` execution and web builds, and packaged release `v1.2.5` as the final PyWeek 42 competition submission.

---

### 2026-10-07

* [2026-10-07 22:02 - 22:28 UTC+08:00] **Post-Competition Polish, Scientific Notation & E-Reader Uniformity (v1.2.6 - v1.2.8):** Executed a post-competition polish cycle driven by [`2do.md`](file:///Users/z3540725/My%20Drive/personal/2026%2009%2022%20PyWeek%2042%20Borrowed%20Time/2do.md) across three successive releases:
  * **v1.2.6:** Rebuilt standalone and WebAssembly packages via [`build.sh`](file:///Users/z3540725/My%20Drive/personal/2026%2009%2022%20PyWeek%2042%20Borrowed%20Time/build.sh), triggered GitHub Pages build API deployments, and verified live caching.
  * **v1.2.7:** Updated death screen score formatting in [`main.py`](file:///Users/z3540725/My%20Drive/personal/2026%2009%2022%20PyWeek%2042%20Borrowed%20Time/main.py) to render scores $\ge 1\,000\,000$ in scientific notation (`1.00e+06`), and adjusted the E-Reader death screen header title from "ECCLESIASTES 12" to "Conclusion".
  * **v1.2.8:** Unified all text, divider rules, subtitle, and closing meditation prose on the E-Reader Game Over screen to a consistent ink palette (`col_ink`), wrote automated regression tests in [`tests/test_mechanics.py`](file:///Users/z3540725/My%20Drive/personal/2026%2009%2022%20PyWeek%2042%20Borrowed%20Time/tests/test_mechanics.py), and tagged/deployed release `v1.2.8`.
