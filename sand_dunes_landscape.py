#!/usr/bin/env python3
"""Continuous 2D Procedural Sand Dunes Landscape Engine.

PyWeek 42 - Borrowed Time.
Implements a continuous 2D procedural landscape with:
  1. TOPOLOGY ENGINE: Layered polygons back-to-front, negative space between procedural curves,
     supra-canvas horizon projection, upward translation velocity inversely proportional to Z-depth
     (fast at bottom, slow at top, asymptotic stalling at horizon), amplitude & frequency scaling.
  2. SHADOW MAPPING: Localized vertical linear gradients within wave geometries (low-luminosity
     superior coordinate / crest, high-luminosity inferior coordinate / base).
  3. ATMOSPHERIC SCATTERING: Global luminosity scalar linked to Z-depth; distal layers optically
     bleach into ambient desert haze, proximal layers retain full saturation.

Can be run interactively or headlessly:
  python sand_dunes_landscape.py              # Interactive Pyxel window
  python sand_dunes_landscape.py --headless   # Automated smoke test & screenshot export
"""

import sys
import math
import argparse
from typing import List, Tuple, Dict, Optional

try:
    import pyxel
except ImportError:
    print("Error: pyxel is required to run sand_dunes_landscape.py.")
    print("Install it with: pip install pyxel")
    sys.exit(1)


# =============================================================================
# TOPOLOGY & PROJECTION CONSTANTS
# =============================================================================
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 800
DEFAULT_HORIZON_Y = -140   # Supra-canvas horizon point (above canvas)
NUM_LAYERS = 16            # Discrete depth layers
SPEED_U = 0.000006         # Inverse-depth translation velocity
MAX_AMPLITUDE = 85.0       # Maximum wave peak-to-trough amplitude in foreground
SAMPLE_STEP_X = 2          # Horizontal curve sampling step (px)


