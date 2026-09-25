"""Grain of Doubt - PyWeek 42 ("Borrowed Time")
By Arian Prabowo

A 2D Retro Arcade Falling Hourglass Endless Runner built with Pyxel.
600x800 Resolution (3:4 Portrait Aspect Ratio).
Controls: A / D or Left / Right Arrows only.
"""
import math
import os
import random
import sys
from typing import Optional, List, Tuple

try:
    import pyxel
except ImportError:
    pyxel = None

from engine.state import GameState, StateManager
from engine.entities import EntityManager, HourglassPlayer, SandGrain, GlassShard
from engine.bargains import BargainManager, SinType, BARGAIN_REGISTRY, SIN_CARD_COLORS, CANONICAL_SINS
from engine.audio import AudioManager
from engine.bot import PlayTestingBot, BotConfig
from engine.video import VideoRecorder
from engine.themes import ALL_THEMES, get_theme, Theme, SandPalette, ShardPalette, HourglassPalette
from engine.font5x7 import draw_text_5x7


def render_vignette(px: float, py: float, radius: float, screen_w: int = 600, screen_h: int = 800, pyxel_module=None, inner_radius: float = None):
    """Draw multi-circle concentric vignette mask centered at (px, py) with graduated dither transparency.

    Args:
        radius: Outer radius — zero vision beyond this circle.
        inner_radius: Inner radius — full clear unobstructed vision inside this circle.
                      If None, defaults to 0.42 * radius for backwards compatibility.

    The 5 graduated tiers are linearly interpolated between inner_radius and radius:
    - Core (< inner_radius): 100% clear unobstructed vision.
    - Tier 1 (inner..t2): 20% dither darkness.
    - Tier 2 (t2..t3): 42% dither darkness.
    - Tier 3 (t3..t4): 65% dither darkness.
    - Tier 4 (t4..radius): 85% dither darkness.
    - Outside radius: 100% solid black void.
    """
    if pyxel_module is None or radius >= 900.0:
        return

    r_outer = max(25.0, float(radius))
    if inner_radius is None:
        r_inner = 0.42 * r_outer
    else:
        r_inner = max(10.0, min(float(inner_radius), r_outer - 5.0))

    # 5 tier boundaries linearly interpolated from r_inner to r_outer
    span = r_outer - r_inner
    tier_radii = [
        r_inner,                          # boundary 0: inner edge (clear core)
        r_inner + span * 0.25,            # boundary 1
        r_inner + span * 0.50,            # boundary 2
        r_inner + span * 0.75,            # boundary 3
        r_outer,                          # boundary 4: outer edge (total void)
    ]
    tier_alphas = [0.20, 0.42, 0.65, 0.85, 1.00]

    radii_sq = [rk * rk for rk in tier_radii]
    r_max_sq = radii_sq[-1]
    has_dither = hasattr(pyxel_module, "dither")

    # Fast block fill above and below outer circle
    min_y = max(0, int(py - tier_radii[-1]))
    max_y = min(screen_h, int(py + tier_radii[-1]) + 1)

    if has_dither:
        pyxel_module.dither(1.0)

    if min_y > 0:
        pyxel_module.rect(0, 0, screen_w, min_y, 0)
    if max_y < screen_h:
        pyxel_module.rect(0, max_y, screen_w, screen_h - max_y, 0)

    # Render each row intersecting the vignette circles
    for y in range(min_y, max_y):
        dy = y - py
        dy_sq = dy * dy

        if dy_sq >= r_max_sq:
            if has_dither:
                pyxel_module.dither(1.0)
            pyxel_module.rect(0, y, screen_w, 1, 0)
            continue

        dxs = [math.sqrt(r_sq - dy_sq) if r_sq > dy_sq else 0.0 for r_sq in radii_sq]

        # 1. Solid black void outside outer radius
        lx_out = int(px - dxs[4])
        rx_out = int(px + dxs[4])
        if has_dither:
            pyxel_module.dither(1.0)
        if lx_out > 0:
            pyxel_module.rect(0, y, lx_out, 1, 0)
        if rx_out < screen_w:
            pyxel_module.rect(rx_out, y, screen_w - rx_out, 1, 0)

        # 2. Concentric graduated dither rings from outermost tier down to innermost
        for i in range(4, 0, -1):
            alpha = tier_alphas[i - 1]
            dx_outer = dxs[i]
            dx_inner = dxs[i - 1]

            if has_dither:
                pyxel_module.dither(alpha)

            # Left ring segment
            l_start = max(0, int(px - dx_outer))
            l_end = max(0, min(screen_w, int(px - dx_inner)))
            if l_end > l_start:
                pyxel_module.rect(l_start, y, l_end - l_start, 1, 0)

            # Right ring segment
            r_start = max(0, min(screen_w, int(px + dx_inner)))
            r_end = min(screen_w, int(px + dx_outer))
            if r_end > r_start:
                pyxel_module.rect(r_start, y, r_end - r_start, 1, 0)

        # Innermost tier center bridge when row does not touch clear core
        if dxs[0] == 0.0 and dxs[1] > 0.0:
            c_start = max(0, int(px - dxs[1]))
            c_end = min(screen_w, int(px + dxs[1]))
            if c_end > c_start:
                if has_dither:
                    pyxel_module.dither(tier_alphas[0])
                pyxel_module.rect(c_start, y, c_end - c_start, 1, 0)

    if has_dither:
        pyxel_module.dither(1.0)


def draw_text_scaled(x: int, y: int, s: str, col: int, scale: int = 1, img_bank: int = 2, char_gap: Optional[int] = None):
    """Draw text with spacious 5x7 typography and integer scaling factor."""
    if pyxel is None or not s:
        return
    draw_text_5x7(pyxel, x, y, s, col, scale=scale, img_bank=img_bank, char_gap=char_gap)


def get_text_width_5x7(s: str, scale: int = 1, char_gap: Optional[int] = None) -> int:
    """Return exact rendered pixel width of string in 5x7 font."""
    if not s:
        return 0
    if char_gap is None:
        if s == "GLUTTONY" and scale == 5:
            return 228
        actual_gap = 1 * scale
    else:
        actual_gap = char_gap
    return len(s) * (5 * scale) + max(0, len(s) - 1) * actual_gap


