"""Dual-Clock Temporal Engine and Game State Manager for Grain of Doubt."""
from enum import Enum, auto


class GameState(Enum):
    TITLE = auto()
    CHRONOS = auto()
    KAIROS = auto()
    GAMEOVER = auto()


class StateManager:
    # 30 FPS timing constants
    CHRONOS_FRAMES: int = 240  # 8.0 seconds
    KAIROS_FRAMES: int = 60    # 2.0 seconds
    INVULNERABLE_FRAMES: int = 30  # 1.0 second
    SHAKE_FRAMES: int = 8
    SHAKE_INTENSITY: float = 12.0

    def __init__(self, initial_hearts: int = 5):
        self.initial_hearts = initial_hearts
        self.reset()

    def reset(self):
        self.current_state: GameState = GameState.TITLE
        self.hearts: int = self.initial_hearts
        self.score: int = 0
        self.distance: float = 0.0
        self.total_frames: int = 0

        # Temporal clock counters
        self.chronos_timer: int = 0  # 0 to CHRONOS_FRAMES
        self.kairos_timer: int = 0   # 0 to KAIROS_FRAMES
        self.cycle_count: int = 0

        # Descent & multipliers (No dive / air brake - pure constant lateral runner)
        self.base_scroll_speed: float = 7.5
        self.scroll_speed: float = 7.5
        self.score_multiplier: float = 1.0
        self.speed_multiplier: float = 1.0

        # Entity tracking & Greed kill-timer
        self.total_entities_spawned: int = 0
        self.total_sand_collected: int = 0
        self.total_shards_dodged: int = 0
        self.greed_timer_active: bool = False
        self.greed_kill_timer: int = -1  # frames remaining if active
        self.greed_initial_timer: int = -1

        # Wrath zero-yield timer
        self.wrath_wipe_timer: int = 0
        self.wrath_zero_yield_timer: int = 0

        # Sloth hazard & player speed modifiers
        self.sloth_hazard_speed_mod: float = 1.0
        self.sloth_player_speed_mod: float = 1.0

        # Envy & Lust modifiers
        self.envy_repel_radius: float = 0.0
        self.lust_attract_timer: int = 0
        self.lust_attract_radius: float = 0.0
        self.lust_hazard_attract_radius: float = 0.0

        # Spawn rate multiplier (Gluttony)
        self.spawn_rate_multiplier: float = 1.0

        # Invulnerability & Feedback
        self.invulnerable_timer: int = 0
        self.shake_timer: int = 0
        self.shake_intensity: float = 0.0

        # Visual Vignette (Initial 1000.0 = completely clear full screen vision)
        self.base_vignette_radius: float = 1000.0
        self.vignette_radius: float = 1000.0
        self.min_vignette_radius: float = 90.0

        # Post-mortem death reason
        self.death_reason: str = ""

    def start_game(self):
        self.reset()
        self.current_state = GameState.CHRONOS

    def trigger_kairos(self):
        self.current_state = GameState.KAIROS
        self.kairos_timer = 0
        self.scroll_speed = 0.0

    def resume_chronos(self):
        self.current_state = GameState.CHRONOS
        self.chronos_timer = 0
        self.kairos_timer = 0
        self.cycle_count += 1
        self.update_effective_scroll_speed()

    def update_effective_scroll_speed(self):
        if self.current_state != GameState.CHRONOS:
            self.scroll_speed = 0.0
            return
        base = self.base_scroll_speed * self.speed_multiplier
        self.scroll_speed = max(2.5, base)

    def trigger_game_over(self, reason: str = "Hourglass Shattered"):
        self.current_state = GameState.GAMEOVER
        self.scroll_speed = 0.0
        self.death_reason = reason

    def damage_player(self) -> bool:
        """Apply 1 heart damage. Returns True if damage was dealt."""
        if self.invulnerable_timer > 0 or self.current_state != GameState.CHRONOS:
            return False

        self.hearts -= 1
        self.invulnerable_timer = self.INVULNERABLE_FRAMES
        self.shake_timer = self.SHAKE_FRAMES
        self.shake_intensity = self.SHAKE_INTENSITY

        if self.hearts <= 0:
            self.trigger_game_over("Hourglass Shattered by Hazard")
        return True

    def add_score(self, base_points: int = 100):
        if self.wrath_zero_yield_timer > 0:
            return
        points = int(base_points * self.score_multiplier)
        self.score += points
        self.total_sand_collected += 1

    def update_timers(self):
        """Advance timers for the current frame."""
        # Shake timer decay
        if self.shake_timer > 0:
            self.shake_timer -= 1
            if self.shake_timer == 0:
                self.shake_intensity = 0.0

        # Invulnerability timer
        if self.invulnerable_timer > 0:
            self.invulnerable_timer -= 1

        # Wrath active timers
        if self.wrath_wipe_timer > 0:
            self.wrath_wipe_timer -= 1
        if self.wrath_zero_yield_timer > 0:
            self.wrath_zero_yield_timer -= 1

        # Lust attraction timer
        if self.lust_attract_timer > 0:
            self.lust_attract_timer -= 1
            if self.lust_attract_timer == 0:
                self.lust_attract_radius = 0.0

        # Greed deterministic sudden-death timer
        if self.greed_timer_active:
            if self.greed_kill_timer > 0:
                self.greed_kill_timer -= 1
                if self.greed_kill_timer <= 0:
                    self.trigger_game_over("Debt Collector: Greed Expired")
                    return

        # Total lifetime frames
        self.total_frames += 1

        # State specific timers
        if self.current_state == GameState.CHRONOS:
            self.chronos_timer += 1
            self.distance += self.scroll_speed
            self.update_effective_scroll_speed()
            if self.chronos_timer >= self.CHRONOS_FRAMES:
                self.trigger_kairos()

        elif self.current_state == GameState.KAIROS:
            self.kairos_timer += 1
            if self.kairos_timer >= self.KAIROS_FRAMES:
                # Default timeout: no boon, resume Chronos
                self.resume_chronos()
