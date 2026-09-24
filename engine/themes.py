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
    render_bg: Callable[[any, int, float, int, int, int, bool], None]

    def get_clear_color(self, greed_active: bool) -> int:
        return self.greed_clear_color if greed_active else self.clear_color

    def render(self, pyxel_mod, cam_x: int, prog: float, dist: int, screen_w: int = 600, screen_h: int = 800, is_greed: bool = False):
        if self.render_bg and pyxel_mod:
            self.render_bg(pyxel_mod, cam_x, prog, dist, screen_w, screen_h, is_greed)


# =============================================================================
# PROCEDURAL BACKGROUND RENDERERS FOR ALL 20 THEMES
# =============================================================================

def bg_skifree_sandfall(pyxel, cam_x: int, prog: float, dist: int, screen_w: int, screen_h: int, is_greed: bool):
    """Theme 1: SkiFree Sandfall (Braided chutes, velocity shearing, sinuous sandbars)."""
    col_crest = 8 if is_greed else (10 if prog > 0.85 and (pyxel.frame_count // 3) % 2 == 0 else 7)
    col_shadow = 0 if is_greed else 9
    col_shadow_deep = 0 if is_greed else 4
    col_stream = 8 if is_greed else (10 if prog > 0.85 else 9)
    col_froth = 14 if is_greed else 7
    col_spray = 8 if is_greed else 10
    col_rock = 0 if is_greed else 4
    col_rock_hl = 8 if is_greed else 7

    # 1. Cascading Flumes & Streamlines
    start_col = int((cam_x - 30) // 22) * 22
    end_col = cam_x + screen_w + 30
    cycle_h = 320
    for col_x in range(start_col, end_col, 22):
        col_hash = (col_x * 73856093) & 0xFFFFFF
        spd = 1.18 + 0.32 * ((col_hash % 100) / 100.0)
        for offset_y in (0, 110, 220):
            sy = (offset_y - int(dist * spd)) % cycle_h - 20
            if -20 <= sy <= screen_h + 20:
                streak_len = 10 + (col_hash % 14)
                meander = int(5.0 * math.sin((sy + dist * 0.04) * 0.015 + col_x * 0.03))
                fx = col_x + meander
                pyxel.line(fx, sy, fx, sy + streak_len, col_stream)
                if (col_hash >> 6) % 3 == 0:
                    pyxel.pset(fx, sy, col_froth)

    # 2. Braided Sandbar Banks
    bar_spacing = 140
    for base_y in range(-bar_spacing, screen_h + bar_spacing, bar_spacing):
        y_anchor = base_y - (dist % bar_spacing)
        prev_x = cam_x - 24
        prev_y = y_anchor + int(24 * math.sin((prev_x + base_y) * 0.009) + 10 * math.cos(prev_x * 0.021))
        for x in range(cam_x - 18, cam_x + screen_w + 24, 6):
            cur_y = y_anchor + int(24 * math.sin((x + base_y) * 0.009) + 10 * math.cos(x * 0.021))
            if -30 <= cur_y <= screen_h + 30:
                chute_val = math.sin(x * 0.007 + (base_y // bar_spacing) * 1.5)
                if chute_val > 0.40:
                    if x % 18 == 0:
                        pyxel.pset(x, cur_y, col_froth)
                        pyxel.pset(x + 2, cur_y + 1, col_stream)
                else:
                    pyxel.line(prev_x, prev_y, x, cur_y, col_crest)
                    pyxel.line(prev_x, prev_y + 1, x, cur_y + 1, col_shadow)
                    if x % 12 == 0:
                        pyxel.line(x, cur_y + 2, x, cur_y + 5, col_shadow_deep)
            prev_x = x
            prev_y = cur_y


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
    """Theme 7: Pro Mode High Contrast Dark (Functional, WCAG AAA contrast, zero noise)."""
    col_ruler = 8 if is_greed else 5
    col_dot = 2 if is_greed else 1
    col_tick_maj = 8 if is_greed else 7
    col_tick_min = 8 if is_greed else 5

    # Side telemetry depth rulers (left and right)
    ruler_spacing = 20
    y_off = int(dist * 0.5) % ruler_spacing
    left_x = cam_x + 16
    right_x = cam_x + screen_w - 16

    pyxel.line(left_x, 0, left_x, screen_h, col_ruler)
    pyxel.line(right_x, 0, right_x, screen_h, col_ruler)

    for y in range(-ruler_spacing, screen_h + ruler_spacing, ruler_spacing):
        sy = y - y_off
        is_major = ((y + int(dist * 0.5)) // ruler_spacing) % 5 == 0
        tick_len = 8 if is_major else 4
        c_tick = col_tick_maj if is_major else col_tick_min
        pyxel.line(left_x, sy, left_x + tick_len, sy, c_tick)
        pyxel.line(right_x - tick_len, sy, right_x, sy, c_tick)

    # Minimal reference grid dots every 100px (100% clean, no visual noise)
    grid_sz = 100
    start_gx = int(cam_x // grid_sz) * grid_sz
    y_grid_off = int(dist * 0.5) % grid_sz
    for gx in range(start_gx, cam_x + screen_w + grid_sz, grid_sz):
        for gy in range(-grid_sz, screen_h + grid_sz, grid_sz):
            sy = gy - y_grid_off
            pyxel.pset(gx, sy, col_dot)


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
    """Theme 11: Pro Mode High Contrast Light (Clinical technical grid, high luminance, pure functional)."""
    col_grid = 8 if is_greed else 6
    col_ruler = 8 if is_greed else 0
    col_tick_maj = 8 if is_greed else 0
    col_tick_min = 8 if is_greed else 5

    # Technical graph drafting grid lines
    grid_sz = 50
    start_gx = int(cam_x // grid_sz) * grid_sz
    y_grid_off = int(dist * 0.5) % grid_sz

    for gx in range(start_gx, cam_x + screen_w + grid_sz, grid_sz):
        pyxel.line(gx, 0, gx, screen_h, col_grid)

    for gy in range(-grid_sz, screen_h + grid_sz, grid_sz):
        sy = gy - y_grid_off
        pyxel.line(cam_x, sy, cam_x + screen_w, sy, col_grid)

    # Left & right depth calibration ruler
    ruler_spacing = 20
    y_off = int(dist * 0.5) % ruler_spacing
    left_x = cam_x + 16
    right_x = cam_x + screen_w - 16

    pyxel.line(left_x, 0, left_x, screen_h, col_ruler)
    pyxel.line(right_x, 0, right_x, screen_h, col_ruler)

    for y in range(-ruler_spacing, screen_h + ruler_spacing, ruler_spacing):
        sy = y - y_off
        is_major = ((y + int(dist * 0.5)) // ruler_spacing) % 5 == 0
        tick_len = 8 if is_major else 4
        c_tick = col_tick_maj if is_major else col_tick_min
        pyxel.line(left_x, sy, left_x + tick_len, sy, c_tick)
        pyxel.line(right_x - tick_len, sy, right_x, sy, c_tick)


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


def bg_stealth_dark(pyxel, cam_x: int, prog: float, dist: int, screen_w: int, screen_h: int, is_greed: bool):
    """Theme 14: Stealth Mode E-Reader Dark (Terminal documentation / paper reading disguise)."""
    col_text = 8 if is_greed else 5
    col_head = 8 if is_greed else 6
    col_decor = 8 if is_greed else 1

    line_spacing = 18
    total_h = len(STEALTH_DARK_DOC) * line_spacing
    scroll_y = int(dist * 0.4) % total_h

    # IDE / E-reader margin gutters
    pyxel.line(cam_x + 18, 0, cam_x + 18, screen_h, col_decor)
    pyxel.line(cam_x + screen_w - 18, 0, cam_x + screen_w - 18, screen_h, col_decor)

    # Render continuous technical text
    text_x = cam_x + 24
    for idx, line in enumerate(STEALTH_DARK_DOC):
        sy = (idx * line_spacing - scroll_y) % total_h
        if -16 <= sy <= screen_h + 16:
            c = col_head if (line.startswith("[") or (len(line) > 2 and line[0].isdigit() and line[1] == ".")) else col_text
            pyxel.text(text_x, sy, line, c)


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


def bg_stealth_light(pyxel, cam_x: int, prog: float, dist: int, screen_w: int, screen_h: int, is_greed: bool):
    """Theme 15: Stealth Mode Book Novel Light (Antique paper novel / literary prose reading disguise)."""
    col_ink = 8 if is_greed else 0
    col_rule = 8 if is_greed else 4
    col_chapter = 8 if is_greed else 4

    line_spacing = 19
    total_h = len(STEALTH_LIGHT_DOC) * line_spacing
    scroll_y = int(dist * 0.4) % total_h

    # Page margins (book layout)
    margin_l = cam_x + 28
    margin_r = cam_x + screen_w - 28
    pyxel.line(margin_l, 0, margin_l, screen_h, col_rule)
    pyxel.line(margin_r, 0, margin_r, screen_h, col_rule)

    # Render literary text lines
    text_x = cam_x + 36
    for idx, line in enumerate(STEALTH_LIGHT_DOC):
        sy = (idx * line_spacing - scroll_y) % total_h
        if -16 <= sy <= screen_h + 16:
            c = col_chapter if (line.startswith("CHAPTER") or line.startswith("THE ARCHITECTURE") or line.startswith("THE WEIGHT")) else col_ink
            pyxel.text(text_x, sy, line, c)


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
    # 8. Copper & Verdigris
    Theme(
        id=7,
        name="COPPER & VERDIGRIS",
        clear_color=4,
        greed_clear_color=2,
        sand=SandPalette(body=9, border=0, glint=10, shadow=0, fat_body=9, fat_border=0, fat_glint=10),
        shard=ShardPalette(facet=3, border=0, glint=11, shadow=0, fat_facet=8, fat_border=0),
        hourglass=HourglassPalette(caps=4, cap_hl=9, cap_rivet=10, glass_walls=3, waist_neck=7, sand_a=9, sand_b=10, shadow=0),
        render_bg=bg_copper_and_verdigris,
    ),
    # 9. Solar Flare
    Theme(
        id=8,
        name="SOLAR FLARE",
        clear_color=9,
        greed_clear_color=2,
        sand=SandPalette(body=7, border=8, glint=10, shadow=4, fat_body=7, fat_border=8, fat_glint=10),
        shard=ShardPalette(facet=0, border=8, glint=7, shadow=8, fat_facet=8, fat_border=7),
        hourglass=HourglassPalette(caps=8, cap_hl=10, cap_rivet=7, glass_walls=7, waist_neck=10, sand_a=7, sand_b=10, shadow=8),
        render_bg=bg_solar_flare,
    ),
    # 10. Monochrome Blueprint
    Theme(
        id=9,
        name="MONOCHROME BLUEPRINT",
        clear_color=1,
        greed_clear_color=0,
        sand=SandPalette(body=7, border=1, glint=12, shadow=0, fat_body=7, fat_border=1, fat_glint=12),
        shard=ShardPalette(facet=7, border=1, glint=12, shadow=0, fat_facet=8, fat_border=7),
        hourglass=HourglassPalette(caps=12, cap_hl=7, cap_rivet=7, glass_walls=12, waist_neck=7, sand_a=7, sand_b=12, shadow=0),
        render_bg=bg_monochrome_blueprint,
    ),
    # 11. Pro Mode (High Contrast Light)
    Theme(
        id=10,
        name="PRO MODE (HIGH CONTRAST LIGHT)",
        clear_color=7,
        greed_clear_color=7,
        sand=SandPalette(body=9, border=0, glint=10, shadow=0, fat_body=9, fat_border=0, fat_glint=10),
        shard=ShardPalette(facet=0, border=0, glint=5, shadow=0, fat_facet=8, fat_border=0),
        hourglass=HourglassPalette(caps=0, cap_hl=5, cap_rivet=0, glass_walls=1, waist_neck=0, sand_a=9, sand_b=10, shadow=5),
        render_bg=bg_pro_mode_light,
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
    # 14. Stealth Mode (E-Reader Dark)
    Theme(
        id=13,
        name="STEALTH MODE (E-READER DARK)",
        clear_color=0,
        greed_clear_color=0,
        sand=SandPalette(body=10, border=0, glint=7, shadow=0, fat_body=10, fat_border=0, fat_glint=7),
        shard=ShardPalette(facet=8, border=0, glint=7, shadow=0, fat_facet=8, fat_border=7),
        hourglass=HourglassPalette(caps=5, cap_hl=6, cap_rivet=7, glass_walls=6, waist_neck=12, sand_a=10, sand_b=7, shadow=0),
        render_bg=bg_stealth_dark,
    ),
    # 15. Stealth Mode (Book Novel Light)
    Theme(
        id=14,
        name="STEALTH MODE (BOOK NOVEL LIGHT)",
        clear_color=15,
        greed_clear_color=15,
        sand=SandPalette(body=9, border=4, glint=10, shadow=4, fat_body=9, fat_border=4, fat_glint=10),
        shard=ShardPalette(facet=8, border=4, glint=7, shadow=4, fat_facet=8, fat_border=0),
        hourglass=HourglassPalette(caps=4, cap_hl=9, cap_rivet=10, glass_walls=0, waist_neck=7, sand_a=9, sand_b=10, shadow=4),
        render_bg=bg_stealth_light,
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
