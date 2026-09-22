# Grain of Doubt

> **By Arian Prabowo**  
> **Version:** v0.8.0  
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
| `1` - `7` (in Dev Mode) | Fixed Faustian Pact | Instant-apply sin pact in order (1:Pride .. 7:Sloth) |
| `B` (in Dev Mode) | Playtest Bot | Toggle autonomous GOFAI kinematic playtesting bot (dev mode only) |
| `V` (in Dev Mode) | Video Recording | Toggle MP4 video capture to disk (dev mode only) |
| `Q` | Quit | Exit game |

---

## 📜 The Seven Deadly Sins (Faustian Bargains & Exact Parameters)

*Exact mathematical values ($k \ge 0$ is the repeat pact count):*

1. **Pride:**
   * *Boon:* Spawns golden sand in organic randomized clusters: $+1$ grain per pact level (1st pact: pairs $= 2$ grains; 2nd: triplets $= 3$; 3rd: quadruplets $= 4$; grains share trajectory with randomized non-overlapping offsets; 1 sand = 1 point).
   * *Curse:* Increases descent velocity multiplier by $+25\% \times 1.5^k$ ($+0.50$ on 1st pact, $+0.75$ on 2nd, $+1.125$ on 3rd).
2. **Greed:**
   * *Boon:* Instant bounty harvest granting $(N_{sands\_collected} + N_{shards\_dodged}) \times 5.0 \times 0.75^k$ points ($5.0$ pts/entity on 1st pact, $3.75$ on 2nd, $2.81$ on 3rd).
   * *Curse:* Triggers **Borrowed Time** for a randomized window of **10.0 to 18.0 seconds** ($300$ to $540$ frames). Void erupts into blood crimson with ember stars, descent velocity increases by $+20\% \times 1.5^k$, spawn density increases by $+25\% \times 1.5^k$, and collecting sand **multiplies current score by 110%** ($Score \leftarrow \max(Score + 1, \lfloor Score \times 1.10 \rfloor)$) instead of adding 1 point! Remaining duration is displayed in the Dev Mode telemetry overlay.
3. **Lust:**
   * *Boon:* Generates a golden sand magnetic attraction vortex with a radius of $220.0 \times 0.75^k$ px ($220$px on 1st pact, $165$px on 2nd, $124$px on 3rd) active for 10.0 seconds ($300$ frames).
   * *Curse:* Generates a permanent lethal glass shard magnetic attraction vortex with a radius of $180.0 \times 1.5^k$ px ($180$px on 1st pact, $270$px on 2nd, $405$px on 3rd).
4. **Envy:**
   * *Boon:* Instantly reaps all golden sand grains currently visible on the screen, immediately awarding their score and triggering radiant particle bursts.
   * *Curse:* Inflicts **Vignette Vision**, restricting your visual range to a dark circular tunnel vision mask with radius $260.0 \times 0.80^k$ px ($260$px on 1st pact, $208$px on 2nd, $166$px on 3rd, minimum $90$px).
5. **Gluttony:**
   * *Boon:* Accelerates global sand grain and entity generation rate multiplier by $+80\% \times 0.75^k$ ($+0.80$ on 1st pact, $+0.60$ on 2nd, $+0.45$ on 3rd).
   * *Curse:* Multiplies hazard glass shard density and spawn rate by $+80\% \times 1.5^k$ ($+0.80$ on 1st pact, $+1.20$ on 2nd, $+1.80$ on 3rd).
6. **Wrath:**
   * *Boon:* Purges 100% of active glass shards from the screen and grants hazard immunity for $10.0 \times 0.75^k$ seconds ($300$ frames on 1st pact, $225$ frames on 2nd, $169$ frames on 3rd).
   * *Curse:* Zero-Yield state: collected sands award 0 points for $10.0 \times 1.5^k$ seconds ($300$ frames on 1st pact, $450$ frames on 2nd, $675$ frames on 3rd).
7. **Sloth:**
   * *Boon:* Freeze Hazards immediately ($0.0$ velocity), slowly recovering speed linearly over $8.0$ seconds ($240$ frames) back to full speed ($1.0$).
   * *Curse:* Imposes lateral drag on hourglass steering, reducing horizontal translation speed by $5\% \times 1.5^k$ ($0.05$ reduction on 1st pact, $0.075$ on 2nd, down to minimum $0.35$ modifier).

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

### 1. Run with Launcher
```bash
./run.sh
```

### 2. Manual Run
```bash
# Setup environment
uv venv --python 3.12 .venv
source .venv/bin/activate
uv pip install pyxel pytest

# Run with Pyxel
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
