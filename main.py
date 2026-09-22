"""Grain of Doubt - PyWeek 42 ("Borrowed Time")
By Arian Prabowo

A 2D Retro Arcade Falling Hourglass Endless Runner built with Pyxel.
600x800 Resolution (3:4 Portrait Aspect Ratio).
Controls: A / D or Left / Right Arrows only.
"""
import math
import random
import sys
from typing import Optional, List, Tuple

try:
    import pyxel
except ImportError:
    pyxel = None

from engine.state import GameState, StateManager
from engine.entities import EntityManager, HourglassPlayer, SandGrain, GlassShard
from engine.bargains import BargainManager, SinType
from engine.audio import AudioManager
from engine.bot import PlayTestingBot, BotConfig
from engine.video import VideoRecorder


def render_vignette(px: float, py: float, radius: float, screen_w: int = 600, screen_h: int = 800, pyxel_module=None):
    """Draw multi-circle concentric vignette mask centered at (px, py) with graduated dither transparency.

    - Outside R4 (1.00 * radius): 100% solid black void.
    - Tier 4 (0.88..1.00 * radius): 85% dither darkness.
    - Tier 3 (0.74..0.88 * radius): 65% dither darkness.
    - Tier 2 (0.58..0.74 * radius): 42% dither darkness.
    - Tier 1 (0.42..0.58 * radius): 20% dither darkness.
    - Core (< 0.42 * radius): 100% clear unobstructed vision.
    """
    if pyxel_module is None or radius >= 900.0:
        return

    r = max(25.0, float(radius))
    tiers = [
        (0.42 * r, 0.20),
        (0.58 * r, 0.42),
        (0.74 * r, 0.65),
        (0.88 * r, 0.85),
        (1.00 * r, 1.00),
    ]
    radii_sq = [rk * rk for rk, _ in tiers]
    r_max_sq = radii_sq[-1]
    has_dither = hasattr(pyxel_module, "dither")

    # Fast block fill above and below outer circle
    min_y = max(0, int(py - tiers[-1][0]))
    max_y = min(screen_h, int(py + tiers[-1][0]) + 1)

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

        # 1. Solid black void outside outer radius R4
        lx_out = int(px - dxs[4])
        rx_out = int(px + dxs[4])
        if has_dither:
            pyxel_module.dither(1.0)
        if lx_out > 0:
            pyxel_module.rect(0, y, lx_out, 1, 0)
        if rx_out < screen_w:
            pyxel_module.rect(rx_out, y, screen_w - rx_out, 1, 0)

        # 2. Concentric graduated dither rings from Tier 4 down to Tier 1
        for i in range(4, 0, -1):
            alpha = tiers[i - 1][1]
            dx_outer = dxs[i]
            dx_inner = dxs[i - 1]

            if has_dither:
                pyxel_module.dither(alpha)

            # Left ring segment: [px - dx_outer, px - dx_inner]
            l_start = max(0, int(px - dx_outer))
            l_end = max(0, min(screen_w, int(px - dx_inner)))
            if l_end > l_start:
                pyxel_module.rect(l_start, y, l_end - l_start, 1, 0)

            # Right ring segment: [px + dx_inner, px + dx_outer]
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
                    pyxel_module.dither(tiers[0][1])
                pyxel_module.rect(c_start, y, c_end - c_start, 1, 0)

    if has_dither:
        pyxel_module.dither(1.0)


def draw_text_scaled(x: int, y: int, s: str, col: int, scale: int = 1, img_bank: int = 2):
    """Draw text with integer scaling factor using offscreen buffer."""
    if pyxel is None:
        return
    if scale <= 1:
        pyxel.text(x, y, s, col)
        return
    w = len(s) * 4 + 4
    h = 8
    pyxel.images[img_bank].cls(0)
    pyxel.images[img_bank].text(0, 0, s, col)
    # Offset blt position so the scaled output starts exactly at (x, y)
    blt_x = x + int(w * (scale - 1) / 2)
    blt_y = y + int(h * (scale - 1) / 2)
    pyxel.blt(blt_x, blt_y, img_bank, 0, 0, w, h, colkey=0, scale=scale)


