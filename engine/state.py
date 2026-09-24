"""Dual-Clock Temporal Engine and Game State Manager for Grain of Doubt."""
from enum import Enum, auto


class GameState(Enum):
    TITLE = auto()
    CHRONOS = auto()
    KAIROS = auto()
    GAMEOVER = auto()
    LORE = auto()


class StateManager:
    # 30 FPS timing constants
    CHRONOS_FRAMES: int = 300  # 10.0 seconds
    KAIROS_FRAMES: int = 300   # 10.0 seconds
    INVULNERABLE_FRAMES: int = 20  # 0.66 second for tighter evasion
    SHAKE_FRAMES: int = 8
    SHAKE_INTENSITY: float = 12.0
    SLOTH_FREEZE_FRAMES: int = 240  # 8.0 seconds at 30 FPS

    def __init__(self, initial_hearts: int = 5):
        self.initial_hearts = initial_hearts
        self.reset()

    def reset(self):
        self.current_state: GameState = GameState.TITLE
        self.hearts: int = self.initial_hearts
        self.score: int = 0
        self.distance: float = 0.0
        self.total_frames: int = 0
        self.godmode: bool = False

        # Temporal clock counters
        self.chronos_timer: int = 0  # 0 to CHRONOS_FRAMES
        self.kairos_timer: int = 0   # 0 to KAIROS_FRAMES
        self.cycle_count: int = 0

        # Descent & multipliers (No dive / air brake - pure constant lateral runner)
        self.base_scroll_speed: float = 7.5
        self.scroll_speed: float = 7.5
        self.score_multiplier: float = 1.0
        self.speed_multiplier: float = 1.0

        # Entity tracking & Greed Borrowed Time state
        self.total_entities_spawned: int = 0
        self.total_sand_collected: int = 0
        self.total_shards_dodged: int = 0
        self.greed_active: bool = False
        self.greed_level: int = 0
        self.greed_timer: int = 0
        self.greed_duration: int = 0

        # Sin level tracker
        self.pride_level: int = 0
        self.envy_level: int = 0
        self.gluttony_level: int = 0

        # Wrath zero-yield timer
        self.wrath_wipe_timer: int = 0
        self.wrath_zero_yield_timer: int = 0

        # Sloth hazard freeze timer (8s recovery) & player speed modifier
        self.sloth_freeze_timer: int = 0
        self.sloth_player_speed_mod: float = 1.0

        # Envy & Lust modifiers
        self.envy_repel_radius: float = 0.0
        self.envy_mega_lust_timer: int = 0
        self.lust_attract_timer: int = 0
        self.lust_attract_radius: float = 0.0
        self.lust_hazard_attract_radius: float = 0.0

        # Spawn rate multiplier (Gluttony)
        self.spawn_rate_multiplier: float = 1.0

        # Invulnerability & Feedback
        self.invulnerable_timer: int = 0
        self.shake_timer: int = 0
        self.shake_intensity: float = 0.0
        self.player_score_flash_timer: int = 0

        # Visual Vignette (Envy): outer = zero vision beyond, inner = full clear vision
        self.base_vignette_radius: float = 1000.0
        self.vignette_radius: float = 1000.0       # outer circle (zero vision beyond)
        self.vignette_inner_radius: float = 900.0   # inner circle (full clear vision)
        self.min_vignette_radius: float = 60.0

        # Post-mortem death reason
        self.death_reason: str = ""

    @property
    def sloth_hazard_speed_mod(self) -> float:
        """Linearly recovers from 0.0 (frozen) back to 1.0 over 8.0s (240 frames)."""
        if self.sloth_freeze_timer > 0:
            recovery_ratio = 1.0 - (self.sloth_freeze_timer / float(self.SLOTH_FREEZE_FRAMES))
            return max(0.0, min(1.0, recovery_ratio))
        return 1.0

    @sloth_hazard_speed_mod.setter
    def sloth_hazard_speed_mod(self, val: float):
        if val <= 0.0:
            self.sloth_freeze_timer = self.SLOTH_FREEZE_FRAMES
        elif val >= 1.0:
            self.sloth_freeze_timer = 0
        else:
            self.sloth_freeze_timer = int((1.0 - val) * self.SLOTH_FREEZE_FRAMES)

    @property
    def envy_mega_lust_active(self) -> bool:
        return self.envy_mega_lust_timer > 0

    @property
    def envy_mega_lust_radius(self) -> float:
        if self.envy_mega_lust_timer > 0:
            return 2.0 * self.vignette_radius
        return 0.0

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
        if self.godmode or self.invulnerable_timer > 0 or self.current_state != GameState.CHRONOS:
            return False

        self.hearts -= 1
        self.invulnerable_timer = self.INVULNERABLE_FRAMES
        self.shake_timer = self.SHAKE_FRAMES
        self.shake_intensity = self.SHAKE_INTENSITY

        if self.hearts <= 0:
            self.trigger_game_over("Hourglass Shattered by Hazard")
        return True

    def trigger_shake(self, duration: int = 10, intensity: float = 12.0) -> None:
        """Trigger screen shake for given duration in frames and intensity in pixels."""
        self.shake_timer = duration
        self.shake_intensity = intensity

    def add_score(self, base_points: int = 1):
        if self.wrath_zero_yield_timer > 0:
            return
        self.total_sand_collected += base_points
        if self.greed_active:
            # During Greed Borrowed Time: sand multiplies current score by 110%
            # Gluttony fat sand (base_points=3) simulates collecting 3 small sands sequentially
            for _ in range(base_points):
                if self.score <= 0:
                    self.score = 1
                else:
                    self.score = max(self.score + 1, int(self.score * 1.10))
        else:
            points = int(base_points * self.score_multiplier)
            self.score += points

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

        # Player score interior flash timer
        if self.player_score_flash_timer > 0:
            self.player_score_flash_timer -= 1

        # Wrath active timers
        if self.wrath_wipe_timer > 0:
            self.wrath_wipe_timer -= 1
        if self.wrath_zero_yield_timer > 0:
            self.wrath_zero_yield_timer -= 1

        # Lust attraction is permanent for both sand and hazards (no timer decay)

        # Envy temporary Mega Lust timer (2.0s = 60 frames)
        if self.envy_mega_lust_timer > 0:
            self.envy_mega_lust_timer -= 1

        # Sloth hazard freeze timer
        if self.sloth_freeze_timer > 0:
            self.sloth_freeze_timer -= 1

        # Total lifetime frames
        self.total_frames += 1

        # State specific timers
        if self.current_state == GameState.CHRONOS:
            self.chronos_timer += 1
            self.distance += self.scroll_speed
            self.update_effective_scroll_speed()

            # Greed Borrowed Time timer countdown (Lethal Expiration: Debt Collected)
            if self.greed_active and self.greed_timer > 0:
                self.greed_timer -= 1
                if self.greed_timer <= 0:
                    self.greed_active = False
                    self.trigger_game_over("Borrowed Time Expired: Debt Collected")

            if self.chronos_timer >= self.CHRONOS_FRAMES:
                self.trigger_kairos()

        elif self.current_state == GameState.KAIROS:
            self.kairos_timer += 1
            if self.kairos_timer >= self.KAIROS_FRAMES:
                # 2.0s expired without sealing a bargain: Hourglass shatters!
                self.trigger_game_over("Paralyzed by Doubt: Kairos Expired")
