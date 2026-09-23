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
from engine.bargains import BargainManager, SinType, BARGAIN_REGISTRY
from engine.audio import AudioManager
from engine.bot import PlayTestingBot, BotConfig
from engine.video import VideoRecorder


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
    VERSION: str = "v0.18.0"
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
                # Bot waits 6.0s (180 frames) before restarting instead of immediately restarting
                if self.auto_restart_timer >= 180 and self.game_over_timer >= 180:
                    self.auto_restart_timer = 0
                    self.start_new_game()
                elif self.game_over_timer >= 60:
                    if (pyxel.btnp(pyxel.KEY_LEFT) or pyxel.btnp(pyxel.KEY_RIGHT) or
                        pyxel.btnp(pyxel.KEY_A) or pyxel.btnp(pyxel.KEY_D) or
                        pyxel.btnp(pyxel.KEY_R) or pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.KEY_RETURN) or
                        pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT)):
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

        # Clear background void (Color 15: Warm daylight sand, or blood-red twilight if Greed is active)
        if self.state.greed_active:
            # Color 2 is dark purple/crimson void; subtle pulsing gives borrowed time atmosphere
            bg_col = 2 if (pyxel.frame_count // 18) % 2 == 0 else 4
            pyxel.cls(bg_col)
        else:
            pyxel.cls(15)

        # Compute Chronos progress towards Kairos (0.0 to 1.0)
        prog = 0.0
        if self.state.current_state == GameState.CHRONOS:
            prog = self.state.chronos_timer / float(self.state.CHRONOS_FRAMES)

        # Draw procedural SkiFree-style sand dune moguls, wind ripples, and pebbles
        self.draw_skifree_desert_terrain(cam_x, prog)

        if self.state.current_state == GameState.TITLE:
            pyxel.camera(0, 0)
            self.draw_title_screen()
            return

        # Draw Sand grains in world coordinates with high daylight contrast (drop shadow + amber outline)
        for sand in self.entities.sands:
            c = 10 if (pyxel.frame_count // 3 + int(sand.shimmer_phase * 4)) % 2 == 0 else 9
            if getattr(sand, "is_fat", False):
                # Cast warm shadow on sand
                pyxel.rect(int(sand.x - 11), int(sand.y - 11), 26, 26, 4)
                # Golden chunk body
                pyxel.rect(int(sand.x - 13), int(sand.y - 13), 26, 26, c)
                pyxel.rectb(int(sand.x - 13), int(sand.y - 13), 26, 26, 4)
                pyxel.rectb(int(sand.x - 12), int(sand.y - 12), 24, 24, 7)
                pyxel.rect(int(sand.x - 5), int(sand.y - 5), 10, 10, 7)
            else:
                # Cast warm shadow on sand
                pyxel.rect(int(sand.x - 4), int(sand.y - 4), 10, 10, 4)
                # Golden grain body
                pyxel.rect(int(sand.x - 5), int(sand.y - 5), 10, 10, c)
                pyxel.rectb(int(sand.x - 5), int(sand.y - 5), 10, 10, 4)
                pyxel.rect(int(sand.x - 2), int(sand.y - 2), 4, 4, 7)  # Center glint

        # Draw Glass shards in world coordinates
        for shard in self.entities.shards:
            self.draw_glass_shard(shard)

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
            inner_radius=self.state.vignette_inner_radius,
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

    def draw_skifree_desert_terrain(self, cam_x: int, prog: float = 0.0):
        """Draw procedural Full Daylight Desert slope inspired by SkiFree.
        Generates deterministic sand dune moguls, wind ripples, desert pebbles, and fine sand stipple.
        All terrain features are anchored in world coordinates and scroll continuously upward with descent.
        """
        dist = int(self.state.distance)
        is_greed = self.state.greed_active

        # Palette configuration for daylight vs blood-sun Greed
        if is_greed:
            col_crest = 8            # Blood red crest
            col_shadow = 0           # Black shadow
            col_shadow_deep = 0
            col_ripple = 8           # Crimson wind ripple
            col_rock = 0             # Black stone
            col_rock_hl = 8          # Red glint
            col_grain_a = 8          # Red grain mote
            col_grain_b = 14         # Pink grain mote
        elif prog > 0.85:
            # Imminent Kairos urgency glint
            flash = (pyxel.frame_count // 3) % 2 == 0
            col_crest = 10 if flash else 7
            col_shadow = 9
            col_shadow_deep = 4
            col_ripple = 10 if flash else 9
            col_rock = 4
            col_rock_hl = 7
            col_grain_a = 10 if flash else 7
            col_grain_b = 9
        else:
            col_crest = 7            # Sunlit warm white ridge highlight
            col_shadow = 9           # Warm orange/tan slope shadow
            col_shadow_deep = 4      # Rich amber-brown base shadow
            col_ripple = 9           # Subtle warm wind ripple
            col_rock = 4             # Desert sandstone pebble
            col_rock_hl = 7          # Sunlight glint on pebble
            col_grain_a = 7          # Fine sand sun spark
            col_grain_b = 9          # Fine sand golden grit

        GRID_W = 65
        GRID_H = 65

        # Bounding box of cells currently visible on screen
        min_cell_x = int((cam_x - 40) // GRID_W)
        max_cell_x = int((cam_x + self.SCREEN_WIDTH + 40) // GRID_W) + 1

        min_cell_y = int((dist - 40) // GRID_H)
        max_cell_y = int((dist + self.SCREEN_HEIGHT + 40) // GRID_H) + 1

        for cell_y in range(min_cell_y, max_cell_y):
            # Screen Y coordinate of the cell top
            base_sy = cell_y * GRID_H - dist
            for cell_x in range(min_cell_x, max_cell_x):
                # World X coordinate of the cell left
                base_wx = cell_x * GRID_W

                # Deterministic spatial hash for this cell
                h = ((cell_x * 374761393) ^ (cell_y * 668265263)) & 0xFFFFFF

                # Offset within cell
                ox = (h % 35) + 15
                oy = ((h >> 6) % 35) + 15
                fx = base_wx + ox
                fy = base_sy + oy

                if fy < -25 or fy > self.SCREEN_HEIGHT + 25:
                    continue

                ftype = (h >> 12) % 100

                if ftype < 35:
                    # 1. SkiFree-style Sand Mogul (Crescent dune bump with sunlit rim and shadow hollow)
                    pyxel.line(fx - 10, fy, fx - 3, fy - 2, col_crest)
                    pyxel.line(fx - 3, fy - 2, fx + 3, fy - 2, col_crest)
                    pyxel.line(fx + 3, fy - 2, fx + 10, fy, col_crest)
                    pyxel.line(fx - 8, fy + 1, fx + 8, fy + 1, col_shadow)
                    pyxel.line(fx - 4, fy + 2, fx + 4, fy + 2, col_shadow_deep)
                elif ftype < 55:
                    # 2. Wind Ripple Ribs (horizontal sand ripples carved by desert gusts)
                    pyxel.line(fx - 9, fy, fx + 7, fy, col_ripple)
                    pyxel.line(fx - 13, fy + 3, fx + 5, fy + 3, col_ripple)
                    pyxel.line(fx - 6, fy + 6, fx + 11, fy + 6, col_ripple)
                elif ftype < 70:
                    # 3. Desert Sandstone Pebble (little rock on the slope with drop shadow)
                    pyxel.rect(fx, fy, 4, 3, col_rock)
                    pyxel.pset(fx + 1, fy, col_rock_hl)
                    pyxel.line(fx, fy + 3, fx + 3, fy + 3, col_shadow_deep)
                elif ftype < 90:
                    # 4. Fine Sand Grain Stipple (granularity so desert slope has grit and texture)
                    pyxel.pset(fx, fy, col_grain_a)
                    pyxel.pset(fx + 7, fy + 2, col_grain_b)
                    pyxel.pset(fx - 5, fy + 5, col_grain_a)
                    pyxel.pset(fx + 3, fy + 8, col_grain_b)
                else:
                    # 5. Wide Barchan Dune Ridge (sweeping dune crest across the slope)
                    pyxel.line(fx - 22, fy + 2, fx - 7, fy - 2, col_crest)
                    pyxel.line(fx - 7, fy - 2, fx + 7, fy - 2, col_crest)
                    pyxel.line(fx + 7, fy - 2, fx + 22, fy + 2, col_crest)
                    pyxel.line(fx - 18, fy + 3, fx + 18, fy + 3, col_shadow)
                    pyxel.line(fx - 10, fy + 4, fx + 10, fy + 4, col_shadow_deep)

    def draw_atmospheric_dunes_and_glass_background(self, cam_x: int, prog: float = 0.0):
        """Backward-compatible alias for draw_skifree_desert_terrain."""
        self.draw_skifree_desert_terrain(cam_x, prog)

    def draw_celestial_depth_astrolabe(self, cam_x: int, prog: float = 0.0):
        """Backward-compatible alias for draw_skifree_desert_terrain."""
        self.draw_skifree_desert_terrain(cam_x, prog)

    def draw_player_hourglass(self):
        """Draw horizontal hourglass sprite (60x40) that tilts dynamically with control velocity."""
        player = self.entities.player
        px = player.x
        py = player.y

        # Cast drop shadow on the sand slope below the hourglass
        shadow_y = int(py + 16)
        pyxel.line(int(px - 18), shadow_y, int(px + 18), shadow_y, 4)
        pyxel.line(int(px - 22), shadow_y + 1, int(px + 22), shadow_y + 1, 4)
        pyxel.line(int(px - 18), shadow_y + 2, int(px + 18), shadow_y + 2, 4)

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

        # 6. Bulb Sand Levels (dynamically shifting with tilt)
        tilt_ratio = max(-1.0, min(1.0, tilt / 0.38)) if abs(tilt) > 0.01 else 0.0
        # When tilted right (tilt > 0): left bulb drains (scale < 1.0), right bulb fills (scale > 1.0)
        # When tilted left (tilt < 0): right bulb drains (scale < 1.0), left bulb fills (scale > 1.0)
        l_scale = max(0.20, min(1.45, 1.0 - tilt_ratio * 0.50))
        r_scale = max(0.20, min(1.45, 1.0 + tilt_ratio * 0.50))

        # 6. Bulb Sand Levels (dynamically shifting with tilt)
        tilt_ratio = max(-1.0, min(1.0, tilt / 0.38)) if abs(tilt) > 0.01 else 0.0
        l_scale = max(0.20, min(1.45, 1.0 - tilt_ratio * 0.50))
        r_scale = max(0.20, min(1.45, 1.0 + tilt_ratio * 0.50))
        is_score_flash = (self.state.player_score_flash_timer > 0)

        # Left Bulb Sand
        for dx in range(-21, -4, 2):
            half_h = int(13 * (abs(dx) / 24.0) * l_scale)
            if half_h > 1:
                if is_score_flash:
                    col = 7 if (self.state.player_score_flash_timer % 2 == 0) else 10
                else:
                    col = 10 if (dx % 4 == 0) else 9
                p_top = rot(dx, -half_h + 1)
                p_bot = rot(dx, half_h - 1)
                pyxel.line(p_top[0], p_top[1], p_bot[0], p_bot[1], col)

        # Right Bulb Sand
        for dx in range(5, 22, 2):
            half_h = int(13 * (abs(dx) / 24.0) * r_scale)
            if half_h > 1:
                if is_score_flash:
                    col = 7 if (self.state.player_score_flash_timer % 2 == 0) else 10
                else:
                    col = 10 if (dx % 4 == 0) else 9
                p_top = rot(dx, -half_h + 1)
                p_bot = rot(dx, half_h - 1)
                pyxel.line(p_top[0], p_top[1], p_bot[0], p_bot[1], col)

        # 8. Animated Sand Flow across waist:
        # Direction and speed of sand falling across the neck is proportional to how tilted it is
        if abs(tilt) > 0.02:
            flow_sign = 1.0 if tilt > 0 else -1.0
            for i in range(3):
                frac = (player.sand_drain_phase * flow_sign + i * 0.33) % 1.0
                stream_lx = (-5.0 + frac * 10.0) * flow_sign
                stream_ly = math.sin((player.sand_drain_phase + i) * 3.14) * 1.5
                sp = rot(stream_lx, stream_ly)
                col = 7 if is_score_flash else (10 if i == 0 else 9)
                pyxel.rect(sp[0] - 1, sp[1] - 1, 2, 2, col)
        else:
            sp = rot(0, 0)
            col = 7 if is_score_flash else 9
            pyxel.rect(sp[0] - 1, sp[1] - 1, 2, 2, col)

        # 9. Specular Reflections
        pyxel.line(*rot(-18, -10), *rot(-8, -5), 7)
        pyxel.line(*rot(8, -5), *rot(18, -10), 7)

    def draw_glass_shard(self, shard: GlassShard):
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

        # Cast drop shadow on the daylight sand slope
        pyxel.tri(x0 + 3, y0 + 4, x1 + 3, y1 + 4, x2 + 3, y2 + 4, 4)

        if is_fat:
            pyxel.tri(x0, y0, x1, y1, x2, y2, 8)
            pyxel.line(x0, y0, x1, y1, 0)
            pyxel.line(x1, y1, x2, y2, 0)
            pyxel.line(x2, y2, x0, y0, 0)
            pyxel.line(x0, y0, (x1 + x2) // 2, (y1 + y2) // 2, 7)
        else:
            # Pale icy crystalline facet
            pyxel.tri(x0, y0, x1, y1, x2, y2, 6)
            # Crisp black razor perimeter outline
            pyxel.line(x0, y0, x1, y1, 0)
            pyxel.line(x1, y1, x2, y2, 0)
            pyxel.line(x2, y2, x0, y0, 0)
            # Specular glint along leading edge
            if (pyxel.frame_count // 3) % 2 == 0:
                pyxel.line(x0, y0, x1, y1, 7)

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
        time_str = f"TIME: {elapsed_sec:04.1f} s"
        flash_time = (pyxel.frame_count // 15) % 2 == 0
        draw_text_scaled(self.SCREEN_WIDTH // 2 - 47, 14, time_str, 10 if flash_time else 7, scale=2)

        # 3. Score container (Top Right)
        if hasattr(pyxel, "dither"):
            pyxel.dither(0.60)
        pyxel.rect(self.SCREEN_WIDTH - 250, 8, 240, 30, 0)
        if hasattr(pyxel, "dither"):
            pyxel.dither(1.0)
        pyxel.rectb(self.SCREEN_WIDTH - 250, 8, 240, 30, 1)

        score_fmt = f"{self.state.score:,}".replace(",", " ")
        score_str = f"SCORE: {score_fmt}"
        draw_text_scaled(self.SCREEN_WIDTH - 240, 14, score_str, 10, scale=2)

        # Multiplier (inside score container at right)
        if self.state.score_multiplier > 1.05:
            mult_str = f"x{self.state.score_multiplier:.1f}"
            draw_text_scaled(self.SCREEN_WIDTH - 65, 14, mult_str, 9, scale=2)

        # 4. Vertical Pacts List in Catholic Canonical Order at Top Right (All 7 always listed)
        pacts_box_w = 180
        pacts_box_h = 140
        pacts_box_x = self.SCREEN_WIDTH - pacts_box_w - 10
        pacts_box_y = 44
        if hasattr(pyxel, "dither"):
            pyxel.dither(0.60)
        pyxel.rect(pacts_box_x, pacts_box_y, pacts_box_w, pacts_box_h, 0)
        if hasattr(pyxel, "dither"):
            pyxel.dither(1.0)
        pyxel.rectb(pacts_box_x, pacts_box_y, pacts_box_w, pacts_box_h, 1)

        draw_text_scaled(pacts_box_x + 8, pacts_box_y + 4, "FAUSTIAN PACTS", 6, scale=2)
        for idx, sin in enumerate(CANONICAL_SINS):
            k = self.bargains.selection_counts.get(sin, 0)
            row_y = pacts_box_y + 22 + idx * 16
            sin_lbl = sin.name.lower()
            line_txt = f"{idx+1}. {sin_lbl:<10} {k}"
            col = 10 if k > 0 else 5
            draw_text_scaled(pacts_box_x + 8, row_y, line_txt, col, scale=2)

        # Minimal Status Badges when active (drawn below hearts at top left)
        badge_y = 44
        if self.bot_mode and not self.dev_mode:
            pyxel.rect(10, badge_y, 100, 20, 0)
            pyxel.rectb(10, badge_y, 100, 20, 11)
            draw_text_scaled(15, badge_y + 4, "[BOT ON]", 11, scale=2)
            badge_y += 24

        if self.video_recorder.is_recording and not self.dev_mode:
            rec_secs = self.video_recorder.frames_recorded // 30
            flash = (pyxel.frame_count // 6) % 2 == 0
            pyxel.rect(10, badge_y, 100, 20, 0)
            pyxel.rectb(10, badge_y, 100, 20, 8)
            draw_text_scaled(15, badge_y + 4, f"REC {rec_secs:02d} s", 8 if flash else 7, scale=2)
            badge_y += 24

        # Invulnerability Badge
        if self.state.godmode:
            pyxel.rect(10, badge_y, 100, 20, 0)
            pyxel.rectb(10, badge_y, 100, 20, 10)
            draw_text_scaled(15, badge_y + 4, "[GODMODE]", 10, scale=2)
            badge_y += 24

        # Envy Tidal Pull Badge
        if self.state.envy_mega_lust_active:
            lust_secs = (self.state.envy_mega_lust_timer + 29) // 30
            flash = (pyxel.frame_count // 4) % 2 == 0
            pyxel.rect(10, badge_y, 100, 20, 0)
            pyxel.rectb(10, badge_y, 100, 20, 10 if flash else 9)
            draw_text_scaled(15, badge_y + 4, f"TIDAL PULL {lust_secs} s", 10 if flash else 7, scale=2)
            badge_y += 24

        # Greed Borrowed Time Warning Indicator
        if self.state.greed_active:
            flash = (pyxel.frame_count // 5) % 2 == 0
            col = 8 if flash else 9
            if self.dev_mode:
                msg = f"BORROWED TIME ({self.state.greed_timer / 30.0:.1f} s)"
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

            # Card background & frame
            bg_col = 1 if not is_selected else 5
            border_col = 10 if (is_selected and (pyxel.frame_count // 3) % 2 == 0) else (6 if is_selected else 1)

            if sin == SinType.GLUTTONY:
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
                    draw_bent_outline(1, 10)
            else:
                pyxel.rect(cx, col_y, col_w, col_h, bg_col)
                pyxel.rectb(cx, col_y, col_w, col_h, border_col)
                if is_selected:
                    pyxel.rectb(cx + 1, col_y + 1, col_w - 2, col_h - 2, 10)

            # Directional badge (justified center)
            badge_col = 8 if is_selected else 1
            pyxel.rect(cx + 14, col_y + 12, col_w - 28, 28, badge_col)
            badge_lbl = col_labels[i]
            badge_w = (len(badge_lbl) * 4 - 1) * 2
            draw_text_scaled(cx + col_w // 2 - badge_w // 2, col_y + 18, badge_lbl, 7, scale=2)

            # Pure Sin Name: significantly bigger, fills entire box horizontally based on longest character, justified center
            max_sin_len = max(len(d.name) for d in BARGAIN_REGISTRY.values())
            title_scale = max(1, int((col_w - 11) / (max_sin_len * 4 - 1)))
            name = defn.name.upper()
            if sin == SinType.GLUTTONY:
                # Make Gluttony so big it gets out of the frame a little bit (looks intentional)
                title_scale = 8
            title_w = (len(name) * 4 - 1) * title_scale
            center_x = cx + col_w // 2
            title_x = center_x - title_w // 2
            draw_text_scaled(title_x, col_y + 46, name, 10 if is_selected else 7, scale=title_scale)

            # Level indicator (justified center below title)
            lvl_str = f"LEVEL: {k}"
            lvl_w = (len(lvl_str) * 4 - 1) * 2
            lvl_x = center_x - lvl_w // 2
            draw_text_scaled(lvl_x, col_y + 88, lvl_str, 9, scale=2)

            # Visual divider
            pyxel.line(cx + 14, col_y + 106, cx + col_w - 14, col_y + 106, 6)

            # Boon section
            draw_text_scaled(cx + 16, col_y + 120, "PRO (NOW):", 11, scale=2)
            if sin == SinType.PRIDE:
                group_name = ["Pairs", "Triplets", "Quadruplets", "Quintuplets"][min(3, k)]
                draw_text_scaled(cx + 16, col_y + 144, "Sand Clusters", 7, scale=2)
                draw_text_scaled(cx + 16, col_y + 168, f"{group_name} (+{k+1} grains)", 11, scale=2)
            elif sin == SinType.ENVY:
                next_k = k + 1
                k_eff = next_k + 2
                outer_preview = int(1200.0 * (0.8 ** k_eff))
                mega_r = outer_preview * 2
                draw_text_scaled(cx + 16, col_y + 144, "Tidal Pull (2.0s)", 7, scale=2)
                draw_text_scaled(cx + 16, col_y + 168, f"Pull {mega_r}px Radius", 11, scale=2)
            elif sin == SinType.GREED:
                draw_text_scaled(cx + 16, col_y + 144, "Score Multiplier", 7, scale=2)
                draw_text_scaled(cx + 16, col_y + 168, "x110% per sand", 11, scale=2)
            elif sin == SinType.SLOTH:
                draw_text_scaled(cx + 16, col_y + 144, "Lazy Reprieve", 7, scale=2)
                draw_text_scaled(cx + 16, col_y + 168, "Hurl Hazards Down (2s)", 11, scale=2)
            elif sin == SinType.LUST:
                draw_text_scaled(cx + 16, col_y + 144, "Sand Magnet", 7, scale=2)
                draw_text_scaled(cx + 16, col_y + 168, f"{100 + k * 50}px (Permanent)", 11, scale=2)
            elif sin == SinType.GLUTTONY:
                next_k = k + 1
                next_fat = (1.0 - (0.90 ** next_k)) * 100.0
                draw_text_scaled(cx + 16, col_y + 144, "Fat Grains (3x Pts)", 7, scale=2)
                draw_text_scaled(cx + 16, col_y + 168, f"{next_fat:.1f}% Fat (10x Area)", 11, scale=2)
            elif sin == SinType.WRATH:
                draw_text_scaled(cx + 16, col_y + 144, "Wrath Explosion", 7, scale=2)
                draw_text_scaled(cx + 16, col_y + 168, "Blast 1200px Radius", 11, scale=2)
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
                next_k = k + 1
                k_eff = next_k + 2
                outer_preview = int(1200.0 * (0.8 ** k_eff))
                inner_preview = int(1000.0 * (0.8 ** (k_eff + 1)))
                draw_text_scaled(cx + 16, col_y + 244, "Vignette Vision", 7, scale=2)
                draw_text_scaled(cx + 16, col_y + 268, f"{outer_preview}/{inner_preview} px", 8, scale=2)
            elif sin == SinType.SLOTH:
                drag = 0.20 * (1.5 ** k) * 100
                draw_text_scaled(cx + 16, col_y + 244, "Lateral Drag", 7, scale=2)
                draw_text_scaled(cx + 16, col_y + 268, f"-{drag:.0f}% Steering (Wave)", 8, scale=2)
            elif sin == SinType.LUST:
                draw_text_scaled(cx + 16, col_y + 244, "Hazard Magnet", 7, scale=2)
                draw_text_scaled(cx + 16, col_y + 268, f"{100 + k * 50}px (Permanent)", 8, scale=2)
            elif sin == SinType.GLUTTONY:
                next_k = k + 1
                next_fat = (1.0 - (0.90 ** next_k)) * 100.0
                draw_text_scaled(cx + 16, col_y + 244, "Fat Glass Shards", 7, scale=2)
                draw_text_scaled(cx + 16, col_y + 268, f"{next_fat:.1f}% Fat (10x Area)", 8, scale=2)
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
        # Pulsing logo centered with dark drop shadow for high contrast on daylight sand
        draw_text_scaled(190, 72, "GRAIN OF DOUBT", 4, scale=4)
        draw_text_scaled(188, 70, "GRAIN OF DOUBT", 10, scale=4)

        draw_text_scaled(162, 127, "PYWEEK 42 : BORROWED TIME", 4, scale=2)
        draw_text_scaled(160, 125, "PYWEEK 42 : BORROWED TIME", 9, scale=2)

        draw_text_scaled(238, 157, "BY ARIAN PRABOWO", 4, scale=2)
        draw_text_scaled(236, 155, "BY ARIAN PRABOWO", 7, scale=2)

        if self.dev_mode:
            draw_text_scaled(216, 178, f"VERSION: {self.VERSION} [DEV MODE]", 3, scale=2)

        # Subtitles centered in rich indigo & red for crisp daylight contrast
        draw_text_scaled(110, 205, "FALL DOWN THE DESERT SLOPE", 1, scale=2)
        draw_text_scaled(110, 232, "COLLECT GOLDEN SAND TO SURVIVE", 4, scale=2)
        draw_text_scaled(95, 259, "DODGE LETHAL FALLING GLASS SHARDS", 8, scale=2)

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
            draw_text_scaled(62, 654, "PRESS ARROWS OR TOUCH BUTTONS TO START", 4, scale=2)
            draw_text_scaled(60, 652, "PRESS ARROWS OR TOUCH BUTTONS TO START", 10, scale=2)

        # Draw the 2 mobile buttons at bottom of title screen (mobile only)
        if self.is_mobile:
            self.draw_touch_buttons()

        if self.dev_mode:
            draw_text_scaled(self.SCREEN_WIDTH - 140, self.SCREEN_HEIGHT - 20, f"[DEV] {self.VERSION}", 3, scale=2)

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
        score_fmt = f"{self.state.score:,}".replace(",", " ")
        sand_fmt = f"{self.state.total_sand_collected:,}".replace(",", " ")
        shards_fmt = f"{self.state.total_shards_dodged:,}".replace(",", " ")
        pacts_fmt = f"{len(self.bargains.history):,}".replace(",", " ")
        draw_text_scaled(80, 218, f"FINAL SCORE   : {score_fmt}", 10, scale=2)
        draw_text_scaled(80, 246, f"SAND REAPED   : {sand_fmt}", 9, scale=2)
        draw_text_scaled(80, 274, f"SHARDS EVADED : {shards_fmt}", 6, scale=2)
        draw_text_scaled(80, 302, f"PACTS SEALED  : {pacts_fmt}", 8, scale=2)

        # Draw all 7 canonical sins vertically without 'k=' or 'canonical order'
        draw_text_scaled(80, 332, "PACTS SEALED SUMMARY:", 9, scale=2)
        for idx, sin in enumerate(CANONICAL_SINS):
            k = self.bargains.selection_counts.get(sin, 0)
            col = 10 if k > 0 else 5
            row_y = 356 + idx * 20
            draw_text_scaled(100, row_y, f"{idx+1}. {sin.name.upper():<9} : {k}", col, scale=2)

        # Debounce prompt, Bot restart indicator & Return to Menu shortcut
        if self.game_over_timer < 60:
            rem = (60 - self.game_over_timer + 29) // 30
            draw_text_scaled(120, 620, f"MOURN THY LOSS ({rem}s)... | [X] MENU", 8, scale=2)
        elif self.bot_mode:
            rem_bot = (180 - self.auto_restart_timer + 29) // 30
            draw_text_scaled(80, 620, f"BOT RESTART IN {rem_bot}s | [SPACE] NOW | [X] MENU", 10, scale=2)
        else:
            blink = (pyxel.frame_count // 10) % 2 == 0
            if blink:
                draw_text_scaled(70, 620, "PRESS ANY KEY TO RESTART | [X] MENU", 7, scale=2)

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
        draw_text_scaled(box_x + 12, box_y + 92, f"SPAWN: x{spawn_m:.2f} | SANDS:{n_sands} SHARDS:{n_shards} | VIG:{self.state.vignette_radius:.0f}/{self.state.vignette_inner_radius:.0f}px", 9, scale=2)

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
