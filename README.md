# Grain of Doubt

> **By Arian Prabowo**  
> **Version:** v1.1.2  
> **PyWeek 42 Entry ("Borrowed Time")** — September 2026  
> An endless retro downhill falling-hourglass arcade runner built with the **Pyxel** retro game engine.  
> **Target Resolution:** 600 × 800 pixels (3:4 Portrait Aspect Ratio, Infinite Horizontal Arena).  
> **Game Design Document:** [p04.md](file:///Users/z3540725/My%20Drive/personal/2026%2009%2022%20PyWeek%2042%20Borrowed%20Time/p04.md)

**PLAY! https://aprbw.github.io/pyweek42/index.html**

[![Pyxel](https://img.shields.io/badge/Engine-Pyxel%202.9.9-blue)](https://github.com/kitao/pyxel)
[![Python](https://img.shields.io/badge/Python-3.12-brightgreen)](https://www.python.org/)
[![Status](https://img.shields.io/badge/Tests-Passing-success)](#automated-validation-gates)

---

## ⏳ Narrative & Gameplay Premise

You control a fragile hourglass falling through the neck of an infinite, crumbling cosmic hourglass (**"Hourglass-ception"**).
Steer left or right to avoid falling glass shards while collecting glistening golden grains of sand.

### Chronos vs. Kairos (The Dual-Clock Engine)
* **Chronos (10.0s descent):** Relentless kinetic tension. Steer left or right across an infinitely wide horizontal arena (±4.5 screen procedural generation horizon) to dodge oncoming glass shards while reaping cascading sand motes.
* **Kairos (10.0s circuit breaker):** Every 10.0 seconds, normal time freezes. You are presented with **2 Faustian Bargain cards** drawn from the Seven Deadly Sins. You have 10.0 seconds to choose (with an initial 1.0s safety lockout)—if you hesitate, doubt shatters your vessel (*Paralyzed by Doubt: Kairos Expired*). A vertical side timer drains from top to bottom.
  * **Input Re-press Protection:** Entering Kairos requires unpressing/releasing lateral steering first before choosing, preventing accidental card selection if holding arrows during Chronos.
* **Faustian Bargains:** Every bargain grants an immediate survival boon at the cost of a permanent curse. Repeatedly choosing sins compounds their effects.

### Dynamic Glass Shards: Scalene Geometry & Continuous Angular Spin
* Glass shards are rendered as dynamically generated, randomized non-right-angled (acute/scalene) triangles rather than uniform right triangles.
* Each shard spins continuously with an individual randomized angular velocity (`spin_speed` ∈ [-0.18, -0.04] ∪ [0.04, 0.18] rad/frame), creating realistic tumbling debris during Chronos descent.

### Deep World Simulation & Hazard Catch-up (10 Seconds Down)
* To support downward push mechanics (such as **Sloth's Lazy Reprieve** downward throw and **Wrath's Explosion** blast), the active entity simulation domain extends several screens downward ($y \le 6000.0$ pixels, approximately 10–12 seconds of scroll time).
* Entities blasted or hurled far downward are not prematurely culled; they remain fully simulated with second-order Newtonian physics, deceleration, and viscous damping. As time marches forward, these pushed hazards inevitably scroll back upward into player territory—ensuring that every survival choice carries lasting gameplay consequences.

---

## 🎨 10 Curated Divergent Aesthetic Themes (Available to All Players)

You can freely switch between **10 completely unique, maximally divergent aesthetic themes** in real time—both directly on the **Title Screen (Home Page)** and during gameplay—using the number keys `0` through `9`, or `,` (previous) and `.` (next):

0. **Dunes in the Cosmic Hourglass**: Continuous 2D procedural sand dune landscape with a **Topology Engine** (layered polygons rendered back-to-front; negative space geometry prohibiting stroke lines; inverse Z-depth upward velocity converging at supra-canvas horizon $Y_H = -140$; speed $>10\times$ faster at bottom than top), **Shadow Mapping** (intra-layer vertical linear gradients from dark crests to light bases), **Atmospheric Scattering** (global luminosity scalar desaturating distal ridges into ambient desert haze), and a cosmic perspective glitch warning when Kairos is imminent.
1. **Pro Mode Light**: Clinical white engineering canvas, relative background grid motion (1.6x scroll speed so hazards fall down relative to grid), dual vertical Chronos countdown progress bars at extreme left and right borders (top to bottom), pitch-black obsidian shards, amber sand, and extreme luminance delta (>20:1 contrast). Zero drop shadows.
2. **Pro Mode Dark**: Pure pitch-black canvas, relative background grid motion (1.6x scroll speed so hazards fall down relative to grid), dual vertical Chronos countdown progress bars at extreme left and right borders (top to bottom), solid opaque HUD panels, and vibrant Cyan (`Color 12`) unselected pact list (WCAG AAA). Zero drop shadows.
3. **E-Reader Light**: Warm cream parchment digital e-reader displaying genuine **Ecclesiastes 3:1-22 (King James Version)** in double-sized font (`scale=2`, $8 \times 12$ px characters) formatted as continuous, justified un-indented prose. Floating arcade HUD panels are 100% suppressed; gameplay telemetry is seamlessly disguised as an authentic scripture paragraph between verses 8 and 9 without modern brackets or parentheses. Shards render at **30% alpha** and sand/hourglass at **60% alpha** as subtle translucent watermarks.
4. **E-Reader Dark**: Midnight slate companion to E-Reader Light. Double-sized Ecclesiastes 3 KJV text, disguised KJV scripture telemetry paragraph, 100% suppressed floating HUD, and 30%/60% alpha translucent gameplay elements.
5. **Glacial Crevasse**: Deep sub-zero glacial chasm with sheer vertical meltwater streams, horizontal firn ice strata, and shimmering crystalline frost motes.
6. **Magma Caldera**: Volcanic caldera, basalt crags, obsidian riverbed, and bubbling liquid lava flumes with glowing embers.
7. **Retro Terminal Matrix**: Phosphor green cathode-ray tube monitor with falling hexadecimal digital glyph rain and scanline texture.
8. **Zen Ink Wash (Sumi-e)**: Traditional Japanese washi parchment, black ink calligraphy brush strokes, and red cinnabar seal.
9. **Pastel Sakura**: Cute, girly pastel pink aesthetic with cherry blossom petals drifting with organic sinusoidal sway, soft peach clouds, and twinkling fairy stars.

Each theme dynamically transforms the procedural background terrain as well as the complete color palettes of the player's hourglass, sand grains, and glass shards to ensure aesthetic harmony and sharp contrast!

---

## 🎮 Controls

| Control | Action | Mechanic |
| :--- | :--- | :--- |
| `A` / `D` or `Left` / `Right` | Lateral Steering | Steer hourglass horizontally (viscous damping coefficient: 0.82) |
| Touch `< LEFT` / `RIGHT >` | Mobile Touch Steering | High-contrast on-screen buttons (visible on mobile only) or bottom screen tap |
| `Left` / `Right` or Tap Card | Select Faustian Bargain | Steer left or right during Kairos to choose between the 2 bargain cards within 10.0s (1.0s safety lockout; requires fresh press after release) |
| `L` / `H` | Lore & Learn to Play Codex | Open 3-page interactive codex (Narrative, Dual-Clock Engine, Seven Covenants). Navigate with `A`/`D` or arrows; press `Right` on last page or `X` to return |
| `Space` / `Enter` or Tap Screen | Start / Restart | Start game or restart after a 2.0s post-mortem lockout (debounced) |
| `X` | Return to Menu / Quit | In gameplay or Lore screen: return to Title Menu. On Title Menu: quit game (no-op in browser) |
| `0` - `9` | Direct Theme Select | Jump instantly to any of the 10 curated themes (0:Dunes, 1:Pro Light, 2:Pro Dark, 3:E-Reader Light, 4:E-Reader Dark, 5:Glacial, 6:Caldera, 7:Terminal, 8:Sumi-e, 9:Pastel Sakura) |
| `,` (Comma) | Previous Theme | Cycle backwards through all 10 curated themes (works on Title Screen and in-game) |
| `.` (Period) | Next Theme | Cycle forward through all 10 curated themes (works on Title Screen and in-game) |
| `~` / `` ` `` (Backtick) | Toggle Dev Mode | On-screen debug HUD, live telemetry, and shortcut cheats |
| `I` (in Dev Mode) | Toggle God Mode | Invulnerability toggle (immune to glass shards and void collision) |
| `B` (in Dev Mode) | Toggle GOFAI Bot | Autonomous kinematic AI playtesting agent (human-like 2.0s deliberation delay, 80% speed handicap) |
| `V` (in Dev Mode) | Toggle MP4 Recording | Lossless FFmpeg background canvas video recorder |
| `1` - `7` (in Dev Mode) | Add Faustian Pact | Instant-apply sin pact level (1:Pride, 2:Greed, 3:Lust, 4:Envy, 5:Gluttony, 6:Wrath, 7:Sloth) |
| `Q`, `W`, `E`, `R`, `T`, `Y`, `U` (in Dev Mode) | Reduce Faustian Pact | Decrement corresponding sin pact level (Q:Pride, W:Greed, E:Lust, R:Envy, T:Gluttony, Y:Wrath, U:Sloth) |

---

## 📜 Seven Deadly Faustian Bargains

Every 10.0 seconds (300 frames), normal time flow stops and **Kairos** strikes. The player is presented with **two randomly chosen Faustian Bargains** in Catholic Gregorian canonical order. You have exactly 10.0 seconds (300 frames) to choose one (with an initial 1.0s safety lockout), or your hourglass shatters instantly.

*Exact mathematical values (where k ≥ 0 is the repeat pact count):*

1. **Pride:**
   * *Boon:* Spawns golden sand in organic randomized clusters: +1 grain per pact level (1st pact: pairs = 2 grains; 2nd: triplets = 3; 3rd: quadruplets = 4; grains share trajectory with randomized non-overlapping offsets; 1 sand = 1 point).
   * *Curse:* Increases descent velocity multiplier by flat +25% per pact level (+0.25).
2. **Greed:**
   * Triggers **Borrowed Time**
   * *Boon:* During Borrowed Time, each sand multiplies the current score by 110% (Score = max(Score + 1, floor(Score × 1.10))) instead of adding 1 point.
   * *Curse:* Triggers **Borrowed Time** for a randomized window of **10.0 to 18.0 seconds** (300 to 540 frames). At the end, you definitely die (*Borrowed Time Expired: Debt Collected*). Warning HUD shows `BORROWED TIME`, and Dev Mode displays the countdown timer.
3. **Lust:**
   * *Boon:* Sand magnetic attraction permanently pulls golden sands within radius toward hourglass (100.0px on 1st pact, +50.0px on subsequent pacts).
   * *Curse:* Hazard magnetic attraction permanently pulls glass shards within radius toward hourglass (100.0px on 1st pact, +50.0px on subsequent pacts).
4. **Envy:**
   * *Boon:* Activates **Tidal Pull** for 2.0 seconds (60 frames), very strongly attracting all golden sand grains within 2× the current vignette pixel radius (1228px on Pact 1) toward the hourglass with full Newtonian momentum.
   * *Curse:* Inflicts **Vignette Vision**, a multi-circle concentric mask with 5 graduated dither transparency tiers between an inner clear core and outer void boundary. Envy 1 starts at former Envy 3 ($k_{\text{eff}} = k + 2$):
     * **Outermost circle** (zero vision beyond): radius = 1200 × 0.8^(k+2) px (Pact 1: 614.4px, Pact 2: 491.5px, Pact 3: 393.2px, Pact 4: 314.6px, Pact 5: 251.7px).
     * **Innermost circle** (full clear vision): radius = 1000 × 0.8^(k+3) px (Pact 1: 409.6px, Pact 2: 327.7px, Pact 3: 262.1px, Pact 4: 209.7px, Pact 5: 167.8px).
5. **Gluttony:**
   * At Gluttony level $N$, normal entity chance is $0.9^N$ and fat entity chance is $1.0 - 0.9^N$ (Level 0: 0% fat, 100% normal).
   * *Boon:* **Fat Sand Grains** — $\sim 3\times$ larger radius/length-wise ($10\times$ area), awarding $3\times$ score ($3$ points per grain).
   * *Curse:* **Fat Glass Shards** — $\sim 2.8\times$ linear dimensions ($10\times$ area), creating massive, menacing hazard obstacles.
6. **Wrath:**
   * *Boon:* **Wrath Blast** — Detonates an instant kinetic explosion centered on the player: all entities (both golden sand grains and glass shards) within a **1200-pixel radius** are blasted outward with a smooth multi-frame acceleration impulse away from the hourglass. Zero visual particle clutter.
   * *Curse:* Zero yield: all sand grains collected yield 0 points for 10.0 seconds (300 frames).
7. **Sloth:**
   * *Boon:* **Lazy Reprieve** — Sloth means lazy; lazy means doing nothing! All glass shards below the player within 3 screens wide are hurled downward toward the bottom horizon over a multi-frame burst. For ~2.0 to 2.5 seconds, the descent space below you is completely cleared of hazards, allowing you to literally do nothing and survive.
   * *Curse:* The hurled glass shards catch up and overlap with bottom-seeded hazards, forming a doubly dangerous wave of glass at the bottom horizon that scrolls back upward. Additionally, imposes permanent compounding lateral drag on hourglass steering, reducing horizontal translation speed by -20% × 1.5^k (0.20 reduction on 1st pact, 0.30 on 2nd, 0.45 on 3rd; minimum modifier 0.20).

---

## 🏗️ Architecture & Project Structure

```
.
├── main.py                     # Entry point, Pyxel canvas loop, vignette mask, HUD, dev overlay
├── engine/
│   ├── __init__.py
│   ├── state.py                # GameState enum, StateManager, Chronos/Kairos timers
│   ├── entities.py             # HourglassPlayer, SandGrain, GlassShard, EntityManager
│   ├── bargains.py             # Faustian Bargain registry, compounding decay mathematics
│   ├── themes.py               # 20 Divergent Aesthetic Themes, procedural backgrounds & palettes
│   ├── bot.py                  # GOFAI kinematic playtesting agent (trajectory projection)
│   ├── video.py                # Real-time FFmpeg MP4 recording engine
│   └── audio.py                # 4-channel procedural retro synth sound matrix
├── tests/
│   ├── __init__.py
│   ├── test_bot.py             # Playtest bot & kinematic simulation validation
│   └── test_mechanics.py       # Automated unit test suite covering validation gates
├── playtest_bot.py             # Headless benchmark evaluation suite
├── grain_of_doubt.pyxapp       # Standalone binary package
├── grain_of_doubt.html         # Emscripten / WebAssembly distribution bundle
├── index.html                  # GitHub Pages web entrypoint
├── run.sh                      # Local game launcher
└── build.sh                    # Automated test & packaging pipeline
```

---

## 🚀 Quick Start & Execution

### 1. Run with PyWeek Standard Runner
```bash
python run_game.py
```

### 2. Run with Launcher
```bash
./run.sh
```

### 3. Manual Run
```bash
# Setup environment
uv venv --python 3.12 .venv
source .venv/bin/activate
uv pip install -r requirements.txt

# Run with Pyxel directly
python -m pyxel run main.py

# Run with Autonomous Bot
python main.py --bot
```

### 3. Run Automated Validation Gates
```bash
.venv/bin/pytest tests/ -v
```

### 4. Run Bot Headless Benchmark
```bash
python playtest_bot.py
```

### 5. Build Packaging Pipeline
```bash
./build.sh
```

### 6. WebAssembly Browser Play
Open `index.html` via any local HTTP server:
```bash
python3 -m http.server 8000
# Open http://127.0.0.1:8000 in your browser
```

### 7. Mobile Browser Play & Anti-Zoom Architecture
* **Direct Touch Arcade Controls**: On touch-enabled devices and mobile screens, intuitive semi-transparent `< LEFT` and `RIGHT >` directional pads render along the lower display. Tapping the left or right halves of the screen also provides direct responsive steering.
* **Pixel-Perfect 3:4 Containment**: Responsive CSS layout preserves the 3:4 portrait aspect ratio without distortion across all phone screens, tablets, and desktop displays.
* **Strict Browser Zoom Prevention**:
  * Viewport declaration: `<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">`.
  * Touch restrictions: `touch-action: none !important`, `overscroll-behavior: none !important`, `-webkit-touch-callout: none !important`, `-webkit-user-select: none !important`.
  * Multi-touch pinch prevention: Intercepts and cancels multi-finger `touchstart` and `touchmove` events (`e.touches.length > 1`).
  * Safari gesture prevention: Intercepts and suppresses `gesturestart`, `gesturechange`, and `gestureend` events.
  * Fast double-tap zoom debounce: Intercepts double taps occurring within 300ms (`touchend`) to prevent mobile Safari/Chrome double-tap zooming.
  * Desktop trackpad/wheel prevention: Cancels `ctrlKey` trackpad pinch-to-zoom wheel events and double clicks (`dblclick`).

---

## 📝 Changelog

> Complete version history for every release from **v0.1.0** through **v1.0.0** is detailed below and in [CHANGELOG.md](CHANGELOG.md).

### v1.0.0 (September 2026)
* **10 Curated Maximally Divergent Themes (`0..9`):**
  * Streamlined roster to 10 ultra-distinct themes mapped to number keys `0` through `9`: Desert Dunes (0), Pro Mode Light (1), Pro Mode Dark (2), Reader Mode Light (3), Reader Mode Dark (4), Monochrome Blueprint (5), Magma Caldera (6), Retro Terminal Matrix (7), Zen Ink Wash (8), and Liminal Vaporwave (9).
* **Reader Mode Ecclesiastes 3 KJV Scripture Telemetry:**
  * Authentic 17th-century King James Bible style phrasing without modern annotations, brackets, or parentheses (*"and three faustian covenants have been made, to wit, two of Pride, and one of Sloth."*).
  * Seamlessly positioned as the second paragraph between Ecclesiastes 3:1-8 and 3:9-13.
  * Balanced gameplay visibility: glass shards rendered at 30% alpha (`pyxel.dither(0.30)`), sand grains and player hourglass at 60% alpha (`pyxel.dither(0.60)`).
* **Dual-Clock 10.0s Cycles & 1.0s Input Safety Lockout:**
  * Chronos descent duration set to 10.0 seconds; Kairos dilemma pause set to 10.0 seconds.
  * Added 1.0-second input lockout upon entering Kairos time to eliminate misclicks from active steering.
  * Bot playtester evaluates pacts with a realistic 2.0-second deliberation delay.
* **Pro Mode Blueprint Grid & Visual Consistency:**
  * Static major and minor blueprint drafting grid remaining fixed in world space.
  * Theme-harmonized Kairos modal styling dynamically matching active theme palettes.
  * Dune Horizon Kairos imminent warning glitch destroying perspective depth with flashing dunes.

### v0.19.0 (September 2026)
* **Continuous 2D Procedural Sand Dunes Landscape (`sand_dunes_landscape.py` & Theme 0):**
  * **Topology Engine**: Layered procedural wave polygons rendered back-to-front. Prohibits explicit stroke outlines—defining dune boundaries entirely through the negative space between sequential procedural waveforms.
  * **Perspective Inverse Z-Depth Velocity**: Projects simulated depth to 2D screen coordinates converging toward a supra-canvas horizon point ($Y_H = -140$). Translation velocity and wave amplitude are modulated inversely against Z-depth ($\frac{dY}{dt} \propto (Y - Y_H)^2$). Proximal dunes at the bottom rush upwards at $>10\times$ the velocity of distal dunes near the top, which experience asymptotic stalling near the horizon.
  * **Intra-Layer Shadow Mapping**: Binds localized vertical linear color gradients within wave geometry—rendering darker crest coordinates transitioning into luminous dune bases to simulate realistic directional self-shadowing.
  * **Atmospheric Scattering**: Overrides localized gradients with a global luminosity scalar linked to Z-depth, desaturating and optically bleaching distant ridges into the ambient desert haze threshold.
  * **Standalone Executable Script**: Run `python sand_dunes_landscape.py` independently with interactive controls (`A`/`D` pan, `W`/`S` scroll speed, `U`/`J` horizon altitude, `P` haze toggle, `C` screenshot).
* **Reader Mode (E-Reader Dark & Light, Themes 13 & 14):**
  * Replaces legacy stealth specifications with an authentic e-reader reading experience.
  * **Scripture Text**: Inscribes the complete, authentic text of **Ecclesiastes 3:1-22 (King James Version)** ("To every thing there is a season, and a time to every purpose under the heaven...").
  * **Double-Sized E-Reader Typography**: Double-scaled font (`scale=2`, $8 \times 12$ px characters) formatted as continuous, un-indented prose, delivering comfortable book readability.
  * **100% Floating HUD Suppression**: Removes all floating arcade UI containers (hearts, score, chronos timer bar, and pact list).
  * **Disguised Line 2 Telemetry**: Formats vital game state seamlessly into the second line of the prose (`Hearts: X/5 | Score: Y | Time: Z.Zs | Pacts: None / List`).
  * **30% Alpha Translucent Gameplay Elements**: Applies `pyxel.dither(0.30)` to the player hourglass, falling triangle glass shards, and cascading sand grains, transforming fast-paced arcade action into subtle watermarks beneath the prose.
* **Pro Mode High-Contrast Functional Redesign (Themes 6 & 7):**
  * Clinical, zero-noise engineering drafting grid with static major (100px) and minor (25px) grid lines fixed to the screen background.
  * Pinned dual vertical Chronos countdown progress bars at extreme left and right margins ($x \in [0, 6]$ and $x \in [594, 600]$), tracking remaining time downwards from top to bottom with urgency pulsing.
  * Color-matched pact cards with uncluttered level advancement indicators.
* **Universal Theme Switching & Home Page Integration**:
  * Theme switching using `,` (previous) and `.` (next) is available to all players anytime, completely decoupled from Dev Mode.
  * Home Page (Title Screen) features high-contrast plaques for 100% legibility across all themes and highlights the 20 divergent themes.
* **Eliminated UI Checkerboard Noise**:
  * Replaced dithered transparency on all UI panels and modals with clean solid opaque backgrounds and high-contrast borders for 100% text readability.
* **Mobile Browser Hardening & Zoom Prevention**:
  * Multi-layer defense against unwanted mobile zooming (pinch-to-zoom, Safari gesturestart, double-tap zoom debounce, and CSS touch-action rules).


### v0.18.0 (September 2026)
* **Complete Visual Decluttering (Zero Particles):**
  * Removed all noisy particle popups (sand sparks, explosion debris, hourglass trail drips). Players enjoy crystal-clear visibility of all incoming grains and shards.
  * Internal scoring feedback: collecting sand grains now causes the hourglass bulbs and waist neck to flash in radiant gold/amber glints directly on the player sprite.
* **Braided Sandfall / Landslide Terrain (Fluid Sand River):**
  * Transformed the canvas into a fluid, rushing golden sand river combining braided sandbars, cascading chutes, velocity shearing flumes, and churning granular froth.
  * *Cascading Flumes & Streamlines*: Striated vertical flow lines streaming through channels with distinct speed multipliers (1.18x to 1.50x), creating genuine fluid velocity shearing and the visceral sensation of an active landslide pouring downhill.
  * *Braided Sandbar Banks & Weaving Channels*: Sinuous, undulating sandbar ridges with sunlit white rims (`7`) and amber slope shadows (`9`/`4`), breached by deep channel chutes where sand rushes through.
  * *Granular Froth & Shoal Pebbles*: Procedural spray motes (`10`/`7`) dancing at chute breaches, miniature sand ripple arcs, and sandstone pebbles on calm shoals.
  * *Greed Blood-River Mode*: When Greed triggers ("Borrowed Time"), the golden river transforms into a subterranean torrent of blood and magma (`2`/`4` base, `8` crimson flumes, `14` pink foam).
* **High-Contrast Entity & Shadow Rendering:**
  * *Sand Grains*: Cast warm drop shadows on the sand and feature rich amber-brown outlines (`4`) around sparkling golden bodies (`10`/`9`) and white facet glints (`7`).
  * *Glass Shards*: Cast distinct drop shadows on the slope (`4`) and have razor-sharp black perimeter outlines (`0`) around translucent icy cyan facets (`6`) with specular glints (`7`).
  * *Player Hourglass*: Casts an oval drop shadow onto the sand slope beneath it, physically anchoring the player to the desert.
* **Gluttony Bent Frame UI:**
  * In the Kairos circuit breaker modal, the card frame borders now visibly bend and bulge outward by 22 pixels around the oversized `GLUTTONY` title, making its massive width look completely intentional, humorous, and thematic.
* **Hourglass Player Silky Gliding Physics:**
  * Rebalanced air friction damping from aggressive `0.85` down to a gentle `0.94` (`air_friction = 0.06`, `base_accel = 2.4`), allowing the player hourglass to glide smoothly and preserve momentum naturally when controls are released.
* **Obtuse Glass Shards & Aerodynamic Tumbling:**
  * Glass shards now procedurally generate as obtuse triangles (one angle $> 90^\circ$, verified by negative dot product $< -8.0$) as well as acute/scalene triangles (never right-angled).
  * Shard spin rate is aerodynamically coupled to horizontal airspeed $V_x$, naturally simulating aerodynamic torque during horizontal drift.
* **Gluttony Fat Entities Rework:**
  * At Gluttony level $N$: Fat entity probability is $1.0 - 0.9^N$ (Level 0: 100% normal).
  * Fat Sand Grains: $\sim 3\times$ larger radius/length-wise ($10\times$ area), awarding $3\times$ points ($3$ points per grain).
  * Fat Glass Shards: $\sim 2.8\times$ linear dimensions ($10\times$ area), creating massive, menacing hazard obstacles.
* **Sloth Bottom Wave Hazard Overlap (Double Danger):**
  * When Sloth hurls shards downward, oncoming hazards are seeded at the bottom horizon ($y \in [1050, 1450]$ px), causing hurled shards to catch up and overlap into a doubly dangerous wall of glass.
* **Envy Recalibration (Envy 1 = Envy 3):**
  * Recalibrated Envy starting point to former Envy 3 ($k_{\text{eff}} = k + 2$): Level 1 outer radius $= 614.4$ px, inner radius $= 409.6$ px.
* **UI & HUD Polish:**
  * Time display formatted with space before units (`TIME: 24.5 s`).
  * Top-right HUD box widened to 180px with full title `FAUSTIAN PACTS`.

### v0.17.0 (September 2026)
* **Multi-Frame Burst Acceleration Curve:**
  * Replaced discrete impulse spikes in Sloth and Wrath with smooth, multi-frame acceleration curves distributed across 10–12 frames.
* **Pride Spatial Hazard Density Preservation:**
  * Scaled wave spawn accumulation directly with `speed_multiplier`. When descent speed is increased by Pride, entity spawn rates scale proportionally so spatial hazard density remains constant.

### v0.16.0 (September 2026)
* **Wrath Rework — Radial Kinetic Explosion:**
  * Replaced screen wipe with an instant, powerful radial shockwave explosion.
  * All entities (both sand grains and glass shards) within a **1200-pixel radius** are blasted outward away from the player with a massive acceleration impulse (`impulse = 46.0 px/frame`).
  * Triggers dramatic screen shake (12px intensity for 20 frames) and dual-ring particle burst shockwaves.
  * Zero-yield curse (10.0s / 300 frames) remains in effect.
* **Lust Rebalance (100px Base + 50px Scaling):**
  * Rebalanced Lust magnetic attraction to prevent early-game overload: base attraction radius reduced from 180px to **100px**, scaling by **+50px** per subsequent pact ($r = 100.0 + k \times 50.0$ px) for both sand and glass shards.
* **Deep World Simulation (10 Seconds Down / Consequence Catch-up):**
  * Expanded entity simulation and despawn boundary down to $y = 6000.0$ pixels (~10–12 seconds of downward descent).
  * Prevents downward-hurled hazards (Sloth Lazy Reprieve and Wrath explosions) from being culled offscreen, ensuring their consequences persist and catch up to the player.
  * Raised terminal velocity clamp to 50.0 px/frame to preserve explosive blast momentum.
* **Dynamic Glass Shard Rotation & Randomized Triangle Geometry:**
  * Replaced uniform right-angled triangles with individually randomized non-right-angled (acute/scalene) triangles verified by vector dot products.
  * Each glass shard now tumbles continuously with an organic, randomized angular velocity.
* **Terminology Standardization:**
  * Enforced strict naming consistency across the entire codebase and documentation: all hazard entities are consistently named **glass shards** (zero occurrences of "razor").

### v0.15.0 (September 2026)
* **Sloth Rework — Lazy Reprieve (Lazy = Doing Nothing):**
  * Reworked Sloth into the "Lazy Reprieve": Sloth means lazy; lazy means doing nothing!
  * In a single high-acceleration impulse frame, all shards below the player within 3 screens wide are hurled downward toward the bottom horizon (`vy >= 38.0`, pushed to `y >= y_player + 520.0`).
  * Creates a 2.0 to 2.5 second safe void directly below the player where they can literally do nothing and survive without touching controls.
  * Trade-off: all thrown shards clump together into a dense, dangerous wave near the bottom horizon that later scrolls back upward.
  * Permanent lateral drag curse remains active (-20% × 1.5^k).
* **Envy Terminology Alignment:**
  * Standardized on **Tidal Pull** across the game HUD, Kairos cards, engine summaries, and documentation.
* **Markdown & LaTeX Typography Polish:**
  * Cleaned up all mathematical delimiters and percent escapes across the documentation to ensure seamless rendering on GitHub Flavored Markdown and KaTeX parsers without syntax errors.

### v0.14.0 (September 2026)
* **Kinematic Momentum & Acceleration Physics for Lust & Envy:**
  * Replaced discrete positional translation with proper second-order Newtonian physics (`acceleration` → `velocity` → `position`).
  * Grains and glass shards accumulate velocity (`vx`, `vy`) under Lust magnetic attraction, Envy Tidal Pull, and Envy repulsion.
  * When Envy Tidal Pull or Lust ends, entities carry their accumulated velocity forward with momentum and smoothly decelerate through natural viscous damping (`0.94` drag), gliding across the screen instead of abruptly stopping.
  * GOFAI bot kinematics updated to integrate entity momentum into spacetime danger projection.

### v0.13.0 (September 2026)
* **Kairos Card Title Typography Overhaul:**
  * Title font is significantly bigger (scale 7, +133% larger than former scale 3).
  * Sized so the longest sin name (`GLUTTONY`, 8 characters) fills nearly the entire card box horizontally (217px rendered width across a 228px card, leaving 5–6px margins).
  * Titles and level indicators are justified center horizontally within each card for instant split-second legibility during the 2.0-second Kairos circuit breaker.

### v0.12.0 (September 2026)
* **Score Formatting with Space Separator:**
  * Removed all leading zeros across HUD and Game Over screen; scores and statistics now format cleanly using a single space thousands separator (e.g. `SCORE: 1 234`, `0`).
* **Envy Tidal Pull Boon:**
  * Reworked Envy into temporary Tidal Pull: for 2.0 seconds (60 frames), all sand grains within 2× the current vignette pixel radius (1920px at Pact 1) are strongly drawn into the hourglass.
* **Hourglass Sand Physics & Tilt Proportionality:**
  * Direction and speed of falling sand (both internal neck flow, dynamic bulb sand redistribution, and external dripping sand cascade) are directly proportional to the hourglass tilt angle.
* **GOFAI Bot Envy Handicap:**
  * The autonomous bot's perception is strictly constrained by Envy's circular vignette boundary, rendering hazards and grains beyond the vignette radius invisible to AI trajectory planning.

### v0.11.0 (September 2026)
* **Difficulty Rebalance: Halved Base Spawn Rate:**
  * Reduced base entity spawn accumulator from 0.45 to 0.225 per frame, halving the initial amount of sand grains and glass shards at the start for a gentler learning curve.
* **Envy Vignette Rework (Dual-Radius):**
  * Outermost circle (zero vision beyond): radius = 1200 × 0.8^k px (Pact 1: 960px, Pact 2: 768px, Pact 3: 614px, Pact 4: 491px, Pact 5: 393px).
  * Innermost circle (full clear vision): radius = 1000 × 0.8^(k+1) px (Pact 1: 640px, Pact 2: 512px, Pact 3: 410px, Pact 4: 328px, Pact 5: 262px).
  * 5 graduated dither tiers are smoothly interpolated between inner and outer radii.
* **Bot Mode Game Over Restart Delay:**
  * Bot no longer immediately restarts upon game over; waits 6.0 seconds (180 frames) with live countdown displayed, allowing players to view final statistics. Pressing Space restarts immediately.

### v0.10.0 (September 2026)
* **X Key Dual-Behaviour:**
  * During gameplay (Chronos / Kairos / Game Over): `X` returns to the Title screen menu without quitting.
  * On Title Screen: `X` exits the application (graceful no-op in browser).
* **Numbered Top-Right Pact Menu:**
  * In-game HUD pact list moved to top right, removed `(7)` header, and formatted as canonical numbered list (`1. pride 0`, `2. greed 0`, etc.).
* **Envy Vignette Radius Documentation:**
  * Documented exact mathematical formula for Envy outer circle radius ($1200 \times 0.8^k$) and inner circle radius ($1000 \times 0.8^{k+1}$).
* **Sloth Drag Modifier Recalibration:**
  * Clarified and corrected 3rd-pact lateral drag multiplier value (0.45).
* **Version Normalization:**
  * Normalized version sequence to semantic increments (`v0.9.0` → `v0.10.0`).

### v0.9.0 (September 2026)
* **Universal PC & Mobile Viewport 3:4 Containment:**
  * Fixed canvas cropping across all PC desktop browsers and mobile screens by implementing pure CSS responsive containment (`--target-w: min(var(--avail-w), calc(var(--avail-h) * 0.75))`).
  * Backed by dynamic JavaScript `fitScreen()`, continuous mutation observation on `document.documentElement`, and `visualViewport` listener.
  * Guarantees zero cropping on any display or aspect ratio (16:9 PC widescreen, 9:19.5 mobile phone, tablet) while preserving the 3:4 portrait aspect ratio.
* **Homepage Dev Mode Version Display:**
  * When in Dev Mode (`~` / `` ` `` key or URL query parameter `?dev`), the game version number is prominently displayed on the main title screen header (`VERSION: v0.9.0 [DEV MODE]`).
* **Lethal Borrowed Time (Greed Overhaul):**
  * Removed "k=??" label from HUD warning, showing clean `BORROWED TIME`.
  * Greed countdown timer is now displayed in Dev Mode overlay telemetry.
  * When Borrowed Time expires, the debt is collected and the player instantly dies with dedicated cause of death (`"BORROWED TIME EXPIRED (DEBT COLLECTED)"`).
* **Game Controls & Quit Key:**
  * Remapped quit shortcut from `Q` to `X` (`pyxel.KEY_X`), preventing accidental quits.
  * Updated title screen, game over screen, and packaging runners.
* **Dev Mode Faustian Pact Reduction:**
  * Keys `Q`, `W`, `E`, `R`, `T`, `Y`, `U` in Dev Mode decrement corresponding pact levels in canonical order (Pride, Greed, Lust, Envy, Gluttony, Wrath, Sloth) and dynamically relax active modifiers.
* **Faustian Bargains Recalibration:**
  * **Pride:** Organic randomized clusters (+1 grain per level, starting with pairs then triplets); flat +25% descent speed per pact.
  * **Greed:** Borrowed Time (10.0–18.0s); sand multiplies score by 110%; lethal timer expiration.
  * **Lust:** Permanent magnetic attraction for both sand and glass shards; subsequent pacts widen attraction radius by +50px.
  * **Gluttony:** Symmetric +50% boost to sand and hazard spawn rates per pact level.
  * **Wrath:** Flat 10.0s hazard wipe and 10.0s zero-yield window; does not compound on repeat pacts.
  * **Sloth:** Immediate hazard freeze (0.0 speed) with linear recovery over 8.0 seconds (240 frames); lateral drag curse scales by -5% × 1.5^k.
* **Automated Testing & Balance:**
  * Expanded test suite to 32 unit tests passing with 100% pass rate.
  * Validated GOFAI kinematic bot stability across multi-episode headless benchmarks.

### v0.8.0 (September 2026)
* **Mobile Viewport Optimization:**
  * Fixed display cutoff on mobile browsers using `100svh`, `env(safe-area-inset-top)` / `bottom`, and an active JS `fitScreen()` visual viewport handler with 48px safety cushion.
  * Preserves 3:4 portrait aspect ratio cleanly centered in all viewports with zero clipping.
* **Kairos Input Re-press Protection:**
  * Prevented accidental pact selection upon entering Kairos if holding lateral keys or touch during Chronos.
  * Players must unpress/release the button first before choosing a pact on fresh press.
* **Sloth Rework (Hazard Freeze & 8s Recovery):**
  * Replaced flat hazard drag with immediate Hazard Freeze (0.0 speed) that linearly recovers back to normal speed over 8.0 seconds (240 frames). Permanent lateral drag curse remains.
* **Pride Organic Cluster Randomization:**
  * Sand clusters now spawn with randomized relative non-overlapping offsets (r ∈ [14, 36] px) while preserving shared velocity and trajectory.
* **Clean End Game Screen:**
  * Removed "k=" syntax from pact counts (shows simple clean counts).
  * Removed "CANONICAL ORDER" wording; now titled "PACTS SEALED SUMMARY:".
  * Version display hidden on game over screen unless Dev Mode is active.
* **Validation & Playtest Balancing:**
  * Updated unit test suite to 25 automated tests.
  * Conducted full 10-episode headless GOFAI kinematic playtesting suite to confirm game loop stability and balance.

### v0.7.0 (September 2026)
* **Dev-Only Bot & Video Toggles:**
  * Restricted bot mode (`B`) and video recording (`V`) triggers exclusively to Dev Mode.
* **Greed Timer & 110% Score Multiplier:**
  * Overhauled Greed: each sand collected multiplies current score by 110% (`floor(score * 1.10)`) during Borrowed Time.
  * Added visual Borrowed Time countdown and debt collection upon expiration.
* **Envy Screen Sand Reap & Vignette Darkness:**
  * Added initial screen-wide sand harvest upon sealing Envy pact.
  * Converted Envy curse into visual darkness with concentric mask boundary.
* **Exact Mathematical Formulations in Documentation:**
  * Added exact formulas ($k \ge 0$) for all 7 deadly sins to README.

### v0.6.0 (September 2026)
* **Mobile Responsive 3:4 Letterbox:**
  * Full responsive web layout maintaining strict 3:4 portrait aspect ratio.
* **Transparent Touch Controls:**
  * Semi-transparent on-screen `< LEFT` and `RIGHT >` touch steering buttons for mobile viewports.
* **±4.5 Screen Spawn Horizon:**
  * Procedural entity generation margin expanding 2700px on each lateral side to support unrestricted horizontal exploration.
* **Game Over 2.0s Debounce Lockout:**
  * Enforced 60-frame lockout preventing accidental restart inputs.
* **Canonical 7 Sins Vertical List:**
  * Arranged Faustian Bargain deck in strict Gregorian Catholic order (SALIGIA).

### v0.5.0 (September 2026)
* **1-Point Golden Sand Standard:**
  * Normalized scoring to 1 point per grain.
* **Pride Sand Clusters:**
  * Pride spawns multiple sand motes in clustered formations.
* **Bottom Alpha Dev Overlay:**
  * Semi-transparent HUD toggled via backtick (`` ` ``) with telemetry and `1`–`7` instant pact injection keys.
* **Enlarged Typography:**
  * Upgraded retro text scale for enhanced readability.

### v0.4.0 (September 2026)
* **SkiFree Infinite Horizontal Arena:**
  * Removed lateral boundary walls; player and hazards navigate an infinite horizontal expanse with smooth camera tracking.
* **Lossless FFmpeg Video Recorder:**
  * Real-time canvas MP4 video export with unique timestamped filenames.
* **Elapsed Time HUD:**
  * Survival timer and descent stopwatch displayed on screen.

### v0.3.0 (September 2026)
* **Dual-Tier Concentric Vignette:**
  * Circular darkness mask with clear central core and 50% dithered boundary ring.
* **5-Heart Life System:**
  * Fragile hourglass vessel with 5 hearts, invulnerability flash, and impact screen shake.
* **Background Temporal Stimuli:**
  * Animated falling cosmic sand streams and parallax dust motes.
* **Dual-Clock Engine (Chronos & Kairos):**
  * 8-second Chronos descent followed by 2-second Kairos circuit breaker with 2-card Faustian Bargain selection.
* **Lateral Drift Physics:**
  * Dynamic X-axis velocity variance and sinusoidal flutter oscillation for falling entities.

### v0.2.0 (September 2026)
* **Resolution Upscale to 600 × 800:**
  * High-definition retro portrait resolution (3:4 aspect ratio).
* **Kinematic Steering:**
  * Lateral movement with viscous damping coefficient ($0.82$).
* **Tilting Hourglass Sprite:**
  * Physical hourglass tilt proportional to horizontal velocity.
* **GOFAI Autonomous Playtesting Bot:**
  * Heuristic AI agent with spacetime trajectory projection for headless evaluation and balance benchmarks.

### v0.1.0 (September 2026)
* **Initial PyWeek 42 Prototype ("Borrowed Time"):**
  * Endless downhill retro falling-hourglass arcade runner concept ("Hourglass-ception").
  * Basic sand collection and glass hazard evasion mechanics.
  * Pyxel retro game engine loop, state manager, and initial asset framework.