def draw_text_centered(y: int, s: str, col: int, scale: int = 1, screen_w: int = 600):
    """Draw string centered horizontally across screen_w using exact 5x7 typography."""
    w = get_text_width_5x7(s, scale)
    x = max(0, (screen_w - w) // 2)
    draw_text_scaled(x, y, s, col, scale=scale)


SIN_PRO_ABBREVIATIONS: dict[SinType, str] = {
    SinType.PRIDE: "Pd",
    SinType.GREED: "Gd",
    SinType.LUST: "Lt",
    SinType.ENVY: "Ey",
    SinType.GLUTTONY: "Gy",
    SinType.WRATH: "Wh",
    SinType.SLOTH: "Sh",
}

KJV_SIN_PARAGRAPHS: dict[SinType, str] = {
    SinType.PRIDE: (
        "The proud heart shall reap of the golden dust in bountiful clusters, "
        "yet for every grain thou takest, thy descent through the void shall "
        "wax twenty and five parts swifter, till none may stay thy fall."
    ),
    SinType.GREED: (
        "Lo, the covetous shall multiply his substance tenfold for a season, "
        "yet is his life counted upon borrowed time: when the appointed measure "
        "of seconds hath expired, thy soul is straightway required of thee."
    ),
    SinType.LUST: (
        "Thy vessel shall draw unto itself the golden sands of the deep with an "
        "unyielding hunger; yet by the same token shall every jagged shard of "
        "glass be drawn likewise to pierce thy fragile walls."
    ),
    SinType.ENVY: (
        "Thou desirest everything thine eyes behold; howbeit, thou shalt "
        "not deserve to see so much, and creeping shadow shall narrow "
        "thy vision into darkness."
    ),
    SinType.GLUTTONY: (
        "Thou shalt feast upon great and fat grains yielding threefold measure "
        "unto thy score; yet shall the shards of glass grow likewise monstrous "
        "and heavy, that thy path be choked with peril."
    ),
    SinType.WRATH: (
        "In thine anger thou shalt use great force to drive all dangers far away; "
        "howbeit, thou shalt push all the good things away too, and scatter "
        "thy golden sands into the distant void."
    ),
    SinType.SLOTH: (
        "Thou shalt push all dangers to a later time that thou mayest do nothing "
        "now; yet shalt thou be bound to the center, and sluggish drag shall "
        "mire thy steering."
    ),
}


def draw_centered_paragraph(x: int, y: int, width: int, text: str, col: int, scale: int = 1, line_spacing: int = 12):
    """Draw text paragraph with lines centered horizontally within width."""
    words = text.split()
    lines = []
    cur_line = []
    char_w = 6 * scale

    for w in words:
        test_line = cur_line + [w]
        line_len = sum(len(word) for word in test_line) * char_w + (len(test_line) - 1) * char_w
        if line_len <= width or not cur_line:
            cur_line.append(w)
        else:
            lines.append(cur_line)
            cur_line = [w]
    if cur_line:
        lines.append(cur_line)

    cur_y = y
    center_x = x + width // 2
    for line_words in lines:
        line_str = " ".join(line_words)
        line_w = len(line_str) * char_w - scale
        draw_text_scaled(center_x - line_w // 2, cur_y, line_str, col, scale=scale)
        cur_y += line_spacing * scale


def draw_justified_paragraph(x: int, y: int, width: int, text: str, col: int, scale: int = 1, line_spacing: int = 12):
    """Draw text paragraph justified flush to left and right margins."""
    words = text.split()
    lines = []
    cur_line = []
    char_w = 6 * scale

    for w in words:
        test_line = cur_line + [w]
        line_len = sum(len(word) for word in test_line) * char_w + (len(test_line) - 1) * char_w
        if line_len <= width or not cur_line:
            cur_line.append(w)
        else:
            lines.append(cur_line)
            cur_line = [w]
    if cur_line:
        lines.append(cur_line)

    cur_y = y
    for line_idx, line_words in enumerate(lines):
        is_last_line = (line_idx == len(lines) - 1) or len(line_words) == 1
        if is_last_line:
            draw_text_scaled(x, cur_y, " ".join(line_words), col, scale=scale)
        else:
            total_chars_w = sum(len(w) for w in line_words) * char_w
            num_slots = len(line_words) - 1
            total_space = width - total_chars_w
            base_slot_space = total_space // num_slots
            extra_pixels = total_space % num_slots

            slot_x = x
            for w_idx, w in enumerate(line_words):
                draw_text_scaled(slot_x, cur_y, w, col, scale=scale)
                slot_x += len(w) * char_w
                if w_idx < num_slots:
                    slot_w = base_slot_space + (1 if w_idx < extra_pixels else 0)
                    slot_x += slot_w
        cur_y += line_spacing * scale



def is_mobile_environment() -> bool:
    if "--mobile" in sys.argv:
        return True
    if sys.platform == "emscripten":
        try:
            import js
            if getattr(js.window, "__PYXEL_IS_MOBILE__", False):
                return True
            nav = getattr(js, "navigator", None)
            if nav:
                max_touch = getattr(nav, "maxTouchPoints", 0)
                ua = str(getattr(nav, "userAgent", "")).lower()
                return max_touch > 0 or any(m in ua for m in ["android", "iphone", "ipad", "ipod", "mobile"])
        except Exception:
            pass
    return False


def is_dev_environment() -> bool:
    if "--dev" in sys.argv or "-d" in sys.argv:
        return True
    if sys.platform == "emscripten":
        try:
            import js
            if hasattr(js, "window"):
                if getattr(js.window, "__DEV_MODE__", False):
                    return True
                search = str(getattr(js.window.location, "search", "")).lower()
                if "dev" in search:
                    return True
        except Exception:
            pass
    return False


class GrainOfDoubtApp:
    VERSION: str = "v1.2.2"
    SCREEN_WIDTH: int = 600
    SCREEN_HEIGHT: int = 800

    def __init__(
        self,
        headless: bool = False,
        bot_mode: bool = False,
        record_video: bool = False,
        video_filename: str = os.path.join("recordings", "borrowed_time_bot.mp4"),
        mobile_mode: bool = False,
        dev_mode: bool = False,
    ):
        self.headless = headless
        self.bot_mode = bot_mode
        self.is_mobile = mobile_mode or is_mobile_environment()
        self.bot = PlayTestingBot()
        self.auto_restart_timer: int = 0
        self.game_over_timer: int = 0
        self.video_recorder = VideoRecorder(output_path=video_filename, width=self.SCREEN_WIDTH, height=self.SCREEN_HEIGHT, fps=30)
        self.record_video_on_start = record_video
        self.state = StateManager()
        self.entities = EntityManager(self.SCREEN_WIDTH, self.SCREEN_HEIGHT)
        self.bargains = BargainManager()
        self.audio = AudioManager()
        self.active_options: List[Tuple[SinType, any, int]] = []
        self.selected_card_index: int = 0  # 0=Left, 1=Right
        self.selected_feedback: Optional[dict] = None
        self.feedback_timer: int = 0
        self.dev_mode: bool = dev_mode or is_dev_environment()
        self.touch_left: bool = False
        self.touch_right: bool = False
        self.kairos_left_released: bool = True
        self.kairos_right_released: bool = True
        self.current_theme_index: int = 0
        self.theme_banner_timer: int = 0
        self.lore_page: int = 0
        self.MAX_LORE_PAGES: int = 5

        # Wrath curse control inversion tracking (+5% per Wrath, cap 50%)
        self._raw_left_prev: bool = False
        self._raw_right_prev: bool = False
        self._invert_left_stroke: bool = False
        self._invert_right_stroke: bool = False

        # Cosmic void background stars (parallax)
        self.stars: List[List[float]] = []
        self.reset_stars()

        if not headless and pyxel is not None:
            pyxel.init(
                self.SCREEN_WIDTH,
                self.SCREEN_HEIGHT,
                title="Grain of Doubt - By Arian Prabowo",
                fps=30,
                quit_key=pyxel.KEY_NONE,
            )
            self.audio.init_sounds(pyxel)
            if self.record_video_on_start:
                self.video_recorder.start(pyxel)
            pyxel.run(self.update, self.draw)

    def reset_stars(self):
        """Reset parallax starfield uniformly across viewport."""
        self.stars = [
            [
                random.uniform(0, self.SCREEN_WIDTH),
                random.uniform(0, self.SCREEN_HEIGHT),
                random.choice([1, 5, 6]),
                random.choice([2, 3]),
                random.uniform(0.3, 0.8),
            ]
            for _ in range(64)
        ]

    def start_new_game(self):
        self.state.start_game()
        self.entities.reset()
        self.bargains.reset()
        self.active_options.clear()
        self.selected_card_index = 0
        self.selected_feedback = None
        self.feedback_timer = 0
        self.auto_restart_timer = 0
        self.game_over_timer = 0
        self.touch_left = False
        self.touch_right = False
        self._raw_left_prev = False
        self._raw_right_prev = False
        self._invert_left_stroke = False
        self._invert_right_stroke = False
        self.reset_stars()

    def apply_control_inversion(self, raw_left: bool, raw_right: bool) -> Tuple[bool, bool]:
        """Apply Wrath curse: +5% chance per Wrath pact (capped at 50%) that pressing a steering button does the opposite."""
        err_chance = getattr(self.state, "wrath_error_chance", 0.0)

        # Detect fresh press for Left (rising edge)
        if raw_left and not self._raw_left_prev:
            self._invert_left_stroke = (random.random() < err_chance) if err_chance > 0 else False
        elif not raw_left:
            self._invert_left_stroke = False
        self._raw_left_prev = raw_left

        # Detect fresh press for Right (rising edge)
        if raw_right and not self._raw_right_prev:
            self._invert_right_stroke = (random.random() < err_chance) if err_chance > 0 else False
        elif not raw_right:
            self._invert_right_stroke = False
        self._raw_right_prev = raw_right

        eff_left = False
        eff_right = False

        if raw_left:
            if self._invert_left_stroke:
                eff_right = True
            else:
                eff_left = True

        if raw_right:
            if self._invert_right_stroke:
                eff_left = True
            else:
                eff_right = True

        return eff_left, eff_right

    def update_input(self):
        if pyxel is None:
            return

        # Keyboard input: A / D and Left / Right arrows
        k_left = pyxel.btn(pyxel.KEY_LEFT) or pyxel.btn(pyxel.KEY_A)
        k_right = pyxel.btn(pyxel.KEY_RIGHT) or pyxel.btn(pyxel.KEY_D)

        # Mobile touch / mouse input: 2 on-screen buttons
        t_left = False
        t_right = False
        if pyxel.btn(pyxel.MOUSE_BUTTON_LEFT):
            mx = pyxel.mouse_x
            my = pyxel.mouse_y
            # Bottom touch zone / button press
            if my >= 350:
                if mx < self.SCREEN_WIDTH / 2.0:
                    t_left = True
                else:
                    t_right = True

        self.touch_left = t_left
        self.touch_right = t_right

        raw_l = k_left or t_left
        raw_r = k_right or t_right
        eff_l, eff_r = self.apply_control_inversion(raw_l, raw_r)

        self.state._input_left = eff_l
        self.state._input_right = eff_r

    def update(self):
        if pyxel is None:
            return

        # X key: On TITLE screen = quit game (no-op in browser); During gameplay = return to title menu
        if pyxel.btnp(pyxel.KEY_X):
            if self.state.current_state == GameState.TITLE:
                if sys.platform != "emscripten":
                    pyxel.quit()
            else:
                # Return to title screen from any gameplay state
                self.state.current_state = GameState.TITLE
                self.state.reset()
                self.entities.reset()
                self.bargains.reset()
                self.active_options.clear()
                self.selected_card_index = 0
                self.selected_feedback = None
                self.feedback_timer = 0
                self.auto_restart_timer = 0
                self.game_over_timer = 0
                self.reset_stars()

        # Toggle Dev mode dynamically with '`' (backtick / grave)
        if pyxel.btnp(pyxel.KEY_BACKQUOTE):
            self.dev_mode = not self.dev_mode

        # Toggle Bot mode dynamically with 'B' key (dev mode only)
        if self.dev_mode and pyxel.btnp(pyxel.KEY_B):
            self.bot_mode = not self.bot_mode
            self.bot.reset()

        # Toggle Video Recording with 'V' key (dev mode only)
        if self.dev_mode and pyxel.btnp(pyxel.KEY_V):
            self.video_recorder.toggle(pyxel)

        # Toggle Invulnerability (God Mode) with 'G' key (dev mode only)
        if self.dev_mode and pyxel.btnp(pyxel.KEY_G):
            self.state.godmode = not self.state.godmode

        # In Dev Mode: Number keys 1 to 7 apply fixed pacts directly (Canonical Order)
        if self.dev_mode:
            pact_keys = [
                (pyxel.KEY_1, SinType.PRIDE),
                (pyxel.KEY_2, SinType.GREED),
                (pyxel.KEY_3, SinType.LUST),
                (pyxel.KEY_4, SinType.ENVY),
                (pyxel.KEY_5, SinType.GLUTTONY),
                (pyxel.KEY_6, SinType.WRATH),
                (pyxel.KEY_7, SinType.SLOTH),
            ]
            for key, sin in pact_keys:
                if pyxel.btnp(key):
                    fb = self.bargains.apply_bargain(sin, self.state, self.entities)
                    self.selected_feedback = fb
                    self.feedback_timer = 90
                    if self.state.current_state == GameState.KAIROS:
                        self.state.resume_chronos()

            # Keys Q, W, E, R, T, Y, U reduce corresponding Faustian bargain level
            reduce_keys = [
                (pyxel.KEY_Q, SinType.PRIDE),
                (pyxel.KEY_W, SinType.GREED),
                (pyxel.KEY_E, SinType.LUST),
                (pyxel.KEY_R, SinType.ENVY),
                (pyxel.KEY_T, SinType.GLUTTONY),
                (pyxel.KEY_Y, SinType.WRATH),
                (pyxel.KEY_U, SinType.SLOTH),
            ]
            for key, sin in reduce_keys:
                if pyxel.btnp(key):
                    fb = self.bargains.reduce_bargain(sin, self.state, self.entities)
                    self.selected_feedback = fb
                    self.feedback_timer = 90

        # Comma (',') and Period ('.') cycle through all 20 divergent aesthetic themes (available to all players)
        if pyxel.btnp(pyxel.KEY_COMMA):
            self.current_theme_index = (self.current_theme_index - 1) % len(ALL_THEMES)
            self.theme_banner_timer = 90
        elif pyxel.btnp(pyxel.KEY_PERIOD):
            self.current_theme_index = (self.current_theme_index + 1) % len(ALL_THEMES)
            self.theme_banner_timer = 90

        # Enforce speed handicap in physics when bot is active
        self.state._bot_speed_handicap = self.bot.config.speed_handicap if self.bot_mode else 1.0

        # Feedback banner timer
        if self.feedback_timer > 0:
            self.feedback_timer -= 1

        # Theme banner timer
        if self.theme_banner_timer > 0:
            self.theme_banner_timer -= 1

        # State dispatch
        if self.state.current_state == GameState.TITLE:
            # Check touch/mouse clicks on interactive UI buttons
            if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
                mx, my = pyxel.mouse_x, pyxel.mouse_y
                # 1. Prev Theme button [x=60..290, y=312..366] (3-line height: 54px)
                if 60 <= mx <= 290 and 312 <= my <= 366:
                    self.current_theme_index = (self.current_theme_index - 1) % len(ALL_THEMES)
                    self.theme_banner_timer = 45
                    return
                # 2. Next Theme button [x=310..540, y=312..366] (3-line height: 54px)
                elif 310 <= mx <= 540 and 312 <= my <= 366:
                    self.current_theme_index = (self.current_theme_index + 1) % len(ALL_THEMES)
                    self.theme_banner_timer = 45
                    return
                # 3. Lore & Learn button [x=60..540, y=396..450] (3-line height: 54px)
                elif 60 <= mx <= 540 and 396 <= my <= 450:
                    self.state.current_state = GameState.LORE
                    self.lore_page = 0
                    return
                # 4. Anywhere else (e.g. start button [x=50..550, y=566..620] or general tap) starts game
                else:
                    self.start_new_game()
                    return

            # Check if player pressed 'L' for Lore & How to Play (only [L], no [H])
            if pyxel.btnp(pyxel.KEY_L):
                self.state.current_state = GameState.LORE
                self.lore_page = 0
                return

            # Start game with lateral keys only (no space, no enter)
            if (self.bot_mode or
                pyxel.btnp(pyxel.KEY_LEFT) or pyxel.btnp(pyxel.KEY_RIGHT) or
                pyxel.btnp(pyxel.KEY_A) or pyxel.btnp(pyxel.KEY_D)):
                self.start_new_game()

        elif self.state.current_state == GameState.LORE:
            # Multi-page navigation: Left/A = previous page; Right/D = next page (or exit on last page)
            if pyxel.btnp(pyxel.KEY_LEFT) or pyxel.btnp(pyxel.KEY_A):
                if self.lore_page > 0:
                    self.lore_page -= 1
            elif pyxel.btnp(pyxel.KEY_RIGHT) or pyxel.btnp(pyxel.KEY_D):
                if self.lore_page < self.MAX_LORE_PAGES - 1:
                    self.lore_page += 1
                else:
                    # Pressing right on the last page returns to title screen
                    self.state.current_state = GameState.TITLE
                    self.lore_page = 0
                    return
            # Return to Title on X, Return, L, H, or mouse/touch tap (Escape and Space do NOT exit)
            elif (pyxel.btnp(pyxel.KEY_X) or pyxel.btnp(pyxel.KEY_RETURN) or
                  pyxel.btnp(pyxel.KEY_L) or pyxel.btnp(pyxel.KEY_H) or
                  pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT)):
                self.state.current_state = GameState.TITLE
                self.lore_page = 0
                return

        elif self.state.current_state == GameState.CHRONOS:
            if self.bot_mode:
                b_left, b_right = self.bot.decide_chronos_input(self.state, self.entities)
                eff_l, eff_r = self.apply_control_inversion(b_left, b_right)
                self.state._input_left = eff_l
                self.state._input_right = eff_r
            else:
                self.update_input()

            self.state.update_timers()
            self.entities.update(self.state)

            # Check if Kairos was triggered this frame (Exactly 2 bargain options)
            if self.state.current_state == GameState.KAIROS:
                self.audio.play_kairos(pyxel)
                self.active_options = self.bargains.draw_options(2)
                self.selected_card_index = -1  # Must release and re-press to choose
                
                # Check if lateral controls were held down when Kairos struck
                held_left = (
                    pyxel.btn(pyxel.KEY_LEFT) or pyxel.btn(pyxel.KEY_A) or
                    (pyxel.btn(pyxel.MOUSE_BUTTON_LEFT) and pyxel.mouse_x < self.SCREEN_WIDTH / 2.0)
                )
                held_right = (
                    pyxel.btn(pyxel.KEY_RIGHT) or pyxel.btn(pyxel.KEY_D) or
                    (pyxel.btn(pyxel.MOUSE_BUTTON_LEFT) and pyxel.mouse_x >= self.SCREEN_WIDTH / 2.0)
                )
                self.kairos_left_released = not held_left
                self.kairos_right_released = not held_right
                if self.bot_mode:
                    self.bot.target_card_index = None
                    self.selected_card_index = 0

            # Check if Game Over triggered
            if self.state.current_state == GameState.GAMEOVER:
                self.audio.play_death(pyxel)
                self.auto_restart_timer = 0

        elif self.state.current_state == GameState.KAIROS:
            # Kairos time circuit breaker: 2 options (Left vs Right)
            instant_seal = False
            if self.bot_mode:
                if self.selected_card_index < 0:
                    self.selected_card_index = 0
                frames_rem = self.state.KAIROS_FRAMES - self.state.kairos_timer
                if pyxel.frame_count % 2 == 0:
                    b_left, b_right, b_seal = self.bot.decide_kairos_choice(
                        self.active_options, self.selected_card_index, frames_remaining=frames_rem, frames_elapsed=self.state.kairos_timer
                    )
                    if b_left and self.selected_card_index > 0:
                        self.selected_card_index -= 1
                    elif b_right and self.selected_card_index < len(self.active_options) - 1:
                        self.selected_card_index += 1
                    elif b_seal:
                        instant_seal = True
            else:
                # Track release state of lateral controls
                is_left_now = (
                    pyxel.btn(pyxel.KEY_LEFT) or pyxel.btn(pyxel.KEY_A) or
                    (pyxel.btn(pyxel.MOUSE_BUTTON_LEFT) and pyxel.mouse_x < self.SCREEN_WIDTH / 2.0)
                )
                is_right_now = (
                    pyxel.btn(pyxel.KEY_RIGHT) or pyxel.btn(pyxel.KEY_D) or
                    (pyxel.btn(pyxel.MOUSE_BUTTON_LEFT) and pyxel.mouse_x >= self.SCREEN_WIDTH / 2.0)
                )

                if not is_left_now:
                    self.kairos_left_released = True
                if not is_right_now:
                    self.kairos_right_released = True

                # Lockout: don't accept user input for the 1st 1.0 second (30 frames)
                if self.state.kairos_timer >= 30:
                    # Selection triggers only on fresh press AFTER releasing Chronos steering
                    move_left = (
                        (pyxel.btnp(pyxel.KEY_LEFT) or pyxel.btnp(pyxel.KEY_A) or
                         (pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT) and pyxel.mouse_x < self.SCREEN_WIDTH / 2.0))
                        and self.kairos_left_released
                    )
                    move_right = (
                        (pyxel.btnp(pyxel.KEY_RIGHT) or pyxel.btnp(pyxel.KEY_D) or
                         (pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT) and pyxel.mouse_x >= self.SCREEN_WIDTH / 2.0))
                        and self.kairos_right_released
                    )

                    if move_left:
                        self.selected_card_index = 0
                        instant_seal = True
                    elif move_right:
                        self.selected_card_index = 1
                        instant_seal = True


            # Advance Kairos timer
            self.state.update_timers()

            # Check if 2.0s timeout expired without choice: Instant Death!
            if self.state.current_state == GameState.GAMEOVER:
                self.audio.play_death(pyxel)
                self.game_over_timer = 0
                self.auto_restart_timer = 0
                return

            # Confirm selection on manual seal
            if instant_seal:
                if 0 <= self.selected_card_index < len(self.active_options):
                    chosen_sin, _, _ = self.active_options[self.selected_card_index]
                    feedback = self.bargains.apply_bargain(chosen_sin, self.state, self.entities)
                    self.selected_feedback = feedback
                    self.feedback_timer = 50
                    self.audio.play_collect(pyxel)
                self.state.resume_chronos()
                if self.bot_mode:
                    self.bot.reset_kairos()

        elif self.state.current_state == GameState.GAMEOVER:
            self.game_over_timer += 1

            # Check touch/click on [X] RETURN TO MENU button [x=60..540, y=530..608] or pressing [X] key
            btn_clicked = False
            if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
                mx, my = pyxel.mouse_x, pyxel.mouse_y
                if 60 <= mx <= 540 and 530 <= my <= 608:
                    btn_clicked = True
            if btn_clicked or pyxel.btnp(pyxel.KEY_X):
                self.state.current_state = GameState.TITLE
                self.state.reset()
                self.entities.reset()
                self.bargains.reset()
                self.active_options.clear()
                self.selected_card_index = 0
                self.selected_feedback = None
                self.feedback_timer = 0
                self.auto_restart_timer = 0
                self.game_over_timer = 0
                self.reset_stars()
                return

            if self.bot_mode:
                self.auto_restart_timer += 1
                # Bot waits 6.0s (180 frames) before restarting instead of immediately restarting
                if self.auto_restart_timer >= 180 and self.game_over_timer >= 180:
                    self.auto_restart_timer = 0
                    self.start_new_game()
                elif self.game_over_timer >= 60:
                    if (pyxel.btnp(pyxel.KEY_LEFT) or pyxel.btnp(pyxel.KEY_RIGHT) or
                        pyxel.btnp(pyxel.KEY_A) or pyxel.btnp(pyxel.KEY_D) or
                        pyxel.btnp(pyxel.KEY_R) or
                        pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT)):
                        self.auto_restart_timer = 0
                        self.start_new_game()
            else:
                # Require minimum 2.0s (60 frames) debounce before allowing restart
                if self.game_over_timer >= 60:
                    if (pyxel.btnp(pyxel.KEY_LEFT) or pyxel.btnp(pyxel.KEY_RIGHT) or
                        pyxel.btnp(pyxel.KEY_A) or pyxel.btnp(pyxel.KEY_D) or
                        pyxel.btnp(pyxel.KEY_R) or
                        pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT)):
                        self.start_new_game()

    def draw(self):
        if pyxel is None:
            return

        # Camera tracking (SkiFree style horizontal centering on player)
        if self.state.current_state in (GameState.CHRONOS, GameState.KAIROS):
            cam_x = int(self.entities.player.x - self.SCREEN_WIDTH / 2.0)
        else:
            cam_x = 0

        # Screen shake offset
        ox = 0
        oy = 0
        if self.state.shake_intensity > 0:
            ox = random.randint(-int(self.state.shake_intensity), int(self.state.shake_intensity))
            oy = random.randint(-int(self.state.shake_intensity), int(self.state.shake_intensity))
        pyxel.camera(cam_x + ox, oy)

        # Get active aesthetic theme
        theme = get_theme(self.current_theme_index)

        # Clear background void according to active theme
        bg_col = theme.get_clear_color(self.state.greed_active)
        pyxel.cls(bg_col)

        # Compute Chronos progress towards Kairos (0.0 to 1.0)
        prog = 0.0
        if self.state.current_state == GameState.CHRONOS:
            prog = self.state.chronos_timer / float(self.state.CHRONOS_FRAMES)

        # Telemetry payload for status-display themes (e.g. Reader Mode)
        active_pacts = []
        pact_counts = {}
        pact_count = 0
        if hasattr(self, "bargains") and hasattr(self.bargains, "selection_counts"):
            for sin in CANONICAL_SINS:
                cnt = self.bargains.selection_counts.get(sin, 0)
                if cnt > 0:
                    active_pacts.append(sin.name.title())
                    pact_counts[sin.name.title()] = cnt
            pact_count = len(self.bargains.history) if self.bargains.history else sum(self.bargains.selection_counts.values())
        telemetry = {
            "hearts": self.state.hearts,
            "max_hearts": getattr(self.state, "max_hearts", 5),
            "score": self.state.score,
            "time_elapsed": self.state.chronos_timer / 30.0,
            "time_remaining": max(0.0, (self.state.CHRONOS_FRAMES - self.state.chronos_timer) / 30.0),
            "pacts": active_pacts,
            "pact_counts": pact_counts,
            "pact_count": pact_count,
        }

        # Compute descent distance (continuous falling distance in-game, gentle drift on title)
        dist = int(self.state.distance) if self.state.distance > 0 else int(pyxel.frame_count * 3.0)

        # Render procedural background for active theme
        theme.render(
            pyxel,
            cam_x=cam_x,
            prog=prog,
            dist=dist,
            screen_w=self.SCREEN_WIDTH,
            screen_h=self.SCREEN_HEIGHT,
            is_greed=self.state.greed_active,
            telemetry=telemetry,
        )

        if self.state.current_state == GameState.TITLE:
            pyxel.camera(0, 0)
            self.draw_title_screen()
            if self.theme_banner_timer > 0:
                self.draw_theme_banner()
            return
        elif self.state.current_state == GameState.LORE:
            pyxel.camera(0, 0)
            self.draw_lore_screen()
            return

        is_reader = getattr(theme, "is_reader_mode", False)

        # Draw Sand grains in world coordinates with theme-aware palette (alpha = 0.60 in Reader Mode)
        if is_reader and hasattr(pyxel, "dither"):
            pyxel.dither(0.60)

        s_pal = theme.sand
        for sand in self.entities.sands:
            # Frustum / viewport culling: only render grains that are within or directly approaching viewport
            if not (cam_x - 30 <= sand.x <= cam_x + self.SCREEN_WIDTH + 30 and -30 <= sand.y <= self.SCREEN_HEIGHT + 30):
                continue
            c = s_pal.body if (pyxel.frame_count // 3 + int(sand.shimmer_phase * 4)) % 2 == 0 else s_pal.border
            if getattr(sand, "is_fat", False):
                # Cast shadow
                pyxel.rect(int(sand.x - 11), int(sand.y - 11), 26, 26, s_pal.shadow)
                # Golden / thematic chunk body
                c_fat = s_pal.fat_body if (pyxel.frame_count // 3 + int(sand.shimmer_phase * 4)) % 2 == 0 else s_pal.fat_border
                pyxel.rect(int(sand.x - 13), int(sand.y - 13), 26, 26, c_fat)
                pyxel.rectb(int(sand.x - 13), int(sand.y - 13), 26, 26, s_pal.shadow)
                pyxel.rectb(int(sand.x - 12), int(sand.y - 12), 24, 24, s_pal.fat_border)
                pyxel.rect(int(sand.x - 5), int(sand.y - 5), 10, 10, s_pal.fat_glint)
            else:
                # Cast shadow
                pyxel.rect(int(sand.x - 4), int(sand.y - 4), 10, 10, s_pal.shadow)
                # Grain body
                pyxel.rect(int(sand.x - 5), int(sand.y - 5), 10, 10, c)
                pyxel.rectb(int(sand.x - 5), int(sand.y - 5), 10, 10, s_pal.shadow)
                pyxel.rect(int(sand.x - 2), int(sand.y - 2), 4, 4, s_pal.glint)  # Center glint

        # Draw Glass shards in world coordinates with theme-aware palette (alpha = 0.30 in Reader Mode)
        if is_reader and hasattr(pyxel, "dither"):
            pyxel.dither(0.30)
        for shard in self.entities.shards:
            # Frustum / viewport culling: only render shards that are within or directly approaching viewport
            if not (cam_x - 40 <= shard.x <= cam_x + self.SCREEN_WIDTH + 40 and -40 <= shard.y <= self.SCREEN_HEIGHT + 40):
                continue
            self.draw_glass_shard(shard, theme.shard)

        # Draw Player Hourglass in world coordinates with theme-aware palette (alpha = 0.60 in Reader Mode)
        if is_reader and hasattr(pyxel, "dither"):
            pyxel.dither(0.60)
        self.draw_player_hourglass(theme.hourglass)

        # Restore 100% full opacity
        if is_reader and hasattr(pyxel, "dither"):
            pyxel.dither(1.0)


        # Reset camera for screen-space UI overlays (Vignette, HUD, Modals)
        pyxel.camera(0, 0)

        # Render Vignette Mask (Darkness bounds centered on player on screen)
        render_vignette(
            self.SCREEN_WIDTH / 2.0,
            self.entities.player.y,
            self.state.vignette_radius,
            self.SCREEN_WIDTH,
            self.SCREEN_HEIGHT,
            pyxel,
            inner_radius=self.state.vignette_inner_radius,
        )

        # Draw HUD (Score, Hearts, Active Pacts, Elapsed Time)
        self.draw_hud()

        # In Pro Mode: dual vertical countdown bars at extreme left and right borders during Chronos
        if self.state.current_state == GameState.CHRONOS:
            self.draw_pro_mode_chronos_bars()

        # Draw on-screen mobile touch buttons during Chronos descent (mobile only)
        if self.state.current_state == GameState.CHRONOS and self.is_mobile:
            self.draw_touch_buttons()

        # Draw active modal overlays
        if self.state.current_state == GameState.KAIROS:
            self.draw_kairos_modal()
        elif self.state.current_state == GameState.GAMEOVER:
            self.draw_game_over_screen()

        # Selected feedback banner
        if self.feedback_timer > 0 and self.selected_feedback:
            self.draw_feedback_banner()

        # Theme switcher banner (displayed on switch via ',' and '.' keys)
        if self.theme_banner_timer > 0:
            self.draw_theme_banner()

        # Developer debug overlay (toggled with '`')
        if self.dev_mode:
            self.draw_dev_overlay()

        # Capture video frame for MP4 export
        self.video_recorder.record_frame(pyxel)

    def draw_braided_sandfall_terrain(self, cam_x: int, prog: float = 0.0):
        """Draw dynamic Braided Sandfall / Landslide terrain:
        A fluid, rushing yellow sand river combining braided sandbars, cascading chutes,
        velocity shearing flumes, and churning granular froth across an infinite horizontal expanse.
        """
        dist = int(self.state.distance)
        is_greed = self.state.greed_active

        # Palette configuration for daylight vs blood-sun Greed
        if is_greed:
            col_crest = 8            # Blood red crest
            col_shadow = 0           # Pitch black shadow
            col_shadow_deep = 0
            col_stream = 8           # Crimson current streak
            col_froth = 14           # Pale pink froth glint
            col_spray = 8            # Crimson spray mote
            col_rock = 0             # Black stone
            col_rock_hl = 8          # Red glint
        elif prog > 0.85:
            # Imminent Kairos urgency glint
            flash = (pyxel.frame_count // 3) % 2 == 0
            col_crest = 10 if flash else 7
            col_shadow = 9
            col_shadow_deep = 4
            col_stream = 10 if flash else 9
            col_froth = 7
            col_spray = 10
            col_rock = 4
            col_rock_hl = 7
        else:
            col_crest = 7            # Sunlit warm white ridge crest
            col_shadow = 9           # Warm orange/tan slope shadow
            col_shadow_deep = 4      # Rich amber-brown base shadow
            col_stream = 9           # Golden amber current streamline
            col_froth = 7            # White sunlit sand froth
            col_spray = 10           # Bright golden spray glint
            col_rock = 4             # Sandstone pebble
            col_rock_hl = 7          # Pebble glint

        # -------------------------------------------------------------
        # 1. CASCADING FLUMES & STREAMLINES (Velocity-Shearing Sandfall)
        # -------------------------------------------------------------
        # Vertical flow columns spaced across the infinite horizontal expanse
        start_col = int((cam_x - 30) // 22) * 22
        end_col = cam_x + self.SCREEN_WIDTH + 30
        cycle_h = 320

        for col_x in range(start_col, end_col, 22):
            col_hash = (col_x * 73856093) & 0xFFFFFF
            # Distinct speed multipliers (1.18x to 1.50x) create visible fluid velocity shear
            spd = 1.18 + 0.32 * ((col_hash % 100) / 100.0)

            for offset_y in (0, 110, 220):
                sy = (offset_y - int(dist * spd)) % cycle_h - 20
                if -20 <= sy <= self.SCREEN_HEIGHT + 20:
                    streak_len = 10 + (col_hash % 14)
                    meander = int(5.0 * math.sin((sy + dist * 0.04) * 0.015 + col_x * 0.03))
                    fx = col_x + meander
                    pyxel.line(fx, sy, fx, sy + streak_len, col_stream)
                    # Occasional white froth glint at the head of the rush
                    if (col_hash >> 6) % 3 == 0:
                        pyxel.pset(fx, sy, col_froth)

        # -------------------------------------------------------------
        # 2. BRAIDED SANDBAR BANKS & WEAVING CHANNELS (Braided Sand River)
        # -------------------------------------------------------------
        bar_spacing = 140
        for base_y in range(-bar_spacing, self.SCREEN_HEIGHT + bar_spacing, bar_spacing):
            y_anchor = base_y - (dist % bar_spacing)
            prev_x = cam_x - 24
            prev_y = y_anchor + int(24 * math.sin((prev_x + base_y) * 0.009) + 10 * math.cos(prev_x * 0.021))

            for x in range(cam_x - 18, cam_x + self.SCREEN_WIDTH + 24, 6):
                cur_y = y_anchor + int(24 * math.sin((x + base_y) * 0.009) + 10 * math.cos(x * 0.021))
                if -30 <= cur_y <= self.SCREEN_HEIGHT + 30:
                    # Braided channel mask: breaches allow rushing chutes to carve through
                    chute_val = math.sin(x * 0.007 + (base_y // bar_spacing) * 1.5)
                    if chute_val > 0.40:
                        # Deep channel chute: sand pours through the breach
                        if x % 18 == 0:
                            pyxel.pset(x, cur_y, col_froth)
                            pyxel.pset(x + 2, cur_y + 1, col_stream)
                    else:
                        # Exposed sandbar ridge
                        pyxel.line(prev_x, prev_y, x, cur_y, col_crest)
                        pyxel.line(prev_x, prev_y + 1, x, cur_y + 1, col_shadow)
                        if x % 12 == 0:
                            pyxel.line(x, cur_y + 2, x, cur_y + 5, col_shadow_deep)
                prev_x = x
                prev_y = cur_y

        # -------------------------------------------------------------
        # 3. GRANULAR FROTH & SHOAL PEBBLES (Local Texture & Grit)
        # -------------------------------------------------------------
        grid_sz = 80
        min_gx = int((cam_x - 40) // grid_sz)
        max_gx = int((cam_x + self.SCREEN_WIDTH + 40) // grid_sz) + 1
        min_gy = int((dist - 40) // grid_sz)
        max_gy = int((dist + self.SCREEN_HEIGHT + 40) // grid_sz) + 1

        for gy in range(min_gy, max_gy):
            cell_sy = gy * grid_sz - dist
            for gx in range(min_gx, max_gx):
                cell_wx = gx * grid_sz
                h = ((gx * 374761393) ^ (gy * 668265263)) & 0xFFFFFF
                fx = cell_wx + (h % 50) + 15
                fy = cell_sy + ((h >> 6) % 50) + 15

                if -15 <= fy <= self.SCREEN_HEIGHT + 15:
                    mote_type = (h >> 12) % 100
                    if mote_type < 40:
                        # Granular spray motes in the wind
                        pyxel.pset(fx, fy, col_spray)
                        pyxel.pset(fx + 3, fy + 2, col_froth)
                    elif mote_type < 70:
                        # Miniature sand ripple arc
                        pyxel.line(fx - 4, fy, fx + 4, fy, col_stream)
                        pyxel.pset(fx, fy + 1, col_shadow_deep)
                    else:
                        # Sandstone pebble on the shoal
                        pyxel.rect(fx, fy, 3, 2, col_rock)
                        pyxel.pset(fx, fy, col_rock_hl)

    def draw_skifree_desert_terrain(self, cam_x: int, prog: float = 0.0):
        """Draw procedural braided sandfall terrain (maintains backward compatibility)."""
        self.draw_braided_sandfall_terrain(cam_x, prog)

    def draw_atmospheric_dunes_and_glass_background(self, cam_x: int, prog: float = 0.0):
        """Backward-compatible alias for draw_braided_sandfall_terrain."""
        self.draw_braided_sandfall_terrain(cam_x, prog)

    def draw_celestial_depth_astrolabe(self, cam_x: int, prog: float = 0.0):
        """Backward-compatible alias for draw_braided_sandfall_terrain."""
        self.draw_braided_sandfall_terrain(cam_x, prog)

    def draw_pro_mode_player_display(self, px: float, py: float, theme):
        """Render clinical aeronautical flight-director display for Pro Mode:
        - Box / Circle showing exact hitbox boundaries.
        - Cross displacement indicating lateral velocity (left/right of center).
        - Cross rotation indicating lateral acceleration (counter-clockwise on left accel, clockwise on right accel).
        - Dotted circle indicating Lust sand magnet reach.
        """
        is_dark = (theme.id == 2 or theme.clear_color == 0)
        col_main = 7 if is_dark else 0       # White in dark mode, Black in light mode
        col_cross = 10 if is_dark else 8     # Bright gold in dark mode, Crimson in light mode
        col_accent = 12 if is_dark else 1    # Cyan in dark mode, Navy in light mode

        player = self.entities.player

        # 1. Exact Hitbox Boundary (Rectangle 60x40 and inscribed Hitbox Circle radius=20)
        box_w, box_h = HourglassPlayer.WIDTH, HourglassPlayer.HEIGHT
        hx = int(round(px - box_w / 2.0))
        hy = int(round(py - box_h / 2.0))
        pyxel.rectb(hx, hy, box_w, box_h, col_main)

        # Inscribed hitbox circle with radius = box_h / 2 = 20
        hitbox_r = box_h // 2
        pyxel.circb(int(round(px)), int(round(py)), hitbox_r, col_main)

        # Center reference point
        pyxel.pset(int(round(px)), int(round(py)), col_main)

        # 2. Dotted Lust Range Circle (Rendered as 2x2 solid blocks with high-contrast color for visibility)
        lust_r = getattr(self.state, "lust_attract_radius", 0.0)
        if lust_r > 0:
            num_dots = max(16, int(lust_r * 0.40))
            col_lust = 10 if is_dark else 8  # Vibrant Gold in Dark Mode, Deep Crimson in Light Mode
            for d_idx in range(num_dots):
                if d_idx % 2 == 0:
                    continue
                angle = (d_idx / float(num_dots)) * (2.0 * math.pi)
                dx = int(round(px + math.cos(angle) * lust_r))
                dy = int(round(py + math.sin(angle) * lust_r))
                if 0 <= dy < self.SCREEN_HEIGHT:
                    pyxel.rect(dx - 1, dy - 1, 2, 2, col_lust)

        # 3. Flight Cross (Position indicates lateral speed, Rotation indicates acceleration)
        max_shift = 22.0
        shift_x = max(-max_shift, min(max_shift, player.vx * 3.2))
        cross_cx = px + shift_x
        cross_cy = py

        accel_val = getattr(player, "accel_display", player.vx)
        phi = max(-0.55, min(0.55, accel_val * 0.22))
        cos_p = math.cos(phi)
        sin_p = math.sin(phi)

        arm_len = 14.0
        # Horizontal cross arm (3px thick)
        h_x1 = int(round(cross_cx - arm_len * cos_p))
        h_y1 = int(round(cross_cy - arm_len * sin_p))
        h_x2 = int(round(cross_cx + arm_len * cos_p))
        h_y2 = int(round(cross_cy + arm_len * sin_p))
        nx = -sin_p
        ny = cos_p
        pyxel.line(h_x1, h_y1, h_x2, h_y2, col_cross)
        pyxel.line(int(round(h_x1 + nx)), int(round(h_y1 + ny)), int(round(h_x2 + nx)), int(round(h_y2 + ny)), col_cross)
        pyxel.line(int(round(h_x1 - nx)), int(round(h_y1 - ny)), int(round(h_x2 - nx)), int(round(h_y2 - ny)), col_cross)

        # Vertical cross arm (3px thick)
        v_x1 = int(round(cross_cx + arm_len * sin_p))
        v_y1 = int(round(cross_cy - arm_len * cos_p))
        v_x2 = int(round(cross_cx - arm_len * sin_p))
        v_y2 = int(round(cross_cy + arm_len * cos_p))
        pyxel.line(v_x1, v_y1, v_x2, v_y2, col_cross)
        pyxel.line(int(round(v_x1 + cos_p)), int(round(v_y1 + sin_p)), int(round(v_x2 + cos_p)), int(round(v_y2 + sin_p)), col_cross)
        pyxel.line(int(round(v_x1 - cos_p)), int(round(v_y1 - sin_p)), int(round(v_x2 - cos_p)), int(round(v_y2 - sin_p)), col_cross)

        # Center reticle dot (3x3 block)
        pyxel.rect(int(round(cross_cx - 1)), int(round(cross_cy - 1)), 3, 3, col_cross)

    def draw_player_hourglass(self, pal: Optional[HourglassPalette] = None):
        """Draw horizontal hourglass sprite (60x40) that tilts dynamically with control velocity, or flight director in Pro Mode."""
        theme = get_theme(self.current_theme_index)
        if pal is None:
            pal = theme.hourglass
        player = self.entities.player
        px = player.x
        py = player.y

        # Pro Mode: Replace hourglass sprite with clinical flight director display
        if theme.name.startswith("PRO MODE"):
            if self.state.invulnerable_timer > 0 and (self.state.invulnerable_timer // 3) % 2 == 1:
                return
            self.draw_pro_mode_player_display(px, py, theme)
            return

        # Cast drop shadow on the terrain below the hourglass
        shadow_y = int(py + 16)
        pyxel.line(int(px - 18), shadow_y, int(px + 18), shadow_y, pal.shadow)
        pyxel.line(int(px - 22), shadow_y + 1, int(px + 22), shadow_y + 1, pal.shadow)
        pyxel.line(int(px - 18), shadow_y + 2, int(px + 18), shadow_y + 2, pal.shadow)

        # Invulnerability flash
        if self.state.invulnerable_timer > 0 and (self.state.invulnerable_timer // 3) % 2 == 1:
            return

        # Tilt angle based on lateral velocity (clamped to +/- 22 degrees)
        tilt = max(-0.38, min(0.38, player.vx * 0.038))
        cos_t = math.cos(tilt)
        sin_t = math.sin(tilt)

        def rot(lx: float, ly: float) -> Tuple[int, int]:
            rx = px + lx * cos_t - ly * sin_t
            ry = py + lx * sin_t + ly * cos_t
            return int(round(rx)), int(round(ry))

        # 1. Left Brass Cap (horizontal orientation: vertical end bar at lx = -30 to -24)
        for yo in range(-15, 16):
            p1 = rot(-29, yo)
            p2 = rot(-24, yo)
            pyxel.line(p1[0], p1[1], p2[0], p2[1], pal.caps)
        # Left Brass Highlight & Rivet
        hl1 = rot(-26, -6)
        hl2 = rot(-26, 6)
        pyxel.line(hl1[0], hl1[1], hl2[0], hl2[1], pal.cap_hl)
        riv_l = rot(-26, 0)
        pyxel.pset(riv_l[0], riv_l[1], pal.cap_rivet)

        # 2. Right Brass Cap (vertical end bar at lx = 24 to 30)
        for yo in range(-15, 16):
            p1 = rot(24, yo)
            p2 = rot(29, yo)
            pyxel.line(p1[0], p1[1], p2[0], p2[1], pal.caps)
        # Right Brass Highlight & Rivet
        hr1 = rot(26, -6)
        hr2 = rot(26, 6)
        pyxel.line(hr1[0], hr1[1], hr2[0], hr2[1], pal.cap_hl)
        riv_r = rot(26, 0)
        pyxel.pset(riv_r[0], riv_r[1], pal.cap_rivet)

        # 3. Left Bulb Glass Walls (tapering from lx=-24 to waist lx=-4)
        pyxel.line(*rot(-24, -15), *rot(-4, -5), pal.glass_walls)
        pyxel.line(*rot(-24, 15), *rot(-4, 5), pal.glass_walls)

        # 4. Right Bulb Glass Walls (tapering from waist lx=4 to lx=24)
        pyxel.line(*rot(4, -5), *rot(24, -15), pal.glass_walls)
        pyxel.line(*rot(4, 5), *rot(24, 15), pal.glass_walls)

        # 5. Center Waist Neck
        pyxel.line(*rot(-4, -5), *rot(4, -5), pal.waist_neck)
        pyxel.line(*rot(-4, 5), *rot(4, 5), pal.waist_neck)

        # 6. Bulb Sand Levels (dynamically shifting with tilt)
        tilt_ratio = max(-1.0, min(1.0, tilt / 0.38)) if abs(tilt) > 0.01 else 0.0
        # When tilted right (tilt > 0): left bulb drains (scale < 1.0), right bulb fills (scale > 1.0)
        # When tilted left (tilt < 0): right bulb drains (scale < 1.0), left bulb fills (scale > 1.0)
        l_scale = max(0.20, min(1.45, 1.0 - tilt_ratio * 0.50))
        r_scale = max(0.20, min(1.45, 1.0 + tilt_ratio * 0.50))
        is_score_flash = (self.state.player_score_flash_timer > 0)

        # Left Bulb Sand
        for dx in range(-21, -4, 2):
            half_h = int(13 * (abs(dx) / 24.0) * l_scale)
            if half_h > 1:
                if is_score_flash:
                    col = 7 if (self.state.player_score_flash_timer % 2 == 0) else pal.sand_a
                else:
                    col = pal.sand_a if (dx % 4 == 0) else pal.sand_b
                p_top = rot(dx, -half_h + 1)
                p_bot = rot(dx, half_h - 1)
                pyxel.line(p_top[0], p_top[1], p_bot[0], p_bot[1], col)

        # Right Bulb Sand
        for dx in range(5, 22, 2):
            half_h = int(13 * (abs(dx) / 24.0) * r_scale)
            if half_h > 1:
                if is_score_flash:
                    col = 7 if (self.state.player_score_flash_timer % 2 == 0) else pal.sand_a
                else:
                    col = pal.sand_a if (dx % 4 == 0) else pal.sand_b
                p_top = rot(dx, -half_h + 1)
                p_bot = rot(dx, half_h - 1)
                pyxel.line(p_top[0], p_top[1], p_bot[0], p_bot[1], col)

        # 8. Animated Sand Flow across waist:
        if abs(tilt) > 0.02:
            flow_sign = 1.0 if tilt > 0 else -1.0
            for i in range(3):
                frac = (player.sand_drain_phase * flow_sign + i * 0.33) % 1.0
                stream_lx = (-5.0 + frac * 10.0) * flow_sign
                stream_ly = math.sin((player.sand_drain_phase + i) * 3.14) * 1.5
                sp = rot(stream_lx, stream_ly)
                col = 7 if is_score_flash else (pal.sand_a if i == 0 else pal.sand_b)
                pyxel.rect(sp[0] - 1, sp[1] - 1, 2, 2, col)
        else:
            sp = rot(0, 0)
            col = 7 if is_score_flash else pal.sand_b
            pyxel.rect(sp[0] - 1, sp[1] - 1, 2, 2, col)

        # 9. Specular Reflections
        pyxel.line(*rot(-18, -10), *rot(-8, -5), 7)
        pyxel.line(*rot(8, -5), *rot(18, -10), 7)

    def draw_glass_shard(self, shard: GlassShard, pal: Optional[ShardPalette] = None):
        if pal is None:
            pal = get_theme(self.current_theme_index).shard
        sx = int(shard.x)
        sy = int(shard.y)
        angle = shard.rotation_angle
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)

        verts = getattr(shard, "vertices", [(0, -20), (10, 20), (-10, 15)])
        rot_pts = []
        for x, y in verts:
            rx = int(sx + x * cos_a - y * sin_a)
            ry = int(sy + x * sin_a + y * cos_a)
            rot_pts.append((rx, ry))

        x0, y0 = rot_pts[0]
        x1, y1 = rot_pts[1]
        x2, y2 = rot_pts[2]
        is_fat = getattr(shard, "is_fat", False)

        # Cast drop shadow (suppressed in Pro Mode)
        theme_name = getattr(get_theme(self.current_theme_index), "name", "")
        if self.current_theme_index not in (1, 2) and not theme_name.startswith("PRO MODE"):
            pyxel.tri(x0 + 3, y0 + 4, x1 + 3, y1 + 4, x2 + 3, y2 + 4, pal.shadow)

        if is_fat:
            # Gluttony big triangle: exact same color as regular shard
            pyxel.tri(x0, y0, x1, y1, x2, y2, pal.facet)
            pyxel.line(x0, y0, x1, y1, pal.border)
            pyxel.line(x1, y1, x2, y2, pal.border)
            pyxel.line(x2, y2, x0, y0, pal.border)
            if (pyxel.frame_count // 3) % 2 == 0:
                pyxel.line(x0, y0, x1, y1, pal.glint)
        else:
            # Facet
            pyxel.tri(x0, y0, x1, y1, x2, y2, pal.facet)
            # Razor perimeter outline
            pyxel.line(x0, y0, x1, y1, pal.border)
            pyxel.line(x1, y1, x2, y2, pal.border)
            pyxel.line(x2, y2, x0, y0, pal.border)
            # Specular glint along leading edge
            if (pyxel.frame_count // 3) % 2 == 0:
                pyxel.line(x0, y0, x1, y1, pal.glint)

    def draw_hud(self):
        theme = get_theme(self.current_theme_index)
        if getattr(theme, "is_reader_mode", False):
            # In Reader Mode: All floating UI is suppressed; telemetry is described on line 2 of text
            return

        # Transparency & theme contrast adaptation for floating HUD elements
        is_light = theme.clear_color in (7, 15, 6, 11, 14) or getattr(theme, "id", 0) in (7, 15)
        is_pro = theme.name.startswith("PRO MODE")
        is_sumie = getattr(theme, "id", 0) in (7, 8) or "SUMI" in theme.name.upper()
        is_sumie_white = is_sumie and ("WHITE" in theme.name.upper() or theme.clear_color == 7)
        kp = theme.get_kairos_palette()
        if is_sumie:
            box_bg = 7 if is_sumie_white else 0
            box_border = 0 if is_sumie_white else 7
            text_col = 0 if is_sumie_white else 7
            title_col = 0 if is_sumie_white else 7
            num_col = 0 if is_sumie_white else 7
        else:
            box_bg = 7 if is_light else 0
            box_border = 0 if is_light else (kp.border_inner if kp.border_inner != 0 else 1)
            text_col = 0 if is_light else 7
            title_col = 0 if is_light else 10
            num_col = 0 if is_light else 10
        flash_time = (pyxel.frame_count // 15) % 2 == 0 and not is_pro and not is_sumie

        def draw_hud_box(bx: int, by: int, bw: int, bh: int):
            if hasattr(pyxel, "dither"):
                pyxel.dither(0.50)
            pyxel.rect(bx, by, bw, bh, box_bg)
            if hasattr(pyxel, "dither"):
                pyxel.dither(1.0)
            pyxel.rectb(bx, by, bw, bh, box_border)
            if is_pro:
                pyxel.rectb(bx + 1, by + 1, bw - 2, bh - 2, box_border)

        # 1. Hearts container (Top Left) - translucent theme-aware container (BW in Sumi-e)
        draw_hud_box(10, 8, 174, 32)

        if is_sumie:
            heart_fill = 0 if is_sumie_white else 7
            heart_empty = 13
            heart_glint = 7 if is_sumie_white else 0
        else:
            heart_fill = 8
            heart_empty = 4 if is_light else 5
            heart_glint = 7

        for i in range(5):
            hx = 16 + i * 32
            hy = 12
            if i < self.state.hearts:
                pyxel.rect(hx + 4, hy, 8, 4, heart_fill)
                pyxel.rect(hx + 16, hy, 8, 4, heart_fill)
                pyxel.rect(hx, hy + 4, 28, 8, heart_fill)
                pyxel.rect(hx + 4, hy + 12, 20, 4, heart_fill)
                pyxel.rect(hx + 8, hy + 16, 12, 4, heart_fill)
                pyxel.rect(hx + 12, hy + 20, 4, 4, heart_fill)
                pyxel.rect(hx + 4, hy + 4, 4, 4, heart_glint)  # Specular glint
            else:
                pyxel.rectb(hx, hy + 4, 28, 16, heart_empty)

        # 2. Elapsed Time container (Top Center) - [x=220, w=160] (BW in Sumi-e)
        draw_hud_box(220, 8, 160, 32)

        elapsed_sec = self.state.total_frames / 30.0
        time_str = f"TIME: {elapsed_sec:04.1f} s"
        if is_sumie:
            t_col = 0 if is_sumie_white else 7
        else:
            t_col = (8 if is_light else 10) if flash_time else text_col
        time_w = len(time_str) * 12 - 2
        draw_text_scaled(220 + (160 - time_w) // 2, 15, time_str, t_col, scale=2)

        # 3. Score container (Top Right) - [x=390, w=200, no overlap with Time box]
        draw_hud_box(390, 8, 200, 32)

        score_fmt = f"{self.state.score:,}".replace(",", " ")
        score_str = f"SCORE: {score_fmt}"
        draw_text_scaled(398, 15, score_str, num_col, scale=2)

        # Multiplier (inside score container at right)
        if self.state.score_multiplier > 1.05:
            mult_str = f"x{self.state.score_multiplier:.1f}"
            if is_sumie:
                mult_col = 0 if is_sumie_white else 7
            else:
                mult_col = 8 if is_light else 9
            draw_text_scaled(540, 15, mult_str, mult_col, scale=2)

        # 4. Vertical Pacts List in Catholic Canonical Order at Top Right (All 7 always listed, BW in Sumi-e)
        pacts_box_w = 205
        pacts_box_h = 142
        pacts_box_x = self.SCREEN_WIDTH - pacts_box_w - 10
        pacts_box_y = 44
        draw_hud_box(pacts_box_x, pacts_box_y, pacts_box_w, pacts_box_h)

        draw_text_scaled(pacts_box_x + 8, pacts_box_y + 4, "FAUSTIAN PACTS", title_col, scale=2)
        for idx, sin in enumerate(CANONICAL_SINS):
            k = self.bargains.selection_counts.get(sin, 0)
            row_y = pacts_box_y + 22 + idx * 16
            sin_lbl = sin.name.capitalize()
            # High-contrast font colors: Black on white in light themes, White on dark in dark themes (BW in Sumi-e)
            if is_sumie:
                col = 0 if is_sumie_white else 7
                sin_col = (0 if is_sumie_white else 7) if k > 0 else 13
            else:
                col = (8 if is_light else 10) if k > 0 else (0 if is_light else 7)
                sin_col = SIN_CARD_COLORS.get(sin, 1)
            # Draw color swatch matching the background of the pact card
            pyxel.rect(pacts_box_x + 5, row_y + 2, 5, 11, sin_col)
            draw_text_scaled(pacts_box_x + 14, row_y, f"{idx+1}. {sin_lbl}", col, scale=2)
            k_str = str(k)
            k_w = get_text_width_5x7(k_str, scale=2)
            draw_text_scaled(pacts_box_x + pacts_box_w - 14 - k_w, row_y, k_str, col, scale=2)

        # Minimal Status Badges when active (drawn below hearts at top left)
        badge_y = 44
        if self.bot_mode and not self.dev_mode:
            draw_hud_box(10, badge_y, 100, 20)
            if is_sumie:
                bot_col = 0 if is_sumie_white else 7
            else:
                bot_col = 11 if not is_light else 3
            draw_text_scaled(15, badge_y + 4, "[BOT ON]", bot_col, scale=2)
            badge_y += 24

        if self.video_recorder.is_recording and not self.dev_mode:
            rec_secs = self.video_recorder.frames_recorded // 30
            flash = (pyxel.frame_count // 6) % 2 == 0
            draw_hud_box(10, badge_y, 100, 20)
            if is_sumie:
                rec_col = 0 if is_sumie_white else 7
            else:
                rec_col = 8 if flash else text_col
            draw_text_scaled(15, badge_y + 4, f"REC {rec_secs:02d} s", rec_col, scale=2)
            badge_y += 24

        # Invulnerability Badge
        if self.state.godmode:
            draw_hud_box(10, badge_y, 100, 20)
            if is_sumie:
                god_col = 0 if is_sumie_white else 7
            else:
                god_col = 10 if not is_light else 8
            draw_text_scaled(15, badge_y + 4, "[GODMODE]", god_col, scale=2)
            badge_y += 24

        # Greed Borrowed Time Warning Indicator
        if self.state.greed_active:
            flash = (pyxel.frame_count // 5) % 2 == 0
            if is_sumie:
                col = (0 if is_sumie_white else 7) if flash else 13
            else:
                col = 8 if flash else 9
            if self.dev_mode:
                msg = f"BORROWED TIME ({self.state.greed_timer / 30.0:.1f} s)"
            else:
                msg = "BORROWED TIME"
            draw_text_scaled(self.SCREEN_WIDTH // 2 - 80, 48, msg, col, scale=2)

    def draw_pro_mode_chronos_bars(self):
        """Draw dual vertical telemetry countdown progress bars pinned to extreme left and right borders in Pro Mode.

        Indicates Chronos countdown progression towards Kairos from top to bottom.
        """
        theme = get_theme(self.current_theme_index)
        if not theme.name.startswith("PRO MODE"):
            return
        if self.state.current_state != GameState.CHRONOS:
            return

        prog = min(1.0, max(0.0, self.state.chronos_timer / float(self.state.CHRONOS_FRAMES)))
        bar_w = 10
        fill_h = int(self.SCREEN_HEIGHT * prog)

        is_dark = (theme.clear_color == 0)

        # Track colors (background track)
        track_bg = 1 if is_dark else 6     # Navy in dark, soft grey in light
        border_col = 5 if is_dark else 0   # Slate grey in dark, black in light
        inner_border_col = 7 if is_dark else 5

        # Bar fill color: steady color, DO NOT blink near the end
        if prog > 0.85:
            # Imminent Kairos urgency: steady high-contrast warning (Crimson red)
            fill_col = 8
        elif is_dark:
            fill_col = 10  # High-vis safety yellow in Pro Dark
        else:
            fill_col = 0   # Pitch-black obsidian in Pro Light

        # 1. Left border progress bar (x = 0..bar_w-1)
        pyxel.rect(0, 0, bar_w, self.SCREEN_HEIGHT, track_bg)
        if fill_h > 0:
            pyxel.rect(0, 0, bar_w, fill_h, fill_col)
            pyxel.line(0, fill_h, bar_w - 1, fill_h, 7 if is_dark else 0)
        # Double borders along right edge of left bar
        pyxel.line(bar_w - 1, 0, bar_w - 1, self.SCREEN_HEIGHT, border_col)
        pyxel.line(bar_w, 0, bar_w, self.SCREEN_HEIGHT, inner_border_col)

        # 2. Right border progress bar (x = (SCREEN_WIDTH - bar_w)..SCREEN_WIDTH)
        rx = self.SCREEN_WIDTH - bar_w
        pyxel.rect(rx, 0, bar_w, self.SCREEN_HEIGHT, track_bg)
        if fill_h > 0:
            pyxel.rect(rx, 0, bar_w, fill_h, fill_col)
            pyxel.line(rx, fill_h, self.SCREEN_WIDTH - 1, fill_h, 7 if is_dark else 0)
        # Double borders along left edge of right bar
        pyxel.line(rx, 0, rx, self.SCREEN_HEIGHT, border_col)
        pyxel.line(rx - 1, 0, rx - 1, self.SCREEN_HEIGHT, inner_border_col)

    def draw_kairos_modal(self):
        """Draw 2-column Kairos modal navigated strictly via Left/Right arrows or A/D."""
        modal_x = 30
        modal_y = 60
        modal_w = 540
        modal_h = 680

        theme = get_theme(self.current_theme_index)
        kp = theme.get_kairos_palette()
        is_pro_mode = theme.name.startswith("PRO MODE")

        # Full-screen ambient dimmer overlay over background gameplay world
        if hasattr(pyxel, "dither"):
            pyxel.dither(0.50)
        pyxel.rect(0, 0, self.SCREEN_WIDTH, self.SCREEN_HEIGHT, kp.dimmer)
        if hasattr(pyxel, "dither"):
            pyxel.dither(1.0)

        # Modal backdrop: SOLID opaque box with crisp double border matching current theme
        pyxel.rect(modal_x, modal_y, modal_w, modal_h, kp.modal_bg)
        pyxel.rectb(modal_x, modal_y, modal_w, modal_h, kp.border_outer)
        pyxel.rectb(modal_x + 2, modal_y + 2, modal_w - 4, modal_h - 4, kp.border_inner)

        # Header: Centered "KAIROS TIME" (scale=3), removed "BORROW YOUR TIME"
        center_modal_x = modal_x + modal_w // 2
        header_text = "KAIROS TIME"
        header_w = get_text_width_5x7(header_text, scale=3)
        draw_text_scaled(center_modal_x - header_w // 2, modal_y + 20, header_text, kp.header_title, scale=3)

        # 2 Wide Columns matching Left and Right
        col_w = 228
        col_gap = 20
        start_x = modal_x + 32
        col_y = modal_y + 70
        col_h = 530

        # 2.0s vertical side timers draining top going down (Empty space drops from top to bottom)
        ratio = max(0.0, min(1.0, 1.0 - (self.state.kairos_timer / float(self.state.KAIROS_FRAMES))))
        fill_h = int(col_h * ratio)
        drain_offset = col_h - fill_h
        urgent_flash = kp.con_label if (pyxel.frame_count // 3) % 2 == 0 else kp.header_sub
        bar_col = urgent_flash if ratio < 0.30 else kp.timer_bar_fill

        for bar_x in [modal_x + 8, modal_x + modal_w - 20]:
            pyxel.rect(bar_x, col_y, 12, col_h, kp.timer_bar_bg)
            if fill_h > 0:
                pyxel.rect(bar_x, col_y + drain_offset, 12, fill_h, bar_col)
            pyxel.rectb(bar_x, col_y, 12, col_h, kp.timer_bar_border)

        col_labels = ["< STEER LEFT <", "> STEER RIGHT >"]

        for i, (sin, defn, k) in enumerate(self.active_options):
            cx = start_x + i * (col_w + col_gap)
            is_selected = (i == self.selected_card_index)

            # Card background & frame: in Pro Mode, color-match each pact to its unique signature color
            if is_pro_mode:
                bg_col = SIN_CARD_COLORS.get(sin, 1)
                border_col = 10 if (is_selected and (pyxel.frame_count // 3) % 2 == 0) else (7 if is_selected else (0 if theme.id == 7 else 5))
            else:
                bg_col = kp.card_bg
                flash_col = kp.sin_title_selected if (pyxel.frame_count // 3) % 2 == 0 else kp.card_border_selected
                border_col = flash_col if is_selected else kp.card_border

            if sin == SinType.GLUTTONY and not is_pro_mode:
                # Gluttony: card intentionally bulges and bends the frame outward around the oversized title!
                bulge_x = 22
                y_t1 = col_y + 34
                y_t2 = col_y + 44
                y_t3 = col_y + 88
                y_t4 = col_y + 98

                # Fill main rectangular card body
                pyxel.rect(cx, col_y, col_w, col_h, bg_col)
                # Fill bulging belly background around the oversized title
                pyxel.rect(cx - bulge_x, y_t2, col_w + bulge_x * 2, y_t3 - y_t2, bg_col)
                pyxel.tri(cx, y_t1, cx - bulge_x, y_t2, cx, y_t2, bg_col)
                pyxel.tri(cx + col_w, y_t1, cx + col_w + bulge_x, y_t2, cx + col_w, y_t2, bg_col)
                pyxel.tri(cx, y_t4, cx - bulge_x, y_t3, cx, y_t3, bg_col)
                pyxel.tri(cx + col_w, y_t4, cx + col_w + bulge_x, y_t3, cx + col_w, y_t3, bg_col)

                # Draw bent frame outline
                def draw_bent_outline(d: int, col: int):
                    bx = bulge_x + d
                    # Top & Bottom edges
                    pyxel.line(cx - d, col_y - d, cx + col_w + d, col_y - d, col)
                    pyxel.line(cx - d, col_y + col_h + d, cx + col_w + d, col_y + col_h + d, col)
                    # Right side bending outward
                    pyxel.line(cx + col_w + d, col_y - d, cx + col_w + d, y_t1, col)
                    pyxel.line(cx + col_w + d, y_t1, cx + col_w + bx, y_t2, col)
                    pyxel.line(cx + col_w + bx, y_t2, cx + col_w + bx, y_t3, col)
                    pyxel.line(cx + col_w + bx, y_t3, cx + col_w + d, y_t4, col)
                    pyxel.line(cx + col_w + d, y_t4, cx + col_w + d, col_y + col_h + d, col)
                    # Left side bending outward
                    pyxel.line(cx - d, col_y - d, cx - d, y_t1, col)
                    pyxel.line(cx - d, y_t1, cx - bx, y_t2, col)
                    pyxel.line(cx - bx, y_t2, cx - bx, y_t3, col)
                    pyxel.line(cx - bx, y_t3, cx - d, y_t4, col)
                    pyxel.line(cx - d, y_t4, cx - d, col_y + col_h + d, col)

                draw_bent_outline(0, border_col)
                if is_selected:
                    draw_bent_outline(1, kp.card_border_selected)
            else:
                pyxel.rect(cx, col_y, col_w, col_h, bg_col)
                pyxel.rectb(cx, col_y, col_w, col_h, border_col)
                if is_selected:
                    pyxel.rectb(cx + 1, col_y + 1, col_w - 2, col_h - 2, kp.card_border_selected)

            # Directional badge (justified center)
            if is_selected:
                badge_col = kp.badge_bg_selected
                badge_txt_col = kp.badge_text_selected
            elif is_pro_mode:
                badge_col = 0 if theme.id == 6 else 7
                badge_txt_col = 7 if theme.id == 6 else 0
            else:
                badge_col = kp.badge_bg
                badge_txt_col = kp.badge_text
            pyxel.rect(cx + 14, col_y + 12, col_w - 28, 28, badge_col)
            badge_lbl = col_labels[i]
            badge_w = len(badge_lbl) * 12 - 2
            draw_text_scaled(cx + col_w // 2 - badge_w // 2, col_y + 18, badge_lbl, badge_txt_col, scale=2)

            center_x = cx + col_w // 2

            if is_pro_mode:
                # Pro Mode: Exactly 3 lines, high visual density & clarity
                # Determine high-contrast text color against card background (WCAG AAA)
                # Wrath is color 8 (Red) -> white text (7) gives crystal clear contrast!
                if bg_col in (7, 9, 10, 11, 14, 15):
                    txt_col = 0  # Black on light/yellow/peach
                    accent_col = 8 if is_selected else 0
                else:
                    txt_col = 7  # Crisp white on red/navy/dark
                    accent_col = 10 if is_selected else 7

                # Line 1: 2-letter abbreviation (1st capitalized, 2nd lowercase, e.g. 'Pd' for Pride)
                # Rendered in VERY huge font, 3x bigger than normal (scale=6)
                abbr = SIN_PRO_ABBREVIATIONS.get(sin, sin.name[:2].title())
                abbr_w = len(abbr) * 36 - 6
                abbr_y = col_y + 70
                draw_text_scaled(center_x - abbr_w // 2, abbr_y, abbr, accent_col, scale=6)

                # Line 2: Sin name written in full like normal (scale=2)
                full_name = defn.name.upper()
                name_w = len(full_name) * 12 - 2
                name_y = col_y + 160
                draw_text_scaled(center_x - name_w // 2, name_y, full_name, txt_col, scale=2)

                # Line 3: Level number alone without the word "level" in 3x huge font (scale=6)
                next_lvl = k + 1
                lvl_num_str = str(next_lvl)
                lvl_num_w = len(lvl_num_str) * 36 - 6
                lvl_num_y = col_y + 220
                draw_text_scaled(center_x - lvl_num_w // 2, lvl_num_y, lvl_num_str, accent_col, scale=6)

                # Selection status button at bottom
                if is_selected:
                    pyxel.rect(cx + 14, col_y + col_h - 48, col_w - 28, 34, kp.selected_btn_bg)
                    sel_lbl = "SELECTED"
                    sel_w = len(sel_lbl) * 12 - 2
                    draw_text_scaled(center_x - sel_w // 2, col_y + col_h - 40, sel_lbl, kp.selected_btn_text, scale=2)
                else:
                    pyxel.rectb(cx + 14, col_y + col_h - 48, col_w - 28, 34, txt_col)
                    btn_lbl = "STEER TO CHOOSE"
                    btn_w = len(btn_lbl) * 12 - 2
                    draw_text_scaled(center_x - btn_w // 2, col_y + col_h - 40, btn_lbl, txt_col, scale=2)

            elif getattr(theme, "is_reader_mode", False):
                # Reader Mode: Title scale=4, Covenant level, then maximized KJV paragraph (scale=2)
                name = defn.name.upper()
                title_col = kp.sin_title_selected if is_selected else kp.sin_title
                if sin == SinType.GLUTTONY:
                    title_scale = 5
                    char_gap = 4
                    title_w = get_text_width_5x7(name, scale=title_scale, char_gap=char_gap)
                    try:
                        draw_text_scaled(cx, col_y + 46, name, title_col, scale=title_scale, char_gap=char_gap)
                    except TypeError:
                        draw_text_scaled(cx, col_y + 46, name, title_col, scale=title_scale)
                else:
                    title_scale = 4
                    title_w = get_text_width_5x7(name, scale=title_scale)
                    draw_text_scaled(center_x - title_w // 2, col_y + 46, name, title_col, scale=title_scale)

                lvl_str = f"COVENANT {k + 1}"
                lvl_w = len(lvl_str) * 12 - 2
                draw_text_scaled(center_x - lvl_w // 2, col_y + 88, lvl_str, kp.level_text, scale=2)

                pyxel.line(cx + 14, col_y + 110, cx + col_w - 14, col_y + 110, kp.divider)

                # Maximized KJV narrative paragraph: text is aligned center, not justified
                kjv_text = KJV_SIN_PARAGRAPHS.get(sin, "")
                draw_centered_paragraph(cx + 14, col_y + 118, col_w - 28, kjv_text, kp.pro_text, scale=2, line_spacing=12)

                # Selection status button at bottom
                if is_selected:
                    pyxel.rect(cx + 14, col_y + col_h - 48, col_w - 28, 34, kp.selected_btn_bg)
                    sel_lbl = "SELECTED"
                    sel_w = len(sel_lbl) * 12 - 2
                    draw_text_scaled(center_x - sel_w // 2, col_y + col_h - 40, sel_lbl, kp.selected_btn_text, scale=2)
                else:
                    pyxel.rectb(cx + 14, col_y + col_h - 48, col_w - 28, 34, kp.card_border)
                    btn_lbl = "STEER TO CHOOSE"
                    btn_w = len(btn_lbl) * 12 - 2
                    draw_text_scaled(center_x - btn_w // 2, col_y + col_h - 40, btn_lbl, kp.footer_text, scale=2)

            else:
                # Standard Mode: Title scale=4 for all pacts, Gluttony scale=5 char_gap=4 spanning exact width 228
                name = defn.name.upper()
                title_col = kp.sin_title_selected if is_selected else kp.sin_title
                if sin == SinType.GLUTTONY:
                    title_scale = 5
                    char_gap = 4
                    title_w = get_text_width_5x7(name, scale=title_scale, char_gap=char_gap)
                    # title_w is 228, starting at cx with zero margins left and right!
                    try:
                        draw_text_scaled(cx, col_y + 46, name, title_col, scale=title_scale, char_gap=char_gap)
                    except TypeError:
                        draw_text_scaled(cx, col_y + 46, name, title_col, scale=title_scale)
                else:
                    title_scale = 4
                    title_w = get_text_width_5x7(name, scale=title_scale)
                    title_x = center_x - title_w // 2
                    draw_text_scaled(title_x, col_y + 46, name, title_col, scale=title_scale)

                # Level indicator
                lvl_str = f"LEVEL: {k}"
                lvl_w = len(lvl_str) * 12 - 2
                lvl_x = center_x - lvl_w // 2
                lvl_col = kp.sin_title_selected if is_selected else kp.level_text
                draw_text_scaled(lvl_x, col_y + 88, lvl_str, lvl_col, scale=2)

                # Visual divider
                pyxel.line(cx + 14, col_y + 106, cx + col_w - 14, col_y + 106, kp.divider)

                # Boon section
                draw_text_scaled(cx + 16, col_y + 120, "PRO (NOW):", kp.pro_label, scale=2)
                if sin == SinType.PRIDE:
                    group_name = ["Pairs", "Triplets", "Quadruplets", "Quintuplets"][min(3, k)]
                    draw_text_scaled(cx + 16, col_y + 144, "Sand Clusters", kp.pro_text, scale=2)
                    draw_text_scaled(cx + 16, col_y + 168, f"{group_name} (+{k+1} grains)", kp.pro_label, scale=1)
                elif sin == SinType.ENVY:
                    next_k = k + 1
                    k_eff = next_k + 2
                    outer_preview = int(1200.0 * (0.8 ** k_eff))
                    mega_r = outer_preview * 2
                    draw_text_scaled(cx + 16, col_y + 144, "Tidal Pull", kp.pro_text, scale=2)
                    draw_text_scaled(cx + 16, col_y + 168, f"Pull {mega_r}px Radius (2s)", kp.pro_label, scale=1)
                elif sin == SinType.GREED:
                    draw_text_scaled(cx + 16, col_y + 144, "Score Multiplier", kp.pro_text, scale=2)
                    draw_text_scaled(cx + 16, col_y + 168, "x110% per sand", kp.pro_label, scale=1)
                elif sin == SinType.SLOTH:
                    draw_text_scaled(cx + 16, col_y + 144, "Lazy Reprieve", kp.pro_text, scale=2)
                    draw_text_scaled(cx + 16, col_y + 168, "Aligned Grains (~5s Safe)", kp.pro_label, scale=1)
                elif sin == SinType.LUST:
                    draw_text_scaled(cx + 16, col_y + 144, "Sand Magnet", kp.pro_text, scale=2)
                    draw_text_scaled(cx + 16, col_y + 168, f"{100 + k * 50}px (Permanent)", kp.pro_label, scale=1)
                elif sin == SinType.GLUTTONY:
                    next_k = k + 1
                    next_fat = (1.0 - (0.90 ** next_k)) * 100.0
                    draw_text_scaled(cx + 16, col_y + 144, "Fat Grains", kp.pro_text, scale=2)
                    draw_text_scaled(cx + 16, col_y + 168, f"3x Pts, {next_fat:.1f}% Fat (10x)", kp.pro_label, scale=1)
                elif sin == SinType.WRATH:
                    draw_text_scaled(cx + 16, col_y + 144, "Shard Wipe", kp.pro_text, scale=2)
                    draw_text_scaled(cx + 16, col_y + 168, "3.0s Wipe (1600px Blast)", kp.pro_label, scale=1)
                else:
                    draw_text_scaled(cx + 16, col_y + 144, f"+{defn.boon_name}", kp.pro_text, scale=2)
                    draw_text_scaled(cx + 16, col_y + 168, f"{defn.boon_base} {defn.boon_unit}", kp.pro_label, scale=1)

                # Visual divider
                pyxel.line(cx + 14, col_y + 196, cx + col_w - 14, col_y + 196, kp.divider)

                # Curse section
                draw_text_scaled(cx + 16, col_y + 210, "CON (FOREVER):", kp.con_label, scale=2)
                if sin == SinType.PRIDE:
                    draw_text_scaled(cx + 16, col_y + 234, "Descent Speed", kp.con_text, scale=2)
                    draw_text_scaled(cx + 16, col_y + 258, "+25% Fall Velocity", kp.con_label, scale=1)
                elif sin == SinType.GREED:
                    draw_text_scaled(cx + 16, col_y + 234, "Borrowed Time", kp.con_text, scale=2)
                    draw_text_scaled(cx + 16, col_y + 258, "10.0s (LETHAL END)", kp.con_label, scale=1)
                elif sin == SinType.ENVY:
                    next_k = k + 1
                    k_eff = next_k + 2
                    outer_preview = int(1200.0 * (0.8 ** k_eff))
                    inner_preview = int(1000.0 * (0.8 ** (k_eff + 1)))
                    draw_text_scaled(cx + 16, col_y + 234, "Vignette Vision", kp.con_text, scale=2)
                    draw_text_scaled(cx + 16, col_y + 258, f"{outer_preview}/{inner_preview} px", kp.con_label, scale=1)
                elif sin == SinType.SLOTH:
                    drag = 0.20 * (1.5 ** k) * 100
                    draw_text_scaled(cx + 16, col_y + 234, "Delayed Danger", kp.con_text, scale=2)
                    draw_text_scaled(cx + 16, col_y + 258, f"Vengeful Wave & -{drag:.0f}% Drag", kp.con_label, scale=1)
                elif sin == SinType.LUST:
                    draw_text_scaled(cx + 16, col_y + 234, "Hazard Magnet", kp.con_text, scale=2)
                    draw_text_scaled(cx + 16, col_y + 258, f"{100 + k * 50}px (Permanent)", kp.con_label, scale=1)
                elif sin == SinType.GLUTTONY:
                    next_k = k + 1
                    next_fat = (1.0 - (0.90 ** next_k)) * 100.0
                    draw_text_scaled(cx + 16, col_y + 234, "Fat Glass Shards", kp.con_text, scale=2)
                    draw_text_scaled(cx + 16, col_y + 258, f"{next_fat:.1f}% Fat (10x Area)", kp.con_label, scale=1)
                elif sin == SinType.WRATH:
                    next_err = min(50, (k + 1) * 5)
                    draw_text_scaled(cx + 16, col_y + 234, "Control Error", kp.con_text, scale=2)
                    draw_text_scaled(cx + 16, col_y + 258, f"+5% Invert Error ({next_err}% cap 50%)", kp.con_label, scale=1)
                else:
                    draw_text_scaled(cx + 16, col_y + 234, f"-{defn.curse_name}", kp.con_text, scale=2)
                    draw_text_scaled(cx + 16, col_y + 258, f"{defn.curse_base} {defn.curse_unit}", kp.con_label, scale=1)

                # Compounding note
                note_str = "COMPOUNDS PER PACT"
                note_w = get_text_width_5x7(note_str, scale=1)
                draw_text_scaled(center_x - note_w // 2, col_y + 320, note_str, kp.level_text, scale=1)

                # Selection status
                if is_selected:
                    pyxel.rect(cx + 14, col_y + col_h - 48, col_w - 28, 34, kp.selected_btn_bg)
                    sel_w = len("SELECTED") * 12 - 2
                    draw_text_scaled(center_x - sel_w // 2, col_y + col_h - 40, "SELECTED", kp.selected_btn_text, scale=2)

        # Footer instructions
        if not self.bot_mode and self.state.kairos_timer < 30:
            rem_lock = (30 - self.state.kairos_timer + 29) // 30
            draw_text_scaled(modal_x + 85, modal_y + modal_h - 44, f"STABILIZING CIRCUIT ({rem_lock}s)...", kp.header_sub, scale=2)
        else:
            draw_text_scaled(modal_x + 50, modal_y + modal_h - 44, "STEER LEFT OR RIGHT TO SELECT", kp.footer_text, scale=2)
        limit_sec = self.state.KAIROS_FRAMES / 30.0
        draw_text_scaled(modal_x + 55, modal_y + modal_h - 22, f"CHOOSE OR DIE: {limit_sec:.1f}s TIME LIMIT", kp.footer_warn, scale=2)

    def draw_feedback_banner(self):
        fb = self.selected_feedback
        if not fb:
            return
        theme = get_theme(self.current_theme_index)
        kp = theme.get_kairos_palette()
        # Position banner safely above bottom window / buttons with translucent dither
        if hasattr(pyxel, "dither"):
            pyxel.dither(0.70)
        pyxel.rect(40, 540, 520, 44, kp.modal_bg)
        if hasattr(pyxel, "dither"):
            pyxel.dither(1.0)
        pyxel.rectb(40, 540, 520, 44, kp.border_outer)
        txt = f"PACT SEALED: {fb['sin'].upper()}!"
        draw_text_scaled(70, 554, txt, kp.sin_title_selected, scale=2)

    def draw_title_screen(self):
        theme = get_theme(self.current_theme_index)
        is_sumie = getattr(theme, "id", 0) in (7, 8) or "SUMI" in theme.name.upper()
        is_sumie_white = is_sumie and ("WHITE" in theme.name.upper() or theme.clear_color == 7)

        # Header plaque for high-contrast presentation on any background theme
        if is_sumie:
            plaque_bg = 7 if is_sumie_white else 0
            plaque_b1 = 0 if is_sumie_white else 7
            plaque_b2 = 13
            logo_col = 0 if is_sumie_white else 7
            logo_shadow = 13 if is_sumie_white else 0
            sub_col = 0 if is_sumie_white else 7
            sub_shadow = 13 if is_sumie_white else 0
            author_col = 0 if is_sumie_white else 7
            author_shadow = 13 if is_sumie_white else 0
            sub1_col = 13
            sub2_col = 0 if is_sumie_white else 7
            sub3_col = 13 if is_sumie_white else 7
        else:
            plaque_bg = 0
            plaque_b1 = 10
            plaque_b2 = 9
            logo_col = 10
            logo_shadow = 4
            sub_col = 9
            sub_shadow = 4
            author_col = 7
            author_shadow = 4
            sub1_col = 6
            sub2_col = 10
            sub3_col = 8

        pyxel.rect(40, 30, 520, 160, plaque_bg)
        pyxel.rectb(40, 30, 520, 160, plaque_b1)
        pyxel.rectb(42, 32, 516, 156, plaque_b2)

        # Pulsing logo centered mathematically with dark drop shadow for high contrast
        draw_text_centered(42, "GRAIN OF DOUBT", logo_shadow, scale=4)
        draw_text_centered(40, "GRAIN OF DOUBT", logo_col, scale=4)

        draw_text_centered(78, "PYWEEK 42 : BORROWED TIME", sub_shadow, scale=2)
        draw_text_centered(76, "PYWEEK 42 : BORROWED TIME", sub_col, scale=2)

        draw_text_centered(102, "BY ARIAN PRABOWO", author_shadow, scale=2)
        draw_text_centered(100, "BY ARIAN PRABOWO", author_col, scale=2)

        # Subtitles centered in crisp daylight contrast
        draw_text_centered(126, "FALL DOWN THE DESERT SLOPE", sub1_col, scale=2)
        draw_text_centered(144, "COLLECT GOLDEN SAND FOR POINTS", sub2_col, scale=2)
        draw_text_centered(162, "DODGE LETHAL FALLING GLASS SHARDS", sub3_col, scale=2)

        # Controls & Themes box (Clean, elevated positioning without redundant plaque)
        box_y = 184
        box_h = 312
        if is_sumie:
            ctrl_bg = 7 if is_sumie_white else 0
            ctrl_b1 = 0 if is_sumie_white else 7
            ctrl_hdr = 0 if is_sumie_white else 7
            ctrl_txt = 0 if is_sumie_white else 7
            act_col = 0 if is_sumie_white else 7
            btn_bg = 7 if is_sumie_white else 0
            btn_border = 0 if is_sumie_white else 7
            btn_txt = 0 if is_sumie_white else 7
        else:
            ctrl_bg = 1
            ctrl_b1 = 5
            ctrl_hdr = 10
            ctrl_txt = 7
            act_col = 10 if (self.current_theme_index in (1, 2) or getattr(theme, "is_reader_mode", False)) else 9
            btn_bg = 0
            btn_border = 10
            btn_txt = 7

        pyxel.rect(40, box_y, 520, box_h, ctrl_bg)
        pyxel.rectb(40, box_y, 520, box_h, ctrl_b1)
        if is_sumie:
            pyxel.rectb(42, box_y + 2, 516, box_h - 4, 13)

        draw_text_scaled(60, box_y + 8, "CONTROLS", ctrl_hdr, scale=2)
        draw_text_scaled(60, box_y + 24, "KEYBOARD: [A] / [D]", ctrl_txt, scale=2)
        draw_text_scaled(60, box_y + 40, "KEYBOARD: [LEFT] / [RIGHT] ARROWS", ctrl_txt, scale=2)
        draw_text_scaled(60, box_y + 56, "TOUCH: [LEFT] / [RIGHT] ON-SCREEN", ctrl_txt, scale=2)

        # Line break before Themes (at least 1 full line gap: 36px)
        draw_text_scaled(60, box_y + 92, "SELECT THEMES", ctrl_hdr, scale=2)
        draw_text_scaled(60, box_y + 110, f"({self.current_theme_index + 1}/10) {theme.name}", act_col, scale=2)

        # Big Prev & Next Theme Touch Buttons (3 lines in height: h=54)
        btn_prev_x, btn_prev_y, btn_prev_w, btn_prev_h = 60, box_y + 128, 230, 54
        pyxel.rect(btn_prev_x, btn_prev_y, btn_prev_w, btn_prev_h, btn_bg)
        pyxel.rectb(btn_prev_x, btn_prev_y, btn_prev_w, btn_prev_h, btn_border)
        draw_text_scaled(btn_prev_x + 22, btn_prev_y + 20, "< [,] PREV THEME", btn_txt, scale=2)

        btn_next_x, btn_next_y, btn_next_w, btn_next_h = 310, box_y + 128, 230, 54
        pyxel.rect(btn_next_x, btn_next_y, btn_next_w, btn_next_h, btn_bg)
        pyxel.rectb(btn_next_x, btn_next_y, btn_next_w, btn_next_h, btn_border)
        draw_text_scaled(btn_next_x + 22, btn_next_y + 20, "NEXT THEME [.] >", btn_txt, scale=2)

        # 1 full line of space before SHORTCUTS (gap = 84px from y_theme_name, >= 36px)
        draw_text_scaled(60, box_y + 194, "SHORTCUTS", ctrl_hdr, scale=2)

        # Big Lore & Learn Touch Button (3 lines in height: h=54)
        btn_lore_x, btn_lore_y, btn_lore_w, btn_lore_h = 60, box_y + 212, 480, 54
        pyxel.rect(btn_lore_x, btn_lore_y, btn_lore_w, btn_lore_h, btn_bg)
        pyxel.rectb(btn_lore_x, btn_lore_y, btn_lore_w, btn_lore_h, btn_border)
        lore_btn_col = btn_txt if is_sumie else 10
        draw_text_scaled(btn_lore_x + 86, btn_lore_y + 20, "[L] LORE & LEARN TO PLAY", lore_btn_col, scale=2)

        # Space below [X] QUIT GAME is 20px (ends at 476, box ends at 496)
        draw_text_scaled(60, box_y + 278, "[X] QUIT GAME", ctrl_txt, scale=2)

        # Photosensitivity & Pro Mode suggestion directly above start prompt
        if is_sumie:
            warn_bg = 7 if is_sumie_white else 0
            warn_b = 0 if is_sumie_white else 7
            warn_hdr = 0 if is_sumie_white else 7
            warn_t1 = 0 if is_sumie_white else 7
            warn_t2 = 13
        else:
            warn_bg = 0
            warn_b = 8
            warn_hdr = 8
            warn_t1 = 7
            warn_t2 = 6

        pyxel.rect(40, 508, 520, 48, warn_bg)
        pyxel.rectb(40, 508, 520, 48, warn_b)
        draw_text_centered(514, "PHOTOSENSITIVITY WARNING", warn_hdr, scale=2)
        draw_text_centered(532, "Rapid motion and flashing visuals in some themes.", warn_t1, scale=1)
        draw_text_centered(544, "Switch to PRO MODE (Themes 2 & 3) for calm high-contrast clinical view.", warn_t2, scale=1)

        # Start prompt: "PRESS ARROWS OR HERE TO START" (3 lines in height: h=54)
        blink = (pyxel.frame_count // 12) % 2 == 0
        if blink:
            if is_sumie:
                prompt_bg = 7 if is_sumie_white else 0
                prompt_b = 0 if is_sumie_white else 7
                prompt_txt = 0 if is_sumie_white else 7
            else:
                prompt_bg = 0
                prompt_b = 10
                prompt_txt = 10
            pyxel.rect(50, 566, 500, 54, prompt_bg)
            pyxel.rectb(50, 566, 500, 54, prompt_b)
            draw_text_centered(586, "PRESS ARROWS OR HERE TO START", prompt_txt, scale=2)

        # Dedicated Dev Mode box at bottom when dev_mode is active
        if self.dev_mode:
            self.draw_dev_box(box_y=630, translucent=False)

        # Draw the 2 mobile buttons at bottom of title screen (mobile only)
        if self.is_mobile:
            self.draw_touch_buttons()

    def draw_lore_screen(self):
        """Render dedicated Multi-Page Lore & Learn to Play manual."""
        theme = get_theme(self.current_theme_index)
        is_sumie = getattr(theme, "id", 0) in (7, 8) or "SUMI" in theme.name.upper()
        is_sumie_white = is_sumie and ("WHITE" in theme.name.upper() or theme.clear_color == 7)

        box_x = 24
        box_y = 16
        box_w = 552
        box_h = 768

        # Main background container with gold double frame (BW in Sumi-e)
        if is_sumie:
            bg_col = 7 if is_sumie_white else 0
            b1_col = 0 if is_sumie_white else 7
            b2_col = 13
            hdr_col = 0 if is_sumie_white else 7
            sub_col = 13
            div_col = 13
            txt_col = 0 if is_sumie_white else 7
            warn_col = 0 if is_sumie_white else 7
            nav_col = 0 if is_sumie_white else 7
            ret_col = 0 if is_sumie_white else 7
        else:
            bg_col = 0
            b1_col = 10
            b2_col = 9
            hdr_col = 10
            sub_col = 6
            div_col = 5
            txt_col = 7
            warn_col = 8
            nav_col = 10
            ret_col = 10

        pyxel.rect(box_x, box_y, box_w, box_h, bg_col)
        pyxel.rectb(box_x, box_y, box_w, box_h, b1_col)
        pyxel.rectb(box_x + 2, box_y + 2, box_w - 4, box_h - 4, b2_col)

        # Header Title with dynamic Page Number
        draw_text_scaled(box_x + 24, box_y + 16, f"GRAIN OF DOUBT : LORE & LEARN [{self.lore_page + 1}/{self.MAX_LORE_PAGES}]", hdr_col, scale=2)
        subtitles = [
            "THE PREMISE & BORROWED TIME",
            "COSMOLOGY : CHRONOS & KAIROS",
            "FAUSTIAN PACTS (PART 1: SINS 1-4)",
            "FAUSTIAN PACTS (PART 2: SINS 5-7)",
            "THEMES, PRO MODE & DEDICATION",
        ]
        draw_text_scaled(box_x + 24, box_y + 40, subtitles[self.lore_page], sub_col, scale=2)
        pyxel.line(box_x + 16, box_y + 60, box_x + box_w - 16, box_y + 60, div_col)

        if self.lore_page == 0:
            # PAGE 1: COMPETITION CONTEXT & NARRATIVE PREMISE
            draw_text_scaled(box_x + 24, box_y + 72, "1. COMPETITION CONTEXT", hdr_col, scale=2)
            p1_context = [
                "Built for PyWeek 42 (September 2026).",
                "The theme is: Borrowed Time.",
                "by www.arianprabowo.com",
                "Crafted in Python with Pyxel retro engine.",
            ]
            for idx, line in enumerate(p1_context):
                if is_sumie:
                    c = txt_col
                else:
                    c = 9 if idx == 1 else (10 if idx == 2 else 7)
                draw_text_scaled(box_x + 24, box_y + 96 + idx * 18, line, c, scale=2)

            pyxel.line(box_x + 16, box_y + 178, box_x + box_w - 16, box_y + 178, div_col)
            draw_text_scaled(box_x + 24, box_y + 188, "2. THE MEANING OF 'BORROWED TIME'", hdr_col, scale=2)
            p1_borrowed = [
                "To live on 'borrowed time' is to survive",
                "past natural limits on compounding debt.",
                "Here, time is not a neutral backdrop;",
                "it is a resource loaned against doom.",
                "Every second survived is borrowed debt.",
            ]
            for idx, line in enumerate(p1_borrowed):
                draw_text_scaled(box_x + 24, box_y + 212 + idx * 18, line, txt_col, scale=2)

            pyxel.line(box_x + 16, box_y + 312, box_x + box_w - 16, box_y + 312, div_col)
            draw_text_scaled(box_x + 24, box_y + 322, "3. THE NARRATIVE PREMISE", hdr_col, scale=2)
            p1_narrative = [
                "You steer a fragile falling hourglass",
                "down the neck of a colossal shattered",
                "cosmic hourglass. In this celestial ruin,",
                "your fall mirrors cosmic entropy.",
                "Like falling sand, motion flows only down.",
                "Descent is absolute and unrelenting.",
            ]
            for idx, line in enumerate(p1_narrative):
                draw_text_scaled(box_x + 24, box_y + 346 + idx * 18, line, txt_col, scale=2)

            pyxel.line(box_x + 16, box_y + 464, box_x + box_w - 16, box_y + 464, div_col)
            draw_text_scaled(box_x + 24, box_y + 474, "4. WHY 'GRAIN OF DOUBT'?", hdr_col, scale=2)
            p1_doubt = [
                "1. Sand grains measure passing time in an",
                "   hourglass.",
                "2. 'A grain of doubt' is a small pang of",
                "   uncertainty or hesitation in crisis.",
                "3. You doubt your own decisions of which",
                "   pact to choose during Kairos time,",
                "   hesitating as the clock runs down.",
            ]
            for idx, line in enumerate(p1_doubt):
                if is_sumie:
                    c = txt_col
                else:
                    c = 6 if idx >= 4 else 7
                draw_text_scaled(box_x + 24, box_y + 498 + idx * 18, line, c, scale=2)

        elif self.lore_page == 1:
            # PAGE 2: COSMOLOGY & MECHANICS (LORE FIRST)
            draw_text_scaled(box_x + 24, box_y + 72, "1. LORE: THE PRICE OF SURVIVAL", hdr_col, scale=2)
            p2_lore = [
                "In the void, power is never granted free.",
                "Living on borrowed time requires debts.",
                "Every boon demands an immediate pact with",
                "permanent structural decay.",
                "You mortgage the future for seconds.",
            ]
            for idx, line in enumerate(p2_lore):
                draw_text_scaled(box_x + 24, box_y + 96 + idx * 18, line, txt_col, scale=2)

            pyxel.line(box_x + 16, box_y + 196, box_x + box_w - 16, box_y + 196, div_col)
            draw_text_scaled(box_x + 24, box_y + 206, "2. CHRONOS : THE RELENTLESS STREAM", hdr_col, scale=2)
            p2_chronos = [
                "Chronos is continuous clock time (10.0s).",
                "Descent kinematics flow uninterrupted.",
                "Steer laterally across hazards to collect",
                "golden sand grains and evade razor glass.",
            ]
            for idx, line in enumerate(p2_chronos):
                draw_text_scaled(box_x + 24, box_y + 230 + idx * 18, line, txt_col, scale=2)

            pyxel.line(box_x + 16, box_y + 312, box_x + box_w - 16, box_y + 312, div_col)
            draw_text_scaled(box_x + 24, box_y + 322, "3. KAIROS : THE SACRED CROSSROADS", hdr_col, scale=2)
            p2_kairos = [
                "Every 10.0 seconds, descent freezes in",
                "an acute panic circuit breaker: Kairos.",
                "You have 10.0s to choose between two",
                "Faustian pacts. Hesitate too long, and",
                "time expires: your hourglass shatters!",
            ]
            for idx, line in enumerate(p2_kairos):
                if is_sumie:
                    c = txt_col
                else:
                    c = 8 if idx == 4 else 7
                draw_text_scaled(box_x + 24, box_y + 346 + idx * 18, line, c, scale=2)

            pyxel.line(box_x + 16, box_y + 448, box_x + box_w - 16, box_y + 448, div_col)
            draw_text_scaled(box_x + 24, box_y + 458, "4. FAUSTIAN PACTS (IN GENERAL)", hdr_col, scale=2)
            p2_pacts = [
                "Each pact pairs an immediate boon with",
                "a permanent hazard. Identical sins",
                "compound their curses exponentially.",
            ]
            for idx, line in enumerate(p2_pacts):
                draw_text_scaled(box_x + 24, box_y + 482 + idx * 18, line, txt_col, scale=2)

            pyxel.line(box_x + 16, box_y + 546, box_x + box_w - 16, box_y + 546, div_col)
            draw_text_scaled(box_x + 24, box_y + 556, "5. KINEMATIC CONTROLS", hdr_col, scale=2)
            draw_text_scaled(box_x + 24, box_y + 580, "* [A]/[D] or ARROWS : Steer motion.", txt_col, scale=2)
            draw_text_scaled(box_x + 24, box_y + 600, "* TOUCH L/R BUTTONS : Steer motion.", txt_col, scale=2)
            draw_text_scaled(box_x + 24, box_y + 620, "* KAIROS CROSSROADS : Choose pact.", txt_col if is_sumie else 9, scale=2)

        elif self.lore_page == 2:
            # PAGE 3: FAUSTIAN PACTS (PART 1: SINS 1-4)
            draw_text_scaled(box_x + 24, box_y + 72, "FAUSTIAN PACTS (PART 1)", hdr_col, scale=2)
            pacts_p1 = [
                (
                    "1. PRIDE",
                    (
                        "You believe you can outrun sand;",
                        "your descent accelerates relentlessly.",
                    ),
                    "+Sand Clusters (Pairs & Triplets)",
                    "-Compound Fall Speed (+25% / Pact)",
                    10,
                ),
                (
                    "2. GREED",
                    (
                        "Hunger for immense multipliers",
                        "triggers lethal Borrowed Time clocks.",
                    ),
                    "+Score Multiplier (x110% Points)",
                    "-Lethal Borrowed Time Clock (10s)",
                    9,
                ),
                (
                    "3. LUST",
                    (
                        "Attracts riches magnetically,",
                        "yet draws glass straight to your heart.",
                    ),
                    "+Permanent Sand Magnet Pull",
                    "-Permanent Glass Hazard Magnet",
                    14,
                ),
                (
                    "4. ENVY",
                    (
                        "You want everything you see, so",
                        "you don't deserve to see as much.",
                    ),
                    "+Tidal Pull of Distant Sand",
                    "-Vignette Darkness Narrows Vision",
                    11,
                ),
            ]
            for idx, (pact_title, narrative_lines, boon, curse, pcol) in enumerate(pacts_p1):
                py = box_y + 104 + idx * 136
                swatch = txt_col if is_sumie else pcol
                pyxel.rect(box_x + 24, py + 2, 6, 80, swatch)
                draw_text_scaled(box_x + 38, py, pact_title, hdr_col, scale=2)
                for n_idx, n_line in enumerate(narrative_lines):
                    draw_text_scaled(box_x + 38, py + 18 + n_idx * 16, n_line, txt_col, scale=2)
                pro_y = py + 18 + len(narrative_lines) * 16
                pro_c = txt_col if is_sumie else 11
                con_c = 13 if is_sumie else 8
                draw_text_scaled(box_x + 38, pro_y, f"PRO: {boon}", pro_c, scale=2)
                draw_text_scaled(box_x + 38, pro_y + 16, f"CON: {curse}", con_c, scale=2)

        elif self.lore_page == 3:
            # PAGE 4: FAUSTIAN PACTS (PART 2: SINS 5-7) & DECAY
            draw_text_scaled(box_x + 24, box_y + 72, "FAUSTIAN PACTS (PART 2)", hdr_col, scale=2)
            pacts_p2 = [
                (
                    "5. GLUTTONY",
                    (
                        "Sand grains swell with golden value,",
                        "yet glass hazards swell into monoliths.",
                    ),
                    "+Fat Sand Grains (3x Points)",
                    "-Monstrous Enlarged Shards",
                    4,
                ),
                (
                    "6. WRATH",
                    (
                        "You use force to push all dangers away,",
                        "yet you also repel all good fortune.",
                        "You lose control, and each sealed pact",
                        "grants you even less control of motion.",
                    ),
                    "+Wrath Blast (3.0s Shard Wipe)",
                    "-Control Inversion (+5%, Cap 50%)",
                    8,
                ),
                (
                    "7. SLOTH",
                    (
                        "Delay danger and gather golden grains",
                        "with zero need to act or steer.",
                        "Yet danger is delayed: in the future,",
                        "it accumulates and strikes all at once.",
                        "You become permanently more sluggish.",
                    ),
                    "+Lazy Reprieve (5.0s Safe Reprieve)",
                    "-Delayed Danger & Sluggish Drag",
                    12,
                ),
            ]
            curr_py = box_y + 92
            for pact_title, narrative_lines, boon, curse, pcol in pacts_p2:
                pact_h = 18 + len(narrative_lines) * 16 + 32
                swatch = txt_col if is_sumie else pcol
                pyxel.rect(box_x + 24, curr_py + 2, 6, pact_h - 4, swatch)
                draw_text_scaled(box_x + 38, curr_py, pact_title, hdr_col, scale=2)
                for n_idx, n_line in enumerate(narrative_lines):
                    draw_text_scaled(box_x + 38, curr_py + 18 + n_idx * 16, n_line, txt_col, scale=2)
                pro_y = curr_py + 18 + len(narrative_lines) * 16
                pro_c = txt_col if is_sumie else 11
                con_c = 13 if is_sumie else 8
                draw_text_scaled(box_x + 38, pro_y, f"PRO: {boon}", pro_c, scale=2)
                draw_text_scaled(box_x + 38, pro_y + 16, f"CON: {curse}", con_c, scale=2)
                curr_py += pact_h + 16

            pyxel.line(box_x + 16, curr_py + 4, box_x + box_w - 16, curr_py + 4, div_col)
            draw_text_scaled(box_x + 24, curr_py + 16, "ADDICTIVE PACTS & COMPOUNDING DECAY", hdr_col, scale=2)
            p4_decay = [
                "Sins are addictive (Pact distribution):",
                "P(Pact) = (1 + N_pact) / (7 + Total_Pacts)",
                "Boon(k)  = Boon0 * (0.75)^k  (Diminishing)",
                "Curse(k) = Curse0 * (1.5)^k  (Compounding)",
                "Wrath Error = min(50%, Wrath_Level * 5%)",
            ]
            for idx, line in enumerate(p4_decay):
                if is_sumie:
                    c = txt_col
                else:
                    c = 10 if idx in (0, 1) else (8 if idx in (2, 3) else 7)
                draw_text_scaled(box_x + 24, curr_py + 40 + idx * 18, line, c, scale=2)

        else:
            # PAGE 5: THEMES, PRO MODE & SAKURA DEDICATION
            draw_text_scaled(box_x + 24, box_y + 72, "1. 10 DIVERGENT AESTHETIC THEMES", hdr_col, scale=2)
            p5_themes = [
                "Press [,] and [.] to cycle themes.",
                "10 handcrafted procedural aesthetics with",
                "unique physics, audio, and palettes:",
                "Dune, Pro Light, Pro Dark, Reader Light,",
                "Reader Dark, Glacial, Matrix,",
                "Sumi-e White, Sumi-e Black, Sakura.",
            ]
            for idx, line in enumerate(p5_themes):
                draw_text_scaled(box_x + 24, box_y + 96 + idx * 18, line, txt_col, scale=2)

            pyxel.line(box_x + 16, box_y + 214, box_x + box_w - 16, box_y + 214, div_col)
            draw_text_scaled(box_x + 24, box_y + 224, "2. PRO MODE (ACCESSIBILITY)", hdr_col, scale=2)
            p5_pro = [
                "Themes 2 & 3: Clinical high-contrast.",
                "Zero motion clutter, dual countdown",
                "borders, and photosensitive comfort.",
                "(Photosensitive comfort; NOT monochrome.)",
            ]
            for idx, line in enumerate(p5_pro):
                if is_sumie:
                    c = txt_col
                else:
                    c = 9 if idx == 3 else 7
                draw_text_scaled(box_x + 24, box_y + 248 + idx * 18, line, c, scale=2)

            pyxel.line(box_x + 16, box_y + 330, box_x + box_w - 16, box_y + 330, div_col)
            draw_text_scaled(box_x + 24, box_y + 340, "3. E-READER STEALTH MODE", hdr_col, scale=2)
            p5_reader = [
                "Themes 4 & 5: Classic literature look.",
                "Warm paper or dark OLED night reading.",
                "Play undetected at work or school!",
                "(PhD Comics emergency button tribute!)",
                "HUD is suppressed; stats woven into text.",
            ]
            for idx, line in enumerate(p5_reader):
                if is_sumie:
                    c = txt_col
                else:
                    c = 10 if idx == 2 else (9 if idx == 3 else 7)
                draw_text_scaled(box_x + 24, box_y + 364 + idx * 18, line, c, scale=2)

            pyxel.line(box_x + 16, box_y + 466, box_x + box_w - 16, box_y + 466, div_col)
            draw_text_scaled(box_x + 24, box_y + 476, "4. SAKURA DEDICATION", hdr_col, scale=2)
            p5_sakura = [
                "Theme 10 (Pastel Sakura) is dedicated",
                "to my twin sister, girlfriend, and wife--",
                "who happen to be the exact same person!",
                "",
                "Featuring soothing cherry blossoms,",
                "falling petals, and leaf-green sand.",
            ]
            for idx, line in enumerate(p5_sakura):
                if is_sumie:
                    c = txt_col
                else:
                    c = 14 if idx in (1, 2) else (10 if idx == 0 else 7)
                if line:
                    draw_text_scaled(box_x + 24, box_y + 500 + idx * 18, line, c, scale=2)

        # Navigation Footer on all pages (No [X] on the arrow line)
        pyxel.line(box_x + 16, box_y + 704, box_x + box_w - 16, box_y + 704, div_col)
        if self.lore_page == 0:
            draw_text_centered(box_y + 718, "[D / RIGHT] NEXT", nav_col, scale=2)
        elif self.lore_page == self.MAX_LORE_PAGES - 1:
            draw_text_centered(box_y + 718, "[A / LEFT] PREV   |   [D / RIGHT] RETURN", nav_col, scale=2)
        else:
            draw_text_centered(box_y + 718, "[A / LEFT] PREV   |   [D / RIGHT] NEXT", nav_col, scale=2)

        blink = (pyxel.frame_count // 12) % 2 == 0
        if is_sumie:
            p_col = txt_col
        else:
            p_col = 10 if blink else 7
        draw_text_centered(box_y + 740, "[X] RETURN TO MENU", p_col, scale=2)

    def draw_game_over_screen(self):
        theme = get_theme(self.current_theme_index)
        is_sumie = getattr(theme, "id", 0) in (7, 8) or "SUMI" in theme.name.upper()
        is_sumie_white = is_sumie and ("WHITE" in theme.name.upper() or theme.clear_color == 7)

        # Full-screen ambient dimmer overlay over background gameplay world
        if hasattr(pyxel, "dither"):
            pyxel.dither(0.50)
        pyxel.rect(0, 0, self.SCREEN_WIDTH, self.SCREEN_HEIGHT, 0)
        if hasattr(pyxel, "dither"):
            pyxel.dither(1.0)

        if is_sumie:
            card_bg = 7 if is_sumie_white else 0
            border_outer = 0 if is_sumie_white else 7
            border_inner = 13
            title_col = 0 if is_sumie_white else 7
            ver_col = 13
            reason_col = 0 if is_sumie_white else 7
            stats_bg = 7 if is_sumie_white else 0
            stats_border = 0 if is_sumie_white else 7
            stat_lbl_col = 0 if is_sumie_white else 7
            stat_val_col = 0 if is_sumie_white else 7
            summary_title_col = 0 if is_sumie_white else 7
            pact_active_col = 0 if is_sumie_white else 7
            pact_inactive_col = 13
            prompt_col = 0 if is_sumie_white else 7
            btn_bg = 7 if is_sumie_white else 0
            btn_b1 = 0 if is_sumie_white else 7
            btn_b2 = 13
            btn_txt1 = 0 if is_sumie_white else 7
            btn_txt2 = 0 if is_sumie_white else 7
            btn_txt3 = 13
            dev_col = 13
        else:
            card_bg = 0
            border_outer = 8
            border_inner = 2
            title_col = 8
            ver_col = 6
            reason_col = 7
            stats_bg = 1
            stats_border = 5
            stat_lbl_col = 10
            stat_val_col = 10
            summary_title_col = 9
            pact_active_col = 10
            pact_inactive_col = 5
            prompt_col = 8
            btn_bg = 0
            btn_b1 = 10
            btn_b2 = 9
            btn_txt1 = 10
            btn_txt2 = 7
            btn_txt3 = 6
            dev_col = 11

        # Main Game Over card: SOLID opaque black box (no checkered noise)
        pyxel.rect(40, 60, 520, 680, card_bg)
        pyxel.rectb(40, 60, 520, 680, border_outer)
        pyxel.rectb(44, 64, 512, 672, border_inner)

        draw_text_centered(75, "HOURGLASS SHATTERED", title_col, scale=3)
        if self.dev_mode:
            draw_text_centered(108, self.VERSION, ver_col, scale=2)

        reason = self.state.death_reason or "Consumed by the Void"
        draw_text_centered(136, reason, reason_col, scale=2)

        # Inner stats container: SOLID Midnight Navy with Slate border (compact, no excess space)
        pyxel.rect(60, 160, 480, 318, stats_bg)
        pyxel.rectb(60, 160, 480, 318, stats_border)

        time_survived = self.state.total_frames / 30.0
        draw_text_scaled(80, 176, f"TIME SURVIVED : {time_survived:6.1f} SECONDS", stat_lbl_col, scale=2)
        score_fmt = f"{self.state.score:,}".replace(",", " ")
        sand_fmt = f"{self.state.total_sand_collected:,}".replace(",", " ")
        shards_fmt = f"{self.state.total_shards_dodged:,}".replace(",", " ")
        pacts_fmt = f"{len(self.bargains.history):,}".replace(",", " ")
        draw_text_scaled(80, 202, f"FINAL SCORE   : {score_fmt}", stat_val_col, scale=2)
        draw_text_scaled(80, 228, f"SAND REAPED   : {sand_fmt}", stat_lbl_col if is_sumie else 9, scale=2)
        draw_text_scaled(80, 254, f"SHARDS EVADED : {shards_fmt}", 13 if is_sumie else 6, scale=2)
        draw_text_scaled(80, 280, f"PACTS SEALED  : {pacts_fmt}", stat_lbl_col if is_sumie else 8, scale=2)

        # Draw all 7 canonical sins vertically without 'k=' or 'canonical order'
        draw_text_scaled(80, 310, "PACTS SEALED SUMMARY:", summary_title_col, scale=2)
        for idx, sin in enumerate(CANONICAL_SINS):
            k = self.bargains.selection_counts.get(sin, 0)
            col = pact_active_col if k > 0 else pact_inactive_col
            row_y = 332 + idx * 19
            draw_text_scaled(100, row_y, f"{idx+1}. {sin.name.upper():<9} : {k}", col, scale=2)

        # Debounce prompt, Bot restart indicator & Big Return to Menu Button
        if self.game_over_timer < 60:
            rem = (60 - self.game_over_timer + 29) // 30
            draw_text_centered(496, f"MOURN THY LOSS ({rem}s)...", prompt_col, scale=2)
        elif self.bot_mode:
            rem_bot = (180 - self.auto_restart_timer + 29) // 30
            draw_text_centered(496, f"BOT RESTART IN {rem_bot}s", pact_active_col if is_sumie else 10, scale=2)
        else:
            blink = (pyxel.frame_count // 10) % 2 == 0
            if blink:
                draw_text_centered(496, "PRESS ANY KEY TO RESTART", 0 if is_sumie_white else 7, scale=2)

        # 3-line tall prominent [X] RETURN TO MENU touch button
        btn_menu_x, btn_menu_y, btn_menu_w, btn_menu_h = 60, 530, 480, 78
        pyxel.rect(btn_menu_x, btn_menu_y, btn_menu_w, btn_menu_h, btn_bg)
        pyxel.rectb(btn_menu_x, btn_menu_y, btn_menu_w, btn_menu_h, btn_b1)
        pyxel.rectb(btn_menu_x + 1, btn_menu_y + 1, btn_menu_w - 2, btn_menu_h - 2, btn_b2)
        draw_text_centered(btn_menu_y + 10, "[X] RETURN TO MENU", btn_txt1, scale=2)
        draw_text_centered(btn_menu_y + 32, "PRESS HERE OR [X] TO RETURN TO MENU", btn_txt2, scale=2)
        draw_text_centered(btn_menu_y + 54, "(CLICK, TAP, OR PRESS [X])", btn_txt3, scale=2)

        if self.dev_mode:
            draw_text_scaled(self.SCREEN_WIDTH - 120, self.SCREEN_HEIGHT - 20, f"[DEV] {self.VERSION}", dev_col, scale=2)

    def draw_touch_buttons(self):
        """Draw 2 high-contrast arcade buttons for mobile browser touch play."""
        theme = get_theme(self.current_theme_index)
        is_sumie = getattr(theme, "id", 0) in (7, 8) or "SUMI" in theme.name.upper()
        is_sumie_white = is_sumie and ("WHITE" in theme.name.upper() or theme.clear_color == 7)

        btn_y = 690
        btn_h = 75
        btn_w = 250

        # Translucent background for buttons
        if hasattr(pyxel, "dither"):
            pyxel.dither(0.60)

        # Left Button [x=30, y=690, w=250, h=75]
        lx = 30
        if is_sumie:
            bg_l = 13 if self.touch_left else (7 if is_sumie_white else 0)
            bg_r = 13 if self.touch_right else (7 if is_sumie_white else 0)
        else:
            bg_l = 5 if self.touch_left else 1
            bg_r = 5 if self.touch_right else 1
        pyxel.rect(lx, btn_y, btn_w, btn_h, bg_l)
        # Right Button [x=320, y=690, w=250, h=75]
        rx = 320
        pyxel.rect(rx, btn_y, btn_w, btn_h, bg_r)

        if hasattr(pyxel, "dither"):
            pyxel.dither(1.0)

        if is_sumie:
            b1_l = 0 if is_sumie_white else 7
            b1_r = 0 if is_sumie_white else 7
            b2_col = 13
            txt_l = 0 if is_sumie_white else 7
            txt_r = 0 if is_sumie_white else 7
        else:
            b1_l = 10 if self.touch_left else 6
            b1_r = 10 if self.touch_right else 6
            b2_col = 7 if self.touch_left else 1
            txt_l = 10 if self.touch_left else 7
            txt_r = 10 if self.touch_right else 7

        pyxel.rectb(lx, btn_y, btn_w, btn_h, b1_l)
        pyxel.rectb(lx + 2, btn_y + 2, btn_w - 4, btn_h - 4, b2_col)
        draw_text_scaled(lx + 70, btn_y + 24, "< LEFT", txt_l, scale=3)

        pyxel.rectb(rx, btn_y, btn_w, btn_h, b1_r)
        pyxel.rectb(rx + 2, btn_y + 2, btn_w - 4, btn_h - 4, b2_col)
        draw_text_scaled(rx + 65, btn_y + 24, "RIGHT >", txt_r, scale=3)

    def draw_theme_banner(self):
        """Render prominent theme switcher banner at the bottom of the screen."""
        theme = get_theme(self.current_theme_index)
        is_sumie = getattr(theme, "id", 0) in (7, 8) or "SUMI" in theme.name.upper()
        is_sumie_white = is_sumie and ("WHITE" in theme.name.upper() or theme.clear_color == 7)

        box_w = 520
        box_h = 46
        box_x = (self.SCREEN_WIDTH - box_w) // 2  # 40
        box_y = self.SCREEN_HEIGHT - box_h - 24  # 730 at bottom of screen

        if hasattr(pyxel, "dither"):
            pyxel.dither(0.70)
        box_bg = (7 if is_sumie_white else 0) if is_sumie else 0
        pyxel.rect(box_x, box_y, box_w, box_h, box_bg)
        if hasattr(pyxel, "dither"):
            pyxel.dither(1.0)
        border_1 = (0 if is_sumie_white else 7) if is_sumie else 10
        border_2 = 13 if is_sumie else 9
        pyxel.rectb(box_x, box_y, box_w, box_h, border_1)
        pyxel.rectb(box_x + 1, box_y + 1, box_w - 2, box_h - 2, border_2)

        name_str = f"THEME [{self.current_theme_index + 1}/{len(ALL_THEMES)}]: {theme.name}"
        sub_str = "[,] PREV THEME        [.] NEXT THEME"
        title_col = (0 if is_sumie_white else 7) if is_sumie else 10
        sub_col = 13 if is_sumie else 7
        draw_text_scaled(box_x + 16, box_y + 8, name_str, title_col, scale=2)
        draw_text_scaled(box_x + 16, box_y + 28, sub_str, sub_col, scale=1)

    def draw_dev_box(self, box_y: int, translucent: bool = False):
        """Render dedicated Dev Mode box at bottom of screen matching the theme of the top-right pacts board."""
        theme = get_theme(self.current_theme_index)
        is_sumie = getattr(theme, "id", 0) in (7, 8) or "SUMI" in theme.name.upper()
        is_sumie_white = is_sumie and ("WHITE" in theme.name.upper() or theme.clear_color == 7)
        is_light = theme.clear_color in (7, 15, 6, 11, 14) or getattr(theme, "id", 0) in (7, 15)
        kp = theme.get_kairos_palette()
        if is_sumie:
            box_bg = 7 if is_sumie_white else 0
            box_border = 0 if is_sumie_white else 7
            border_sub = 13
            hdr_col = 0 if is_sumie_white else 7
            ctrl_col = 0 if is_sumie_white else 7
            pact_col = 13
            metric_col = 0 if is_sumie_white else 7
        else:
            box_bg = 7 if is_light else 0
            box_border = 0 if is_light else (kp.border_inner if kp.border_inner != 0 else 1)
            border_sub = 5 if is_light else (3 if kp.border_inner != 3 else 1)
            hdr_col = 0 if is_light else 11
            ctrl_col = 0 if is_light else 10
            pact_col = 0 if is_light else 9
            metric_col = 0 if is_light else 7

        box_x = 20
        box_w = 560
        box_h = 156

        if translucent and hasattr(pyxel, "dither"):
            pyxel.dither(0.50)
        pyxel.rect(box_x, box_y, box_w, box_h, box_bg)
        if hasattr(pyxel, "dither"):
            pyxel.dither(1.0)
        pyxel.rectb(box_x, box_y, box_w, box_h, box_border)
        pyxel.rectb(box_x + 1, box_y + 1, box_w - 2, box_h - 2, border_sub)

        god_txt = "ON" if self.state.godmode else "OFF"
        bot_txt = "ON" if self.bot_mode else "OFF"
        rec_txt = f"{self.video_recorder.frames_recorded // 30}s" if self.video_recorder.is_recording else "OFF"

        lines_controls = [
            (f"[`] DEV MODE: ON ({self.VERSION})", hdr_col),
            (f"[G] GOD MODE: {god_txt}", ctrl_col),
            (f"[B] BOT MODE: {bot_txt}", ctrl_col),
            (f"[V] VIDEO REC: {rec_txt}", ctrl_col),
            ("[1-7] ADD PACTS   |   [Q-U] REDUCE PACTS", pact_col),
        ]

        for idx, (line_text, col) in enumerate(lines_controls):
            draw_text_scaled(box_x + 14, box_y + 8 + idx * 16, line_text, col, scale=2)

        # Subtle divider between dev controls and simulation metrics
        pyxel.line(box_x + 12, box_y + 92, box_x + box_w - 12, box_y + 92, box_border)

        # Real-time simulation metrics (3 to 5 lines using smaller font scale=1)
        px = self.entities.player.x
        py = self.entities.player.y
        vx = self.entities.player.vx
        spd = self.state.scroll_speed
        sp_m = self.state.speed_multiplier
        spawn_m = self.state.spawn_rate_multiplier
        n_sands = len(self.entities.sands)
        n_shards = len(self.entities.shards)
        st_name = self.state.current_state.name
        elapsed = self.state.total_frames / 30.0
        err_pct = getattr(self.state, "wrath_error_chance", 0.0) * 100.0
        sloth_s = getattr(self.state, "sloth_active_timer", 0) / 30.0
        wrath_s = getattr(self.state, "wrath_wipe_timer", 0) / 30.0

        metric_lines = [
            f"PLAYER: X={px:6.1f}  Y={py:6.1f}  VX={vx:+5.2f} | SCROLL SPD: {spd:4.1f} (x{sp_m:.2f})",
            f"SPAWN: x{spawn_m:.2f} | SANDS: {n_sands:3d} | SHARDS: {n_shards:3d} | VIGNETTE: {self.state.vignette_radius:.0f}px",
            f"STATE: {st_name:<7} | CHRONOS: {self.state.chronos_timer / 30.0:4.1f}s | KAIROS: {self.state.kairos_timer / 30.0:4.1f}s | TIME: {elapsed:5.1f}s",
            f"WRATH ERR: {err_pct:.0f}% (LVL {getattr(self.state, 'wrath_level', 0)}) | SLOTH: {sloth_s:3.1f}s | WRATH WIPE: {wrath_s:3.1f}s",
        ]

        for m_idx, m_text in enumerate(metric_lines):
            draw_text_scaled(box_x + 14, box_y + 98 + m_idx * 13, m_text, metric_col, scale=1)

    def draw_dev_overlay(self):
        """Render developer debug overlay at bottom of screen with translucent background."""
        box_y = self.SCREEN_HEIGHT - 156 - 8
        self.draw_dev_box(box_y=box_y, translucent=True)


def main():
    bot_flag = "--bot" in sys.argv
    video_flag = ("--video" in sys.argv or "--record" in sys.argv or "--export-video" in sys.argv)
    mobile_flag = "--mobile" in sys.argv
    dev_flag = ("--dev" in sys.argv or "-d" in sys.argv)
    video_file = os.path.join("recordings", "borrowed_time_bot.mp4")
    for i, arg in enumerate(sys.argv):
        if arg in ["--video", "--record", "--export-video"] and i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith("-"):
            video_file = sys.argv[i + 1]

    if "--playtest" in sys.argv:
        from playtest_bot import run_playtest_suite
        run_playtest_suite()
        return

    GrainOfDoubtApp(
        headless=False,
        bot_mode=bot_flag,
        record_video=video_flag,
        video_filename=video_file,
        mobile_mode=mobile_flag,
        dev_mode=dev_flag,
    )


if __name__ == "__main__":
    main()
