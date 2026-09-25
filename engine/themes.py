"""20 Divergent Aesthetic Themes for Grain of Doubt (PyWeek 42).

Provides full procedural background renderers, harmonious entity palettes,
and theme registry for real-time switching via comma (',') and period ('.') in Dev Mode.
"""
import math
from dataclasses import dataclass
from typing import Callable, List, Optional
from engine.font5x7 import draw_text_5x7


@dataclass
class SandPalette:
    body: int
    border: int
    glint: int
    shadow: int
    fat_body: int
    fat_border: int
    fat_glint: int


@dataclass
class ShardPalette:
    facet: int
    border: int
    glint: int
    shadow: int
    fat_facet: int
    fat_border: int


@dataclass
class HourglassPalette:
    caps: int
    cap_hl: int
    cap_rivet: int
    glass_walls: int
    waist_neck: int
    sand_a: int
    sand_b: int
    shadow: int


@dataclass
class KairosPalette:
    modal_bg: int              # Modal window background
    dimmer: int                # Full-screen ambient dimmer backdrop
    border_outer: int          # Outer border line
    border_inner: int          # Inner border line
    header_title: int          # "KAIROS CIRCUIT BREAKER" color
    header_sub: int            # "BORROW YOUR TIME" color
    timer_bar_bg: int          # Countdown bar gutter background
    timer_bar_fill: int        # Countdown bar fill color (before urgency flash)
    timer_bar_border: int      # Countdown bar border
    card_bg: int               # Non-selected card background
    card_bg_selected: int      # Selected card background
    card_border: int           # Non-selected card border
    card_border_selected: int  # Selected card border
    badge_bg: int              # Badge background
    badge_text: int            # Badge text color
    badge_bg_selected: int     # Selected badge background
    badge_text_selected: int   # Selected badge text color
    selected_btn_bg: int       # Bottom "SELECTED" button background
    selected_btn_text: int     # Bottom "SELECTED" button text color
    sin_title: int             # Sin title text color
    sin_title_selected: int    # Sin title text color when selected
    level_text: int            # "LEVEL: K" color
    divider: int               # Visual divider line color
    pro_label: int             # "PRO (NOW):" label color
    pro_text: int              # Boon description text color
    con_label: int             # "CON (FOREVER):" label color
    con_text: int              # Curse description text color
    footer_text: int           # "STEER LEFT OR RIGHT TO SELECT" color
    footer_warn: int           # "CHOOSE OR DIE: 2.0s TIME LIMIT" color


DEFAULT_KAIROS_PALETTE = KairosPalette(
    modal_bg=0,
    dimmer=0,
    border_outer=8,
    border_inner=2,
    header_title=7,
    header_sub=8,
    timer_bar_bg=0,
    timer_bar_fill=10,
    timer_bar_border=6,
    card_bg=1,
    card_bg_selected=5,
    card_border=1,
    card_border_selected=6,
    badge_bg=1,
    badge_text=7,
    badge_bg_selected=8,
    badge_text_selected=7,
    selected_btn_bg=10,
    selected_btn_text=0,
    sin_title=7,
    sin_title_selected=10,
    level_text=9,
    divider=2,
    pro_label=11,
    pro_text=7,
    con_label=8,
    con_text=8,
    footer_text=7,
    footer_warn=8,
)


@dataclass
class Theme:
    id: int
    name: str
    clear_color: int
    greed_clear_color: int
    sand: SandPalette
    shard: ShardPalette
    hourglass: HourglassPalette
    render_bg: Callable[..., None]
    kairos: Optional[KairosPalette] = None
    is_reader_mode: bool = False

    def get_clear_color(self, greed_active: bool) -> int:
        return self.greed_clear_color if greed_active else self.clear_color

    def get_kairos_palette(self) -> KairosPalette:
        return self.kairos if self.kairos is not None else DEFAULT_KAIROS_PALETTE

    def render(self, pyxel_mod, cam_x: int, prog: float, dist: int, screen_w: int = 600, screen_h: int = 800, is_greed: bool = False, telemetry: Optional[dict] = None):
        if self.render_bg and pyxel_mod:
            try:
                self.render_bg(pyxel_mod, cam_x, prog, dist, screen_w, screen_h, is_greed, telemetry=telemetry)
            except TypeError:
                self.render_bg(pyxel_mod, cam_x, prog, dist, screen_w, screen_h, is_greed)


# =============================================================================
# PROCEDURAL BACKGROUND RENDERERS FOR ALL 20 THEMES
# =============================================================================

