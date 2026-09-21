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


def render_vignette(px: float, py: float, radius: float, screen_w: int = 600, screen_h: int = 800, pyxel_module=None):
    """Draw circular darkness vignette mask centered at (px, py)."""
    if pyxel_module is None:
        return
    r = max(20.0, radius)
    r_sq = r * r

    for y in range(screen_h):
        dy = y - py
        dy_sq = dy * dy
        if dy_sq >= r_sq:
            pyxel_module.rect(0, y, screen_w, 1, 0)
        else:
            dx = math.sqrt(r_sq - dy_sq)
            lx = int(px - dx)
            rx = int(px + dx)
            if lx > 0:
                pyxel_module.rect(0, y, lx, 1, 0)
            if rx < screen_w:
                pyxel_module.rect(rx, y, screen_w - rx, 1, 0)


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
    pyxel.blt(x, y, img_bank, 0, 0, w, h, colkey=0, scale=scale)


class GrainOfDoubtApp:
    SCREEN_WIDTH: int = 600
    SCREEN_HEIGHT: int = 800

    def __init__(self, headless: bool = False):
        self.headless = headless
        self.state = StateManager()
        self.entities = EntityManager(self.SCREEN_WIDTH, self.SCREEN_HEIGHT)
        self.bargains = BargainManager()
        self.audio = AudioManager()
        self.active_options: List[Tuple[SinType, any, int]] = []
        self.selected_card_index: int = 1  # 0=Left, 1=Center, 2=Right
        self.selected_feedback: Optional[dict] = None
        self.feedback_timer: int = 0

        # Cosmic void background stars (parallax)
        self.stars = [
            [random.uniform(0, self.SCREEN_WIDTH), random.uniform(0, self.SCREEN_HEIGHT), random.choice([1, 5, 6]), random.choice([2, 3])]
            for _ in range(48)
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
            pyxel.run(self.update, self.draw)

    def start_new_game(self):
        self.state.start_game()
        self.entities.reset()
        self.bargains.reset()
        self.active_options.clear()
        self.selected_card_index = 1
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

        # Feedback banner timer
        if self.feedback_timer > 0:
            self.feedback_timer -= 1

        # Background cosmic drift
        scroll_drift = max(2.0, self.state.scroll_speed)
        for star in self.stars:
            star[1] -= scroll_drift * (0.3 if star[2] == 1 else 0.6)
            if star[1] < 0:
                star[1] = self.SCREEN_HEIGHT
                star[0] = random.uniform(0, self.SCREEN_WIDTH)

        # State dispatch
        if self.state.current_state == GameState.TITLE:
            # Start game with any lateral key or space/enter
            if (pyxel.btnp(pyxel.KEY_LEFT) or pyxel.btnp(pyxel.KEY_RIGHT) or
                pyxel.btnp(pyxel.KEY_A) or pyxel.btnp(pyxel.KEY_D) or
                pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.KEY_RETURN)):
                self.start_new_game()

        elif self.state.current_state == GameState.CHRONOS:
            self.update_input()
            self.state.update_timers()
            self.entities.update(self.state)

            # Check if Kairos was triggered this frame
            if self.state.current_state == GameState.KAIROS:
                self.audio.play_kairos(pyxel)
                self.active_options = self.bargains.draw_options(3)
                self.selected_card_index = 1  # Start at Center

            # Check if Game Over triggered
            if self.state.current_state == GameState.GAMEOVER:
                self.audio.play_death(pyxel)

        elif self.state.current_state == GameState.KAIROS:
            # Kairos time circuit breaker: navigate cards with A/D or Left/Right arrows
            move_left = pyxel.btnp(pyxel.KEY_LEFT) or pyxel.btnp(pyxel.KEY_A)
            move_right = pyxel.btnp(pyxel.KEY_RIGHT) or pyxel.btnp(pyxel.KEY_D)

            instant_seal = False
            if move_left:
                if self.selected_card_index > 0:
                    self.selected_card_index -= 1
                else:
                    instant_seal = True  # Double-tap left confirms left card

            elif move_right:
                if self.selected_card_index < len(self.active_options) - 1:
                    self.selected_card_index += 1
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

        elif self.state.current_state == GameState.GAMEOVER:
            # Restart with any control key
            if (pyxel.btnp(pyxel.KEY_LEFT) or pyxel.btnp(pyxel.KEY_RIGHT) or
                pyxel.btnp(pyxel.KEY_A) or pyxel.btnp(pyxel.KEY_D) or
                pyxel.btnp(pyxel.KEY_R) or pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.KEY_RETURN)):
                self.start_new_game()

    def draw(self):
        if pyxel is None:
            return

        # Screen shake offset
        ox = 0
        oy = 0
        if self.state.shake_intensity > 0:
            ox = random.randint(-int(self.state.shake_intensity), int(self.state.shake_intensity))
            oy = random.randint(-int(self.state.shake_intensity), int(self.state.shake_intensity))
        pyxel.camera(ox, oy)

        # Clear background void (Color 0: Black)
        pyxel.cls(0)

        # Draw cosmic void stars
        for sx, sy, sc, sz in self.stars:
            pyxel.rect(int(sx), int(sy), sz, sz, sc)

        # Draw outer cosmic hourglass borders (Hourglass-ception)
        self.draw_cosmic_hourglass_walls()

        if self.state.current_state == GameState.TITLE:
            self.draw_title_screen()
            pyxel.camera(0, 0)
            return

        # Draw Sand grains (10x10 px)
        for sand in self.entities.sands:
            c = 10 if (pyxel.frame_count // 3 + int(sand.shimmer_phase * 4)) % 2 == 0 else 9
            pyxel.rect(int(sand.x - 5), int(sand.y - 5), 10, 10, c)
            pyxel.rect(int(sand.x - 2), int(sand.y - 2), 4, 4, 7)  # Center glint

        # Draw Glass shards (20x40 px rotating triangles)
        for shard in self.entities.shards:
            self.draw_glass_shard(shard)

        # Draw Particles
        for p in self.entities.particles:
            pyxel.rect(int(p.x), int(p.y), p.size, p.size, p.color)

        # Draw Player Hourglass (40x60 px)
        self.draw_player_hourglass()

        # Render Vignette Mask (Darkness bounds)
        render_vignette(
            self.entities.player.x,
            self.entities.player.y,
            self.state.vignette_radius,
            self.SCREEN_WIDTH,
            self.SCREEN_HEIGHT,
            pyxel,
        )

        # Reset camera for HUD overlay
        pyxel.camera(0, 0)

        # Draw HUD (Score, Hearts, Kairos meter, Kill timer)
        self.draw_hud()

        # Draw active modal overlays
        if self.state.current_state == GameState.KAIROS:
            self.draw_kairos_modal()
        elif self.state.current_state == GameState.GAMEOVER:
            self.draw_game_over_screen()

        # Selected feedback banner
        if self.feedback_timer > 0 and self.selected_feedback:
            self.draw_feedback_banner()

    def draw_cosmic_hourglass_walls(self):
        """Draw collapsing outer cosmic hourglass walls on left and right."""
        t = pyxel.frame_count * 0.05
        for y in range(0, self.SCREEN_HEIGHT, 4):
            # Left neck wall
            curve = math.sin(y * 0.01 + t) * 12.0
            lw = int(40 + curve)
            pyxel.rect(0, y, lw, 4, 1)
            pyxel.rect(lw, y, 4, 4, 5)
            pyxel.rect(lw + 4, y, 4, 4, 6)

            # Right neck wall
            rw = int(self.SCREEN_WIDTH - 48 - curve)
            pyxel.rect(rw, y, self.SCREEN_WIDTH - rw, 4, 1)
            pyxel.rect(rw - 4, y, 4, 4, 5)
            pyxel.rect(rw - 8, y, 4, 4, 6)

    def draw_player_hourglass(self):
        player = self.entities.player
        px = int(player.x)
        py = int(player.y)

        # Invulnerability flash
        if self.state.invulnerable_timer > 0 and (self.state.invulnerable_timer // 3) % 2 == 1:
            return

        # Top brass cap (y-30 to y-24)
        pyxel.rect(px - 20, py - 30, 40, 6, 4)
        pyxel.rect(px - 6, py - 30, 12, 6, 9)

        # Top glass bulb (y-24 to y-4)
        pyxel.line(px - 18, py - 24, px - 6, py - 4, 6)
        pyxel.line(px + 18, py - 24, px + 6, py - 4, 6)
        # Top bulb sand
        pyxel.rect(px - 14, py - 22, 28, 8, 10)
        pyxel.rect(px - 10, py - 14, 20, 6, 9)

        # Center waist (y-4 to y+4)
        pyxel.rect(px - 4, py - 2, 8, 4, 7)
        # Dripping sand stream
        drip_y = int((player.sand_drain_phase % 1.0) * 12)
        pyxel.rect(px - 2, py + 2 + drip_y, 4, 4, 10)

        # Bottom glass bulb (y+4 to y+24)
        pyxel.line(px - 6, py + 4, px - 18, py + 24, 6)
        pyxel.line(px + 6, py + 4, px + 18, py + 24, 6)
        # Bottom bulb sand mound
        pyxel.rect(px - 12, py + 12, 24, 10, 10)
        pyxel.rect(px - 8, py + 8, 16, 4, 9)

        # Bottom brass cap (y+24 to y+30)
        pyxel.rect(px - 20, py + 24, 40, 6, 4)
        pyxel.rect(px - 6, py + 24, 12, 6, 9)

        # Glass shine reflections
        pyxel.rect(px - 16, py - 20, 4, 8, 7)
        pyxel.rect(px - 14, py + 14, 4, 6, 7)

    def draw_glass_shard(self, shard: GlassShard):
        sx = int(shard.x)
        sy = int(shard.y)
        angle = shard.rotation_angle
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)

        # 3 points of sharp triangular shard (scaled to 20x40)
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

        # Draw filled triangle
        x0, y0 = rot_pts[0]
        x1, y1 = rot_pts[1]
        x2, y2 = rot_pts[2]
        pyxel.tri(x0, y0, x1, y1, x2, y2, 7)
        pyxel.line(x0, y0, x1, y1, 6)
        pyxel.line(x1, y1, x2, y2, 0)
        pyxel.line(x2, y2, x0, y0, 6)

    def draw_hud(self):
        # Hearts display (Top Left)
        for i in range(3):
            hx = 16 + i * 36
            hy = 14
            if i < self.state.hearts:
                # Red heart (scaled)
                pyxel.rect(hx + 4, hy, 8, 4, 8)
                pyxel.rect(hx + 16, hy, 8, 4, 8)
                pyxel.rect(hx, hy + 4, 28, 8, 8)
                pyxel.rect(hx + 4, hy + 12, 20, 4, 8)
                pyxel.rect(hx + 8, hy + 16, 12, 4, 8)
                pyxel.rect(hx + 12, hy + 20, 4, 4, 8)
                pyxel.rect(hx + 4, hy + 4, 4, 4, 7)  # Specular glint
            else:
                pyxel.rectb(hx, hy + 4, 28, 16, 5)

        # Score (Top Right)
        score_str = f"SCORE: {self.state.score:06d}"
        draw_text_scaled(self.SCREEN_WIDTH - 240, 16, score_str, 10, scale=2)

        # Multiplier
        if self.state.score_multiplier > 1.05:
            mult_str = f"x{self.state.score_multiplier:.1f}"
            draw_text_scaled(self.SCREEN_WIDTH - 120, 36, mult_str, 9, scale=2)

        # Chronos Progress Bar (Top Center)
        if self.state.current_state == GameState.CHRONOS:
            meter_w = 160
            meter_x = (self.SCREEN_WIDTH - meter_w) // 2
            meter_y = 16
            progress = self.state.chronos_timer / float(self.state.CHRONOS_FRAMES)
            fill_w = int(meter_w * progress)

            pyxel.rect(meter_x, meter_y, meter_w, 8, 1)
            color = 8 if progress > 0.80 and (pyxel.frame_count // 3) % 2 == 0 else 10
            pyxel.rect(meter_x, meter_y, fill_w, 8, color)
            pyxel.rectb(meter_x - 2, meter_y - 2, meter_w + 4, 12, 6)

            draw_text_scaled(meter_x + 28, meter_y + 14, "CHRONOS DESCENT", 6, scale=1)

        # Greed Kill-Timer Warning
        if self.state.greed_timer_active and self.state.greed_kill_timer > 0:
            secs_left = self.state.greed_kill_timer / 30.0
            flash = (pyxel.frame_count // 4) % 2 == 0
            col = 8 if flash else 7
            msg = f"DEBT DUE: {secs_left:.1f}s"
            draw_text_scaled(self.SCREEN_WIDTH // 2 - 80, 48, msg, col, scale=2)

        # Wrath Zero Yield Warning
        if self.state.wrath_zero_yield_timer > 0:
            draw_text_scaled(16, 48, "WRATH: ZERO YIELD", 2, scale=2)

    def draw_kairos_modal(self):
        """Draw 3-column Kairos modal navigated strictly via Left/Right arrows or A/D."""
        modal_x = 30
        modal_y = 70
        modal_w = 540
        modal_h = 660

        # Modal backdrop
        pyxel.rect(modal_x, modal_y, modal_w, modal_h, 0)
        pyxel.rectb(modal_x, modal_y, modal_w, modal_h, 8)
        pyxel.rectb(modal_x + 2, modal_y + 2, modal_w - 4, modal_h - 4, 2)

        # Header
        draw_text_scaled(modal_x + 70, modal_y + 18, "KAIROS CIRCUIT BREAKER", 7, scale=2)
        draw_text_scaled(modal_x + 150, modal_y + 40, "BORROW YOUR TIME", 8, scale=2)

        # 2.0s countdown timer bar
        timer_w = 440
        timer_x = modal_x + 50
        timer_y = modal_y + 64
        ratio = 1.0 - (self.state.kairos_timer / float(self.state.KAIROS_FRAMES))
        fill_w = max(0, int(timer_w * ratio))
        pyxel.rect(timer_x, timer_y, timer_w, 6, 1)
        pyxel.rect(timer_x, timer_y, fill_w, 6, 9)

        # 3 Columns matching Left, Center, Right
        col_w = 156
        col_gap = 18
        start_x = modal_x + 20
        col_y = modal_y + 86
        col_h = 500

        col_labels = ["< LEFT", "- CENTER -", "RIGHT >"]

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
            pyxel.rect(cx + 10, col_y + 10, col_w - 20, 24, badge_col)
            draw_text_scaled(cx + 20, col_y + 16, col_labels[i], 7, scale=1)

            # Pure Sin Name (NO "Sands of")
            draw_text_scaled(cx + 14, col_y + 50, defn.name.upper(), 10 if is_selected else 7, scale=2)
            draw_text_scaled(cx + 14, col_y + 72, f"({defn.latin_name})", 6, scale=1)
            draw_text_scaled(cx + 14, col_y + 88, f"LEVEL: k={k}", 9, scale=1)

            # Visual divider
            pyxel.line(cx + 10, col_y + 104, cx + col_w - 10, col_y + 104, 6)

            # Boon section
            boon_val = defn.get_boon_value(k)
            draw_text_scaled(cx + 12, col_y + 120, "PRO (NOW):", 11, scale=1)
            draw_text_scaled(cx + 12, col_y + 136, f"+{defn.boon_name}", 7, scale=1)
            draw_text_scaled(cx + 12, col_y + 152, f"{boon_val:.1f} {defn.boon_unit}", 11, scale=2)

            # Visual divider
            pyxel.line(cx + 10, col_y + 200, cx + col_w - 10, col_y + 200, 2)

            # Curse section
            curse_val = defn.get_curse_value(k)
            draw_text_scaled(cx + 12, col_y + 220, "CON (FOREVER):", 8, scale=1)
            draw_text_scaled(cx + 12, col_y + 236, f"-{defn.curse_name}", 7, scale=1)
            draw_text_scaled(cx + 12, col_y + 252, f"{curse_val:.1f} {defn.curse_unit}", 8, scale=2)

            # Compounding formula indicator
            draw_text_scaled(cx + 12, col_y + 360, "SCALE FACTOR:", 6, scale=1)
            draw_text_scaled(cx + 12, col_y + 376, "Boon: 0.75^k", 6, scale=1)
            draw_text_scaled(cx + 12, col_y + 392, "Curse: 1.50^k", 8, scale=1)

            # Selection status
            if is_selected:
                pyxel.rect(cx + 10, col_y + col_h - 40, col_w - 20, 28, 10)
                draw_text_scaled(cx + 24, col_y + col_h - 32, "SELECTED", 0, scale=1)

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
        # Pulsing logo
        draw_text_scaled(100, 110, "GRAIN OF DOUBT", 10, scale=4)
        draw_text_scaled(130, 160, "PYWEEK 42 : BORROWED TIME", 9, scale=2)

        # Author attribution
        draw_text_scaled(200, 200, "BY ARIAN PRABOWO", 7, scale=2)

        # Subtitles
        draw_text_scaled(120, 260, "FALL DOWN THE COSMIC HOURGLASS", 7, scale=2)
        draw_text_scaled(110, 290, "COLLECT GOLDEN SAND TO SURVIVE", 6, scale=2)
        draw_text_scaled(90, 320, "DODGE LETHAL FALLING GLASS SHARDS", 6, scale=2)

        # Controls box
        pyxel.rect(80, 400, 440, 220, 1)
        pyxel.rectb(80, 400, 440, 220, 5)

        draw_text_scaled(110, 420, "CONTROLS", 10, scale=2)
        draw_text_scaled(110, 460, "A / D or LEFT / RIGHT ARROWS:", 7, scale=2)
        draw_text_scaled(130, 490, "Steer Lateral Descent", 6, scale=2)
        draw_text_scaled(110, 530, "KAIROS TIME-FREEZE:", 8, scale=2)
        draw_text_scaled(130, 560, "Steer Left/Right to Choose Faustian Sin", 6, scale=2)

        # Start prompt
        blink = (pyxel.frame_count // 12) % 2 == 0
        if blink:
            draw_text_scaled(100, 680, "STEER [A]/[D] OR ARROW TO DESCEND", 7, scale=2)

    def draw_game_over_screen(self):
        # Dark overlay
        pyxel.rect(40, 100, 520, 600, 0)
        pyxel.rectb(40, 100, 520, 600, 8)
        pyxel.rectb(44, 104, 512, 592, 2)

        draw_text_scaled(90, 140, "HOURGLASS SHATTERED", 8, scale=3)

        # Author
        draw_text_scaled(210, 184, "BY ARIAN PRABOWO", 6, scale=1)

        reason = self.state.death_reason or "Consumed by the Void"
        draw_text_scaled(80, 220, reason[:32], 7, scale=2)

        # Stats
        draw_text_scaled(80, 280, f"FINAL SCORE  : {self.state.score}", 10, scale=2)
        draw_text_scaled(80, 330, f"SAND REAPED  : {self.state.total_sand_collected}", 6, scale=2)
        draw_text_scaled(80, 380, f"SHARDS EVADED: {self.state.total_shards_dodged}", 6, scale=2)
        draw_text_scaled(80, 430, f"PACTS SEALED : {len(self.bargains.history)}", 9, scale=2)

        # Restart
        blink = (pyxel.frame_count // 10) % 2 == 0
        if blink:
            draw_text_scaled(70, 540, "PRESS ANY KEY TO DESCEND AGAIN", 7, scale=2)


def main():
    GrainOfDoubtApp(headless=False)


if __name__ == "__main__":
    main()
