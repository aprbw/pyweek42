# Grain of Doubt

> **By Arian Prabowo**  
> **PyWeek 42 Entry ("Borrowed Time")** — September 2026  
> An endless retro downhill falling-hourglass arcade runner built with the **Pyxel** retro game engine.  
> **Target Resolution:** $600 \times 800$ pixels ($3:4$ Portrait Aspect Ratio).

**PLAY! https://aprbw.github.io/pyweek42/index.html**

[![Pyxel](https://img.shields.io/badge/Engine-Pyxel%202.9.9-blue)](https://github.com/kitao/pyxel)
[![Python](https://img.shields.io/badge/Python-3.12-brightgreen)](https://www.python.org/)
[![Status](https://img.shields.io/badge/Tests-Passing-success)](#automated-validation-gates)

---

## ⏳ Narrative & Gameplay Premise

You control a fragile hourglass falling through the neck of an infinite, crumbling cosmic hourglass (**"Hourglass-ception"**).
Steer left or right to avoid razor-sharp falling glass shards while collecting glistening golden grains of sand.

### Chronos vs. Kairos (The Dual-Clock Engine)
* **Chronos (8.0s descent):** Relentless kinetic tension. Steer left or right to dodge oncoming glass shards while reaping cascading sand motes.
* **Kairos (2.0s circuit breaker):** Every 8 seconds, normal time freezes. You are presented with **2 Faustian Bargain cards** drawn from the Seven Deadly Sins. You cannot skip—steer left or right to seal your pact.
* **Faustian Bargains:** Every bargain grants an immediate survival boon at the cost of a permanent curse. Repeatedly choosing the same sin compounds the curse.

---

## 🎮 Controls

| Control | Action | Mechanic |
| :--- | :--- | :--- |
| `A` / `D` or `Left` / `Right` | Lateral Steering | Steer hourglass horizontally ($\mu_x = 0.82$ viscous damping) |
| Touch `< LEFT` / `RIGHT >` | Mobile Touch Steering | On-screen arcade buttons or tap bottom half of screen on mobile browser |
| `Left` / `Right` or Tap Card | Select Faustian Bargain | Steer left or right during Kairos to choose between the 2 bargain cards |
| `Space` / `Enter` or Tap Screen | Start / Restart | Start game or restart following fatal hourglass shatter |
| `~` / `` ` `` (Backtick) | Dev Mode Overlay | Toggle developer telemetry overlay (version, bot status, speeds, entity counts) |
| `B` | Playtest Bot | Toggle autonomous GOFAI kinematic playtesting bot |
| `V` | Video Recording | Toggle MP4 video capture to disk |
| `Q` | Quit | Exit game |

---

## 📜 The Seven Deadly Sins (Faustian Bargains)

1. **Gluttony:**
   * *Boon:* Accelerates sand grain generation rate.
   * *Curse:* Multiplies hazard glass shard density.
2. **Pride:**
   * *Boon:* Doubles score multiplier (2x points on all collections and dodges).
   * *Curse:* Increases descent velocity.
3. **Greed:**
   * *Boon:* Converts all accrued sand collections and shard dodges into an instant score bounty.
   * *Curse:* Triggers Borrowed Time for 10 to 18 seconds (escalated speed, halved vision, blood crimson void).
4. **Wrath:**
   * *Boon:* Purges all active hazards from the screen.
   * *Curse:* Enforces zero-yield state (no sand points) for 10 seconds.
5. **Sloth:**
   * *Boon:* Decelerates vertical hazard velocity to ease reaction.
   * *Curse:* Imposes permanent lateral drag on player movement.
6. **Envy:**
   * *Boon:* Retroactively reclaims all bypassed sand motes for bonus points.
   * *Curse:* Establishes a permanent sand repulsion field around the hourglass.
7. **Lust:**
   * *Boon:* Activates magnetic attraction field pulling in golden sand.
   * *Curse:* Establishes magnetic attraction field pulling in glass shards.

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

### 5. WebAssembly Browser Play
Open `index.html` via any local HTTP server:
```bash
python3 -m http.server 8000
# Open http://127.0.0.1:8000 in your browser
```