def bg_sand_dunes_landscape(pyxel, cam_x: int, prog: float, dist: int, screen_w: int, screen_h: int, is_greed: bool, telemetry: Optional[dict] = None):
    """Continuous 2D procedural landscape of undulating sand dunes.
    Topology Engine: Layered negative space curves, supra-canvas horizon projection, continuous upward perspective motion.
    Shadow Mapping: Localized vertical linear gradients within wave geometries (dark superior crest, light inferior base).
    Atmospheric Scattering: Distal layers bleach optically into desaturated ambient haze, proximal retain saturation.
    Seamless Infinite Arena: Generates and draws directly across world coordinates matching cam_x.
    """
    horizon_y = -140
    C = 1200.0
    delta_z = 0.42
    speed_z = 0.003

    z_near = C / (screen_h - horizon_y + 120.0)  # ~ 1.132
    z_far = C / (-30.0 - horizon_y)              # ~ 10.91

    # As dist increases, travel_z increases, causing all dunes to move UP towards the horizon
    travel_z = dist * speed_z
    min_d = int(math.floor((travel_z - z_far) / delta_z))
    max_d = int(math.ceil((travel_z - z_near) / delta_z))

    layers = []
    for d in range(min_d, max_d + 1):
        z = travel_z - d * delta_z
        if z <= 0.2:
            continue
        y = horizon_y + C / z
        layers.append((d, z, y))

    # Sort layers back-to-front: furthest away (smallest Y, largest Z) to closest (largest Y, smallest Z)
    layers.sort(key=lambda item: item[2])

    step_x = 3
    start_x = int(cam_x // step_x) * step_x
    x_samples = list(range(start_x, start_x + screen_w + step_x, step_x))
    total_span_y = float(screen_h - horizon_y)

    num_layers = len(layers)
    warn_ratio = max(0.0, min(1.0, (prog - 0.85) / 0.15)) if prog > 0.85 else 0.0

    curve_profiles = []
    for idx, (d, z, y_persp) in enumerate(layers):
        if warn_ratio > 0.0:
            # Equalize gap between horizontal lines, destroying perspective illusion to show cosmic breakdown
            equal_step = total_span_y / float(max(1, num_layers))
            y_equal = horizon_y + (idx + 1) * equal_step
            y_base = y_persp * (1.0 - warn_ratio) + y_equal * warn_ratio
        else:
            y_base = y_persp

        s = max(0.0, min(1.0, (y_base - horizon_y) / total_span_y))
        # Flatten waves as warning intensifies towards straight equal-spaced horizontal lines
        amp = 90.0 * (s ** 1.30) * (1.0 - warn_ratio * 0.85)

        # Procedural pseudo-random hash derived from layer index d for organic, non-repeating dune waves
        h1 = (math.sin(d * 12.9898 + 78.233) * 43758.5453) % 1.0
        h2 = (math.sin(d * 93.9898 + 67.345) * 24634.6345) % 1.0
        h3 = (math.sin(d * 45.1234 + 19.876) * 31415.9265) % 1.0
        h4 = (math.sin(d * 71.5678 + 33.221) * 52718.2818) % 1.0

        # Randomized wave frequencies and phase offsets
        k1 = (0.005 + 0.004 * h1) + (0.008 + 0.004 * h2) * (1.0 - s)
        k2 = (0.012 + 0.008 * h3) + (0.015 + 0.006 * h4) * (1.0 - s)
        k3 = (0.026 + 0.012 * h2) + (0.020 + 0.010 * h1) * (1.0 - s)

        phi1 = (d * 2.39996 + h1 * 6.28) % (2 * math.pi)
        phi2 = (d * 4.12345 + h2 * 6.28) % (2 * math.pi)
        phi3 = (d * 1.71828 + h3 * 6.28) % (2 * math.pi)

        # Randomized harmonic weights and amplitude modulation
        w2_wt = 0.24 + 0.26 * h4
        w3_wt = 0.10 + 0.12 * h1
        amp_mod = 0.85 + 0.30 * h3

        y_curve = {}
        for xw in x_samples:
            w1 = math.sin(k1 * xw + phi1)
            w2 = math.sin(k2 * xw + phi2) * w2_wt
            w3 = math.cos(k3 * xw + phi3) * w3_wt
            y_curve[xw] = int(y_base - (amp * amp_mod) * (w1 + w2 + w3))

        curve_profiles.append((y_base, s, d, y_curve))

    num_profiles = len(curve_profiles)
    for i in range(num_profiles):
        y_base, s, d, y_curve = curve_profiles[i]
        next_curve = curve_profiles[i + 1][3] if (i + 1 < num_profiles) else None

        for xw in x_samples:
            y_top = max(0, min(screen_h, y_curve[xw]))
            y_bot = screen_h if next_curve is None else max(y_top, min(screen_h, next_curve[xw]))
            if y_bot <= y_top:
                continue

            span = y_bot - y_top

            if is_greed:
                if s > 0.60:
                    c_top, c_mid, c_bot = 0, 2, 8
                    t1 = int(y_top + span * 0.25)
                    t2 = int(y_top + span * 0.65)
                elif s > 0.30:
                    c_top, c_mid, c_bot = 2, 8, 14
                    t1 = int(y_top + span * 0.28)
                    t2 = int(y_top + span * 0.70)
                else:
                    c_top, c_mid, c_bot = 8, 14, 15
                    t1 = int(y_top + span * 0.34)
                    t2 = int(y_top + span * 0.74)
            elif prog > 0.85:
                # Kairos warning: blink to random colors in the 3 palette
                flicker_seed = (pyxel.frame_count // 2 + d * 7 + i * 3) & 0xFFFFFF
                p_pool = [8, 2, 14, 10, 7] if is_greed else [4, 9, 10, 15, 7]
                c_top = p_pool[flicker_seed % len(p_pool)]
                c_mid = p_pool[(flicker_seed * 3 + 1) % len(p_pool)]
                c_bot = p_pool[(flicker_seed * 7 + 2) % len(p_pool)]
                t1 = int(y_top + span * 0.33)
                t2 = int(y_top + span * 0.66)
            else:
                if s > 0.60:
                    c_top, c_mid, c_bot = 4, 9, 10
                    t1 = int(y_top + span * 0.22)
                    t2 = int(y_top + span * 0.62)
                elif s > 0.30:
                    c_top, c_mid, c_bot = 9, 10, 15
                    t1 = int(y_top + span * 0.26)
                    t2 = int(y_top + span * 0.68)
                else:
                    c_top, c_mid, c_bot = 10, 15, 7
                    t1 = int(y_top + span * 0.32)
                    t2 = int(y_top + span * 0.72)

            # Draw at world coordinate xw (Pyxel camera automatically offsets by cam_x to fill viewport)
            if t1 > y_top:
                pyxel.rect(xw, y_top, step_x, t1 - y_top, c_top)
            if t2 > t1:
                pyxel.rect(xw, t1, step_x, t2 - t1, c_mid)
            if y_bot > t2:
                pyxel.rect(xw, t2, step_x, y_bot - t2, c_bot)



def bg_skifree_sandfall(pyxel, cam_x: int, prog: float, dist: int, screen_w: int, screen_h: int, is_greed: bool, telemetry: Optional[dict] = None):
    """Theme 1: SkiFree Sandfall (Continuous 2D Procedural Sand Dunes Landscape)."""
    bg_sand_dunes_landscape(pyxel, cam_x, prog, dist, screen_w, screen_h, is_greed, telemetry=telemetry)



def bg_cosmic_chronometer(pyxel, cam_x: int, prog: float, dist: int, screen_w: int, screen_h: int, is_greed: bool):
    """Theme 2: Cosmic Chronometer (Celestial clockwork, astrolabe dials, depth isobars)."""
    col_ring = 2 if is_greed else (10 if prog > 0.85 else 9)
    col_gear = 0 if is_greed else 5
    col_line = 8 if is_greed else 1

    # Depth isobars drifting upward
    isobar_h = 100
    y_off = int(dist * 0.5) % isobar_h
    for base_y in range(-isobar_h, screen_h + isobar_h, isobar_h):
        sy = base_y - y_off
        pyxel.line(cam_x, sy, cam_x + screen_w, sy, col_line)
        for tx in range(cam_x + 10, cam_x + screen_w, 40):
            pyxel.line(tx, sy - 3, tx, sy + 3, col_gear)

    # Giant astrolabe circles centered across parallax coordinates
    gear_spacing = 380
    gear_x = int((cam_x + screen_w / 2) // gear_spacing) * gear_spacing
    gear_y = ((dist // 2) % 600)
    for r in (60, 140, 220):
        pyxel.circb(gear_x, screen_h // 2 - gear_y + 200, r, col_ring)
        # Gear teeth
        for ang in range(0, 360, 30):
            rad = math.radians(ang + dist * 0.02)
            px = int(gear_x + math.cos(rad) * r)
            py = int(screen_h // 2 - gear_y + 200 + math.sin(rad) * r)
            pyxel.pset(px, py, col_gear)


def bg_abyssal_hourglass(pyxel, cam_x: int, prog: float, dist: int, screen_w: int, screen_h: int, is_greed: bool):
    """Theme 3: Abyssal Hourglass (Massive fluted glass walls and refractive caustics)."""
    col_glass = 2 if is_greed else 6
    col_caustic = 8 if is_greed else 12

    # Left and right colossal fluted glass throat silhouettes
    for y in range(0, screen_h, 8):
        throat_w = int(70 + 40 * math.sin((y + dist * 0.6) * 0.008))
        # Left wall ribs
        pyxel.line(cam_x, y, cam_x + throat_w, y, col_glass)
        pyxel.pset(cam_x + throat_w, y, col_caustic)
        # Right wall ribs
        pyxel.line(cam_x + screen_w - throat_w, y, cam_x + screen_w, y, col_glass)
        pyxel.pset(cam_x + screen_w - throat_w, y, col_caustic)

    # Center falling refractive caustics
    for cx in range(cam_x + 100, cam_x + screen_w - 100, 36):
        sy = (cx * 17 - int(dist * 1.3)) % 400
        pyxel.line(cx, sy, cx + int(4 * math.sin(sy * 0.02)), sy + 30, col_caustic)


def bg_shattered_mirror_chasm(pyxel, cam_x: int, prog: float, dist: int, screen_w: int, screen_h: int, is_greed: bool):
    """Theme 4: Shattered Mirror Chasm (Floating reflective polygonal facets)."""
    col_plane = 2 if is_greed else 6
    col_edge = 8 if is_greed else 7
    col_shadow = 0 if is_greed else 1

    spacing = 160
    start_cx = int((cam_x - 50) // spacing) * spacing
    for gx in range(start_cx, cam_x + screen_w + 50, spacing):
        for gy in range(-spacing, screen_h + spacing, spacing):
            sy = gy - int(dist * 0.7) % spacing
            h = (gx * 374761393 ^ gy * 668265263) & 0xFFFFFF
            w = 25 + (h % 30)
            pyxel.tri(gx, sy - w, gx + w, sy + w, gx - w, sy + w // 2, col_plane)
            pyxel.line(gx, sy - w, gx + w, sy + w, col_edge)
            pyxel.line(gx + w, sy + w, gx - w, sy + w // 2, col_shadow)


def bg_magma_caldera(pyxel, cam_x: int, prog: float, dist: int, screen_w: int, screen_h: int, is_greed: bool):
    """Theme 5: Magma Caldera (Cascading lava rivers down black basalt pillars)."""
    col_lava = 10 if prog > 0.85 else 8
    col_glow = 9
    col_basalt = 0

    # Vertical basalt columns with glowing magma streams in cracks
    start_col = int((cam_x - 30) // 40) * 40
    for col_x in range(start_col, cam_x + screen_w + 30, 40):
        # Magma stream pouring in fissure
        spd = 1.25 + 0.25 * ((col_x * 97) % 5)
        for offset_y in (0, 160, 320):
            sy = (offset_y - int(dist * spd)) % 480 - 20
            pyxel.line(col_x, sy, col_x, sy + 35, col_lava)
            pyxel.pset(col_x - 1, sy + 5, col_glow)
            pyxel.pset(col_x + 1, sy + 15, col_glow)
        # Basalt pillar edge
        pyxel.line(col_x + 18, 0, col_x + 18, screen_h, 5)


def bg_cartographers_scroll(pyxel, cam_x: int, prog: float, dist: int, screen_w: int, screen_h: int, is_greed: bool):
    """Theme 6: Cartographer's Scroll (Sepia topographic contours and compass roses)."""
    col_ink = 0 if is_greed else 4
    col_grid = 2 if is_greed else 9

    # Topographic elevation curves scrolling upward
    spacing = 90
    y_off = int(dist * 0.45) % spacing
    for base_y in range(-spacing, screen_h + spacing, spacing):
        sy = base_y - y_off
        prev_x = cam_x
        prev_y = sy + int(18 * math.sin((cam_x + base_y) * 0.012))
        for x in range(cam_x + 8, cam_x + screen_w + 8, 8):
            cur_y = sy + int(18 * math.sin((x + base_y) * 0.012))
            pyxel.line(prev_x, prev_y, x, cur_y, col_ink)
            prev_x, prev_y = x, cur_y

    # Nautical grid latitude lines
    for gy in range(0, screen_h, 150):
        sy = (gy - int(dist * 0.2)) % screen_h
        pyxel.line(cam_x, sy, cam_x + screen_w, sy, col_grid)


def bg_pro_mode_dark(pyxel, cam_x: int, prog: float, dist: int, screen_w: int, screen_h: int, is_greed: bool):
    """Theme 7: Pro Mode High Contrast Dark (Functional CAD grid anchored to world coordinates)."""
    col_minor = 2 if is_greed else 1   # Faint navy / dark purple
    col_major = 8 if is_greed else 5   # Crisp dark grey

    step_minor = 25
    step_major = 100

    # Horizontal grid lines moving UP at 1.6x descent speed so hazards fall DOWN relative to background
    dist_bg = int(dist * 1.6)
    start_minor_wy = int((dist_bg - step_minor) // step_minor) * step_minor
    end_wy = dist_bg + screen_h + step_major
    for wy in range(start_minor_wy, end_wy + 1, step_minor):
        if wy % step_major != 0:
            sy = wy - dist_bg
            pyxel.line(cam_x - 40, sy, cam_x + screen_w + 40, sy, col_minor)

    start_major_wy = int((dist_bg - step_major) // step_major) * step_major
    for wy in range(start_major_wy, end_wy + 1, step_major):
        sy = wy - dist_bg
        pyxel.line(cam_x - 40, sy, cam_x + screen_w + 40, sy, col_major)

    # Vertical grid lines anchored to fixed world X coordinates (staying in place like monochrome blueprint)
    start_minor_x = int((cam_x - 50) // step_minor) * step_minor
    end_x = cam_x + screen_w + 50
    for x in range(start_minor_x, end_x + 1, step_minor):
        if x % step_major != 0:
            pyxel.line(x, 0, x, screen_h, col_minor)

    start_major_x = int((cam_x - 50) // step_major) * step_major
    for x in range(start_major_x, end_x + 1, step_major):
        pyxel.line(x, 0, x, screen_h, col_major)


def bg_copper_and_verdigris(pyxel, cam_x: int, prog: float, dist: int, screen_w: int, screen_h: int, is_greed: bool):
    """Theme 8: Copper & Verdigris (Weathered bronze plates and patinated teal seams)."""
    col_seam = 8 if is_greed else 3
    col_patina = 14 if is_greed else 11
    col_rivet = 0 if is_greed else 9

    # Massive riveted metal plates
    plate_w = 120
    plate_h = 160
    start_px = int((cam_x - 30) // plate_w) * plate_w
    y_off = int(dist * 0.6) % plate_h

    for px in range(start_px, cam_x + screen_w + 30, plate_w):
        pyxel.line(px, 0, px, screen_h, col_seam)
        for py in range(-plate_h, screen_h + plate_h, plate_h):
            sy = py - y_off
            pyxel.line(px, sy, px + plate_w, sy, col_seam)
            # Rivets on plate corner
            pyxel.pset(px + 4, sy + 4, col_rivet)
            pyxel.pset(px + 8, sy + 4, col_patina)


def bg_solar_flare(pyxel, cam_x: int, prog: float, dist: int, screen_w: int, screen_h: int, is_greed: bool):
    """Theme 9: Solar Flare (Blazing corona streams and solar prominence magnetic loops)."""
    col_corona = 8 if is_greed else 7
    col_loop = 2 if is_greed else 8

    # Blinding vertical coronal rays
    for i in range(14):
        rx = cam_x + (i * 45 + (int(dist * 0.1) % 45))
        sy = (i * 65 - int(dist * 1.4)) % screen_h
        pyxel.line(rx, sy, rx, sy + 45, col_corona)

    # Magnetic prominence loops
    loop_spacing = 220
    y_off = int(dist * 0.5) % loop_spacing
    for ly in range(-loop_spacing, screen_h + loop_spacing, loop_spacing):
        sy = ly - y_off
        pyxel.circb(cam_x + screen_w // 2, sy, 70, col_loop)


def bg_monochrome_blueprint(pyxel, cam_x: int, prog: float, dist: int, screen_w: int, screen_h: int, is_greed: bool):
    """Theme 10: Monochrome Blueprint (Technical drafting grid coordinates and dimensions)."""
    col_grid = 2 if is_greed else 12
    col_line = 8 if is_greed else 7

    # Precise isometric / cartesian drafting grid
    grid_sz = 40
    start_gx = int(cam_x // grid_sz) * grid_sz
    y_off = int(dist * 0.5) % grid_sz

    for gx in range(start_gx, cam_x + screen_w + grid_sz, grid_sz):
        pyxel.line(gx, 0, gx, screen_h, col_grid)

    for gy in range(-grid_sz, screen_h + grid_sz, grid_sz):
        sy = gy - y_off
        pyxel.line(cam_x, sy, cam_x + screen_w, sy, col_grid)
        # Drafting coordinate tick
        if gy % 120 == 0:
            pyxel.line(cam_x + 10, sy - 4, cam_x + 10, sy + 4, col_line)


def bg_pro_mode_light(pyxel, cam_x: int, prog: float, dist: int, screen_w: int, screen_h: int, is_greed: bool):
    """Theme 8: Pro Mode High Contrast Light (Clinical technical grid anchored to world coordinates)."""
    col_minor = 2 if is_greed else 6   # Light grey
    col_major = 8 if is_greed else 5   # Darker slate grey

    step_minor = 25
    step_major = 100

    # Horizontal grid lines moving UP at 1.6x descent speed so hazards fall DOWN relative to background
    dist_bg = int(dist * 1.6)
    start_minor_wy = int((dist_bg - step_minor) // step_minor) * step_minor
    end_wy = dist_bg + screen_h + step_major
    for wy in range(start_minor_wy, end_wy + 1, step_minor):
        if wy % step_major != 0:
            sy = wy - dist_bg
            pyxel.line(cam_x - 40, sy, cam_x + screen_w + 40, sy, col_minor)

    start_major_wy = int((dist_bg - step_major) // step_major) * step_major
    for wy in range(start_major_wy, end_wy + 1, step_major):
        sy = wy - dist_bg
        pyxel.line(cam_x - 40, sy, cam_x + screen_w + 40, sy, col_major)

    # Vertical grid lines anchored to fixed world X coordinates (staying in place like monochrome blueprint)
    start_minor_x = int((cam_x - 50) // step_minor) * step_minor
    end_x = cam_x + screen_w + 50
    for x in range(start_minor_x, end_x + 1, step_minor):
        if x % step_major != 0:
            pyxel.line(x, 0, x, screen_h, col_minor)

    start_major_x = int((cam_x - 50) // step_major) * step_major
    for x in range(start_major_x, end_x + 1, step_major):
        pyxel.line(x, 0, x, screen_h, col_major)


def bg_glacial_crevasse(pyxel, cam_x: int, prog: float, dist: int, screen_w: int, screen_h: int, is_greed: bool, telemetry: Optional[dict] = None):
    """Theme 5: Glacial Crevasse (Vertical meltwater torrents, sheer blue ice shelves, and crystalline frost motes)."""
    col_water = 8 if is_greed else 12
    col_shelf = 0 if is_greed else 6

    # Sheer vertical meltwater streams and ice spires
    start_x = int((cam_x - 30) // 30) * 30
    for wx in range(start_x, cam_x + screen_w + 30, 30):
        spd = 1.2 + 0.3 * ((wx * 31) % 4)
        sy = (wx * 19 - int(dist * spd)) % 360 - 20
        pyxel.line(wx, sy, wx, sy + 25, col_water)
        pyxel.pset(wx, sy + 26, 7)

    # Horizontal compressed firn ice strata
    for y in range(0, screen_h, 90):
        sy = (y - int(dist * 0.4)) % screen_h
        pyxel.line(cam_x, sy, cam_x + screen_w, sy, col_shelf)

    # Shimmering crystalline frost crystals
    for f_idx in range(16):
        f_seed = f_idx * 53 + 17
        fx = int(cam_x + (f_seed * 97) % screen_w)
        fy = int((f_seed * 71 - dist * 0.7) % screen_h)
        col_frost = 7 if (f_seed % 2 == 0) else 6
        pyxel.pset(fx, fy, col_frost)


def bg_retro_terminal_matrix(pyxel, cam_x: int, prog: float, dist: int, screen_w: int, screen_h: int, is_greed: bool):
    """Theme 13: Retro Terminal Matrix (Streaming green phosphor matrix rain and scanlines)."""
    col_code = 8 if is_greed else 11
    col_dim = 2 if is_greed else 3

    # Streaming vertical digital matrix columns
    start_c = int((cam_x - 20) // 18) * 18
    for cx in range(start_c, cam_x + screen_w + 20, 18):
        spd = 1.1 + 0.4 * ((cx * 47) % 5)
        sy = (cx * 13 - int(dist * spd)) % 300 - 15
        for seg in range(5):
            c = col_code if seg == 0 else col_dim
            pyxel.pset(cx, sy + seg * 4, c)

    # CRT scanlines
    for y in range(0, screen_h, 4):
        pyxel.line(cam_x, y, cam_x + screen_w, y, 0)


STEALTH_DARK_DOC = [
    "[ RFC-4209: SPECIFICATION OF TEMPORAL FLOW & STATE COMPACTION ]",
    "Status: Informational / Standards Track                      Category: Core Systems",
    "================================================================================",
    "",
    "1. INTRODUCTION AND MATHEMATICAL FOUNDATIONS",
    "The discrete temporal engine operates on non-inertial phase-space coordinates.",
    "Let S(t) = {x(t), y(t), v_x(t), v_y(t)} represent the state of an active grain.",
    "Under uniform gravitational drift g = 9.81 m/s^2, the Lagrangian reduces to:",
    "      L(x, v, t) = 0.5 * m * |v|^2 - U(x, t) + lambda(t) * Phi(x)",
    "where Phi(x) defines the hyperbolic throat boundaries of the vessel manifold.",
    "",
    "2. THE ENTROPY-MOMENTUM BALANCE LEMMA",
    "Theorem 2.1 (Entropic Debt Invariance):",
    "In any closed chronological continuum, borrowed time must be repaid with parity.",
    "Any cumulative phase variance Delta_T > 0 generates localized micro-fractures,",
    "projected into coordinate space as high-reflectance crystalline shards.",
    "",
    "Proof: Integrating total phase divergence over spatial domain Omega:",
    "      oint_{dOmega} J_temporal . n dA = -d/dt (System_Entropy)",
    "As d/dt(Entropy) approaches singularity, boundary elasticity drops to zero.",
    "",
    "3. PSEUDOCODE: GRANULAR TRAJECTORY PROPAGATION",
    "function propagate_grain(grain: StateVector, dt: float, field: FlowField):",
    "    grain.vy <- clamp(grain.vy + GRAVITY * dt, -TERMINAL_VELOCITY, TERMINAL_VELOCITY)",
    "    grain.vx <- grain.vx * DAMPING_FACTOR + grain.steering_force * LATERAL_IMPULSE",
    "    if detect_boundary_collision(grain.x, grain.y, field.neck_profile):",
    "        grain.vx <- -grain.vx * RESTITUTION_COEFFICIENT",
    "        emit_collision_telemetry(grain.id, grain.energy)",
    "    yield grain",
    "end function",
    "",
    "4. RELATIVISTIC KAIROS DILATION",
    "During Kairos events, subjective frame delta tau scales inversely with velocity.",
    "Sub-luminal drift provides granular resolution for precision lateral steering.",
    "Warning: Engaging Greed state triggers irreversible boundary decay cascades.",
    "",
    "5. EMPIRICAL BENCHMARK OBSERVATIONS",
    "Run Count: 10,000 automated cycles across 20 divergent topological domains.",
    "Mean survival depth: 1,428 units. Maximum debt repayment recorded: 99.8%.",
    "System status: NOMINAL. Memory footprint: 48.2 KB. Garbage collection: IDLE.",
    "Thread 0: RUNNING. Thread 1: STREAMING. Cache line hit rate: 99.4%.",
    "",
    "6. APPENDIX A: SYSTEM PARAMETERS & CONSTANTS",
    "  * GRAVITY_ACCEL   = 0.35 px/frame^2",
    "  * TERMINAL_FALL   = 8.50 px/frame",
    "  * RESTITUTION     = 0.42 (semi-elastic glass collision)",
    "  * SHARD_COLLISION = TRUE (instantaneous damage callback)",
    "  * GREED_MULTIPLIER= 2.00x score / 1.50x peril",
    "",
    "7. ERROR RECOVERY & BOUNDARY RESTORATION",
    "In event of catastrophic shard impact, state reverts to last stable checkpoint.",
    "Entropy penalty is amortized over remaining sand reservoir volume.",
    "All telemetry logs are mirrored to local persistent storage.",
    "",
    "--------------------------------------------------------------------------------",
    "// END OF RFC-4209 SECTION // CONTINUOUS SCROLL ACTIVE // ALL SYSTEMS NOMINAL //",
    "",
]


STEALTH_LIGHT_DOC = [
    "CHAPTER IV",
    "THE ARCHITECTURE OF BORROWED SECONDS",
    "",
    "The sand did not fall as water falls, with heedless and unbroken grace.",
    "It fell grain by solitary grain, each tiny sphere a fragment of an hour",
    "measured out and spent before the sun had risen over the eastern cliffs.",
    "In the dim stillness between two heartbeats, a single mote hesitated,",
    "catching the golden daylight that filtered through the narrow glass neck.",
    "",
    "To borrow time, as the old horologists of Alexandria were fond of noting,",
    "is to enter into an irrevocable covenant with the inevitable.",
    "One does not truly possess the hours stolen from tomorrow; one merely",
    "delays the reckoning, carrying the mounting weight upon slender glass walls.",
    "",
    "\"Look down,\" she whispered, leaning over the carved brass balustrade.",
    "\"Do you see the shards gleaming among the drifts of dark quartz dust?",
    "Those are the memories that could not survive the narrow constriction.\"",
    "Every glass must narrow at its waist; that is the law of its design.",
    "Without that choke, there would be no count, no rhythm, no urgency.",
    "There would be only eternity, flat and barren as an untracked dune.",
    "",
    "He watched the amber stream accelerate, pulled downward by an unyielding",
    "tether that no prayer could sever. The air in the chamber grew dense",
    "with the dry scent of powdered stone and ancient afternoon sunbeams.",
    "To steer through this torrent was not a matter of strength, but of quiet",
    "submission to the flow, leaning gently into the eddies where the sand",
    "parted, ever mindful of the sharp edges waiting in the shadow.",
    "",
    "A second struck. Then another. The count resumed its steady pace.",
    "And in that quiet descent, the debt was paid in full.",
    "",
    "- = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = -",
    "",
    "CHAPTER V",
    "THE WEIGHT OF THE LOWER CHAMBER",
    "",
    "When the upper bulb has emptied, the world does not end.",
    "It simply waits for a patient hand to turn the world upside down.",
    "Every fall is merely the prelude to the great inversion.",
    "Yet until that turning comes, the downward journey is all that remains.",
    "We gather the scattered grains, each one a promise kept against the dark.",
    "The walls tremble as the wind rises outside the tower.",
    "Still the glass holds. Still the amber river flows unbroken.",
    "",
    "The shadow of the gnomon shifts across the marble floor.",
    "No breath is wasted. Every grain recovered is an extra heartbeat.",
    "",
    "- = - = - = - = - = - = - = - = - = - = - = - = - = - = - = - = -",
    "",
    "[ Continued on page 86 ... ]",
    "",
]


ECCLESIASTES_3_KJV_LINES = [
    "To every thing there is a season, and a time to every",
    "purpose under the heaven: A time to be born, and a time to",
    "die; a time to plant, and a time to pluck up that which is",
    "planted; A time to kill, and a time to heal; a time to",
    "break down, and a time to build up; A time to weep, and a",
    "time to laugh; a time to mourn, and a time to dance; A",
    "time to cast away stones, and a time to gather stones",
    "together; a time to embrace, and a time to refrain from",
    "embracing; A time to get, and a time to lose; a time to",
    "keep, and a time to cast away; A time to rend, and a time",
    "to sew; a time to keep silence, and a time to speak; A",
    "time to love, and a time to hate; a time of war, and a",
    "time of peace. What profit hath he that worketh in that",
    "wherein he laboureth? I have seen the travail, which God",
    "hath given to the sons of men to be exercised in it.",
    "He hath made every thing beautiful in his time: also he",
    "hath set the world in their heart, so that no man can",
    "find out the work that God maketh from the beginning to",
    "the end. I know that there is no good in them, but for",
    "a man to rejoice, and to do good in his life. And also",
    "that every man should eat and drink, and enjoy the good",
    "of all his labour, it is the gift of God. I know that,",
    "whatsoever God doeth, it shall be for ever: nothing can",
    "be put to it, nor any thing taken from it: and God doeth",
    "it, that men should fear before him. That which hath",
    "been is now; and that which is to be hath already been;",
    "and God requireth that which is past. And moreover I saw",
    "under the sun the place of judgment, that wickedness was",
    "there; and the place of righteousness, that iniquity",
    "was there. I said in mine heart, God shall judge the",
    "righteous and the wicked: for there is a time there for",
    "every purpose and for every work. I said in mine heart",
    "concerning the estate of the sons of men, that God might",
    "manifest them, and that they might see that they",
    "themselves are beasts. For that which befalleth the sons",
    "of men befalleth beasts; even one thing befalleth them:",
    "as the one dieth, so dieth the other; yea, they have all",
    "one breath; so that a man hath no preeminence above a",
    "beast: for all is vanity. All go unto one place; all are",
    "of the dust, and all turn to dust again. Who knoweth the",
    "spirit of man that goeth upward, and the spirit of the",
    "beast that goeth downward to the earth? Wherefore I",
    "perceive that there is nothing better, than that a man",
    "should rejoice in his own works; for that is his portion:",
    "for who shall bring him to see what shall be after him?",
]


def draw_text_scaled_helper(pyxel, x: int, y: int, s: str, col: int, scale: int = 2, img_bank: int = 2):
    """Render scaled typography using dedicated 5x7 font engine."""
    if not s or pyxel is None:
        return
    draw_text_5x7(pyxel, x, y, s, col, scale=scale, img_bank=img_bank)


def render_reader_mode_text(
    pyxel,
    cam_x: int,
    prog: float,
    dist: int,
    screen_w: int,
    screen_h: int,
    is_greed: bool,
    col_ink: int,
    col_rule: int,
    telemetry: Optional[dict] = None,
):
    """Render Reader Mode with justified paragraphs, integrated telemetry, and 10s Chronos scroll."""
    margin_l = cam_x + 36
    margin_r = cam_x + screen_w - 36
    max_w = margin_r - margin_l

    # Margin border rules
    pyxel.line(margin_l - 4, 0, margin_l - 4, screen_h, col_rule)
    pyxel.line(margin_r + 4, 0, margin_r + 4, screen_h, col_rule)

    # Telemetry formatted seamlessly as scripture paragraph in KJV style (strictly no brackets)
    def _to_kjv_num(n: int) -> str:
        words = {
            0: "no", 1: "one", 2: "two", 3: "three", 4: "four",
            5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine",
            10: "ten", 11: "eleven", 12: "twelve"
        }
        return words.get(n, str(n))

    if telemetry:
        h = telemetry.get("hearts", 5)
        mh = telemetry.get("max_hearts", 5)
        sc = telemetry.get("score", 0)
        t_elapsed = telemetry.get("time_elapsed", 0.0)
        pacts = telemetry.get("pacts", [])
        pact_counts = telemetry.get("pact_counts", {})
        if not pact_counts and pacts:
            pact_counts = {p: 1 for p in pacts}
        pact_count = telemetry.get("pact_count", sum(pact_counts.values()) if pact_counts else len(pacts))

        if pact_count == 0:
            cov_clause = "and no faustian covenant hath yet been made."
        elif pact_count == 1:
            sin_name = list(pact_counts.keys())[0] if pact_counts else (pacts[0] if pacts else "Pride")
            cov_clause = f"and one faustian covenant hath been made, even one of {sin_name}."
        else:
            parts = [f"{_to_kjv_num(c)} of {s}" for s, c in pact_counts.items()]
            if len(parts) == 1:
                breakdown = parts[0]
            elif len(parts) == 2:
                breakdown = f"{parts[0]}, and {parts[1]}"
            else:
                breakdown = ", ".join(parts[:-1]) + f", and {parts[-1]}"
            cov_clause = f"and {_to_kjv_num(pact_count)} faustian covenants have been made, to wit, {breakdown}."

        telemetry_para = (
            f"The vessel holdeth {h} of {mh} measures intact, "
            f"and {sc} sacred grains reaped from the sands; "
            f"even as {t_elapsed:.1f} moments of borrowed time have now elapsed under heaven, "
            f"{cov_clause}"
        )
    else:
        telemetry_para = (
            "The vessel holdeth 5 of 5 measures intact, "
            "and 0 sacred grains reaped from the sands; "
            "even as 0.0 moments of borrowed time have now elapsed under heaven, "
            "and no faustian covenant hath yet been made."
        )

    # Full text divided into scriptural paragraphs with telemetry placed as the 3rd paragraph
    scripture_paras = [
        (
            "To every thing there is a season, and a time to every purpose under the heaven: "
            "A time to be born, and a time to die; a time to plant, and a time to pluck up that which is planted; "
            "A time to kill, and a time to heal; a time to break down, and a time to build up; "
            "A time to weep, and a time to laugh; a time to mourn, and a time to dance; "
            "A time to cast away stones, and a time to gather stones together; "
            "A time to embrace, and a time to refrain from embracing; "
            "A time to get, and a time to lose; a time to keep, and a time to cast away; "
            "A time to rend, and a time to sew; a time to keep silence, and a time to speak; "
            "A time to love, and a time to hate; a time of war, and a time of peace."
        ),
        (
            "What profit hath he that worketh in that wherein he laboureth? "
            "I have seen the travail, which God hath given to the sons of men to be exercised in it. "
            "He hath made every thing beautiful in his time: also he hath set the world in their heart, "
            "so that no man can find out the work that God maketh from the beginning to the end. "
            "I know that there is no good in them, but for a man to rejoice, and to do good in his life. "
            "And also that every man should eat and drink, and enjoy the good of all his labour, it is the gift of God."
        ),
        telemetry_para,
        (
            "I know that, whatsoever God doeth, it shall be for ever: nothing can be put to it, "
            "nor any thing taken from it: and God doeth it, that men should fear before him. "
            "That which hath been is now; and that which is to be hath already been; "
            "and God requireth that which is past. And moreover I saw under the sun the place of judgment, "
            "that wickedness was there; and the place of righteousness, that iniquity was there."
        ),
        (
            "I said in mine heart, God shall judge the righteous and the wicked: "
            "for there is a time there for every purpose and for every work. "
            "I said in mine heart concerning the estate of the sons of men, that God might manifest them, "
            "and that they might see that they themselves are beasts. For that which befalleth the sons of men "
            "befalleth beasts; even one thing befalleth them: as the one dieth, so dieth the other; yea, they have all "
            "one breath; so that a man hath no preeminence above a beast: for all is vanity. "
            "All go unto one place; all are of the dust, and all turn to dust again. "
            "Who knoweth the spirit of man that goeth upward, and the spirit of the beast that goeth downward to the earth? "
            "Wherefore I perceive that there is nothing better, than that a man should rejoice in his own works; "
            "for that is his portion: for who shall bring him to see what shall be after him?"
        ),
    ]

    # Wrap scripture paragraphs individually with dedicated fixed vertical layout
    line_h = 19
    para_gap = 10
    char_w = 12  # 5x7 typography at scale=2: 6px stride * 2 = 12px

    wrapped_paras = []
    for para in scripture_paras:
        words = para.split()
        curr_line = []
        curr_w = 0
        p_lines = []
        for w in words:
            wl = len(w) * char_w
            needed = wl if not curr_line else (char_w + wl)
            if curr_w + needed <= max_w:
                curr_line.append(w)
                curr_w += needed
            else:
                if curr_line:
                    p_lines.append((curr_line, False))
                curr_line = [w]
                curr_w = wl
        if curr_line:
            p_lines.append((curr_line, True))
        wrapped_paras.append(p_lines)

    # Completely stable, rock-solid vertical positioning:
    # Paragraphs 0, 1, 3, 4 are 100% stationary and never jiggle.
    # Paragraph 2 (dynamic telemetry info para) has a dedicated slot in the middle.
    # scroll_y is fixed at 0 so the entire page behaves like genuine stable digital e-reader ink.
    start_y = 20
    p0_h = len(wrapped_paras[0]) * line_h + para_gap
    p1_h = len(wrapped_paras[1]) * line_h + para_gap
    p2_slot = 4 * line_h + para_gap  # Dedicated 4-line slot for dynamic telemetry

    para_y_starts = [
        start_y,
        start_y + p0_h,
        start_y + p0_h + p1_h,
        start_y + p0_h + p1_h + p2_slot,
        start_y + p0_h + p1_h + p2_slot + len(wrapped_paras[3]) * line_h + para_gap,
    ]

    for p_idx, lines in enumerate(wrapped_paras):
        base_sy = para_y_starts[p_idx]
        for l_idx, (words, is_para_end) in enumerate(lines):
            sy = base_sy + l_idx * line_h
            if 0 <= sy <= screen_h - line_h:
                if is_para_end or len(words) <= 1:
                    # Left-aligned for final line of paragraph
                    wx = margin_l
                    for w in words:
                        draw_text_scaled_helper(pyxel, int(wx), sy, w, col_ink, scale=2)
                        wx += len(w) * char_w + char_w
                else:
                    # Fully justified alignment across margin_l to margin_r
                    tot_words_w = sum(len(w) * char_w for w in words)
                    extra = max_w - tot_words_w
                    gap = max(float(char_w), extra / float(max(1, len(words) - 1)))
                    curr_wx = float(margin_l)
                    for w in words:
                        draw_text_scaled_helper(pyxel, int(round(curr_wx)), sy, w, col_ink, scale=2)
                        curr_wx += len(w) * char_w + gap


def bg_reader_dark(pyxel, cam_x: int, prog: float, dist: int, screen_w: int, screen_h: int, is_greed: bool, telemetry: Optional[dict] = None):
    """Theme 14: Reader Mode E-Reader Dark (Ecclesiastes 3 KJV in dark OLED mode)."""
    col_ink = 8 if is_greed else 6     # Moonlight soft grey text (crimson in greed)
    col_rule = 8 if is_greed else 1    # Rule divider
    render_reader_mode_text(pyxel, cam_x, prog, dist, screen_w, screen_h, is_greed, col_ink, col_rule, telemetry)


def bg_reader_light(pyxel, cam_x: int, prog: float, dist: int, screen_w: int, screen_h: int, is_greed: bool, telemetry: Optional[dict] = None):
    """Theme 15: Reader Mode E-Reader Light (Ecclesiastes 3 KJV on warm cream e-reader paper)."""
    col_ink = 8 if is_greed else 0     # Pitch-black ink (crimson in greed)
    col_rule = 8 if is_greed else 4    # Sepia margin rule
    render_reader_mode_text(pyxel, cam_x, prog, dist, screen_w, screen_h, is_greed, col_ink, col_rule, telemetry)


# Aliases for backward compatibility
bg_stealth_dark = bg_reader_dark
bg_stealth_light = bg_reader_light



def bg_neon_noir_megacity(pyxel, cam_x: int, prog: float, dist: int, screen_w: int, screen_h: int, is_greed: bool):
    """Theme 16: Neon Noir Megacity (Rain-slicked skyscraper chasm with neon beams)."""
    col_neon = 8 if is_greed else 14
    col_laser = 8 if is_greed else 12
    col_rain = 6

    # Diagonal torrential rain vectors
    for i in range(30):
        rx = cam_x + ((i * 47 + int(dist * 0.2)) % screen_w)
        ry = (i * 28 - int(dist * 1.5)) % screen_h
        pyxel.line(rx, ry, rx - 3, ry + 12, col_rain)

    # Vertical neon skyscraper edge lights
    for nx in (cam_x + 60, cam_x + screen_w - 60):
        pyxel.line(nx, 0, nx, screen_h, col_neon)
        pyxel.line(nx + 1, 0, nx + 1, screen_h, col_laser)


def bg_liminal_vaporwave(pyxel, cam_x: int, prog: float, dist: int, screen_w: int, screen_h: int, is_greed: bool):
    """Theme 17: Liminal Vaporwave (Pastel wireframe perspective grids and sunset horizons)."""
    col_grid = 8 if is_greed else 12
    col_sun = 10 if prog > 0.85 else 1

    # Wireframe grid lines rushing towards horizon
    grid_spacing = 50
    y_off = int(dist * 0.8) % grid_spacing
    for gy in range(-grid_spacing, screen_h + grid_spacing, grid_spacing):
        sy = gy - y_off
        pyxel.line(cam_x, sy, cam_x + screen_w, sy, col_grid)

    for gx in range(cam_x, cam_x + screen_w, 40):
        pyxel.line(gx, 0, gx, screen_h, col_grid)


def bg_chalkboard_theory(pyxel, cam_x: int, prog: float, dist: int, screen_w: int, screen_h: int, is_greed: bool):
    """Theme 18: Chalkboard Theory (Dusty white physics equations, integral curves, tensors)."""
    col_chalk = 8 if is_greed else 7
    col_note = 2 if is_greed else 10

    # Integral curves and wave equations scrolling upward
    spacing = 130
    y_off = int(dist * 0.4) % spacing
    for base_y in range(-spacing, screen_h + spacing, spacing):
        sy = base_y - y_off
        for x in range(cam_x + 20, cam_x + screen_w - 20, 70):
            # Integral sign: curve up and down
            pyxel.line(x, sy - 15, x + 3, sy - 12, col_chalk)
            pyxel.line(x + 3, sy - 12, x + 3, sy + 12, col_chalk)
            pyxel.line(x + 3, sy + 12, x + 6, sy + 15, col_chalk)
            # Greek letter / notation tick
            pyxel.pset(x + 12, sy, col_note)


def bg_blood_moon_eclipse(pyxel, cam_x: int, prog: float, dist: int, screen_w: int, screen_h: int, is_greed: bool):
    """Theme 19: Blood Moon Eclipse (Ritual crimson halo rings and drifting eldritch ash)."""
    col_ring = 8
    col_ash = 7 if (pyxel.frame_count // 3) % 2 == 0 else 2

    # Concentric occult moon rings
    moon_x = cam_x + screen_w // 2
    moon_y = (dist // 2) % (screen_h * 2) - 100
    for r in (40, 80, 130, 190):
        pyxel.circb(moon_x, moon_y, r, col_ring)

    # Drifting ritual ash motes
    for i in range(20):
        ax = cam_x + ((i * 59 + int(dist * 0.1)) % screen_w)
        ay = (i * 41 - int(dist * 1.1)) % screen_h
        pyxel.pset(ax, ay, col_ash)


def bg_zen_ink_wash(pyxel, cam_x: int, prog: float, dist: int, screen_w: int, screen_h: int, is_greed: bool):
    """Theme 20: Zen Ink Wash / Sumi-e (Calligraphic brushstrokes and mountain mist washes)."""
    col_ink = 0 if is_greed else 5
    col_seal = 0

    # Mountain ridges in monochrome wash
    spacing = 150
    y_off = int(dist * 0.4) % spacing
    for base_y in range(-spacing, screen_h + spacing, spacing):
        sy = base_y - y_off
        prev_x = cam_x
        prev_y = sy + int(28 * math.sin((cam_x + base_y) * 0.007))
        for x in range(cam_x + 6, cam_x + screen_w + 6, 6):
            cur_y = sy + int(28 * math.sin((x + base_y) * 0.007))
            pyxel.line(prev_x, prev_y, x, cur_y, col_ink)
            prev_x, prev_y = x, cur_y

    # Red seal stamp
    seal_y = (dist // 2) % 400
    pyxel.rectb(cam_x + screen_w - 40, seal_y, 16, 16, col_seal)
    pyxel.pset(cam_x + screen_w - 32, seal_y + 8, col_seal)


# =============================================================================
# KAIROS PALETTES FOR ALL 20 THEMES
# =============================================================================

KAIROS_SKIFREE_SANDFALL = KairosPalette(
    modal_bg=4, dimmer=4, border_outer=10, border_inner=9,
    header_title=15, header_sub=10,
    timer_bar_bg=4, timer_bar_fill=10, timer_bar_border=9,
    card_bg=4, card_bg_selected=4, card_border=9, card_border_selected=10,
    badge_bg=9, badge_text=0, badge_bg_selected=10, badge_text_selected=0,
    selected_btn_bg=10, selected_btn_text=0,
    sin_title=10, sin_title_selected=7, level_text=15, divider=9,
    pro_label=10, pro_text=7, con_label=8, con_text=15,
    footer_text=7, footer_warn=8,
)

KAIROS_COSMIC_CHRONOMETER = KairosPalette(
    modal_bg=1, dimmer=1, border_outer=12, border_inner=5,
    header_title=7, header_sub=12,
    timer_bar_bg=0, timer_bar_fill=12, timer_bar_border=7,
    card_bg=0, card_bg_selected=5, card_border=1, card_border_selected=12,
    badge_bg=1, badge_text=12, badge_bg_selected=12, badge_text_selected=1,
    selected_btn_bg=12, selected_btn_text=1,
    sin_title=7, sin_title_selected=10, level_text=12, divider=1,
    pro_label=12, pro_text=7, con_label=8, con_text=14,
    footer_text=7, footer_warn=12,
)

KAIROS_ABYSSAL_HOURGLASS = KairosPalette(
    modal_bg=0, dimmer=0, border_outer=6, border_inner=1,
    header_title=7, header_sub=12,
    timer_bar_bg=1, timer_bar_fill=12, timer_bar_border=6,
    card_bg=1, card_bg_selected=5, card_border=1, card_border_selected=6,
    badge_bg=1, badge_text=6, badge_bg_selected=6, badge_text_selected=0,
    selected_btn_bg=6, selected_btn_text=0,
    sin_title=7, sin_title_selected=12, level_text=6, divider=1,
    pro_label=12, pro_text=7, con_label=8, con_text=6,
    footer_text=6, footer_warn=12,
)

KAIROS_SHATTERED_MIRROR_CHASM = KairosPalette(
    modal_bg=2, dimmer=2, border_outer=14, border_inner=13,
    header_title=7, header_sub=14,
    timer_bar_bg=2, timer_bar_fill=14, timer_bar_border=7,
    card_bg=13, card_bg_selected=2, card_border=7, card_border_selected=14,
    badge_bg=2, badge_text=7, badge_bg_selected=14, badge_text_selected=0,
    selected_btn_bg=14, selected_btn_text=0,
    sin_title=7, sin_title_selected=10, level_text=14, divider=13,
    pro_label=12, pro_text=7, con_label=8, con_text=14,
    footer_text=7, footer_warn=14,
)

KAIROS_MAGMA_CALDERA = KairosPalette(
    modal_bg=0, dimmer=0, border_outer=8, border_inner=9,
    header_title=10, header_sub=9,
    timer_bar_bg=0, timer_bar_fill=9, timer_bar_border=8,
    card_bg=2, card_bg_selected=4, card_border=8, card_border_selected=10,
    badge_bg=8, badge_text=10, badge_bg_selected=8, badge_text_selected=10,
    selected_btn_bg=10, selected_btn_text=0,
    sin_title=10, sin_title_selected=7, level_text=9, divider=8,
    pro_label=9, pro_text=10, con_label=8, con_text=9,
    footer_text=9, footer_warn=8,
)

KAIROS_CARTOGRAPHERS_SCROLL = KairosPalette(
    modal_bg=15, dimmer=4, border_outer=4, border_inner=9,
    header_title=4, header_sub=8,
    timer_bar_bg=7, timer_bar_fill=9, timer_bar_border=4,
    card_bg=7, card_bg_selected=15, card_border=4, card_border_selected=9,
    badge_bg=4, badge_text=15, badge_bg_selected=8, badge_text_selected=15,
    selected_btn_bg=8, selected_btn_text=15,
    sin_title=4, sin_title_selected=8, level_text=9, divider=4,
    pro_label=3, pro_text=4, con_label=8, con_text=4,
    footer_text=4, footer_warn=8,
)

KAIROS_PRO_MODE_DARK = KairosPalette(
    modal_bg=0, dimmer=0, border_outer=7, border_inner=5,
    header_title=7, header_sub=10,
    timer_bar_bg=0, timer_bar_fill=10, timer_bar_border=7,
    card_bg=0, card_bg_selected=5, card_border=5, card_border_selected=7,
    badge_bg=0, badge_text=7, badge_bg_selected=10, badge_text_selected=0,
    selected_btn_bg=10, selected_btn_text=0,
    sin_title=7, sin_title_selected=10, level_text=10, divider=5,
    pro_label=11, pro_text=7, con_label=8, con_text=7,
    footer_text=7, footer_warn=10,
)

KAIROS_PRO_MODE_LIGHT = KairosPalette(
    modal_bg=7, dimmer=5, border_outer=0, border_inner=5,
    header_title=0, header_sub=8,
    timer_bar_bg=6, timer_bar_fill=0, timer_bar_border=0,
    card_bg=7, card_bg_selected=6, card_border=0, card_border_selected=8,
    badge_bg=0, badge_text=7, badge_bg_selected=0, badge_text_selected=7,
    selected_btn_bg=0, selected_btn_text=7,
    sin_title=0, sin_title_selected=8, level_text=0, divider=5,
    pro_label=3, pro_text=0, con_label=8, con_text=0,
    footer_text=0, footer_warn=8,
)

KAIROS_COPPER_VERDIGRIS = KairosPalette(
    modal_bg=4, dimmer=4, border_outer=11, border_inner=9,
    header_title=10, header_sub=11,
    timer_bar_bg=4, timer_bar_fill=10, timer_bar_border=11,
    card_bg=3, card_bg_selected=4, card_border=11, card_border_selected=10,
    badge_bg=3, badge_text=11, badge_bg_selected=10, badge_text_selected=0,
    selected_btn_bg=10, selected_btn_text=0,
    sin_title=10, sin_title_selected=7, level_text=9, divider=11,
    pro_label=11, pro_text=7, con_label=8, con_text=9,
    footer_text=10, footer_warn=8,
)

KAIROS_SOLAR_FLARE = KairosPalette(
    modal_bg=8, dimmer=2, border_outer=10, border_inner=9,
    header_title=7, header_sub=10,
    timer_bar_bg=8, timer_bar_fill=10, timer_bar_border=7,
    card_bg=2, card_bg_selected=8, card_border=9, card_border_selected=10,
    badge_bg=8, badge_text=10, badge_bg_selected=10, badge_text_selected=0,
    selected_btn_bg=10, selected_btn_text=0,
    sin_title=10, sin_title_selected=7, level_text=9, divider=9,
    pro_label=10, pro_text=7, con_label=8, con_text=9,
    footer_text=10, footer_warn=7,
)

KAIROS_MONOCHROME_BLUEPRINT = KairosPalette(
    modal_bg=1, dimmer=1, border_outer=7, border_inner=12,
    header_title=7, header_sub=12,
    timer_bar_bg=1, timer_bar_fill=12, timer_bar_border=7,
    card_bg=0, card_bg_selected=1, card_border=12, card_border_selected=7,
    badge_bg=12, badge_text=1, badge_bg_selected=7, badge_text_selected=1,
    selected_btn_bg=7, selected_btn_text=1,
    sin_title=7, sin_title_selected=12, level_text=12, divider=12,
    pro_label=12, pro_text=7, con_label=7, con_text=6,
    footer_text=12, footer_warn=7,
)

KAIROS_GLACIAL_CREVASSE = KairosPalette(
    modal_bg=1, dimmer=1, border_outer=12, border_inner=6,
    header_title=7, header_sub=12,
    timer_bar_bg=1, timer_bar_fill=12, timer_bar_border=6,
    card_bg=5, card_bg_selected=1, card_border=6, card_border_selected=12,
    badge_bg=1, badge_text=12, badge_bg_selected=12, badge_text_selected=0,
    selected_btn_bg=12, selected_btn_text=0,
    sin_title=7, sin_title_selected=12, level_text=6, divider=6,
    pro_label=12, pro_text=7, con_label=8, con_text=6,
    footer_text=6, footer_warn=12,
)

KAIROS_RETRO_TERMINAL_MATRIX = KairosPalette(
    modal_bg=0, dimmer=0, border_outer=11, border_inner=3,
    header_title=11, header_sub=3,
    timer_bar_bg=0, timer_bar_fill=11, timer_bar_border=3,
    card_bg=0, card_bg_selected=3, card_border=3, card_border_selected=11,
    badge_bg=3, badge_text=11, badge_bg_selected=11, badge_text_selected=0,
    selected_btn_bg=11, selected_btn_text=0,
    sin_title=11, sin_title_selected=7, level_text=11, divider=3,
    pro_label=11, pro_text=7, con_label=8, con_text=11,
    footer_text=11, footer_warn=8,
)

KAIROS_READER_MODE_DARK = KairosPalette(
    modal_bg=0, dimmer=0, border_outer=6, border_inner=5,
    header_title=7, header_sub=6,
    timer_bar_bg=0, timer_bar_fill=6, timer_bar_border=5,
    card_bg=5, card_bg_selected=0, card_border=5, card_border_selected=6,
    badge_bg=5, badge_text=7, badge_bg_selected=6, badge_text_selected=0,
    selected_btn_bg=6, selected_btn_text=0,
    sin_title=7, sin_title_selected=10, level_text=6, divider=5,
    pro_label=6, pro_text=7, con_label=8, con_text=6,
    footer_text=6, footer_warn=8,
)

KAIROS_READER_MODE_LIGHT = KairosPalette(
    modal_bg=15, dimmer=5, border_outer=4, border_inner=5,
    header_title=0, header_sub=4,
    timer_bar_bg=7, timer_bar_fill=4, timer_bar_border=5,
    card_bg=7, card_bg_selected=15, card_border=5, card_border_selected=4,
    badge_bg=4, badge_text=7, badge_bg_selected=4, badge_text_selected=15,
    selected_btn_bg=4, selected_btn_text=15,
    sin_title=0, sin_title_selected=4, level_text=5, divider=5,
    pro_label=3, pro_text=0, con_label=8, con_text=0,
    footer_text=0, footer_warn=8,
)

KAIROS_NEON_NOIR_MEGACITY = KairosPalette(
    modal_bg=0, dimmer=0, border_outer=14, border_inner=12,
    header_title=12, header_sub=14,
    timer_bar_bg=0, timer_bar_fill=14, timer_bar_border=12,
    card_bg=1, card_bg_selected=2, card_border=12, card_border_selected=14,
    badge_bg=14, badge_text=0, badge_bg_selected=12, badge_text_selected=0,
    selected_btn_bg=12, selected_btn_text=0,
    sin_title=12, sin_title_selected=10, level_text=14, divider=12,
    pro_label=12, pro_text=7, con_label=14, con_text=8,
    footer_text=12, footer_warn=14,
)

KAIROS_LIMINAL_VAPORWAVE = KairosPalette(
    modal_bg=2, dimmer=2, border_outer=14, border_inner=12,
    header_title=7, header_sub=14,
    timer_bar_bg=2, timer_bar_fill=12, timer_bar_border=14,
    card_bg=13, card_bg_selected=2, card_border=14, card_border_selected=12,
    badge_bg=12, badge_text=0, badge_bg_selected=14, badge_text_selected=0,
    selected_btn_bg=14, selected_btn_text=0,
    sin_title=7, sin_title_selected=10, level_text=14, divider=12,
    pro_label=12, pro_text=7, con_label=14, con_text=10,
    footer_text=7, footer_warn=14,
)

KAIROS_CHALKBOARD_THEORY = KairosPalette(
    modal_bg=13, dimmer=5, border_outer=7, border_inner=6,
    header_title=7, header_sub=10,
    timer_bar_bg=5, timer_bar_fill=10, timer_bar_border=7,
    card_bg=5, card_bg_selected=13, card_border=6, card_border_selected=7,
    badge_bg=5, badge_text=7, badge_bg_selected=10, badge_text_selected=0,
    selected_btn_bg=10, selected_btn_text=0,
    sin_title=7, sin_title_selected=10, level_text=10, divider=6,
    pro_label=10, pro_text=7, con_label=8, con_text=7,
    footer_text=7, footer_warn=10,
)

KAIROS_BLOOD_MOON_ECLIPSE = KairosPalette(
    modal_bg=0, dimmer=0, border_outer=8, border_inner=2,
    header_title=7, header_sub=8,
    timer_bar_bg=0, timer_bar_fill=8, timer_bar_border=2,
    card_bg=2, card_bg_selected=0, card_border=8, card_border_selected=7,
    badge_bg=8, badge_text=7, badge_bg_selected=8, badge_text_selected=7,
    selected_btn_bg=8, selected_btn_text=7,
    sin_title=7, sin_title_selected=10, level_text=8, divider=8,
    pro_label=8, pro_text=7, con_label=8, con_text=9,
    footer_text=7, footer_warn=8,
)

KAIROS_ZEN_INK_WASH = KairosPalette(
    modal_bg=7, dimmer=5, border_outer=0, border_inner=5,
    header_title=0, header_sub=5,
    timer_bar_bg=15, timer_bar_fill=0, timer_bar_border=5,
    card_bg=15, card_bg_selected=7, card_border=0, card_border_selected=5,
    badge_bg=0, badge_text=7, badge_bg_selected=5, badge_text_selected=7,
    selected_btn_bg=0, selected_btn_text=7,
    sin_title=0, sin_title_selected=5, level_text=5, divider=5,
    pro_label=0, pro_text=0, con_label=5, con_text=0,
    footer_text=0, footer_warn=0,
)


def bg_pastel_sakura(pyxel, cam_x: int, prog: float, dist: int, screen_w: int, screen_h: int, is_greed: bool, telemetry: Optional[dict] = None):
    """Theme 9: Pastel Sakura (Cute, girly blossom drift with floating cherry petals, soft pastel clouds, and twinkling stars)."""
    # 1. Peaceful, non-epileptic Kairos countdown gradient over the final 2.0 seconds (prog >= 0.80).
    # Slowly transitions background from flat pink (14) into an organic vertical gradient:
    # Pink at top to earthy brown (4) at bottom.
    if prog > 0.80 and not is_greed:
        t_kairos = min(1.0, (prog - 0.80) / 0.20)
        grad_h = int(screen_h * 0.70 * t_kairos)
        start_gy = screen_h - grad_h
        for gy in range(start_gy, screen_h):
            pos = (gy - start_gy) / float(max(1, grad_h))  # 0.0 at top of gradient, 1.0 at bottom
            # Dither bands for ultra-smooth organic gradient without color banding or flashing
            if pos > 0.75:
                col = 4
            elif pos > 0.50:
                col = 4 if ((gy + cam_x) % 2 == 0) else 15
            elif pos > 0.25:
                col = 15 if ((gy + cam_x) % 2 == 0) else 14
            else:
                col = 14 if ((gy + cam_x) % 4 != 0) else 15
            pyxel.line(cam_x, gy, cam_x + screen_w, gy, col)

    # 2. Floating cherry blossom petals with organic sinusoidal sway and horizontal parallax
    num_petals = 28
    for i in range(num_petals):
        seed = i * 47 + 13
        speed = 0.45 + 0.35 * ((seed % 7) / 7.0)
        drift_amp = 16.0 + 10.0 * ((seed % 5) / 5.0)
        drift_freq = 0.035 + 0.02 * ((seed % 3) / 3.0)
        p_factor = 0.45 + 0.30 * ((seed % 4) / 4.0)

        base_x = (seed * 83) % (screen_w + 100) - 50
        sway = math.sin((dist * 0.04 + seed) * drift_freq) * drift_amp
        px = int(cam_x * p_factor + base_x + sway)

        # Petals drift upward relative to camera descent
        py = int((seed * 137 - dist * speed * 1.2) % (screen_h + 40)) - 20

        # Colors: soft white 7, pale peach 15, ruby 8, or gold 10
        c_petal = 7 if (seed % 3 == 0) else 15
        c_core = 8 if (seed % 2 == 0) else 14
        if is_greed:
            c_petal = 2
            c_core = 8

        # Draw cute petal droplet (cross / diamond shaped)
        pyxel.pset(px, py, c_core)
        pyxel.pset(px - 1, py, c_petal)
        pyxel.pset(px + 1, py, c_petal)
        pyxel.pset(px, py - 1, c_petal)
        pyxel.pset(px, py + 1, c_petal)
        pyxel.pset(px - 1, py - 1, 7)

    # 3. Twinkling fairy sparkles with horizontal parallax for clear lateral movement feedback
    for s_idx in range(16):
        s_seed = s_idx * 61 + 29
        p_star = 0.30 + 0.35 * ((s_idx % 5) / 5.0)
        sx = int(cam_x * p_star + (s_seed * 107) % screen_w)
        sy = int((s_seed * 79 - dist * 0.5) % screen_h)
        twinkle = (pyxel.frame_count // 6 + s_idx) % 4
        if twinkle == 0:
            pyxel.pset(sx, sy, 7)
        elif twinkle == 1:
            pyxel.pset(sx, sy, 10)
            pyxel.pset(sx + 1, sy, 7)
            pyxel.pset(sx - 1, sy, 7)
            pyxel.pset(sx, sy + 1, 7)
            pyxel.pset(sx - 1, sy, 7)
        elif twinkle == 2:
            pyxel.pset(sx, sy, 15)

    # 4. Soft breeze streaks
    for w_idx in range(4):
        wy = int((w_idx * 210 - dist * 0.8) % screen_h)
        col_wisp = 15 if (w_idx % 2 == 0) else 7
        if is_greed:
            col_wisp = 2
        pyxel.line(cam_x + 30, wy, cam_x + screen_w - 30, wy - 24, col_wisp)


# Kairos Palette for Theme 9 (Pastel Sakura):
# Uses purple (2) and brown (4) of sakura tree soil/branches instead of hard-to-read pink (14)
KAIROS_PASTEL_SAKURA = KairosPalette(
    modal_bg=4, dimmer=2, border_outer=10, border_inner=2,
    header_title=7, header_sub=10,
    timer_bar_bg=2, timer_bar_fill=10, timer_bar_border=7,
    card_bg=2, card_bg_selected=2, card_border=10, card_border_selected=7,
    badge_bg=4, badge_text=10, badge_bg_selected=2, badge_text_selected=7,
    selected_btn_bg=10, selected_btn_text=0,
    sin_title=7, sin_title_selected=10, level_text=10, divider=10,
    pro_label=11, pro_text=7, con_label=8, con_text=10,
    footer_text=7, footer_warn=10,
)


# =============================================================================
# THEME REGISTRY
# =============================================================================

ALL_THEMES: List[Theme] = [
    # 0. Dunes in the Cosmic Hourglass (formerly Desert Dunes / SkiFree Sandfall)
    Theme(
        id=0,
        name="DUNES IN THE COSMIC HOURGLASS",
        clear_color=15,
        greed_clear_color=2,
        sand=SandPalette(body=10, border=4, glint=7, shadow=4, fat_body=10, fat_border=4, fat_glint=7),
        shard=ShardPalette(facet=6, border=0, glint=7, shadow=4, fat_facet=6, fat_border=0),
        hourglass=HourglassPalette(caps=4, cap_hl=9, cap_rivet=10, glass_walls=6, waist_neck=7, sand_a=10, sand_b=9, shadow=4),
        render_bg=bg_sand_dunes_landscape,
        kairos=KAIROS_SKIFREE_SANDFALL,
    ),
    # 1. Pro Mode Light
    Theme(
        id=1,
        name="PRO MODE LIGHT",
        clear_color=7,
        greed_clear_color=7,
        sand=SandPalette(body=9, border=0, glint=10, shadow=0, fat_body=9, fat_border=0, fat_glint=10),
        shard=ShardPalette(facet=0, border=0, glint=5, shadow=0, fat_facet=0, fat_border=0),
        hourglass=HourglassPalette(caps=0, cap_hl=5, cap_rivet=0, glass_walls=1, waist_neck=0, sand_a=9, sand_b=10, shadow=5),
        render_bg=bg_pro_mode_light,
        kairos=KAIROS_PRO_MODE_LIGHT,
    ),
    # 2. Pro Mode Dark
    Theme(
        id=2,
        name="PRO MODE DARK",
        clear_color=0,
        greed_clear_color=0,
        sand=SandPalette(body=10, border=0, glint=7, shadow=0, fat_body=10, fat_border=0, fat_glint=7),
        shard=ShardPalette(facet=12, border=0, glint=7, shadow=0, fat_facet=12, fat_border=7),
        hourglass=HourglassPalette(caps=7, cap_hl=7, cap_rivet=0, glass_walls=12, waist_neck=7, sand_a=10, sand_b=7, shadow=0),
        render_bg=bg_pro_mode_dark,
        kairos=KAIROS_PRO_MODE_DARK,
    ),
    # 3. E-Reader Light
    Theme(
        id=3,
        name="E-READER LIGHT",
        clear_color=15,
        greed_clear_color=15,
        sand=SandPalette(body=9, border=4, glint=10, shadow=4, fat_body=9, fat_border=4, fat_glint=10),
        shard=ShardPalette(facet=8, border=4, glint=7, shadow=4, fat_facet=8, fat_border=0),
        hourglass=HourglassPalette(caps=4, cap_hl=9, cap_rivet=10, glass_walls=0, waist_neck=7, sand_a=9, sand_b=10, shadow=4),
        render_bg=bg_reader_light,
        kairos=KAIROS_READER_MODE_LIGHT,
        is_reader_mode=True,
    ),
    # 4. E-Reader Dark
    Theme(
        id=4,
        name="E-READER DARK",
        clear_color=0,
        greed_clear_color=0,
        sand=SandPalette(body=10, border=0, glint=7, shadow=0, fat_body=10, fat_border=0, fat_glint=7),
        shard=ShardPalette(facet=8, border=0, glint=7, shadow=0, fat_facet=8, fat_border=7),
        hourglass=HourglassPalette(caps=5, cap_hl=6, cap_rivet=7, glass_walls=6, waist_neck=12, sand_a=10, sand_b=7, shadow=0),
        render_bg=bg_reader_dark,
        kairos=KAIROS_READER_MODE_DARK,
        is_reader_mode=True,
    ),
    # 5. Glacial Crevasse (Replaced Monochrome Blueprint)
    Theme(
        id=5,
        name="GLACIAL CREVASSE",
        clear_color=1,
        greed_clear_color=0,
        sand=SandPalette(body=6, border=1, glint=7, shadow=5, fat_body=6, fat_border=1, fat_glint=7),
        shard=ShardPalette(facet=7, border=6, glint=12, shadow=5, fat_facet=7, fat_border=12),
        hourglass=HourglassPalette(caps=6, cap_hl=7, cap_rivet=12, glass_walls=7, waist_neck=12, sand_a=6, sand_b=7, shadow=5),
        render_bg=bg_glacial_crevasse,
        kairos=KAIROS_GLACIAL_CREVASSE,
    ),
    # 6. Magma Caldera
    Theme(
        id=6,
        name="MAGMA CALDERA",
        clear_color=0,
        greed_clear_color=2,
        sand=SandPalette(body=10, border=8, glint=7, shadow=0, fat_body=10, fat_border=8, fat_glint=7),
        shard=ShardPalette(facet=0, border=8, glint=7, shadow=8, fat_facet=0, fat_border=7),
        hourglass=HourglassPalette(caps=5, cap_hl=8, cap_rivet=10, glass_walls=8, waist_neck=7, sand_a=10, sand_b=8, shadow=0),
        render_bg=bg_magma_caldera,
        kairos=KAIROS_MAGMA_CALDERA,
    ),
    # 7. Retro Terminal Matrix
    Theme(
        id=7,
        name="RETRO TERMINAL MATRIX",
        clear_color=0,
        greed_clear_color=2,
        sand=SandPalette(body=11, border=0, glint=7, shadow=0, fat_body=11, fat_border=0, fat_glint=7),
        shard=ShardPalette(facet=3, border=0, glint=11, shadow=0, fat_facet=3, fat_border=7),
        hourglass=HourglassPalette(caps=3, cap_hl=11, cap_rivet=7, glass_walls=3, waist_neck=11, sand_a=11, sand_b=3, shadow=0),
        render_bg=bg_retro_terminal_matrix,
        kairos=KAIROS_RETRO_TERMINAL_MATRIX,
    ),
    # 8. Zen Ink Wash (Sumi-e)
    Theme(
        id=8,
        name="ZEN INK WASH (SUMI-E)",
        clear_color=7,
        greed_clear_color=0,
        sand=SandPalette(body=0, border=5, glint=7, shadow=5, fat_body=0, fat_border=5, fat_glint=7),
        shard=ShardPalette(facet=0, border=5, glint=7, shadow=5, fat_facet=0, fat_border=0),
        hourglass=HourglassPalette(caps=0, cap_hl=7, cap_rivet=5, glass_walls=5, waist_neck=0, sand_a=0, sand_b=5, shadow=5),
        render_bg=bg_zen_ink_wash,
        kairos=KAIROS_ZEN_INK_WASH,
    ),
    # 9. Pastel Sakura (Cute, girly pastel pink theme with pure leaf green sand)
    Theme(
        id=9,
        name="PASTEL SAKURA",
        clear_color=14,
        greed_clear_color=2,
        sand=SandPalette(body=11, border=3, glint=11, shadow=3, fat_body=11, fat_border=3, fat_glint=11),
        shard=ShardPalette(facet=8, border=7, glint=15, shadow=2, fat_facet=8, fat_border=7),
        hourglass=HourglassPalette(caps=7, cap_hl=15, cap_rivet=11, glass_walls=7, waist_neck=14, sand_a=11, sand_b=3, shadow=2),
        render_bg=bg_pastel_sakura,
        kairos=KAIROS_PASTEL_SAKURA,
    ),
]


def get_theme(index: int) -> Theme:
    """Return theme by modular index (0..9)."""
    return ALL_THEMES[index % len(ALL_THEMES)]
