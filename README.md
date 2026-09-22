# Grain of Doubt

> **By Arian Prabowo**  
> **Version:** v0.6.0  
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
* **Faustian Bargains:** Every bargain grants an immediate survival boon at the cost of a permanent curse. Repeatedly choosing sins compounds their effects.

---

## 🎮 Controls

| Control | Action | Mechanic |
| :--- | :--- | :--- |
| `A` / `D` or `Left` / `Right` | Lateral Steering | Steer hourglass horizontally ($\mu_x = 0.82$ viscous damping) |
| Touch `< LEFT` / `RIGHT >` | Mobile Touch Steering | Semi-transparent on-screen buttons (visible on mobile only) or bottom screen tap |
| `Left` / `Right` or Tap Card | Select Faustian Bargain | Steer left or right during Kairos to choose between the 2 bargain cards within 2.0s |
| `Space` / `Enter` or Tap Screen | Start / Restart | Start game or restart after a 2.0s post-mortem lockout (debounced) |
| `~` / `` ` `` (Backtick) | Dev Mode Overlay | Toggle developer telemetry overlay (hidden on title screen unless active) |
| `1` - `7` (in Dev Mode) | Fixed Faustian Pact | Instant-apply sin pact in canonical order (1:Pride .. 7:Sloth) |
| `B` | Playtest Bot | Toggle autonomous GOFAI kinematic playtesting bot |
| `V` | Video Recording | Toggle MP4 video capture to disk |
| `Q` | Quit | Exit game |

---

## 📜 The Seven Deadly Sins (Faustian Bargains)

*Presented in Gregorian / Catholic Canonical Order:*

1. **Pride:**
   * *Boon:* Spawns golden sand in clusters (pairs on 1st pact, triplets on 2nd, quadruplets on 3rd; 1 sand = 1 point).
   * *Curse:* Increases descent velocity.
2. **Greed:**
   * *Boon:* Converts all accrued sand collections and shard dodges into an instant score bounty.
   * *Curse:* Triggers Borrowed Time for 10 to 18 seconds (escalated speed, halved vision, blood crimson void).
3. **Lust:**
   * *Boon:* Activates magnetic attraction field pulling in golden sand.
   * *Curse:* Establishes magnetic attraction field pulling in glass shards.
4. **Envy:**
   * *Boon:* Retroactively reclaims all bypassed sand motes for bonus points.
   * *Curse:* Establishes a permanent sand repulsion field around the hourglass.
5. **Gluttony:**
   * *Boon:* Accelerates sand grain generation rate.
   * *Curse:* Multiplies hazard glass shard density.
6. **Wrath:**
   * *Boon:* Purges all active hazards from the screen.
   * *Curse:* Enforces zero-yield state (no sand points) for 10 seconds.
7. **Sloth:**
   * *Boon:* Decelerates vertical hazard velocity to ease reaction.
   * *Curse:* Imposes permanent lateral drag on player movement.

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
