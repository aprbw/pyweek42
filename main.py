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
    """Draw dual-tier concentric vignette mask centered at (px, py).

    Outer zone (distance > r_outer): 100% solid black darkness.
    Middle ring (r_inner < distance <= r_outer): 50% alpha dithered shadow.
    Inner core (distance <= r_inner): 100% clear unobstructed vision.
    """
    if pyxel_module is None:
        return
    r_outer = max(25.0, float(radius))
    r_inner = max(15.0, r_outer * 0.70)
    r_outer_sq = r_outer * r_outer
    r_inner_sq = r_inner * r_inner

    has_dither = hasattr(pyxel_module, "dither")

    for y in range(screen_h):
        dy = y - py
        dy_sq = dy * dy

        if dy_sq >= r_outer_sq:
            # Entire line is outside outer circle: solid black
            if has_dither:
                pyxel_module.dither(1.0)
            pyxel_module.rect(0, y, screen_w, 1, 0)
        else:
            dx_out = math.sqrt(r_outer_sq - dy_sq)
            lx_out = int(px - dx_out)
            rx_out = int(px + dx_out)

            # Solid black outer edges
            if has_dither:
                pyxel_module.dither(1.0)
            if lx_out > 0:
                pyxel_module.rect(0, y, lx_out, 1, 0)
            if rx_out < screen_w:
                pyxel_module.rect(rx_out, y, screen_w - rx_out, 1, 0)

            # 50% alpha transition ring
            if has_dither:
                pyxel_module.dither(0.5)

            if dy_sq >= r_inner_sq:
                # Mid section is entirely in 50% alpha zone
                start_x = max(0, lx_out)
                end_x = min(screen_w, rx_out)
                if end_x > start_x:
                    pyxel_module.rect(start_x, y, end_x - start_x, 1, 0)
            else:
                dx_in = math.sqrt(r_inner_sq - dy_sq)
                lx_in = int(px - dx_in)
                rx_in = int(px + dx_in)

                # Left alpha ring segment
                s1 = max(0, lx_out)
                e1 = max(0, min(screen_w, lx_in))
                if e1 > s1:
                    pyxel_module.rect(s1, y, e1 - s1, 1, 0)

                # Right alpha ring segment
                s2 = max(0, min(screen_w, rx_in))
                e2 = min(screen_w, rx_out)
                if e2 > s2:
                    pyxel_module.rect(s2, y, e2 - s2, 1, 0)

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


