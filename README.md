# Grain of Doubt

> **By Arian Prabowo**  
> **Version:** v0.14.0  
> **PyWeek 42 Entry ("Borrowed Time")** — September 2026  
> An endless retro downhill falling-hourglass arcade runner built with the **Pyxel** retro game engine.  
> **Target Resolution:** $600 \times 800$ pixels ($3:4$ Portrait Aspect Ratio, Infinite Horizontal Arena).

**PLAY! https://aprbw.github.io/pyweek42/index.html**

[![Pyxel](https://img.shields.io/badge/Engine-Pyxel%202.9.9-blue)](https://github.com/kitao/pyxel)
[![Python](https://img.shields.io/badge/Python-3.12-brightgreen)](https://www.python.org/)
[![Status](https://img.shields.io/badge/Tests-Passing-success)](#automated-validation-gates)

---

## ⏳ Narrative & Gameplay Premise

You control a fragile hourglass falling through the neck of an infinite, crumbling cosmic hourglass (**"Hourglass-ception"**).
Steer left or right to avoid razor-sharp falling glass shards while collecting glistening golden grains of sand.

### Chronos vs. Kairos (The Dual-Clock Engine)
* **Chronos (8.0s descent):** Relentless kinetic tension. Steer left or right across an infinitely wide horizontal arena ($\pm 4.5$ screen procedural generation horizon) to dodge oncoming glass shards while reaping cascading sand motes.
* **Kairos (2.0s circuit breaker):** Every 8 seconds, normal time freezes. You are presented with **2 Faustian Bargain cards** drawn from the Seven Deadly Sins. You must choose within 2.0 seconds—if you hesitate, doubt shatters your vessel (*Paralyzed by Doubt: Kairos Expired*). A vertical side timer drains from top to bottom.
  * **Input Re-press Protection:** Entering Kairos requires unpressing/releasing lateral steering first before choosing, preventing accidental card selection if holding arrows during Chronos.
* **Faustian Bargains:** Every bargain grants an immediate survival boon at the cost of a permanent curse. Repeatedly choosing sins compounds their effects.

---

## 🎮 Controls

| Control | Action | Mechanic |
| :--- | :--- | :--- |
| `A` / `D` or `Left` / `Right` | Lateral Steering | Steer hourglass horizontally ($\mu_x = 0.82$ viscous damping) |
| Touch `< LEFT` / `RIGHT >` | Mobile Touch Steering | Semi-transparent on-screen buttons (visible on mobile only) or bottom screen tap |
| `Left` / `Right` or Tap Card | Select Faustian Bargain | Steer left or right during Kairos to choose between the 2 bargain cards within 2.0s (requires fresh press after release) |
| `Space` / `Enter` or Tap Screen | Start / Restart | Start game or restart after a 2.0s post-mortem lockout (debounced) |
| `X` | Return to Menu / Quit | In gameplay: return to Title Menu. On Title Menu: quit game (no-op in browser) |
| `~` / `` ` `` (Backtick) | Toggle Dev Mode | On-screen debug HUD, live telemetry, and shortcut cheats |
| `I` (in Dev Mode) | Toggle God Mode | Invulnerability toggle (immune to razor shards and void collision) |
| `B` (in Dev Mode) | Toggle GOFAI Bot | Autonomous kinematic AI playtesting agent (80% speed handicap, 20% bottom blind zone) |
| `V` (in Dev Mode) | Toggle MP4 Recording | Lossless FFmpeg background canvas video recorder |
| `1` - `7` (in Dev Mode) | Add Faustian Pact | Instant-apply sin pact level (1:Pride, 2:Greed, 3:Lust, 4:Envy, 5:Gluttony, 6:Wrath, 7:Sloth) |
| `Q`, `W`, `E`, `R`, `T`, `Y`, `U` (in Dev Mode) | Reduce Faustian Pact | Decrement corresponding sin pact level (Q:Pride, W:Greed, E:Lust, R:Envy, T:Gluttony, Y:Wrath, U:Sloth) |

---

## 📜 Seven Deadly Faustian Bargains

Every 10.0 seconds ($300$ frames), normal time flow stops and **Kairos** strikes. The player is presented with **two randomly chosen Faustian Bargains** in Catholic Gregorian canonical order. You have exactly 2.0 seconds ($60$ frames) to choose one, or your hourglass shatters instantly.

*Exact mathematical values ($k \ge 0$ is the repeat pact count):*

1. **Pride:**
   * *Boon:* Spawns golden sand in organic randomized clusters: $+1$ grain per pact level (1st pact: pairs $= 2$ grains; 2nd: triplets $= 3$; 3rd: quadruplets $= 4$; grains share trajectory with randomized non-overlapping offsets; 1 sand = 1 point).
   * *Curse:* Increases descent velocity multiplier by flat $+25\%$ per pact level ($+0.25$).
2. **Greed:**
   * Triggers **Borrowed Time**
   * *Boon:* During Borrowed Time, each sand multiplies the current score by 110% ($Score \leftarrow \max(Score + 1, \lfloor Score \times 1.10 \rfloor)$) instead of adding 1 point.
   * *Curse:* Triggers **Borrowed Time** for a randomized window of **10.0 to 18.0 seconds** ($300$ to $540$ frames). At the end, you definitely die (*Borrowed Time Expired: Debt Collected*). Warning HUD shows `BORROWED TIME`, and Dev Mode displays the countdown timer.
3. **Lust:**
   * *Boon:* Sand magnetic attraction permanently pulls golden sands within radius toward hourglass ($180.0$px on 1st pact, $+60.0$px on subsequent pacts).
   * *Curse:* Hazard magnetic attraction permanently pulls razor glass shards within radius toward hourglass ($180.0$px on 1st pact, $+60.0$px on subsequent pacts).
4. **Envy:**
   * *Boon:* Activates **Mega Lust** for 2.0 seconds (60 frames), very strongly attracting all golden sand grains within $2\times$ the current vignette pixel radius ($2 \times R_{\text{vignette}}$, $1920$px on Pact 1) toward the hourglass.
   * *Curse:* Inflicts **Vignette Vision**, a multi-circle concentric mask with 5 graduated dither transparency tiers between an inner clear core and outer void boundary.
     * **Outermost circle** (zero vision beyond): $1200 \times 0.8^k$ px — Pact 1 → $960$px, Pact 2 → $768$px, Pact 3 → $614$px, Pact 4 → $491$px, Pact 5 → $393$px.
     * **Innermost circle** (full clear vision): $1000 \times 0.8^{k+1}$ px — Pact 1 → $640$px, Pact 2 → $512$px, Pact 3 → $410$px, Pact 4 → $328$px, Pact 5 → $262$px.
5. **Gluttony:**
   * *Boon:* Increases golden sand spawn rate by $+50\%$ per pact level ($+0.50$).
   * *Curse:* Increases razor hazard spawn rate by $+50\%$ per pact level ($+0.50$).
6. **Wrath:**
   * *Boon:* Instantly purges all razor hazards on screen, granting a 10.0-second ($300$ frames) hazard-free grace window. (The only sin that does not compound after multiple use).
   * *Curse:* Zero yield: all sand grains collected yield 0 points for 10.0 seconds ($300$ frames).
7. **Sloth:**
   * *Boon:* Freeze Hazards immediately ($0.0$ velocity), slowly recovering speed linearly over $8.0$ seconds ($240$ frames) back to full speed ($1.0$).
   * *Curse:* Imposes lateral drag on hourglass steering, reducing horizontal translation speed by $20\% \times 1.5^k$ ($0.20$ reduction on 1st pact, $0.30$ on 2nd, $0.45$ on 3rd; minimum modifier $0.20$).

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

---

## 📝 Changelog

### v0.14.0 (September 2026)
* **Kinematic Momentum & Acceleration Physics for Lust & Envy:**
  * Replaced discrete positional translation with proper second-order Newtonian physics (`acceleration` $\to$ `velocity` $\to$ `position`).
  * Grains and razor shards accumulate velocity (`vx`, `vy`) under Lust magnetic attraction, Envy Mega Lust pull, and Envy repulsion.
  * When Envy Mega Lust or Lust ends, entities carry their accumulated velocity forward with momentum and smoothly decelerate through natural viscous damping (`0.94` drag), gliding across the screen instead of abruptly stopping.
  * GOFAI bot kinematics updated to integrate entity momentum into spacetime danger projection.

### v0.13.0 (September 2026)
* **Kairos Card Title Typography Overhaul:**
  * Title font is significantly bigger (scale 7, +133% larger than former scale 3).
  * Sized so the longest sin name (`GLUTTONY`, 8 characters) fills nearly the entire card box horizontally (217px rendered width across a 228px card, leaving 5–6px margins).
  * Titles and level indicators are justified center horizontally within each card for instant split-second legibility during the 2.0-second Kairos circuit breaker.

### v0.12.0 (September 2026)
* **Score Formatting with Space Separator:**
  * Removed all leading zeros across HUD and Game Over screen; scores and statistics now format cleanly using a single space thousands separator (e.g. `SCORE: 1 234`, `0`).
* **Envy Mega Lust Boon:**
  * Reworked Envy into temporary Mega Lust: for 2.0 seconds (60 frames), all sand grains within $2\times$ the current vignette pixel radius ($1920$px at Pact 1) are strongly drawn into the hourglass.
* **Hourglass Sand Physics & Tilt Proportionality:**
  * Direction and speed of falling sand (both internal neck flow, dynamic bulb sand redistribution, and external dripping sand cascade) are directly proportional to the hourglass tilt angle.
* **GOFAI Bot Envy Handicap:**
  * The autonomous bot's perception is strictly constrained by Envy's circular vignette boundary, rendering hazards and grains beyond the vignette radius invisible to AI trajectory planning.

### v0.11.0 (September 2026)
* **Difficulty Rebalance: Halved Base Spawn Rate:**
  * Reduced base entity spawn accumulator from $0.45$ to $0.225$ per frame, halving the initial amount of sand grains and glass shards at the start for a gentler learning curve.
* **Envy Vignette Rework (Dual-Radius):**
  * Outermost circle (zero vision beyond): radius $= 1200 \times 0.8^k$ px (Pact 1: 960px, Pact 2: 768px, Pact 3: 614px, Pact 4: 491px, Pact 5: 393px).
  * Innermost circle (full clear vision): radius $= 1000 \times 0.8^{k+1}$ px (Pact 1: 640px, Pact 2: 512px, Pact 3: 410px, Pact 4: 328px, Pact 5: 262px).
  * 5 graduated dither tiers are smoothly interpolated between inner and outer radii.
* **Top-Right Numbered Pact Menu:**
  * In-game HUD pact list moved to top right, removed `(7)` header, and formatted as canonical numbered list (`1. pride 0`, `2. greed 0`, etc.).
* **X Key Dual-Behaviour:**
  * During gameplay (Chronos / Kairos / Game Over): `X` returns to the Title screen menu without quitting.
  * On Title Screen: `X` exits the application (graceful no-op in browser).
* **Bot Mode Game Over Restart Delay:**
  * Bot no longer immediately restarts upon game over; waits 6.0 seconds (180 frames) with live countdown displayed, allowing players to view final statistics. Pressing Space restarts immediately.

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
  * **Pride:** Organic randomized clusters (+1 grain per level, starting with pairs then triplets); flat $+25\%$ descent speed per pact.
  * **Greed:** Borrowed Time (10.0–18.0s); sand multiplies score by $110\%$; lethal timer expiration.
  * **Lust:** Permanent magnetic attraction for both sand and razor hazards; subsequent pacts widen attraction radius by $+60$px.
  * **Gluttony:** Symmetric $+50\%$ boost to sand and hazard spawn rates per pact level.
  * **Wrath:** Flat 10.0s hazard wipe and 10.0s zero-yield window; does not compound on repeat pacts.
  * **Sloth:** Immediate hazard freeze ($0.0$ speed) with linear recovery over $8.0$ seconds ($240$ frames); lateral drag curse scales by $-5\% \times 1.5^k$.
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
  * Replaced flat hazard drag with immediate Hazard Freeze ($0.0$ speed) that linearly recovers back to normal speed over $8.0$ seconds ($240$ frames). Permanent lateral drag curse remains.
* **Pride Organic Cluster Randomization:**
  * Sand clusters now spawn with randomized relative non-overlapping offsets ($r \in [14, 36]$ px) while preserving shared velocity and trajectory.
* **Clean End Game Screen:**
  * Removed "k=" syntax from pact counts (shows simple clean counts).
  * Removed "CANONICAL ORDER" wording; now titled "PACTS SEALED SUMMARY:".
  * Version display hidden on game over screen unless Dev Mode is active.
* **Validation & Playtest Balancing:**
  * Updated unit test suite to 25 automated tests.
  * Conducted full 10-episode headless GOFAI kinematic playtesting suite to confirm game loop stability and balance.
