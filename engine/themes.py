"""20 Divergent Aesthetic Themes for Grain of Doubt (PyWeek 42).

Provides full procedural background renderers, harmonious entity palettes,
and theme registry for real-time switching via comma (',') and period ('.') in Dev Mode.
"""
import math
from dataclasses import dataclass
from typing import Callable, List, Optional


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
class Theme:
    id: int
    name: str
    clear_color: int
    greed_clear_color: int
    sand: SandPalette
    shard: ShardPalette
    hourglass: HourglassPalette
    render_bg: Callable[..., None]
    is_reader_mode: bool = False

    def get_clear_color(self, greed_active: bool) -> int:
        return self.greed_clear_color if greed_active else self.clear_color

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
    Topology Engine: Layered negative space curves, supra-canvas horizon projection, inverse Z-depth velocity.
    Shadow Mapping: Localized vertical linear gradients within wave geometries (dark superior, light inferior).
    Atmospheric Scattering: Distal layers bleach optically into desaturated ambient haze, proximal retain saturation.
    """
    horizon_y = -140
    num_layers = 16
    u_min = 1.0 / (screen_h - horizon_y + 100)
    u_max = 1.0 / max(10, (25 - horizon_y))
    step_u = (u_max - u_min) / float(num_layers)
    u_range = u_max - u_min
    speed_u = 0.000006

    layers = []
    for k in range(num_layers):
        u = u_min + ((k * step_u + dist * speed_u) % u_range)
        y_base = horizon_y + 1.0 / u
        layers.append((y_base, k))

    layers.sort(key=lambda item: item[0])

    step_x = 2
    x_samples = list(range(0, screen_w + step_x, step_x))
    curve_profiles = []
    total_span_y = float(screen_h - horizon_y)

    for y_base, k in layers:
        s = max(0.0, min(1.0, (y_base - horizon_y) / total_span_y))
        amp = 85.0 * (s ** 1.35)

        k1 = 0.007 + 0.010 * (1.0 - s)
        k2 = 0.016 + 0.018 * (1.0 - s)
        k3 = 0.035 + 0.025 * (1.0 - s)

        phi1 = k * 2.39996 + 0.4
        phi2 = k * 4.12345 + 1.1
        phi3 = k * 1.71828

        y_curve = {}
        for x in x_samples:
            xw = cam_x + x
            w1 = math.sin(k1 * xw + phi1)
            w2 = math.sin(k2 * xw + phi2) * 0.38
            w3 = math.cos(k3 * xw + phi3) * 0.14
            y_curve[x] = int(y_base - amp * (w1 + w2 + w3))

        curve_profiles.append((y_base, s, k, y_curve))

    num_profiles = len(curve_profiles)
    for i in range(num_profiles):
        y_base, s, k, y_curve = curve_profiles[i]
        next_curve = curve_profiles[i + 1][3] if (i + 1 < num_profiles) else None

        for x in x_samples:
            y_top = max(0, min(screen_h, y_curve[x]))
            y_bot = screen_h if next_curve is None else max(0, min(screen_h, next_curve[x]))
            if y_bot <= y_top:
                continue

            span = y_bot - y_top

            if is_greed:
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
            elif prog > 0.85 and (pyxel.frame_count // 3) % 2 == 0:
                c_top, c_mid, c_bot = 9, 10, 7
                t1 = int(y_top + span * 0.20)
                t2 = int(y_top + span * 0.60)
            else:
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

            if t1 > y_top:
                pyxel.rect(x, y_top, step_x, t1 - y_top, c_top)
            if t2 > t1:
                pyxel.rect(x, t1, step_x, t2 - t1, c_mid)
            if y_bot > t2:
                pyxel.rect(x, t2, step_x, y_bot - t2, c_bot)


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
    """Theme 7: Pro Mode High Contrast Dark (Functional, static CAD grid, zero noise)."""
    col_minor = 2 if is_greed else 1   # Faint navy / dark purple
    col_major = 8 if is_greed else 5   # Crisp dark grey

    # Minor grid lines (every 25px) - completely static to screen back, not following descent
    for x in range(0, screen_w + 1, 25):
        if x % 100 != 0:
            pyxel.line(cam_x + x, 0, cam_x + x, screen_h, col_minor)
    for y in range(0, screen_h + 1, 25):
        if y % 100 != 0:
            pyxel.line(cam_x, y, cam_x + screen_w, y, col_minor)

    # Major grid lines (every 100px) - completely static to screen back
    for x in range(0, screen_w + 1, 100):
        pyxel.line(cam_x + x, 0, cam_x + x, screen_h, col_major)
    for y in range(0, screen_h + 1, 100):
        pyxel.line(cam_x, y, cam_x + screen_w, y, col_major)


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
    """Theme 8: Pro Mode High Contrast Light (Clinical technical grid, high luminance, pure functional)."""
    col_minor = 2 if is_greed else 6   # Light grey
    col_major = 8 if is_greed else 5   # Darker slate grey

    # Minor grid lines (every 25px) - completely static to screen back, not following descent
    for x in range(0, screen_w + 1, 25):
        if x % 100 != 0:
            pyxel.line(cam_x + x, 0, cam_x + x, screen_h, col_minor)
    for y in range(0, screen_h + 1, 25):
        if y % 100 != 0:
            pyxel.line(cam_x, y, cam_x + screen_w, y, col_minor)

    # Major grid lines (every 100px) - completely static to screen back
    for x in range(0, screen_w + 1, 100):
        pyxel.line(cam_x + x, 0, cam_x + x, screen_h, col_major)
    for y in range(0, screen_h + 1, 100):
        pyxel.line(cam_x, y, cam_x + screen_w, y, col_major)


def bg_glacial_crevasse(pyxel, cam_x: int, prog: float, dist: int, screen_w: int, screen_h: int, is_greed: bool):
    """Theme 12: Glacial Crevasse (Vertical meltwater torrents and sheer blue ice shelves)."""
    col_water = 8 if is_greed else 12
    col_shelf = 0 if is_greed else 6

    # Sheer vertical meltwater streams
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
    """Render scaled typography using dedicated image bank without texture corruption."""
    if not s:
        return
    w = min(256, len(s) * 4 + 4)
    h = 8
    bg_key = 1 if col == 0 else 0
    pyxel.images[img_bank].cls(bg_key)
    pyxel.images[img_bank].text(0, 0, s, col)
    blt_x = x + int(w * (scale - 1) / 2)
    blt_y = y + int(h * (scale - 1) / 2)
    pyxel.blt(blt_x, blt_y, img_bank, 0, 0, w, h, colkey=bg_key, scale=scale)


def bg_reader_dark(pyxel, cam_x: int, prog: float, dist: int, screen_w: int, screen_h: int, is_greed: bool, telemetry: Optional[dict] = None):
    """Theme 14: Reader Mode E-Reader Dark (Ecclesiastes 3 KJV e-reader in dark OLED mode)."""
    col_ink = 8 if is_greed else 6     # Moonlight soft grey text
    col_head = 8 if is_greed else 7    # Header white
    col_rule = 8 if is_greed else 1    # Rule divider
    col_stat = 8 if is_greed else 7    # Status text

    margin_l = cam_x + 32
    margin_r = cam_x + screen_w - 32
    pyxel.line(margin_l, 0, margin_l, screen_h, col_rule)
    pyxel.line(margin_r, 0, margin_r, screen_h, col_rule)

    text_x = cam_x + 44

    # Line 1: Running header
    draw_text_scaled_helper(pyxel, text_x, 16, "ECCLESIASTES 3 (KJV)  --  BORROWED TIME", col_head, scale=2)

    # Line 2: Telemetry status disguise (Hearts, Score, Time, Pacts)
    if telemetry:
        h = telemetry.get("hearts", 3)
        mh = telemetry.get("max_hearts", 3)
        sc = telemetry.get("score", 0)
        t_rem = telemetry.get("time_remaining", 15.0)
        pacts = telemetry.get("pacts", [])
        p_str = ", ".join(pacts) if pacts else "None"
        line2 = f"Hearts: {h}/{mh}   Score: {sc}   Time: {t_rem:.1f}s   Pacts: {p_str}"
    else:
        line2 = "Hearts: 3/3   Score: 0   Time: 15.0s   Pacts: None"
    draw_text_scaled_helper(pyxel, text_x, 38, line2, col_stat, scale=2)

    # Divider under Line 2
    pyxel.line(margin_l, 58, margin_r, 58, col_rule)

    # Verses: Double size font, continuous e-reader wrapping, scrolling with fall
    line_spacing = 20
    total_h = len(ECCLESIASTES_3_KJV_LINES) * line_spacing
    scroll_y = int(dist * 0.4) % total_h
    start_y = 66

    for idx, line in enumerate(ECCLESIASTES_3_KJV_LINES):
        sy = start_y + (idx * line_spacing - scroll_y) % total_h
        if 48 <= sy <= screen_h + 10:
            draw_text_scaled_helper(pyxel, text_x, sy, line, col_ink, scale=2)


def bg_reader_light(pyxel, cam_x: int, prog: float, dist: int, screen_w: int, screen_h: int, is_greed: bool, telemetry: Optional[dict] = None):
    """Theme 15: Reader Mode E-Reader Light (Ecclesiastes 3 KJV on warm cream e-reader paper)."""
    col_ink = 8 if is_greed else 0     # Pitch-black ink
    col_head = 8 if is_greed else 4    # Sepia / dark brown header
    col_rule = 8 if is_greed else 4    # Sepia margin rule
    col_stat = 8 if is_greed else 0    # Ink status text

    margin_l = cam_x + 32
    margin_r = cam_x + screen_w - 32
    pyxel.line(margin_l, 0, margin_l, screen_h, col_rule)
    pyxel.line(margin_r, 0, margin_r, screen_h, col_rule)

    text_x = cam_x + 44

    # Line 1: Running header
    draw_text_scaled_helper(pyxel, text_x, 16, "ECCLESIASTES 3 (KJV)  --  BORROWED TIME", col_head, scale=2)

    # Line 2: Telemetry status disguise (Hearts, Score, Time, Pacts)
    if telemetry:
        h = telemetry.get("hearts", 3)
        mh = telemetry.get("max_hearts", 3)
        sc = telemetry.get("score", 0)
        t_rem = telemetry.get("time_remaining", 15.0)
        pacts = telemetry.get("pacts", [])
        p_str = ", ".join(pacts) if pacts else "None"
        line2 = f"Hearts: {h}/{mh}   Score: {sc}   Time: {t_rem:.1f}s   Pacts: {p_str}"
    else:
        line2 = "Hearts: 3/3   Score: 0   Time: 15.0s   Pacts: None"
    draw_text_scaled_helper(pyxel, text_x, 38, line2, col_stat, scale=2)

    # Divider under Line 2
    pyxel.line(margin_l, 58, margin_r, 58, col_rule)

    # Verses: Double size font, continuous e-reader wrapping, scrolling with fall
    line_spacing = 20
    total_h = len(ECCLESIASTES_3_KJV_LINES) * line_spacing
    scroll_y = int(dist * 0.4) % total_h
    start_y = 66

    for idx, line in enumerate(ECCLESIASTES_3_KJV_LINES):
        sy = start_y + (idx * line_spacing - scroll_y) % total_h
        if 48 <= sy <= screen_h + 10:
            draw_text_scaled_helper(pyxel, text_x, sy, line, col_ink, scale=2)


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
    col_seal = 8

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
# THEME REGISTRY
# =============================================================================

ALL_THEMES: List[Theme] = [
    # 1. SkiFree Sandfall
    Theme(
        id=0,
        name="SKIFREE SANDFALL",
        clear_color=15,
        greed_clear_color=2,
        sand=SandPalette(body=10, border=4, glint=7, shadow=4, fat_body=10, fat_border=4, fat_glint=7),
        shard=ShardPalette(facet=6, border=0, glint=7, shadow=4, fat_facet=8, fat_border=0),
        hourglass=HourglassPalette(caps=4, cap_hl=9, cap_rivet=10, glass_walls=6, waist_neck=7, sand_a=10, sand_b=9, shadow=4),
        render_bg=bg_skifree_sandfall,
    ),
    # 2. Cosmic Chronometer
    Theme(
        id=1,
        name="COSMIC CHRONOMETER",
        clear_color=1,
        greed_clear_color=0,
        sand=SandPalette(body=10, border=1, glint=7, shadow=0, fat_body=10, fat_border=1, fat_glint=7),
        shard=ShardPalette(facet=13, border=1, glint=7, shadow=0, fat_facet=8, fat_border=0),
        hourglass=HourglassPalette(caps=4, cap_hl=9, cap_rivet=10, glass_walls=13, waist_neck=7, sand_a=10, sand_b=9, shadow=0),
        render_bg=bg_cosmic_chronometer,
    ),
    # 3. Abyssal Hourglass
    Theme(
        id=2,
        name="ABYSSAL HOURGLASS",
        clear_color=0,
        greed_clear_color=2,
        sand=SandPalette(body=10, border=0, glint=7, shadow=0, fat_body=10, fat_border=0, fat_glint=7),
        shard=ShardPalette(facet=0, border=6, glint=7, shadow=0, fat_facet=8, fat_border=7),
        hourglass=HourglassPalette(caps=1, cap_hl=6, cap_rivet=7, glass_walls=6, waist_neck=7, sand_a=10, sand_b=9, shadow=0),
        render_bg=bg_abyssal_hourglass,
    ),
    # 4. Shattered Mirror Chasm
    Theme(
        id=3,
        name="SHATTERED MIRROR CHASM",
        clear_color=13,
        greed_clear_color=2,
        sand=SandPalette(body=7, border=1, glint=12, shadow=1, fat_body=7, fat_border=1, fat_glint=12),
        shard=ShardPalette(facet=7, border=1, glint=14, shadow=1, fat_facet=8, fat_border=0),
        hourglass=HourglassPalette(caps=1, cap_hl=6, cap_rivet=7, glass_walls=12, waist_neck=7, sand_a=7, sand_b=12, shadow=1),
        render_bg=bg_shattered_mirror_chasm,
    ),
    # 5. Magma Caldera
    Theme(
        id=4,
        name="MAGMA CALDERA",
        clear_color=0,
        greed_clear_color=2,
        sand=SandPalette(body=10, border=8, glint=7, shadow=0, fat_body=10, fat_border=8, fat_glint=7),
        shard=ShardPalette(facet=0, border=8, glint=7, shadow=8, fat_facet=8, fat_border=7),
        hourglass=HourglassPalette(caps=5, cap_hl=8, cap_rivet=10, glass_walls=8, waist_neck=7, sand_a=10, sand_b=8, shadow=0),
        render_bg=bg_magma_caldera,
    ),
    # 6. Cartographer's Scroll
    Theme(
        id=5,
        name="CARTOGRAPHER'S SCROLL",
        clear_color=15,
        greed_clear_color=4,
        sand=SandPalette(body=9, border=4, glint=10, shadow=4, fat_body=9, fat_border=4, fat_glint=10),
        shard=ShardPalette(facet=0, border=4, glint=7, shadow=4, fat_facet=8, fat_border=0),
        hourglass=HourglassPalette(caps=4, cap_hl=9, cap_rivet=10, glass_walls=4, waist_neck=7, sand_a=9, sand_b=10, shadow=4),
        render_bg=bg_cartographers_scroll,
    ),
    # 7. Pro Mode (High Contrast Dark)
    Theme(
        id=6,
        name="PRO MODE (HIGH CONTRAST DARK)",
        clear_color=0,
        greed_clear_color=0,
        sand=SandPalette(body=10, border=0, glint=7, shadow=0, fat_body=10, fat_border=0, fat_glint=7),
        shard=ShardPalette(facet=12, border=0, glint=7, shadow=0, fat_facet=8, fat_border=7),
        hourglass=HourglassPalette(caps=7, cap_hl=7, cap_rivet=0, glass_walls=12, waist_neck=7, sand_a=10, sand_b=7, shadow=0),
        render_bg=bg_pro_mode_dark,
    ),
    # 8. Pro Mode (High Contrast Light)
    Theme(
        id=7,
        name="PRO MODE (HIGH CONTRAST LIGHT)",
        clear_color=7,
        greed_clear_color=7,
        sand=SandPalette(body=9, border=0, glint=10, shadow=0, fat_body=9, fat_border=0, fat_glint=10),
        shard=ShardPalette(facet=0, border=0, glint=5, shadow=0, fat_facet=8, fat_border=0),
        hourglass=HourglassPalette(caps=0, cap_hl=5, cap_rivet=0, glass_walls=1, waist_neck=0, sand_a=9, sand_b=10, shadow=5),
        render_bg=bg_pro_mode_light,
    ),
    # 9. Copper & Verdigris
    Theme(
        id=8,
        name="COPPER & VERDIGRIS",
        clear_color=4,
        greed_clear_color=2,
        sand=SandPalette(body=9, border=0, glint=10, shadow=0, fat_body=9, fat_border=0, fat_glint=10),
        shard=ShardPalette(facet=3, border=0, glint=11, shadow=0, fat_facet=8, fat_border=0),
        hourglass=HourglassPalette(caps=4, cap_hl=9, cap_rivet=10, glass_walls=3, waist_neck=7, sand_a=9, sand_b=10, shadow=0),
        render_bg=bg_copper_and_verdigris,
    ),
    # 10. Solar Flare
    Theme(
        id=9,
        name="SOLAR FLARE",
        clear_color=9,
        greed_clear_color=2,
        sand=SandPalette(body=7, border=8, glint=10, shadow=4, fat_body=7, fat_border=8, fat_glint=10),
        shard=ShardPalette(facet=0, border=8, glint=7, shadow=8, fat_facet=8, fat_border=7),
        hourglass=HourglassPalette(caps=8, cap_hl=10, cap_rivet=7, glass_walls=7, waist_neck=10, sand_a=7, sand_b=10, shadow=8),
        render_bg=bg_solar_flare,
    ),
    # 11. Monochrome Blueprint
    Theme(
        id=10,
        name="MONOCHROME BLUEPRINT",
        clear_color=1,
        greed_clear_color=0,
        sand=SandPalette(body=7, border=1, glint=12, shadow=0, fat_body=7, fat_border=1, fat_glint=12),
        shard=ShardPalette(facet=7, border=1, glint=12, shadow=0, fat_facet=8, fat_border=7),
        hourglass=HourglassPalette(caps=12, cap_hl=7, cap_rivet=7, glass_walls=12, waist_neck=7, sand_a=7, sand_b=12, shadow=0),
        render_bg=bg_monochrome_blueprint,
    ),
    # 12. Glacial Crevasse
    Theme(
        id=11,
        name="GLACIAL CREVASSE",
        clear_color=1,
        greed_clear_color=0,
        sand=SandPalette(body=12, border=1, glint=7, shadow=0, fat_body=12, fat_border=1, fat_glint=7),
        shard=ShardPalette(facet=7, border=1, glint=6, shadow=0, fat_facet=8, fat_border=7),
        hourglass=HourglassPalette(caps=12, cap_hl=6, cap_rivet=7, glass_walls=6, waist_neck=7, sand_a=12, sand_b=7, shadow=0),
        render_bg=bg_glacial_crevasse,
    ),
    # 13. Retro Terminal Matrix
    Theme(
        id=12,
        name="RETRO TERMINAL MATRIX",
        clear_color=0,
        greed_clear_color=2,
        sand=SandPalette(body=11, border=0, glint=7, shadow=0, fat_body=11, fat_border=0, fat_glint=7),
        shard=ShardPalette(facet=3, border=0, glint=11, shadow=0, fat_facet=8, fat_border=7),
        hourglass=HourglassPalette(caps=3, cap_hl=11, cap_rivet=7, glass_walls=3, waist_neck=11, sand_a=11, sand_b=3, shadow=0),
        render_bg=bg_retro_terminal_matrix,
    ),
    # 14. Reader Mode (E-Reader Dark)
    Theme(
        id=13,
        name="READER MODE (E-READER DARK)",
        clear_color=0,
        greed_clear_color=0,
        sand=SandPalette(body=10, border=0, glint=7, shadow=0, fat_body=10, fat_border=0, fat_glint=7),
        shard=ShardPalette(facet=8, border=0, glint=7, shadow=0, fat_facet=8, fat_border=7),
        hourglass=HourglassPalette(caps=5, cap_hl=6, cap_rivet=7, glass_walls=6, waist_neck=12, sand_a=10, sand_b=7, shadow=0),
        render_bg=bg_reader_dark,
        is_reader_mode=True,
    ),
    # 15. Reader Mode (E-Reader Light)
    Theme(
        id=14,
        name="READER MODE (E-READER LIGHT)",
        clear_color=15,
        greed_clear_color=15,
        sand=SandPalette(body=9, border=4, glint=10, shadow=4, fat_body=9, fat_border=4, fat_glint=10),
        shard=ShardPalette(facet=8, border=4, glint=7, shadow=4, fat_facet=8, fat_border=0),
        hourglass=HourglassPalette(caps=4, cap_hl=9, cap_rivet=10, glass_walls=0, waist_neck=7, sand_a=9, sand_b=10, shadow=4),
        render_bg=bg_reader_light,
        is_reader_mode=True,
    ),
    # 16. Neon Noir Megacity
    Theme(
        id=15,
        name="NEON NOIR MEGACITY",
        clear_color=0,
        greed_clear_color=2,
        sand=SandPalette(body=10, border=8, glint=7, shadow=0, fat_body=10, fat_border=8, fat_glint=7),
        shard=ShardPalette(facet=14, border=0, glint=12, shadow=0, fat_facet=8, fat_border=7),
        hourglass=HourglassPalette(caps=1, cap_hl=14, cap_rivet=12, glass_walls=12, waist_neck=14, sand_a=10, sand_b=14, shadow=0),
        render_bg=bg_neon_noir_megacity,
    ),
    # 17. Liminal Vaporwave
    Theme(
        id=16,
        name="LIMINAL VAPORWAVE",
        clear_color=14,
        greed_clear_color=2,
        sand=SandPalette(body=10, border=1, glint=7, shadow=1, fat_body=10, fat_border=1, fat_glint=7),
        shard=ShardPalette(facet=12, border=1, glint=7, shadow=1, fat_facet=8, fat_border=0),
        hourglass=HourglassPalette(caps=1, cap_hl=12, cap_rivet=7, glass_walls=12, waist_neck=14, sand_a=10, sand_b=12, shadow=1),
        render_bg=bg_liminal_vaporwave,
    ),
    # 18. Chalkboard Theory
    Theme(
        id=17,
        name="CHALKBOARD THEORY",
        clear_color=5,
        greed_clear_color=2,
        sand=SandPalette(body=10, border=5, glint=7, shadow=0, fat_body=10, fat_border=5, fat_glint=7),
        shard=ShardPalette(facet=0, border=7, glint=6, shadow=0, fat_facet=8, fat_border=7),
        hourglass=HourglassPalette(caps=0, cap_hl=6, cap_rivet=7, glass_walls=6, waist_neck=7, sand_a=10, sand_b=7, shadow=0),
        render_bg=bg_chalkboard_theory,
    ),
    # 19. Blood Moon Eclipse
    Theme(
        id=18,
        name="BLOOD MOON ECLIPSE",
        clear_color=2,
        greed_clear_color=0,
        sand=SandPalette(body=9, border=2, glint=8, shadow=0, fat_body=9, fat_border=2, fat_glint=8),
        shard=ShardPalette(facet=8, border=0, glint=7, shadow=0, fat_facet=8, fat_border=7),
        hourglass=HourglassPalette(caps=2, cap_hl=8, cap_rivet=7, glass_walls=8, waist_neck=7, sand_a=9, sand_b=8, shadow=0),
        render_bg=bg_blood_moon_eclipse,
    ),
    # 20. Zen Ink Wash (Sumi-e)
    Theme(
        id=19,
        name="ZEN INK WASH (SUMI-E)",
        clear_color=7,
        greed_clear_color=2,
        sand=SandPalette(body=9, border=0, glint=10, shadow=5, fat_body=9, fat_border=0, fat_glint=10),
        shard=ShardPalette(facet=0, border=5, glint=7, shadow=5, fat_facet=8, fat_border=0),
        hourglass=HourglassPalette(caps=0, cap_hl=5, cap_rivet=8, glass_walls=5, waist_neck=0, sand_a=9, sand_b=0, shadow=5),
        render_bg=bg_zen_ink_wash,
    ),
]


def get_theme(index: int) -> Theme:
    """Return theme by modular index (0..19)."""
    return ALL_THEMES[index % len(ALL_THEMES)]
