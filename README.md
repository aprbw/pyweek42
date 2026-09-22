# Grain of Doubt

> **By Arian Prabowo**  
> **Version:** v0.10.0  
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
| `~` / `` ` `` (Backtick) | Dev Mode Overlay | Toggle developer telemetry overlay (hidden on title screen unless active) |
| `1` - `7` (in Dev Mode) | Add Faustian Pact | Instant-apply sin pact level (1:Pride, 2:Greed, 3:Lust, 4:Envy, 5:Gluttony, 6:Wrath, 7:Sloth) |
| `Q`, `W`, `E`, `R`, `T`, `Y`, `U` (in Dev Mode) | Reduce Faustian Pact | Decrement corresponding sin pact level (Q:Pride, W:Greed, E:Lust, R:Envy, T:Gluttony, Y:Wrath, U:Sloth) |
| `I` (in Dev Mode) | Toggle God Mode | Toggle complete invulnerability against all hazard damage |
| `B` (in Dev Mode) | Playtest Bot | Toggle autonomous GOFAI kinematic playtesting bot (dev mode only) |
| `V` (in Dev Mode) | Video Recording | Toggle MP4 video capture to disk (dev mode only) |
| `X` | Quit / Menu | On Title screen: Quit game. During gameplay: return to Title menu |

---

## 📜 The Seven Deadly Sins (Faustian Bargains & Exact Parameters)

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
   * *Boon:* Instantly reaps all golden sand grains currently visible on the screen, immediately awarding their score and triggering radiant particle bursts.
   * *Curse:* Inflicts **Vignette Vision**, a multi-circle concentric mask with 5 graduated dither transparency tiers. Radius $= \max(90,\, 260 \times 0.80^{k-1})$ px.
     * **Outermost circle** (zero vision beyond): Pact 1 → $260$px, Pact 2 → $208$px, Pact 3 → $166$px, Pact 4 → $133$px, Pact 5 → $107$px, Pact 6+ → $90$px (minimum).
     * **Innermost circle** (full clear vision): $0.42 \times$ radius — Pact 1 → $109$px, Pact 2 → $87$px, Pact 3 → $70$px, Pact 4 → $56$px, Pact 5 → $45$px, Pact 6+ → $38$px.
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

### v0.10.0 (September 2026)
* **X Key Dual-Behaviour:**
  * On **Title Screen**: `X` quits the game (no-op in browser).
  * **During Gameplay** (Chronos / Kairos / Game Over): `X` returns to the Title menu without quitting.
* **Pact Menu Numbered List:**
  * In-game HUD pact list now shows canonical numbering (`1. PRIDE 0`, `2. GREED 0`, etc.) instead of `(7)` header.
* **README Envy Radius Progression:**
  * Documented exact outermost (zero vision) and innermost (full clear vision) circle radii per pact level.

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
