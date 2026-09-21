"""Grain of Doubt - PyWeek 42
A 2D Retro Arcade Falling Hourglass Endless Runner built with Pyxel.
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


def render_vignette(px: float, py: float, radius: float, screen_w: int = 120, screen_h: int = 160, pyxel_module=None):
    """Draw circular darkness vignette mask centered at (px, py)."""
    if pyxel_module is None:
        return
    r = max(4.0, radius)
    r_sq = r * r

    for y in range(screen_h):
        dy = y - py
        dy_sq = dy * dy
        if dy_sq >= r_sq:
            # Entire row outside radius: fill black
            pyxel_module.rect(0, y, screen_w, 1, 0)
        else:
            dx = math.sqrt(r_sq - dy_sq)
            lx = int(px - dx)
            rx = int(px + dx)
            if lx > 0:
                pyxel_module.rect(0, y, lx, 1, 0)
            if rx < screen_w:
                pyxel_module.rect(rx, y, screen_w - rx, 1, 0)


class GrainOfDoubtApp:
    SCREEN_WIDTH: int = 120
    SCREEN_HEIGHT: int = 160

    def __init__(self, headless: bool = False):
        self.headless = headless
        self.state = StateManager()
        self.entities = EntityManager(self.SCREEN_WIDTH, self.SCREEN_HEIGHT)
        self.bargains = BargainManager()
        self.audio = AudioManager()
        self.active_options: List[Tuple[SinType, any, int]] = []
        self.selected_feedback: Optional[dict] = None
        self.feedback_timer: int = 0

        # Cosmic void background stars
        self.stars = [
            [random.uniform(0, self.SCREEN_WIDTH), random.uniform(0, self.SCREEN_HEIGHT), random.choice([1, 5, 6])]
            for _ in range(32)
        ]

        if not headless and pyxel is not None:
            pyxel.init(
                self.SCREEN_WIDTH,
                self.SCREEN_HEIGHT,
                title="Grain of Doubt",
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
        self.selected_feedback = None

    def update_input(self):
        if pyxel is None:
            return

        # Player inputs for Chronos
        left = pyxel.btn(pyxel.KEY_LEFT) or pyxel.btn(pyxel.KEY_A)
        right = pyxel.btn(pyxel.KEY_RIGHT) or pyxel.btn(pyxel.KEY_D)
        up = pyxel.btn(pyxel.KEY_UP) or pyxel.btn(pyxel.KEY_W)
        down = pyxel.btn(pyxel.KEY_DOWN) or pyxel.btn(pyxel.KEY_S)

        self.state._input_left = left
        self.state._input_right = right
        self.state._input_up = up
        self.state._input_down = down
        self.state.dive_active = down
        self.state.brake_active = up

    def update(self):
        if pyxel is None:
            return

        # Feedback banner timer
        if self.feedback_timer > 0:
            self.feedback_timer -= 1

        # Background cosmic drift
        scroll_drift = max(0.4, self.state.scroll_speed)
        for star in self.stars:
            star[1] -= scroll_drift * (0.3 if star[2] == 1 else 0.6)
            if star[1] < 0:
                star[1] = self.SCREEN_HEIGHT
                star[0] = random.uniform(0, self.SCREEN_WIDTH)

        # State dispatch
        if self.state.current_state == GameState.TITLE:
            if pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.KEY_RETURN) or pyxel.btnp(pyxel.KEY_Z):
                self.start_new_game()

        elif self.state.current_state == GameState.CHRONOS:
            self.update_input()
            prev_state = self.state.current_state
            self.state.update_timers()
            self.entities.update(self.state)

            # Check if Kairos was triggered this frame
            if self.state.current_state == GameState.KAIROS:
                self.audio.play_kairos(pyxel)
                self.active_options = self.bargains.draw_options(3)

            # Check if Game Over triggered
            if self.state.current_state == GameState.GAMEOVER:
                self.audio.play_death(pyxel)

        elif self.state.current_state == GameState.KAIROS:
            # Kairos time circuit breaker: wait for selection 1, 2, 3 or timeout
            chosen_index = -1
            if pyxel.btnp(pyxel.KEY_1) or pyxel.btnp(pyxel.KEY_KP_1):
                chosen_index = 0
            elif pyxel.btnp(pyxel.KEY_2) or pyxel.btnp(pyxel.KEY_KP_2):
                chosen_index = 1
            elif pyxel.btnp(pyxel.KEY_3) or pyxel.btnp(pyxel.KEY_KP_3):
                chosen_index = 2

            if 0 <= chosen_index < len(self.active_options):
                chosen_sin, _, _ = self.active_options[chosen_index]
                feedback = self.bargains.apply_bargain(chosen_sin, self.state, self.entities)
                self.selected_feedback = feedback
                self.feedback_timer = 45
                self.audio.play_collect(pyxel)
                self.state.resume_chronos()
            else:
                # Advance Kairos timer toward timeout
                self.state.update_timers()
                if self.state.current_state == GameState.CHRONOS:
                    # Timed out without choice: penalty of silence
                    self.state.vignette_radius = max(self.state.min_vignette_radius, self.state.vignette_radius - 2.0)

        elif self.state.current_state == GameState.GAMEOVER:
            if pyxel.btnp(pyxel.KEY_R) or pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.KEY_RETURN):
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
        for sx, sy, sc in self.stars:
            pyxel.pset(int(sx), int(sy), sc)

        # Draw outer cosmic hourglass borders (Hourglass-ception)
        self.draw_cosmic_hourglass_walls()

        if self.state.current_state == GameState.TITLE:
            self.draw_title_screen()
            pyxel.camera(0, 0)
            return

        # Draw Sand grains
        for sand in self.entities.sands:
            c = 10 if (pyxel.frame_count // 3 + int(sand.shimmer_phase * 4)) % 2 == 0 else 9
            pyxel.rect(int(sand.x - 1), int(sand.y - 1), 2, 2, c)
            # Glint pixel
            pyxel.pset(int(sand.x), int(sand.y), 7)

        # Draw Glass shards
        for shard in self.entities.shards:
            self.draw_glass_shard(shard)

        # Draw Particles
        for p in self.entities.particles:
            pyxel.pset(int(p.x), int(p.y), p.color)

        # Draw Player Hourglass
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
        for y in range(0, self.SCREEN_HEIGHT, 2):
            # Left neck wall: gentle inward curve
            curve = math.sin(y * 0.05 + t) * 2.5
            lw = int(8 + curve)
            pyxel.rect(0, y, lw, 2, 1)
            pyxel.pset(lw, y, 5)
            pyxel.pset(lw + 1, y, 6)

            # Right neck wall
            rw = int(self.SCREEN_WIDTH - 8 - curve)
            pyxel.rect(rw, y, self.SCREEN_WIDTH - rw, 2, 1)
            pyxel.pset(rw, y, 5)
            pyxel.pset(rw - 1, y, 6)

    def draw_player_hourglass(self):
        player = self.entities.player
        px = int(player.x)
        py = int(player.y)

        # Invulnerability flash
        if self.state.invulnerable_timer > 0 and (self.state.invulnerable_timer // 3) % 2 == 1:
            return

        # Top brass cap
        pyxel.line(px - 4, py - 6, px + 4, py - 6, 4)
        pyxel.pset(px, py - 6, 9)

        # Top glass bulb
        pyxel.line(px - 3, py - 5, px - 1, py - 2, 6)
        pyxel.line(px + 3, py - 5, px + 1, py - 2, 6)
        # Top bulb sand
        pyxel.rect(px - 2, py - 5, 5, 2, 10)
        pyxel.pset(px - 1, py - 3, 9)
        pyxel.pset(px + 1, py - 3, 9)

        # Center waist
        pyxel.pset(px, py, 7)
        # Dripping sand mote
        drip_offset = int((player.sand_drain_phase % 1.0) * 3)
        pyxel.pset(px, py + 1 + drip_offset, 10)

        # Bottom glass bulb
        pyxel.line(px - 1, py + 2, px - 3, py + 5, 6)
        pyxel.line(px + 1, py + 2, px + 3, py + 5, 6)
        # Bottom bulb sand mound
        pyxel.rect(px - 2, py + 4, 5, 2, 10)
        pyxel.pset(px, py + 3, 9)

        # Bottom brass cap
        pyxel.line(px - 4, py + 6, px + 4, py + 6, 4)
        pyxel.pset(px, py + 6, 9)

        # Glass shine reflections
        pyxel.pset(px - 3, py - 4, 7)
        pyxel.pset(px - 2, py + 4, 7)

    def draw_glass_shard(self, shard: GlassShard):
        sx = int(shard.x)
        sy = int(shard.y)
        angle = shard.rotation_angle
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)

        # 3 points of sharp triangular shard
        pts = [
            (0, -4),
            (2, 4),
            (-2, 3),
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
            hx = 3 + i * 8
            hy = 3
            if i < self.state.hearts:
                # Red heart
                pyxel.rect(hx + 1, hy, 2, 1, 8)
                pyxel.rect(hx + 4, hy, 2, 1, 8)
                pyxel.rect(hx, hy + 1, 7, 2, 8)
                pyxel.rect(hx + 1, hy + 3, 5, 1, 8)
                pyxel.rect(hx + 2, hy + 4, 3, 1, 8)
                pyxel.pset(hx + 3, hy + 5, 8)
                pyxel.pset(hx + 1, hy + 1, 7)  # highlight
            else:
                # Empty shattered heart frame
                pyxel.rectb(hx, hy + 1, 7, 3, 5)

        # Score (Top Right)
        score_str = f"{self.state.score:06d}"
        pyxel.text(self.SCREEN_WIDTH - 28, 3, score_str, 10)

        # Multiplier
        if self.state.score_multiplier > 1.05:
            mult_str = f"x{self.state.score_multiplier:.1f}"
            pyxel.text(self.SCREEN_WIDTH - 28, 10, mult_str, 9)

        # Chronos Cycle Progress Bar (Top Center)
        if self.state.current_state == GameState.CHRONOS:
            meter_w = 36
            meter_x = (self.SCREEN_WIDTH - meter_w) // 2
            meter_y = 3
            progress = self.state.chronos_timer / float(self.state.CHRONOS_FRAMES)
            fill_w = int(meter_w * progress)

            pyxel.rect(meter_x, meter_y, meter_w, 3, 1)
            color = 8 if progress > 0.80 and (pyxel.frame_count // 3) % 2 == 0 else 10
            pyxel.rect(meter_x, meter_y, fill_w, 3, color)
            pyxel.rectb(meter_x - 1, meter_y - 1, meter_w + 2, 5, 6)

            # Tiny label
            pyxel.text(meter_x + 6, meter_y + 4, "CHRONOS", 6)

        # Greed Kill-Timer Warning (Ominous countdown)
        if self.state.greed_timer_active and self.state.greed_kill_timer > 0:
            secs_left = self.state.greed_kill_timer / 30.0
            flash = (pyxel.frame_count // 4) % 2 == 0
            col = 8 if flash else 7
            msg = f"DEBT: {secs_left:.1f}s"
            pyxel.text(self.SCREEN_WIDTH // 2 - 20, 15, msg, col)

        # Wrath Zero Yield Warning
        if self.state.wrath_zero_yield_timer > 0:
            pyxel.text(3, 15, "ZERO YIELD", 2)

    def draw_kairos_modal(self):
        """Draw Kairos Circuit Breaker UI modal with 3 Faustian Bargains."""
        modal_x = 5
        modal_y = 10
        modal_w = 110
        modal_h = 142

        # Semi-dark backdrop
        pyxel.rect(modal_x, modal_y, modal_w, modal_h, 0)
        pyxel.rectb(modal_x, modal_y, modal_w, modal_h, 8)
        pyxel.rectb(modal_x + 1, modal_y + 1, modal_w - 2, modal_h - 2, 2)

        # Header
        pyxel.text(modal_x + 8, modal_y + 4, "KAIROS CIRCUIT BREAKER", 7)
        pyxel.text(modal_x + 22, modal_y + 11, "BORROW YOUR TIME", 8)

        # Countdown timer bar
        timer_w = 90
        timer_x = modal_x + 10
        timer_y = modal_y + 18
        ratio = 1.0 - (self.state.kairos_timer / float(self.state.KAIROS_FRAMES))
        fill_w = max(0, int(timer_w * ratio))
        pyxel.rect(timer_x, timer_y, timer_w, 2, 1)
        pyxel.rect(timer_x, timer_y, fill_w, 2, 9)

        # 3 Option cards (generous vertical room)
        for i, (sin, defn, k) in enumerate(self.active_options):
            cy = modal_y + 23 + i * 36
            cw = modal_w - 8
            cx = modal_x + 4

            # Card background
            pyxel.rect(cx, cy, cw, 33, 1)
            pyxel.rectb(cx, cy, cw, 33, 6)

            # Key badge
            pyxel.rect(cx + 2, cy + 2, 13, 14, 8)
            pyxel.text(cx + 4, cy + 6, f"[{i + 1}]", 7)

            # Sin Name & level
            title_txt = f"{defn.name.upper()[:16]}"
            pyxel.text(cx + 18, cy + 3, title_txt, 10)
            pyxel.text(cx + 84, cy + 3, f"k={k}", 9)

            # Boon & Curse
            boon_val = defn.get_boon_value(k)
            curse_val = defn.get_curse_value(k)
            boon_txt = f"+{defn.boon_name[:12]} ({boon_val:.1f})"
            curse_txt = f"-{defn.curse_name[:12]} ({curse_val:.1f})"
            pyxel.text(cx + 18, cy + 12, boon_txt, 11)
            pyxel.text(cx + 18, cy + 21, curse_txt, 8)

        # Footer
        pyxel.text(modal_x + 6, modal_y + 133, "PRESS 1, 2, OR 3 TO SEAL", 6)

    def draw_feedback_banner(self):
        fb = self.selected_feedback
        if not fb:
            return
        pyxel.rect(6, 144, 108, 12, 0)
        pyxel.rectb(6, 144, 108, 12, 10)
        txt = f"PACT: {fb['sin'].upper()[:14]} SEALED"
        pyxel.text(10, 147, txt, 10)

    def draw_title_screen(self):
        # Pulsing logo
        title_y = 18
        pyxel.text(32, title_y, "GRAIN OF DOUBT", 10)
        pyxel.text(12, title_y + 9, "PYWEEK 42 : BORROWED TIME", 9)

        # Subtitle
        pyxel.text(14, 38, "FALL DOWN COSMIC VOID", 7)
        pyxel.text(10, 46, "COLLECT GOLD SAND TO LIVE", 6)
        pyxel.text(8, 54, "DODGE LETHAL GLASS SHARDS", 6)

        # Controls summary
        pyxel.rect(6, 68, 108, 62, 1)
        pyxel.rectb(6, 68, 108, 62, 5)
        pyxel.text(10, 72, "A/D, LEFT/RIGHT: Steer", 7)
        pyxel.text(10, 82, "W / UP  : Brake (-25%)", 6)
        pyxel.text(10, 92, "S / DOWN: Dive  (+50%)", 9)
        pyxel.text(10, 102, "1, 2, 3 : Kairos Pact", 8)
        pyxel.text(10, 114, "Q : Quit Game", 5)

        # Start prompt
        blink = (pyxel.frame_count // 12) % 2 == 0
        if blink:
            pyxel.text(14, 142, "PRESS [SPACE] TO DESCEND", 7)

    def draw_game_over_screen(self):
        # Dark overlay
        pyxel.rect(8, 18, 104, 124, 0)
        pyxel.rectb(8, 18, 104, 124, 8)
        pyxel.rectb(10, 20, 100, 120, 2)

        pyxel.text(22, 26, "HOURGLASS SHATTERED", 8)

        reason = self.state.death_reason or "Consumed by the Void"
        pyxel.text(12, 38, reason[:22], 7)

        # Stats
        pyxel.text(14, 54, f"FINAL SCORE : {self.state.score}", 10)
        pyxel.text(14, 68, f"SAND REAPED : {self.state.total_sand_collected}", 6)
        pyxel.text(14, 82, f"SHARDS DODGED: {self.state.total_shards_dodged}", 6)
        pyxel.text(14, 96, f"PACTS SEALED : {len(self.bargains.history)}", 9)

        # Restart
        blink = (pyxel.frame_count // 10) % 2 == 0
        if blink:
            pyxel.text(18, 120, "PRESS [R] TO RESTART", 7)


def main():
    GrainOfDoubtApp(headless=False)


if __name__ == "__main__":
    main()