class GrainOfDoubtApp:
    VERSION: str = "v0.4.0"
    SCREEN_WIDTH: int = 600
    SCREEN_HEIGHT: int = 800

    def __init__(
        self,
        headless: bool = False,
        bot_mode: bool = False,
        record_video: bool = False,
        video_filename: str = "borrowed_time_bot.mp4",
    ):
        self.headless = headless
        self.bot_mode = bot_mode
        self.bot = PlayTestingBot()
        self.auto_restart_timer: int = 0
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

        # Cosmic void background stars (parallax)
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

        if not headless and pyxel is not None:
            pyxel.init(
                self.SCREEN_WIDTH,
                self.SCREEN_HEIGHT,
                title="Grain of Doubt - By Arian Prabowo",
                fps=30,
                quit_key=pyxel.KEY_Q,
            )
            self.audio.init_sounds(pyxel)
            if self.record_video_on_start:
                self.video_recorder.start(pyxel)
            pyxel.run(self.update, self.draw)

    def start_new_game(self):
        self.state.start_game()
        self.entities.reset()
        self.bargains.reset()
        self.active_options.clear()
        self.selected_card_index = 0
        self.selected_feedback = None

    def update_input(self):
        if pyxel is None:
            return

        # ONLY A / D and Left / Right arrows
        left = pyxel.btn(pyxel.KEY_LEFT) or pyxel.btn(pyxel.KEY_A)
        right = pyxel.btn(pyxel.KEY_RIGHT) or pyxel.btn(pyxel.KEY_D)

        self.state._input_left = left
        self.state._input_right = right

    def update(self):
        if pyxel is None:
            return

        # Toggle Bot mode dynamically with 'B' key
        if pyxel.btnp(pyxel.KEY_B):
            self.bot_mode = not self.bot_mode
            self.bot.reset()

        # Toggle Video Recording with 'V' key
        if pyxel.btnp(pyxel.KEY_V):
            self.video_recorder.toggle(pyxel)

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
            # Start game with any lateral key or space/enter, or auto-start if bot mode
            if (self.bot_mode or
                pyxel.btnp(pyxel.KEY_LEFT) or pyxel.btnp(pyxel.KEY_RIGHT) or
                pyxel.btnp(pyxel.KEY_A) or pyxel.btnp(pyxel.KEY_D) or
                pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.KEY_RETURN)):
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
                self.selected_card_index = 0  # 0=Left, 1=Right
                if self.bot_mode:
                    self.bot.target_card_index = None

            # Check if Game Over triggered
            if self.state.current_state == GameState.GAMEOVER:
                self.audio.play_death(pyxel)
                self.auto_restart_timer = 0

        elif self.state.current_state == GameState.KAIROS:
            # Kairos time circuit breaker: 2 options (Left vs Right)
            instant_seal = False
            if self.bot_mode:
                if pyxel.frame_count % 2 == 0:
                    b_left, b_right, b_seal = self.bot.decide_kairos_choice(
                        self.active_options, self.selected_card_index
                    )
                    if b_left and self.selected_card_index > 0:
                        self.selected_card_index -= 1
                    elif b_right and self.selected_card_index < len(self.active_options) - 1:
                        self.selected_card_index += 1
                    elif b_seal:
                        instant_seal = True
            else:
                move_left = pyxel.btnp(pyxel.KEY_LEFT) or pyxel.btnp(pyxel.KEY_A)
                move_right = pyxel.btnp(pyxel.KEY_RIGHT) or pyxel.btnp(pyxel.KEY_D)

                if move_left:
                    if self.selected_card_index == 1:
                        self.selected_card_index = 0
                    else:
                        instant_seal = True  # Double-tap left confirms left card

                elif move_right:
                    if self.selected_card_index == 0:
                        self.selected_card_index = 1
                    else:
                        instant_seal = True  # Double-tap right confirms right card

                # Space/Enter also confirms immediately
                if pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.KEY_RETURN):
                    instant_seal = True

            # Advance Kairos timer
            self.state.update_timers()

            # Confirm selection on timeout or manual seal
            if instant_seal or self.state.current_state == GameState.CHRONOS:
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
            if self.bot_mode:
                self.auto_restart_timer += 1
                if self.auto_restart_timer >= 60:
                    self.auto_restart_timer = 0
                    self.start_new_game()
            else:
                # Restart with any control key
                if (pyxel.btnp(pyxel.KEY_LEFT) or pyxel.btnp(pyxel.KEY_RIGHT) or
                    pyxel.btnp(pyxel.KEY_A) or pyxel.btnp(pyxel.KEY_D) or
                    pyxel.btnp(pyxel.KEY_R) or pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.KEY_RETURN)):
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

        # Clear background void (Color 0: Black)
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

            if prog < 0.35:
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

        # Draw HUD (Score, Hearts, Active Pacts, Elapsed Time, Version, Kill timer)
        self.draw_hud()

        # Draw active modal overlays
        if self.state.current_state == GameState.KAIROS:
            self.draw_kairos_modal()
        elif self.state.current_state == GameState.GAMEOVER:
            self.draw_game_over_screen()

        # Selected feedback banner
        if self.feedback_timer > 0 and self.selected_feedback:
            self.draw_feedback_banner()

        # Capture video frame for MP4 export
        self.video_recorder.record_frame(pyxel)

    def draw_cosmic_nebula_streams(self, cam_x: int, prog: float = 0.0):
        """Draw ethereal celestial aurora ribbons across infinite horizontal void."""
        t = pyxel.frame_count * (0.04 + prog * 0.06)
        if prog < 0.65:
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
        # Hearts display (Top Left) - up to 5 hearts
        for i in range(5):
            hx = 16 + i * 32
            hy = 14
            if i < self.state.hearts:
                # Red heart
                pyxel.rect(hx + 4, hy, 8, 4, 8)
                pyxel.rect(hx + 16, hy, 8, 4, 8)
                pyxel.rect(hx, hy + 4, 28, 8, 8)
                pyxel.rect(hx + 4, hy + 12, 20, 4, 8)
                pyxel.rect(hx + 8, hy + 16, 12, 4, 8)
                pyxel.rect(hx + 12, hy + 20, 4, 4, 8)
                pyxel.rect(hx + 4, hy + 4, 4, 4, 7)  # Specular glint
            else:
                pyxel.rectb(hx, hy + 4, 28, 16, 5)

        # Active Pacts Display (Under hearts)
        active_pacts = [(sin, k) for sin, k in self.bargains.selection_counts.items() if k > 0]
        if active_pacts:
            pact_items = [f"{sin.name} k={k}" for sin, k in active_pacts]
            pact_text = "PACTS: " + " | ".join(pact_items)
            pact_w = min(360, len(pact_text) * 4 + 14)
            pyxel.rect(14, 44, pact_w, 18, 0)
            pyxel.rectb(14, 44, pact_w, 18, 10 if (pyxel.frame_count // 10) % 2 == 0 else 9)
            draw_text_scaled(18, 49, pact_text, 10, scale=1)
        else:
            pyxel.rect(14, 44, 160, 18, 0)
            pyxel.rectb(14, 44, 160, 18, 1)
            draw_text_scaled(18, 49, "PACTS: NONE (0 ACTIVE)", 5, scale=1)

        # Elapsed Time (Top Center)
        elapsed_sec = self.state.total_frames / 30.0
        time_str = f"TIME: {elapsed_sec:04.1f}s"
        flash_time = (pyxel.frame_count // 15) % 2 == 0
        draw_text_scaled(self.SCREEN_WIDTH // 2 - 56, 16, time_str, 10 if flash_time else 7, scale=2)

        # Version stamp
        draw_text_scaled(self.SCREEN_WIDTH - 52, self.SCREEN_HEIGHT - 14, self.VERSION, 5, scale=1)

        # Score (Top Right)
        score_str = f"SCORE: {self.state.score:06d}"
        draw_text_scaled(self.SCREEN_WIDTH - 240, 16, score_str, 10, scale=2)

        # Multiplier
        if self.state.score_multiplier > 1.05:
            mult_str = f"x{self.state.score_multiplier:.1f}"
            draw_text_scaled(self.SCREEN_WIDTH - 120, 36, mult_str, 9, scale=2)

        # Bot Auto-Play Indicator
        if self.bot_mode:
            pyxel.rect(self.SCREEN_WIDTH - 245, 54, 235, 18, 0)
            pyxel.rectb(self.SCREEN_WIDTH - 245, 54, 235, 18, 11)
            draw_text_scaled(self.SCREEN_WIDTH - 238, 59, "[BOT ON: 80% SPD, 20% BLIND]", 11, scale=1)
        else:
            draw_text_scaled(self.SCREEN_WIDTH - 110, 59, "[B] BOT: OFF", 5, scale=1)

        # Video Recording Indicator
        if self.video_recorder.is_recording:
            flash = (pyxel.frame_count // 6) % 2 == 0
            if flash:
                pyxel.circ(self.SCREEN_WIDTH - 235, 84, 4, 8)
            rec_secs = self.video_recorder.frames_recorded // 30
            draw_text_scaled(self.SCREEN_WIDTH - 225, 80, f"REC: {rec_secs:02d}s", 8 if flash else 7, scale=1)
        else:
            draw_text_scaled(self.SCREEN_WIDTH - 110, 80, "[V] REC: OFF", 5, scale=1)

        # Greed Kill-Timer Warning
        if self.state.greed_timer_active and self.state.greed_kill_timer > 0:
            secs_left = self.state.greed_kill_timer / 30.0
            flash = (pyxel.frame_count // 4) % 2 == 0
            col = 8 if flash else 7
            msg = f"DEBT DUE: {secs_left:.1f}s"
            draw_text_scaled(self.SCREEN_WIDTH // 2 - 80, 48, msg, col, scale=2)

        # Wrath Zero Yield Warning
        if self.state.wrath_zero_yield_timer > 0:
            draw_text_scaled(16, 70, "WRATH: ZERO YIELD", 2, scale=2)

    def draw_kairos_modal(self):
        """Draw 2-column Kairos modal navigated strictly via Left/Right arrows or A/D."""
        modal_x = 30
        modal_y = 60
        modal_w = 540
        modal_h = 680

        # Modal backdrop
        pyxel.rect(modal_x, modal_y, modal_w, modal_h, 0)
        pyxel.rectb(modal_x, modal_y, modal_w, modal_h, 8)
        pyxel.rectb(modal_x + 2, modal_y + 2, modal_w - 4, modal_h - 4, 2)

        # Header
        draw_text_scaled(modal_x + 70, modal_y + 16, "KAIROS CIRCUIT BREAKER", 7, scale=2)
        draw_text_scaled(modal_x + 150, modal_y + 38, "BORROW YOUR TIME", 8, scale=2)

        # 2.0s countdown timer bar
        timer_w = 440
        timer_x = modal_x + 50
        timer_y = modal_y + 62
        ratio = 1.0 - (self.state.kairos_timer / float(self.state.KAIROS_FRAMES))
        fill_w = max(0, int(timer_w * ratio))
        pyxel.rect(timer_x, timer_y, timer_w, 6, 1)
        pyxel.rect(timer_x, timer_y, fill_w, 6, 9)

        # 2 Wide Columns matching Left and Right
        col_w = 236
        col_gap = 24
        start_x = modal_x + 22
        col_y = modal_y + 82
        col_h = 520

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
            pyxel.rect(cx + 14, col_y + 12, col_w - 28, 26, badge_col)
            draw_text_scaled(cx + 40, col_y + 19, col_labels[i], 7, scale=1)

            # Pure Sin Name
            draw_text_scaled(cx + 16, col_y + 52, defn.name.upper(), 10 if is_selected else 7, scale=2)
            draw_text_scaled(cx + 16, col_y + 76, f"({defn.latin_name})", 6, scale=1)
            draw_text_scaled(cx + 16, col_y + 94, f"LEVEL: k={k}", 9, scale=1)

            # Visual divider
            pyxel.line(cx + 14, col_y + 112, cx + col_w - 14, col_y + 112, 6)

            # Boon section
            boon_val = defn.get_boon_value(k)
            draw_text_scaled(cx + 16, col_y + 128, "PRO (NOW):", 11, scale=1)
            draw_text_scaled(cx + 16, col_y + 146, f"+{defn.boon_name}", 7, scale=1)
            draw_text_scaled(cx + 16, col_y + 166, f"{boon_val:.1f} {defn.boon_unit}", 11, scale=2)

            # Visual divider
            pyxel.line(cx + 14, col_y + 220, cx + col_w - 14, col_y + 220, 2)

            # Curse section
            curse_val = defn.get_curse_value(k)
            draw_text_scaled(cx + 16, col_y + 240, "CON (FOREVER):", 8, scale=1)
            draw_text_scaled(cx + 16, col_y + 258, f"-{defn.curse_name}", 7, scale=1)
            draw_text_scaled(cx + 16, col_y + 278, f"{curse_val:.1f} {defn.curse_unit}", 8, scale=2)

            # Compounding formula indicator
            draw_text_scaled(cx + 16, col_y + 380, "COMPOUNDING FORMULA:", 6, scale=1)
            draw_text_scaled(cx + 16, col_y + 400, "Boon: 0.75^k  (Diminishing)", 6, scale=1)
            draw_text_scaled(cx + 16, col_y + 420, "Curse: 1.50^k (Compounding)", 8, scale=1)

            # Selection status
            if is_selected:
                pyxel.rect(cx + 14, col_y + col_h - 44, col_w - 28, 30, 10)
                draw_text_scaled(cx + 56, col_y + col_h - 34, "SELECTED", 0, scale=1)

        # Footer instructions
        draw_text_scaled(modal_x + 80, modal_y + modal_h - 44, "STEER [A]/[D] OR ARROWS TO SELECT PACT", 7, scale=1)
        draw_text_scaled(modal_x + 110, modal_y + modal_h - 26, "SEALS AUTOMATICALLY UPON TIMEOUT", 6, scale=1)

    def draw_feedback_banner(self):
        fb = self.selected_feedback
        if not fb:
            return
        pyxel.rect(40, 720, 520, 44, 0)
        pyxel.rectb(40, 720, 520, 44, 10)
        txt = f"PACT SEALED: {fb['sin'].upper()}!"
        draw_text_scaled(80, 734, txt, 10, scale=2)

    def draw_title_screen(self):
        # Pulsing logo centered
        draw_text_scaled(188, 90, "GRAIN OF DOUBT", 10, scale=4)
        draw_text_scaled(200, 140, "PYWEEK 42 : BORROWED TIME", 9, scale=2)
        draw_text_scaled(272, 164, self.VERSION, 9, scale=1)
        draw_text_scaled(236, 178, "BY ARIAN PRABOWO", 7, scale=2)

        # Subtitles centered
        draw_text_scaled(180, 225, "FALL DOWN THE COSMIC HOURGLASS", 7, scale=2)
        draw_text_scaled(180, 260, "COLLECT GOLDEN SAND TO SURVIVE", 6, scale=2)
        draw_text_scaled(168, 295, "DODGE LETHAL FALLING GLASS SHARDS", 6, scale=2)

        # Controls box
        pyxel.rect(60, 360, 480, 270, 1)
        pyxel.rectb(60, 360, 480, 270, 5)

        draw_text_scaled(90, 380, "CONTROLS & HOW TO PLAY (INFINITE SKI-FREE ARENA)", 10, scale=1)
        draw_text_scaled(90, 405, "A / D or LEFT / RIGHT ARROWS", 7, scale=2)
        draw_text_scaled(110, 435, "Steer Lateral Descent to Catch Sand & Dodge Glass", 6, scale=1)
        draw_text_scaled(90, 470, "KAIROS TIME-FREEZE (2 PACTS)", 8, scale=2)
        draw_text_scaled(110, 500, "Steer Left or Right to Seal Faustian Sin", 6, scale=1)
        draw_text_scaled(90, 535, "SHORTCUTS", 9, scale=1)
        draw_text_scaled(110, 555, "[B] Toggle Bot Mode  |  [V] Toggle Video Rec", 7, scale=1)
        draw_text_scaled(110, 575, "[Q] Quit Game        |  [R] Quick Restart", 5, scale=1)

        # Start prompt
        blink = (pyxel.frame_count // 12) % 2 == 0
        if blink:
            draw_text_scaled(168, 675, "STEER [A]/[D] OR ARROW TO DESCEND", 7, scale=2)

        draw_text_scaled(self.SCREEN_WIDTH - 52, self.SCREEN_HEIGHT - 14, self.VERSION, 5, scale=1)

    def draw_game_over_screen(self):
        # Dark overlay box
        pyxel.rect(40, 80, 520, 640, 0)
        pyxel.rectb(40, 80, 520, 640, 8)
        pyxel.rectb(44, 84, 512, 632, 2)

        draw_text_scaled(186, 105, "HOURGLASS SHATTERED", 8, scale=3)
        draw_text_scaled(275, 142, self.VERSION, 6, scale=1)
        draw_text_scaled(236, 156, "BY ARIAN PRABOWO", 6, scale=1)

        reason = self.state.death_reason or "Consumed by the Void"
        draw_text_scaled(70, 185, reason[:36], 7, scale=2)

        # Inner stats container
        pyxel.rect(60, 225, 480, 270, 1)
        pyxel.rectb(60, 225, 480, 270, 5)

        time_survived = self.state.total_frames / 30.0
        draw_text_scaled(80, 245, f"TIME SURVIVED : {time_survived:6.1f} SECONDS", 10, scale=2)
        draw_text_scaled(80, 290, f"FINAL SCORE   : {self.state.score:6d}", 10, scale=2)
        draw_text_scaled(80, 335, f"SAND REAPED   : {self.state.total_sand_collected:6d}", 9, scale=2)
        draw_text_scaled(80, 380, f"SHARDS EVADED : {self.state.total_shards_dodged:6d}", 6, scale=2)
        draw_text_scaled(80, 425, f"PACTS SEALED  : {len(self.bargains.history):6d}", 8, scale=2)

        # Active pact breakdown
        active_pacts = [(s.name, k) for s, k in self.bargains.selection_counts.items() if k > 0]
        if active_pacts:
            pact_str = ", ".join([f"{name}(k={k})" for name, k in active_pacts])
            draw_text_scaled(70, 515, f"ACTIVE PACTS: {pact_str}"[:60], 9, scale=1)
        else:
            draw_text_scaled(70, 515, "ACTIVE PACTS: NONE (CLEAN SOUL)", 5, scale=1)

        # Restart prompt
        blink = (pyxel.frame_count // 10) % 2 == 0
        if blink:
            draw_text_scaled(160, 580, "PRESS ANY KEY TO DESCEND AGAIN", 7, scale=2)

        draw_text_scaled(self.SCREEN_WIDTH - 52, self.SCREEN_HEIGHT - 14, self.VERSION, 5, scale=1)


def main():
    bot_flag = "--bot" in sys.argv
    video_flag = ("--video" in sys.argv or "--record" in sys.argv or "--export-video" in sys.argv)
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
    )


if __name__ == "__main__":
    main()