CANONICAL_SINS: List[SinType] = [
    SinType.PRIDE,
    SinType.GREED,
    SinType.LUST,
    SinType.ENVY,
    SinType.GLUTTONY,
    SinType.WRATH,
    SinType.SLOTH,
]


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
    VERSION: str = "v0.10.0"
    SCREEN_WIDTH: int = 600
    SCREEN_HEIGHT: int = 800

    def __init__(
        self,
        headless: bool = False,
        bot_mode: bool = False,
        record_video: bool = False,
        video_filename: str = "borrowed_time_bot.mp4",
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
        self.reset_stars()

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

        self.state._input_left = k_left or t_left
        self.state._input_right = k_right or t_right

    def update(self):
        if pyxel is None:
            return

        # X key: On TITLE screen = quit game; During gameplay = return to title menu
        if not self.headless and pyxel.btnp(pyxel.KEY_X):
            if self.state.current_state == GameState.TITLE:
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

        # Toggle Invulnerability (God Mode) with 'I' key (dev mode only)
        if self.dev_mode and pyxel.btnp(pyxel.KEY_I):
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

        # Enforce speed handicap in physics when bot is active
        self.state._bot_speed_handicap = self.bot.config.speed_handicap if self.bot_mode else 1.0

        # Feedback banner timer
        if self.feedback_timer > 0:
            self.feedback_timer -= 1

        # Background cosmic drift (speed accelerates as Kairos approaches)
        chronos_prog = 0.0
        if self.state.current_state == GameState.CHRONOS:
            chronos_prog = self.state.chronos_timer / float(self.state.CHRONOS_FRAMES)

        speed_factor = 1.0 + chronos_prog * 1.5
        scroll_drift = max(2.0, self.state.scroll_speed) * speed_factor
        cam_x = self.entities.player.x - self.SCREEN_WIDTH / 2.0

        for star in self.stars:
            star[1] -= scroll_drift * star[4]
            if star[1] < 0:
                star[1] = self.SCREEN_HEIGHT
                star[0] = random.uniform(cam_x - 120, cam_x + self.SCREEN_WIDTH + 120)

        # State dispatch
        if self.state.current_state == GameState.TITLE:
            # Start game with any lateral key, space/enter, or mouse/touch tap
            if (self.bot_mode or
                pyxel.btnp(pyxel.KEY_LEFT) or pyxel.btnp(pyxel.KEY_RIGHT) or
                pyxel.btnp(pyxel.KEY_A) or pyxel.btnp(pyxel.KEY_D) or
                pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.KEY_RETURN) or
                pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT)):
                self.start_new_game()

        elif self.state.current_state == GameState.CHRONOS:
            if self.bot_mode:
                b_left, b_right = self.bot.decide_chronos_input(self.state, self.entities)
                self.state._input_left = b_left
                self.state._input_right = b_right
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
                        self.active_options, self.selected_card_index, frames_remaining=frames_rem
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

                # Space/Enter also confirms immediately
                if pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.KEY_RETURN):
                    if self.selected_card_index < 0:
                        self.selected_card_index = 0
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
            if self.bot_mode:
                self.auto_restart_timer += 1
                if self.auto_restart_timer >= 60 and self.game_over_timer >= 60:
                    self.auto_restart_timer = 0
                    self.start_new_game()
            else:
                # Require minimum 2.0s (60 frames) debounce before allowing restart
                if self.game_over_timer >= 60:
                    if (pyxel.btnp(pyxel.KEY_LEFT) or pyxel.btnp(pyxel.KEY_RIGHT) or
                        pyxel.btnp(pyxel.KEY_A) or pyxel.btnp(pyxel.KEY_D) or
                        pyxel.btnp(pyxel.KEY_R) or pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.KEY_RETURN) or
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

        # Clear background void (Color 0: Black, or ominous cosmic blood-night if Greed is active)
        if self.state.greed_active:
            # Color 2 is dark purple/crimson void; subtle pulsing gives borrowed time atmosphere
            bg_col = 2 if (pyxel.frame_count // 18) % 2 == 0 else 0
            pyxel.cls(bg_col)
        else:
            pyxel.cls(0)

        # Compute Chronos progress towards Kairos (0.0 to 1.0)
        prog = 0.0
        if self.state.current_state == GameState.CHRONOS:
            prog = self.state.chronos_timer / float(self.state.CHRONOS_FRAMES)

        # Draw cosmic void stars (color and shimmer dynamically shift, parallax wrapped relative to cam_x)
        wrap_w = self.SCREEN_WIDTH + 240
        for star in self.stars:
            sx, sy, base_c, sz, spd = star
            rel_x = (sx - cam_x * spd * 0.4) % wrap_w - 120
            draw_sx = cam_x + rel_x

            if self.state.greed_active:
                # Borrowed Time: stars turn into burning crimson embers
                flame_pulse = (pyxel.frame_count // 3 + int(sx)) % 3
                sc = [8, 9, 10][flame_pulse]
            elif prog < 0.35:
                sc = base_c
            elif prog < 0.65:
                sc = 9 if base_c == 6 else (6 if base_c == 5 else 5)
            elif prog < 0.85:
                sc = 10 if base_c in (5, 6) else (7 if (pyxel.frame_count // 4) % 2 == 0 else 9)
            else:
                pulse = (pyxel.frame_count // 2 + int(sx)) % 4
                sc = [8, 9, 10, 7][pulse]

            pyxel.rect(int(draw_sx), int(sy), sz, sz, sc)

        # Draw drifting astral aurora ribbons across infinite horizontal void
        self.draw_cosmic_nebula_streams(cam_x, prog)

        if self.state.current_state == GameState.TITLE:
            pyxel.camera(0, 0)
            self.draw_title_screen()
            return

        # Draw Sand grains in world coordinates
        for sand in self.entities.sands:
            c = 10 if (pyxel.frame_count // 3 + int(sand.shimmer_phase * 4)) % 2 == 0 else 9
            pyxel.rect(int(sand.x - 5), int(sand.y - 5), 10, 10, c)
            pyxel.rect(int(sand.x - 2), int(sand.y - 2), 4, 4, 7)  # Center glint

        # Draw Glass shards in world coordinates
        for shard in self.entities.shards:
            self.draw_glass_shard(shard)

        # Draw Particles in world coordinates
        for p in self.entities.particles:
            pyxel.rect(int(p.x), int(p.y), p.size, p.size, p.color)

        # Draw Player Hourglass in world coordinates
        self.draw_player_hourglass()

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
        )

        # Draw HUD (Score, Hearts, Active Pacts, Elapsed Time)
        self.draw_hud()

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

        # Developer debug overlay (toggled with '`')
        if self.dev_mode:
            self.draw_dev_overlay()

        # Capture video frame for MP4 export
        self.video_recorder.record_frame(pyxel)

    def draw_cosmic_nebula_streams(self, cam_x: int, prog: float = 0.0):
        """Draw ethereal celestial aurora ribbons across infinite horizontal void."""
        t = self.state.total_frames * (0.04 + prog * 0.06)
        if self.state.greed_active:
            flash = (pyxel.frame_count // 4) % 2 == 0
            col_inner = 8 if flash else 9  # Burning crimson/orange flares
            col_outer = 4                  # Dark rust void boundary
        elif prog < 0.65:
            col_inner = 5
            col_outer = 1
        elif prog < 0.85:
            col_inner = 9
            col_outer = 2
        else:
            flash = (pyxel.frame_count // 3) % 2 == 0
            col_inner = 8 if flash else 10
            col_outer = 2

        start_grid = (cam_x // 350 - 1) * 350
        for stream_base_x in range(start_grid, start_grid + self.SCREEN_WIDTH + 700, 350):
            for y in range(0, self.SCREEN_HEIGHT, 8):
                drift = math.sin(y * 0.015 + t + stream_base_x * 0.005) * 16.0
                rx = int(stream_base_x + drift)
                pyxel.rect(rx - 2, y, 4, 8, col_outer)
                pyxel.rect(rx - 1, y, 2, 8, col_inner)

    def draw_player_hourglass(self):
        """Draw horizontal hourglass sprite (60x40) that tilts dynamically with control velocity."""
        player = self.entities.player
        px = player.x
        py = player.y

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
            pyxel.line(p1[0], p1[1], p2[0], p2[1], 4)
        # Left Brass Highlight & Rivet
        hl1 = rot(-26, -6)
        hl2 = rot(-26, 6)
        pyxel.line(hl1[0], hl1[1], hl2[0], hl2[1], 9)
        riv_l = rot(-26, 0)
        pyxel.pset(riv_l[0], riv_l[1], 10)

        # 2. Right Brass Cap (vertical end bar at lx = 24 to 30)
        for yo in range(-15, 16):
            p1 = rot(24, yo)
            p2 = rot(29, yo)
            pyxel.line(p1[0], p1[1], p2[0], p2[1], 4)
        # Right Brass Highlight & Rivet
        hr1 = rot(26, -6)
        hr2 = rot(26, 6)
        pyxel.line(hr1[0], hr1[1], hr2[0], hr2[1], 9)
        riv_r = rot(26, 0)
        pyxel.pset(riv_r[0], riv_r[1], 10)

        # 3. Left Bulb Glass Walls (tapering from lx=-24 to waist lx=-4)
        pyxel.line(*rot(-24, -15), *rot(-4, -5), 6)
        pyxel.line(*rot(-24, 15), *rot(-4, 5), 6)

        # 4. Right Bulb Glass Walls (tapering from waist lx=4 to lx=24)
        pyxel.line(*rot(4, -5), *rot(24, -15), 6)
        pyxel.line(*rot(4, 5), *rot(24, 15), 6)

        # 5. Center Waist Neck
        pyxel.line(*rot(-4, -5), *rot(4, -5), 7)
        pyxel.line(*rot(-4, 5), *rot(4, 5), 7)

        # 6. Left Bulb Sand
        for dx in range(-21, -4, 2):
            half_h = int(13 * (abs(dx) / 24.0))
            if half_h > 1:
                col = 10 if (dx % 4 == 0) else 9
                p_top = rot(dx, -half_h + 1)
                p_bot = rot(dx, half_h - 1)
                pyxel.line(p_top[0], p_top[1], p_bot[0], p_bot[1], col)

        # 7. Right Bulb Sand
        for dx in range(5, 22, 2):
            half_h = int(13 * (abs(dx) / 24.0))
            if half_h > 1:
                col = 10 if (dx % 4 == 0) else 9
                p_top = rot(dx, -half_h + 1)
                p_bot = rot(dx, half_h - 1)
                pyxel.line(p_top[0], p_top[1], p_bot[0], p_bot[1], col)

        # 8. Animated Sand Flow across waist
        stream_x = ((player.sand_drain_phase % 1.0) - 0.5) * 6.0
        sp = rot(stream_x, 0)
        pyxel.rect(sp[0] - 1, sp[1] - 1, 3, 3, 10)

        # 9. Specular Reflections
        pyxel.line(*rot(-18, -10), *rot(-8, -5), 7)
        pyxel.line(*rot(8, -5), *rot(18, -10), 7)

    def draw_glass_shard(self, shard: GlassShard):
        sx = int(shard.x)
        sy = int(shard.y)
        angle = shard.rotation_angle
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)

        pts = [
            (0, -20),
            (10, 20),
            (-10, 15),
        ]
        rot_pts = []
        for x, y in pts:
            rx = int(sx + x * cos_a - y * sin_a)
            ry = int(sy + x * sin_a + y * cos_a)
            rot_pts.append((rx, ry))

        x0, y0 = rot_pts[0]
        x1, y1 = rot_pts[1]
        x2, y2 = rot_pts[2]
        pyxel.tri(x0, y0, x1, y1, x2, y2, 7)
        pyxel.line(x0, y0, x1, y1, 6)
        pyxel.line(x1, y1, x2, y2, 0)
        pyxel.line(x2, y2, x0, y0, 6)

    def draw_hud(self):
        # Universal Dither Alpha on HUD containers
        # 1. Hearts container (Top Left)
        if hasattr(pyxel, "dither"):
            pyxel.dither(0.60)
        pyxel.rect(10, 8, 172, 30, 0)
        if hasattr(pyxel, "dither"):
            pyxel.dither(1.0)
        pyxel.rectb(10, 8, 172, 30, 1)

        for i in range(5):
            hx = 16 + i * 32
            hy = 12
            if i < self.state.hearts:
                pyxel.rect(hx + 4, hy, 8, 4, 8)
                pyxel.rect(hx + 16, hy, 8, 4, 8)
                pyxel.rect(hx, hy + 4, 28, 8, 8)
                pyxel.rect(hx + 4, hy + 12, 20, 4, 8)
                pyxel.rect(hx + 8, hy + 16, 12, 4, 8)
                pyxel.rect(hx + 12, hy + 20, 4, 4, 8)
                pyxel.rect(hx + 4, hy + 4, 4, 4, 7)  # Specular glint
            else:
                pyxel.rectb(hx, hy + 4, 28, 16, 5)

        # 2. Elapsed Time container (Top Center)
        if hasattr(pyxel, "dither"):
            pyxel.dither(0.60)
        pyxel.rect(self.SCREEN_WIDTH // 2 - 76, 8, 152, 30, 0)
        if hasattr(pyxel, "dither"):
            pyxel.dither(1.0)
        pyxel.rectb(self.SCREEN_WIDTH // 2 - 76, 8, 152, 30, 1)

        elapsed_sec = self.state.total_frames / 30.0
        time_str = f"TIME: {elapsed_sec:04.1f}s"
        flash_time = (pyxel.frame_count // 15) % 2 == 0
        draw_text_scaled(self.SCREEN_WIDTH // 2 - 62, 14, time_str, 10 if flash_time else 7, scale=2)

        # 3. Score container (Top Right)
        if hasattr(pyxel, "dither"):
            pyxel.dither(0.60)
        pyxel.rect(self.SCREEN_WIDTH - 250, 8, 240, 30, 0)
        if hasattr(pyxel, "dither"):
            pyxel.dither(1.0)
        pyxel.rectb(self.SCREEN_WIDTH - 250, 8, 240, 30, 1)

        score_str = f"SCORE: {self.state.score:06d}"
        draw_text_scaled(self.SCREEN_WIDTH - 240, 14, score_str, 10, scale=2)

        # Multiplier
        if self.state.score_multiplier > 1.05:
            mult_str = f"x{self.state.score_multiplier:.1f}"
            draw_text_scaled(self.SCREEN_WIDTH - 90, 42, mult_str, 9, scale=2)

        # 4. Vertical Pacts List in Catholic Canonical Order (All 7 always listed)
        pacts_box_w = 146
        pacts_box_h = 140
        if hasattr(pyxel, "dither"):
            pyxel.dither(0.60)
        pyxel.rect(10, 44, pacts_box_w, pacts_box_h, 0)
        if hasattr(pyxel, "dither"):
            pyxel.dither(1.0)
        pyxel.rectb(10, 44, pacts_box_w, pacts_box_h, 1)

        draw_text_scaled(16, 48, "PACTS", 6, scale=2)
        for idx, sin in enumerate(CANONICAL_SINS):
            k = self.bargains.selection_counts.get(sin, 0)
            row_y = 66 + idx * 16
            sin_lbl = sin.name[:7].upper()
            line_txt = f"{idx+1}. {sin_lbl:<7} {k}"
            col = 10 if k > 0 else 5
            draw_text_scaled(16, row_y, line_txt, col, scale=2)

        # Minimal Status Badges when active (Full details in Dev Mode '`')
        if self.bot_mode and not self.dev_mode:
            pyxel.rect(self.SCREEN_WIDTH - 110, 42, 100, 20, 0)
            pyxel.rectb(self.SCREEN_WIDTH - 110, 42, 100, 20, 11)
            draw_text_scaled(self.SCREEN_WIDTH - 105, 46, "[BOT ON]", 11, scale=2)

        if self.video_recorder.is_recording and not self.dev_mode:
            rec_secs = self.video_recorder.frames_recorded // 30
            flash = (pyxel.frame_count // 6) % 2 == 0
            pyxel.rect(self.SCREEN_WIDTH - 110, 66, 100, 20, 0)
            pyxel.rectb(self.SCREEN_WIDTH - 110, 66, 100, 20, 8)
            draw_text_scaled(self.SCREEN_WIDTH - 105, 70, f"REC {rec_secs:02d}s", 8 if flash else 7, scale=2)

        # Invulnerability Badge
        if self.state.godmode:
            pyxel.rect(self.SCREEN_WIDTH - 110, 90, 100, 20, 0)
            pyxel.rectb(self.SCREEN_WIDTH - 110, 90, 100, 20, 10)
            draw_text_scaled(self.SCREEN_WIDTH - 105, 94, "[GODMODE]", 10, scale=2)

        # Greed Borrowed Time Warning Indicator
        if self.state.greed_active:
            flash = (pyxel.frame_count // 5) % 2 == 0
            col = 8 if flash else 9
            if self.dev_mode:
                msg = f"BORROWED TIME ({self.state.greed_timer / 30.0:.1f}s)"
            else:
                msg = "BORROWED TIME"
            draw_text_scaled(self.SCREEN_WIDTH // 2 - 80, 48, msg, col, scale=2)

        # Wrath Zero Yield Warning
        if self.state.wrath_zero_yield_timer > 0:
            draw_text_scaled(16, 190, "WRATH: ZERO YIELD", 8, scale=2)

    def draw_kairos_modal(self):
        """Draw 2-column Kairos modal navigated strictly via Left/Right arrows or A/D."""
        modal_x = 30
        modal_y = 60
        modal_w = 540
        modal_h = 680

        # Modal backdrop with dither alpha
        if hasattr(pyxel, "dither"):
            pyxel.dither(0.85)
        pyxel.rect(modal_x, modal_y, modal_w, modal_h, 0)
        if hasattr(pyxel, "dither"):
            pyxel.dither(1.0)
        pyxel.rectb(modal_x, modal_y, modal_w, modal_h, 8)
        pyxel.rectb(modal_x + 2, modal_y + 2, modal_w - 4, modal_h - 4, 2)

        # Header
        draw_text_scaled(modal_x + 70, modal_y + 16, "KAIROS CIRCUIT BREAKER", 7, scale=2)
        draw_text_scaled(modal_x + 150, modal_y + 38, "BORROW YOUR TIME", 8, scale=2)

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
        bar_col = (8 if (pyxel.frame_count // 3) % 2 == 0 else 9) if ratio < 0.30 else 10

        for bar_x in [modal_x + 8, modal_x + modal_w - 20]:
            pyxel.rect(bar_x, col_y, 12, col_h, 0)
            if fill_h > 0:
                pyxel.rect(bar_x, col_y + drain_offset, 12, fill_h, bar_col)
            pyxel.rectb(bar_x, col_y, 12, col_h, 6)

        col_labels = ["< STEER LEFT <", "> STEER RIGHT >"]

        for i, (sin, defn, k) in enumerate(self.active_options):
            cx = start_x + i * (col_w + col_gap)
            is_selected = (i == self.selected_card_index)

            # Card background
            bg_col = 1 if not is_selected else 5
            pyxel.rect(cx, col_y, col_w, col_h, bg_col)

            # Card border (flashing gold if selected)
            border_col = 10 if (is_selected and (pyxel.frame_count // 3) % 2 == 0) else (6 if is_selected else 1)
            pyxel.rectb(cx, col_y, col_w, col_h, border_col)
            if is_selected:
                pyxel.rectb(cx + 1, col_y + 1, col_w - 2, col_h - 2, 10)

            # Directional badge
            badge_col = 8 if is_selected else 1
            pyxel.rect(cx + 14, col_y + 12, col_w - 28, 28, badge_col)
            draw_text_scaled(cx + 26, col_y + 18, col_labels[i], 7, scale=2)

            # Pure Sin Name (NO LATIN NAME)
            draw_text_scaled(cx + 16, col_y + 50, defn.name.upper(), 10 if is_selected else 7, scale=3)
            draw_text_scaled(cx + 16, col_y + 82, f"LEVEL: k={k}", 9, scale=2)

            # Visual divider
            pyxel.line(cx + 14, col_y + 106, cx + col_w - 14, col_y + 106, 6)

            # Boon section
            draw_text_scaled(cx + 16, col_y + 120, "PRO (NOW):", 11, scale=2)
            if sin == SinType.PRIDE:
                group_name = ["Pairs", "Triplets", "Quadruplets", "Quintuplets"][min(3, k)]
                draw_text_scaled(cx + 16, col_y + 144, "Sand Clusters", 7, scale=2)
                draw_text_scaled(cx + 16, col_y + 168, f"{group_name} (+{k+1} grains)", 11, scale=2)
            elif sin == SinType.ENVY:
                draw_text_scaled(cx + 16, col_y + 144, "Reap Screen Sand", 7, scale=2)
                draw_text_scaled(cx + 16, col_y + 168, "All Visible Sands", 11, scale=2)
            elif sin == SinType.GREED:
                draw_text_scaled(cx + 16, col_y + 144, "Score Multiplier", 7, scale=2)
                draw_text_scaled(cx + 16, col_y + 168, "x110% per sand", 11, scale=2)
            elif sin == SinType.SLOTH:
                draw_text_scaled(cx + 16, col_y + 144, "Freeze Hazards", 7, scale=2)
                draw_text_scaled(cx + 16, col_y + 168, "8.0s Speed Recovery", 11, scale=2)
            elif sin == SinType.LUST:
                draw_text_scaled(cx + 16, col_y + 144, "Sand Magnet", 7, scale=2)
                draw_text_scaled(cx + 16, col_y + 168, f"{180 + k * 60}px (Permanent)", 11, scale=2)
            elif sin == SinType.GLUTTONY:
                draw_text_scaled(cx + 16, col_y + 144, "+Sand Spawn Rate", 7, scale=2)
                draw_text_scaled(cx + 16, col_y + 168, "+50% Sand Rate", 11, scale=2)
            elif sin == SinType.WRATH:
                draw_text_scaled(cx + 16, col_y + 144, "Hazard Purge", 7, scale=2)
                draw_text_scaled(cx + 16, col_y + 168, "10.0s Screen Clear", 11, scale=2)
            else:
                draw_text_scaled(cx + 16, col_y + 144, f"+{defn.boon_name}", 7, scale=2)
                draw_text_scaled(cx + 16, col_y + 168, f"{defn.boon_base} {defn.boon_unit}", 11, scale=2)

            # Visual divider
            pyxel.line(cx + 14, col_y + 206, cx + col_w - 14, col_y + 206, 2)

            # Curse section
            draw_text_scaled(cx + 16, col_y + 220, "CON (FOREVER):", 8, scale=2)
            if sin == SinType.PRIDE:
                draw_text_scaled(cx + 16, col_y + 244, "Descent Speed", 7, scale=2)
                draw_text_scaled(cx + 16, col_y + 268, "+25% Fall Velocity", 8, scale=2)
            elif sin == SinType.GREED:
                draw_text_scaled(cx + 16, col_y + 244, "Borrowed Time", 7, scale=2)
                draw_text_scaled(cx + 16, col_y + 268, "10-18s (LETHAL END)", 8, scale=2)
            elif sin == SinType.ENVY:
                draw_text_scaled(cx + 16, col_y + 244, "Vignette Vision", 7, scale=2)
                draw_text_scaled(cx + 16, col_y + 268, f"{int(260.0 * (0.8**k))}px Tunnel", 8, scale=2)
            elif sin == SinType.SLOTH:
                drag = 0.20 * (1.5 ** k) * 100
                draw_text_scaled(cx + 16, col_y + 244, "Lateral Drag", 7, scale=2)
                draw_text_scaled(cx + 16, col_y + 268, f"-{drag:.0f}% Steering", 8, scale=2)
            elif sin == SinType.LUST:
                draw_text_scaled(cx + 16, col_y + 244, "Hazard Magnet", 7, scale=2)
                draw_text_scaled(cx + 16, col_y + 268, f"{180 + k * 60}px (Permanent)", 8, scale=2)
            elif sin == SinType.GLUTTONY:
                draw_text_scaled(cx + 16, col_y + 244, "+Hazard Spawn Rate", 7, scale=2)
                draw_text_scaled(cx + 16, col_y + 268, "+50% Hazard Rate", 8, scale=2)
            elif sin == SinType.WRATH:
                draw_text_scaled(cx + 16, col_y + 244, "Zero Yield", 7, scale=2)
                draw_text_scaled(cx + 16, col_y + 268, "10.0s Zero Yield", 8, scale=2)
            else:
                draw_text_scaled(cx + 16, col_y + 244, f"-{defn.curse_name}", 7, scale=2)
                draw_text_scaled(cx + 16, col_y + 268, f"{defn.curse_base} {defn.curse_unit}", 8, scale=2)

            # Compounding note
            draw_text_scaled(cx + 16, col_y + 350, "COMPOUNDS PER PACT", 6, scale=2)

            # Selection status
            if is_selected:
                pyxel.rect(cx + 14, col_y + col_h - 48, col_w - 28, 34, 10)
                draw_text_scaled(cx + 52, col_y + col_h - 40, "SELECTED", 0, scale=2)

        # Footer instructions
        draw_text_scaled(modal_x + 50, modal_y + modal_h - 44, "STEER LEFT OR RIGHT TO SELECT", 7, scale=2)
        draw_text_scaled(modal_x + 60, modal_y + modal_h - 22, "CHOOSE OR DIE: 2.0s TIME LIMIT", 8, scale=2)

    def draw_feedback_banner(self):
        fb = self.selected_feedback
        if not fb:
            return
        # Position banner safely above bottom window / buttons
        pyxel.rect(40, 540, 520, 44, 0)
        pyxel.rectb(40, 540, 520, 44, 10)
        txt = f"PACT SEALED: {fb['sin'].upper()}!"
        draw_text_scaled(70, 554, txt, 10, scale=2)

    def draw_title_screen(self):
        # Pulsing logo centered
        draw_text_scaled(188, 70, "GRAIN OF DOUBT", 10, scale=4)
        draw_text_scaled(160, 125, "PYWEEK 42 : BORROWED TIME", 9, scale=2)
        draw_text_scaled(236, 155, "BY ARIAN PRABOWO", 7, scale=2)

        if self.dev_mode:
            draw_text_scaled(216, 178, f"VERSION: {self.VERSION} [DEV MODE]", 11, scale=2)

        # Subtitles centered
        draw_text_scaled(110, 205, "FALL DOWN THE COSMIC HOURGLASS", 7, scale=2)
        draw_text_scaled(110, 232, "COLLECT GOLDEN SAND TO SURVIVE", 6, scale=2)
        draw_text_scaled(95, 259, "DODGE LETHAL FALLING GLASS SHARDS", 6, scale=2)

        # Controls box
        pyxel.rect(40, 300, 520, 335, 1)
        pyxel.rectb(40, 300, 520, 335, 5)

        draw_text_scaled(60, 320, "CONTROLS & HOW TO PLAY", 10, scale=2)
        draw_text_scaled(60, 350, "A / D  or  LEFT / RIGHT ARROWS", 7, scale=2)
        draw_text_scaled(60, 380, "Steer descent to catch sand & dodge glass", 6, scale=2)

        draw_text_scaled(60, 420, "MOBILE / TOUCH CONTROLS", 10, scale=2)
        draw_text_scaled(60, 450, "< LEFT BUTTON   |   RIGHT BUTTON >", 7, scale=2)
        draw_text_scaled(60, 480, "Tap buttons or screen half to steer", 6, scale=2)

        draw_text_scaled(60, 520, "SHORTCUTS", 9, scale=2)
        if self.dev_mode:
            draw_text_scaled(60, 550, "[`] DEV  |  [I] INVULN  |  [B] BOT  |  [V] REC", 11, scale=2)
            draw_text_scaled(60, 580, "[X] QUIT  |  [SPACE] START", 5, scale=2)
        else:
            draw_text_scaled(60, 550, "[X] QUIT  |  [SPACE] START", 5, scale=2)

        # Start prompt
        blink = (pyxel.frame_count // 12) % 2 == 0
        if blink:
            draw_text_scaled(60, 652, "PRESS ARROWS OR TOUCH BUTTONS TO START", 7, scale=2)

        # Draw the 2 mobile buttons at bottom of title screen (mobile only)
        if self.is_mobile:
            self.draw_touch_buttons()

        if self.dev_mode:
            draw_text_scaled(self.SCREEN_WIDTH - 140, self.SCREEN_HEIGHT - 20, f"[DEV] {self.VERSION}", 11, scale=2)

    def draw_game_over_screen(self):
        # Dark overlay box with dither alpha
        if hasattr(pyxel, "dither"):
            pyxel.dither(0.80)
        pyxel.rect(40, 60, 520, 680, 0)
        if hasattr(pyxel, "dither"):
            pyxel.dither(1.0)
        pyxel.rectb(40, 60, 520, 680, 8)
        pyxel.rectb(44, 64, 512, 672, 2)

        draw_text_scaled(186, 75, "HOURGLASS SHATTERED", 8, scale=3)
        if self.dev_mode:
            draw_text_scaled(260, 108, self.VERSION, 6, scale=2)
        draw_text_scaled(210, 128, "BY ARIAN PRABOWO", 6, scale=2)

        reason = self.state.death_reason or "Consumed by the Void"
        draw_text_scaled(70, 150, reason[:36], 7, scale=2)

        # Inner stats container with dither alpha
        if hasattr(pyxel, "dither"):
            pyxel.dither(0.65)
        pyxel.rect(60, 175, 480, 420, 1)
        if hasattr(pyxel, "dither"):
            pyxel.dither(1.0)
        pyxel.rectb(60, 175, 480, 420, 5)

        time_survived = self.state.total_frames / 30.0
        draw_text_scaled(80, 190, f"TIME SURVIVED : {time_survived:6.1f} SECONDS", 10, scale=2)
        draw_text_scaled(80, 218, f"FINAL SCORE   : {self.state.score:6d}", 10, scale=2)
        draw_text_scaled(80, 246, f"SAND REAPED   : {self.state.total_sand_collected:6d}", 9, scale=2)
        draw_text_scaled(80, 274, f"SHARDS EVADED : {self.state.total_shards_dodged:6d}", 6, scale=2)
        draw_text_scaled(80, 302, f"PACTS SEALED  : {len(self.bargains.history):6d}", 8, scale=2)

        # Draw all 7 canonical sins vertically without 'k=' or 'canonical order'
        draw_text_scaled(80, 332, "PACTS SEALED SUMMARY:", 9, scale=2)
        for idx, sin in enumerate(CANONICAL_SINS):
            k = self.bargains.selection_counts.get(sin, 0)
            col = 10 if k > 0 else 5
            row_y = 356 + idx * 20
            draw_text_scaled(100, row_y, f"{idx+1}. {sin.name.upper():<9} : {k}", col, scale=2)

        # 2-Second Debounce prompt
        if self.game_over_timer < 60:
            rem = (60 - self.game_over_timer + 29) // 30
            draw_text_scaled(150, 620, f"MOURN THY LOSS ({rem}s)...", 8, scale=2)
        else:
            blink = (pyxel.frame_count // 10) % 2 == 0
            if blink:
                draw_text_scaled(100, 620, "PRESS ANY KEY OR TAP TO RESTART", 7, scale=2)

        if self.dev_mode:
            draw_text_scaled(self.SCREEN_WIDTH - 120, self.SCREEN_HEIGHT - 20, f"[DEV] {self.VERSION}", 11, scale=2)

    def draw_touch_buttons(self):
        """Draw 2 high-contrast arcade buttons for mobile browser touch play."""
        btn_y = 690
        btn_h = 75
        btn_w = 250

        # Left Button [x=30, y=690, w=250, h=75]
        lx = 30
        if hasattr(pyxel, "dither"):
            pyxel.dither(0.60 if self.touch_left else 0.30)
        pyxel.rect(lx, btn_y, btn_w, btn_h, 5 if self.touch_left else 1)
        if hasattr(pyxel, "dither"):
            pyxel.dither(1.0)
        pyxel.rectb(lx, btn_y, btn_w, btn_h, 10 if self.touch_left else 6)
        pyxel.rectb(lx + 2, btn_y + 2, btn_w - 4, btn_h - 4, 7 if self.touch_left else 1)
        draw_text_scaled(lx + 70, btn_y + 24, "< LEFT", 10 if self.touch_left else 7, scale=3)

        # Right Button [x=320, y=690, w=250, h=75]
        rx = 320
        if hasattr(pyxel, "dither"):
            pyxel.dither(0.60 if self.touch_right else 0.30)
        pyxel.rect(rx, btn_y, btn_w, btn_h, 5 if self.touch_right else 1)
        if hasattr(pyxel, "dither"):
            pyxel.dither(1.0)
        pyxel.rectb(rx, btn_y, btn_w, btn_h, 10 if self.touch_right else 6)
        pyxel.rectb(rx + 2, btn_y + 2, btn_w - 4, btn_h - 4, 7 if self.touch_right else 1)
        draw_text_scaled(rx + 65, btn_y + 24, "RIGHT >", 10 if self.touch_right else 7, scale=3)

    def draw_dev_overlay(self):
        """Render developer debug overlay at bottom of screen with alpha transparency."""
        box_x = 10
        box_w = 580
        box_h = 160
        box_y = self.SCREEN_HEIGHT - box_h - 10  # 630..790

        # Alpha semi-transparent dark panel with mint neon border
        if hasattr(pyxel, "dither"):
            pyxel.dither(0.70)
        pyxel.rect(box_x, box_y, box_w, box_h, 0)
        if hasattr(pyxel, "dither"):
            pyxel.dither(1.0)
        pyxel.rectb(box_x, box_y, box_w, box_h, 11)
        pyxel.rectb(box_x + 1, box_y + 1, box_w - 2, box_h - 2, 3)

        bot_str = "ON" if self.bot_mode else "OFF"
        rec_str = "ON" if self.video_recorder.is_recording else "OFF"
        inv_str = "ACTIVE (IMMORTAL)" if self.state.godmode else "OFF"

        # Line 1: Header + Version + Shortcut for Invulnerability
        draw_text_scaled(box_x + 12, box_y + 8, f"[DEV MODE] (` close) {self.VERSION} | SHORTCUT: [I] INVULNERABILITY: {inv_str}", 11, scale=2)

        # Line 2: Other shortcuts and Faustian Bargains controls
        draw_text_scaled(box_x + 12, box_y + 36, f"[B] BOT:{bot_str}  [V] REC:{rec_str}  [X] MENU  |  PACTS: 1-7:ADD  Q-U:REDUCE", 10, scale=2)

        # Line 3: Player and Camera telemetry
        px = self.entities.player.x
        vx = self.entities.player.vx
        spd = self.state.scroll_speed
        sp_m = self.state.speed_multiplier
        draw_text_scaled(box_x + 12, box_y + 64, f"PLAYER: X={px:.0f} VX={vx:.2f} | SPD:{spd:.1f} (x{sp_m:.2f})", 7, scale=2)

        # Line 4: Entities and Spawning telemetry
        spawn_m = self.state.spawn_rate_multiplier
        n_sands = len(self.entities.sands)
        n_shards = len(self.entities.shards)
        draw_text_scaled(box_x + 12, box_y + 92, f"SPAWN: x{spawn_m:.2f} | SANDS:{n_sands} SHARDS:{n_shards} | VIG:{self.state.vignette_radius:.0f}px", 9, scale=2)

        # Line 5: State and Timer telemetry
        elapsed = self.state.total_frames / 30.0
        st_name = self.state.current_state.name
        greed_str = f"{self.state.greed_timer / 30.0:4.1f}s (LETHAL)" if self.state.greed_active else "OFF"
        draw_text_scaled(box_x + 12, box_y + 120, f"STATE:{st_name} | GREED:{greed_str} | TIME:{elapsed:4.1f}s | PRIDE:{self.state.pride_level}", 6, scale=2)


def main():
    bot_flag = "--bot" in sys.argv
    video_flag = ("--video" in sys.argv or "--record" in sys.argv or "--export-video" in sys.argv)
    mobile_flag = "--mobile" in sys.argv
    dev_flag = ("--dev" in sys.argv or "-d" in sys.argv)
    video_file = "borrowed_time_bot.mp4"
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