class SandDunesLandscape:
    """Continuous 2D Procedural Sand Dunes Landscape Simulator."""

    def __init__(
        self,
        screen_w: int = SCREEN_WIDTH,
        screen_h: int = SCREEN_HEIGHT,
        horizon_y: int = DEFAULT_HORIZON_Y,
        num_layers: int = NUM_LAYERS,
        headless: bool = False,
    ):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.horizon_y = horizon_y
        self.num_layers = num_layers
        self.headless = headless

        # Simulation telemetry
        self.cam_x = 0.0
        self.dist = 0.0
        self.drift_speed = 3.2
        self.lateral_speed = 0.0
        self.is_paused = False
        self.scattering_mode = 0  # 0: Standard desert haze, 1: High noon bleaching, 2: Sunset glow

        # Precompute depth bounds in inverse space (u = 1 / (Y - horizon_y))
        # At canvas bottom (plus margin): u_min
        # Near horizon (above canvas top): u_max
        self._recompute_depth_bounds()

    def _recompute_depth_bounds(self):
        self.u_min = 1.0 / (self.screen_h - self.horizon_y + 100)
        self.u_max = 1.0 / max(10, (25 - self.horizon_y))
        self.step_u = (self.u_max - self.u_min) / float(self.num_layers)

    def update(self):
        """Advance procedural simulation frame."""
        if not self.headless:
            # Lateral steering (A / D or Left / Right arrows)
            steer = 0.0
            if pyxel.btn(pyxel.KEY_LEFT) or pyxel.btn(pyxel.KEY_A):
                steer -= 6.0
            if pyxel.btn(pyxel.KEY_RIGHT) or pyxel.btn(pyxel.KEY_D):
                steer += 6.0
            self.cam_x += steer

            # Vertical drift speed adjustment (W / S or Up / Down)
            if pyxel.btn(pyxel.KEY_W):
                self.drift_speed = min(12.0, self.drift_speed + 0.1)
            if pyxel.btn(pyxel.KEY_S):
                self.drift_speed = max(0.5, self.drift_speed - 0.1)

            # Horizon altitude tuning (PageUp / PageDown or U / J)
            if pyxel.btnp(pyxel.KEY_U):
                self.horizon_y -= 10
                self._recompute_depth_bounds()
            if pyxel.btnp(pyxel.KEY_J):
                self.horizon_y = min(-20, self.horizon_y + 10)
                self._recompute_depth_bounds()

            # Pause toggle (Space)
            if pyxel.btnp(pyxel.KEY_SPACE):
                self.is_paused = not self.is_paused

            # Atmospheric mode toggle (P)
            if pyxel.btnp(pyxel.KEY_P):
                self.scattering_mode = (self.scattering_mode + 1) % 3

            # Screenshot capture (C)
            if pyxel.btnp(pyxel.KEY_C):
                pyxel.screenshot(f"screenshot_dunes_frame_{int(self.dist)}.png")

            # Quit (Q or Esc)
            if pyxel.btnp(pyxel.KEY_Q) or pyxel.btnp(pyxel.KEY_ESCAPE):
                pyxel.quit()

        if not self.is_paused:
            self.dist += self.drift_speed

    def render_dunes(
        self,
        pyxel_mod,
        cam_x: float,
        dist: float,
        is_greed: bool = False,
    ):
        """Render continuous layered sand dunes from back to front.

        TOPOLOGY ENGINE:
          - Constructs layered polygons from back to front (distal to proximal).
          - No explicit stroke lines; structural forms defined entirely via negative space.
          - Y-axis coordinates projected converging at supra-canvas horizon_y.
          - Modulates translation velocity and amplitude inversely against Z-depth.
        SHADOW MAPPING:
          - Localized vertical linear gradients within sequential wave geometries.
          - Low-luminosity superior bounding coordinate, high-luminosity inferior.
        ATMOSPHERIC SCATTERING:
          - Global luminosity scalar linked to Z-depth.
          - Distal layers bleach into ambient desert haze; proximal layers retain full saturation.
        """
        # Collect active depth layers
        layers: List[Tuple[float, int]] = []
        u_range = self.u_max - self.u_min
        for k in range(self.num_layers):
            u = self.u_min + ((k * self.step_u + dist * SPEED_U) % u_range)
            y_base = self.horizon_y + 1.0 / u
            layers.append((y_base, k))

        # Sort back-to-front (distal/top to proximal/bottom)
        layers.sort(key=lambda item: item[0])

        x_samples = list(range(0, self.screen_w + SAMPLE_STEP_X, SAMPLE_STEP_X))
        curve_profiles = []

        total_span_y = float(self.screen_h - self.horizon_y)

        for y_base, k in layers:
            # Normalized proximity scalar s: 0.0 at horizon (distal), 1.0 at canvas bottom (proximal)
            s = max(0.0, min(1.0, (y_base - self.horizon_y) / total_span_y))

            # Amplitude scales with proximity: proximal has maximum amplitude; distal has minimum
            amp = MAX_AMPLITUDE * (s ** 1.35)

            # Spatial frequency scales inversely: distal layers have dense fine ripples; proximal have broad waves
            k1 = 0.007 + 0.010 * (1.0 - s)
            k2 = 0.016 + 0.018 * (1.0 - s)
            k3 = 0.035 + 0.025 * (1.0 - s)

            phi1 = k * 2.39996 + 0.4
            phi2 = k * 4.12345 + 1.1
            phi3 = k * 1.71828

            y_curve: Dict[int, int] = {}
            for x in x_samples:
                xw = cam_x + x
                # Asymmetric compound harmonic wave (windward dune face)
                w1 = math.sin(k1 * xw + phi1)
                w2 = math.sin(k2 * xw + phi2) * 0.38
                w3 = math.cos(k3 * xw + phi3) * 0.14
                y_curve[x] = int(y_base - amp * (w1 + w2 + w3))

            curve_profiles.append((y_base, s, k, y_curve))

        # Draw layers back-to-front (Painter's algorithm; forms defined purely by negative space)
        num_profiles = len(curve_profiles)
        for i in range(num_profiles):
            y_base, s, k, y_curve = curve_profiles[i]
            next_curve = curve_profiles[i + 1][3] if (i + 1 < num_profiles) else None

            for x in x_samples:
                y_top = max(0, min(self.screen_h, y_curve[x]))
                y_bot = self.screen_h if next_curve is None else max(0, min(self.screen_h, next_curve[x]))

                if y_bot <= y_top:
                    continue

                span = y_bot - y_top

                # SHADOW MAPPING & ATMOSPHERIC SCATTERING
                # Select palette triad: (superior shadow, mid-slope body, inferior sunlit highlight)
                if is_greed:
                    # Greed / Blood-Dune apocalyptic state
                    if s > 0.60:
                        c_top, c_mid, c_bot = 0, 2, 8
                        t1 = int(y_top + span * 0.25)
                        t2 = int(y_top + span * 0.65)
                    elif s > 0.32:
                        c_top, c_mid, c_bot = 2, 8, 14
                        t1 = int(y_top + span * 0.28)
                        t2 = int(y_top + span * 0.70)
                    else:
                        c_top, c_mid, c_bot = 8, 14, 15
                        t1 = int(y_top + span * 0.34)
                        t2 = int(y_top + span * 0.74)
                elif self.scattering_mode == 1:
                    # High Noon Sun bleaching
                    if s > 0.60:
                        c_top, c_mid, c_bot = 9, 10, 15
                        t1 = int(y_top + span * 0.20)
                        t2 = int(y_top + span * 0.60)
                    else:
                        c_top, c_mid, c_bot = 10, 15, 7
                        t1 = int(y_top + span * 0.30)
                        t2 = int(y_top + span * 0.70)
                else:
                    # Standard Desert Haze:
                    # Proximal layers retain full saturation (deep shadow 4, amber 9, gold 10)
                    # Distal layers bleach towards high-luminosity atmospheric threshold (7, 15)
                    if s > 0.60:
                        c_top, c_mid, c_bot = 4, 9, 10
                        t1 = int(y_top + span * 0.22)
                        t2 = int(y_top + span * 0.62)
                    elif s > 0.32:
                        c_top, c_mid, c_bot = 9, 10, 15
                        t1 = int(y_top + span * 0.26)
                        t2 = int(y_top + span * 0.68)
                    else:
                        c_top, c_mid, c_bot = 10, 15, 7
                        t1 = int(y_top + span * 0.32)
                        t2 = int(y_top + span * 0.72)

                # Zone 1: Superior bounding crest (shadow mapping)
                if t1 > y_top:
                    pyxel_mod.rect(x, y_top, SAMPLE_STEP_X, t1 - y_top, c_top)
                # Zone 2: Mid-slope body
                if t2 > t1:
                    pyxel_mod.rect(x, t1, SAMPLE_STEP_X, t2 - t1, c_mid)
                # Zone 3: Inferior bounding base (sunlit highlight)
                if y_bot > t2:
                    pyxel_mod.rect(x, t2, SAMPLE_STEP_X, y_bot - t2, c_bot)

    def draw(self):
        """Render complete landscape frame."""
        # Sky background matches atmospheric bleaching threshold
        pyxel.cls(15 if self.scattering_mode != 1 else 7)

        # Render layered negative-space dunes
        self.render_dunes(pyxel, self.cam_x, self.dist)

        # HUD overlay (interactive instructions)
        if not self.headless:
            pyxel.rect(10, 10, 580, 50, 0)
            pyxel.rectb(10, 10, 580, 50, 10)
            pyxel.text(18, 16, "CONTINUOUS 2D PROCEDURAL SAND DUNES LANDSCAPE", 10)
            pyxel.text(18, 28, f"HORIZON Y: {self.horizon_y}px | SPEED: {self.drift_speed:.1f} | CAM X: {int(self.cam_x)} | MODE: {self.scattering_mode}", 7)
            pyxel.text(18, 40, "[A/D] PAN CAMERA   [W/S] SPEED   [U/J] HORIZON   [P] HAZE MODE   [C] SNAP", 9)


def run_standalone():
    parser = argparse.ArgumentParser(description="Continuous 2D Procedural Sand Dunes Landscape Simulator")
    parser.add_argument("--headless", action="store_true", help="Run headlessly for smoke testing and screenshot export")
    parser.add_argument("--frames", type=int, default=30, help="Number of frames to simulate in headless mode")
    parser.add_argument("--output", type=str, default="screenshot_sand_dunes.png", help="Output path for headless screenshot")
    args = parser.parse_args()

    landscape = SandDunesLandscape(headless=args.headless)

    if args.headless:
        pyxel.init(SCREEN_WIDTH, SCREEN_HEIGHT, headless=True)
        for _ in range(args.frames):
            landscape.update()
        landscape.draw()
        pyxel.screenshot(args.output)
        print(f"Smoke test successful: {args.frames} frames rendered. Screenshot saved to {args.output}")
        sys.exit(0)
    else:
        pyxel.init(SCREEN_WIDTH, SCREEN_HEIGHT, title="Procedural Sand Dunes Landscape - PyWeek 42", fps=30)
        pyxel.run(landscape.update, landscape.draw)


if __name__ == "__main__":
    run_standalone()
