# Grain of Doubt

> **By Arian Prabowo**  
> **PyWeek 42 Entry ("Borrowed Time")** — September 2026  
> An endless retro downhill falling-hourglass arcade runner built with the **Pyxel** retro game engine.  
> **Target Resolution:** $600 \times 800$ pixels ($3:4$ Portrait Aspect Ratio).

[![Pyxel](https://img.shields.io/badge/Engine-Pyxel%202.9.9-blue)](https://github.com/kitao/pyxel)
[![Python](https://img.shields.io/badge/Python-3.12-brightgreen)](https://www.python.org/)
[![Status](https://img.shields.io/badge/Tests-Passing-success)](#automated-validation-gates)

---

## ⏳ Narrative & Gameplay Premise

You control a fragile hourglass falling through the neck of an infinite, crumbling cosmic hourglass (**"Hourglass-ception"**).
Gravity is unstoppable—you cannot stop or reverse descent. You can only steer left or right to avoid razor-sharp falling glass shards while collecting glistening golden grains of sand.

### Chronos vs. Kairos (The Dual-Clock Engine)
* **Chronos (8.0s descent):** Relentless kinetic tension. Steer left or right to dodge oncoming glass shards while reaping cascading sand motes. (No braking, no diving—terminal gravity is fixed).
* **Kairos (2.0s circuit breaker):** Every 8 seconds, normal time freezes. You are confronted with **3 mandatory Faustian Bargain cards** drawn from the Seven Deadly Sins. You cannot skip—you must choose a sin.
* **Faustian Bargains:** Every bargain grants an immediate survival boon at the cost of a permanent, compounding structural curse. Choosing the same sin repeatedly diminishes the boon while exponentially multiplying the curse ($Boon \propto 0.75^k$, $Curse \propto 1.50^k$).

---

## 🎮 Controls

The game strictly features single-axis lateral navigation. **No aero-brake, no deep dive.**

| Key | Action | Mechanic |
| :--- | :--- | :--- |
| `A` / `D` or `Left` / `Right` | Lateral Steering | Steer hourglass horizontally ($\mu_x = 0.82$ viscous damping) |
| `A` / `D` or `Left` / `Right` | Select Faustian Bargain | Move selection between Left, Center, and Right sin cards in Kairos |
| `Space` / `Enter` | Descend / Start / Confirm | Start game or instantly confirm card in Kairos |
| `R` | Restart | Restart following fatal hourglass shatter |
| `Q` | Quit | Exit game |

---

## 📜 The Seven Deadly Sins (Faustian Bargains)

1. **Gluttony (*Gula*):**
   * *Boon:* Accelerates sand grain generation rate.
   * *Curse:* Multiplies hazard glass shard density.
2. **Pride (*Superbia*):**
   * *Boon:* Multiplies global score yield.
   * *Curse:* Increases descent velocity and temporal acceleration.
3. **Greed (*Avaritia*):**
   * *Boon:* Converts all accrued dodges and collections into score multiplier.
   * *Curse:* Initializes an ominous deterministic sudden-death kill-timer.
4. **Wrath (*Ira*):**
   * *Boon:* Completely purges all active hazards from the screen.
   * *Curse:* Enforces zero-yield state (no sand points) for penalty duration.
5. **Sloth (*Acedia*):**
   * *Boon:* Decelerates vertical hazard velocity to ease reaction.
   * *Curse:* Imposes permanent lateral drag on player movement.
6. **Envy (*Invidia*):**
   * *Boon:* Retroactively reclaims all bypassed sand motes for points.
   * *Curse:* Establishes a permanent sand repulsion field around the hourglass.
7. **Lust (*Luxuria*):**
   * *Boon:* Activates temporary magnetic attraction field for golden sand.
   * *Curse:* Establishes a permanent magnetic attraction field for glass shards.

---

## 🏗️ Architecture & Project Structure

```
.
├── main.py                     # Entry point, Pyxel canvas loop, vignette mask, HUD
├── engine/
│   ├── __init__.py
│   ├── state.py                # GameState enum, StateManager, Chronos/Kairos timers
│   ├── entities.py             # HourglassPlayer, SandGrain, GlassShard, EntityManager
│   ├── bargains.py             # Faustian Bargain registry, compounding decay mathematics
│   └── audio.py                # 4-channel procedural retro synth sound matrix
├── tests/
│   ├── __init__.py
│   └── test_mechanics.py       # Automated unit test suite covering all 5 validation gates
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
```

### 3. Run Automated Validation Gates
```bash
.venv/bin/pytest tests/test_mechanics.py -v
```

### 4. Build Packaging Pipeline
```bash
./build.sh
```

### 5. WebAssembly Browser Play
Open `index.html` via any local HTTP server:
```bash
python3 -m http.server 8000
# Open http://127.0.0.1:8000 in your browser
```
