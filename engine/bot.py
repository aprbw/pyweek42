"""GOFAI Playtesting Bot for Grain of Doubt.

Uses classical Good Old-Fashioned AI (GOFAI) kinematic trajectory simulation
and spacetime collision avoidance. Zero ML/RL/DL. Fully deterministic and explainable.
"""
from dataclasses import dataclass
import math
import random
from typing import List, Tuple, Optional

from engine.state import GameState, StateManager
from engine.entities import EntityManager, SandGrain, GlassShard, aabb_overlap
from engine.bargains import SinType


@dataclass
class BotConfig:
    """Configurable playtesting bot parameters and handicaps."""
    # Speed handicap: 80% maximum acceleration / speed
    speed_handicap: float = 0.80

    # Vision handicap: cannot see entities in bottom 20% of the screen (y > 640)
    bottom_blind_ratio: float = 0.20

    # Safety buffers for hazard avoidance
    hazard_safety_margin_x: float = 16.0
    hazard_safety_margin_y: float = 12.0

    # Lookahead planning horizon (in frames at 30 FPS, ~0.8s)
    horizon_frames: int = 24

    # Target sin policy: never greed
    forbidden_sins: Tuple[SinType, ...] = (SinType.GREED,)


class PlayTestingBot:
    """Automated playtesting agent using GOFAI trajectory search."""

    def __init__(self, config: Optional[BotConfig] = None, seed: Optional[int] = None):
        self.config = config or BotConfig()
        self.rng = random.Random(seed)
        self.target_card_index: Optional[int] = None
        self.frame_counter: int = 0

    def get_vision_threshold_y(self, screen_h: int = 800) -> float:
        """Returns maximum y coordinate visible to the bot."""
        return screen_h * (1.0 - self.config.bottom_blind_ratio)

    def filter_visible_shards(
        self,
        shards: List[GlassShard],
        screen_h: int = 800,
        player_x: Optional[float] = None,
        player_y: Optional[float] = None,
        vignette_radius: Optional[float] = None,
    ) -> List[GlassShard]:
        """Handicap: Shards in bottom 20% (y > threshold) are invisible.
        Envy Handicap: Shards outside circular vignette vision radius are completely invisible."""
        threshold = self.get_vision_threshold_y(screen_h)
        filtered = [s for s in shards if s.alive and s.y <= threshold]
        if vignette_radius is not None and vignette_radius < 950.0 and player_x is not None and player_y is not None:
            filtered = [s for s in filtered if math.hypot(s.x - player_x, s.y - player_y) <= vignette_radius]
        return filtered

    def filter_visible_sands(
        self,
        sands: List[SandGrain],
        screen_h: int = 800,
        player_x: Optional[float] = None,
        player_y: Optional[float] = None,
        vignette_radius: Optional[float] = None,
    ) -> List[SandGrain]:
        """Handicap: Sands in bottom 20% (y > threshold) are invisible.
        Envy Handicap: Sands outside circular vignette vision radius are completely invisible."""
        threshold = self.get_vision_threshold_y(screen_h)
        filtered = [s for s in sands if s.alive and s.y <= threshold]
        if vignette_radius is not None and vignette_radius < 950.0 and player_x is not None and player_y is not None:
            filtered = [s for s in filtered if math.hypot(s.x - player_x, s.y - player_y) <= vignette_radius]
        return filtered

    def evaluate_trajectory(
        self,
        actions: List[int],
        start_x: float,
        start_vx: float,
        player_y: float,
        visible_shards: List[GlassShard],
        visible_sands: List[SandGrain],
        scroll_speed: float,
        hazard_speed_mod: float,
        player_speed_mod: float,
        screen_w: int = 600,
    ) -> float:
        """Simulate kinematic trajectory forward and return fitness score.

        Actions is a list of lateral inputs (-1=LEFT, 0=NONE, +1=RIGHT) per frame.
        """
        score = 0.0
        cur_x = start_x
        cur_vx = start_vx

        base_accel = 6.0
        friction = 0.82
        effective_accel = base_accel * player_speed_mod * self.config.speed_handicap

        player_w = 60.0
        player_h = 40.0

        for t, act in enumerate(actions, start=1):
            # Kinematic step (infinite horizontal arena)
            ax = act * effective_accel
            cur_vx = (cur_vx + ax) * friction
            cur_x = cur_x + cur_vx

            # Check collision with visible shards at time t (incorporating individual speed variance)
            for shard in visible_shards:
                shard_spd_var = getattr(shard, "speed_variance", 1.0)
                eff_hazard_spd = scroll_speed * hazard_speed_mod * shard_spd_var
                sy_future = shard.y - eff_hazard_spd * t
                sx_future = shard.x + shard.lateral_drift * t

                # Check danger box with safety margins
                dx = abs(cur_x - sx_future)
                dy = abs(player_y - sy_future)

                col_w = (player_w + shard.HITBOX_W) / 2.0
                col_h = (player_h + shard.HITBOX_H) / 2.0

                safe_w = col_w + self.config.hazard_safety_margin_x
                safe_h = col_h + self.config.hazard_safety_margin_y

                if dx < col_w and dy < col_h:
                    # Lethal collision! Catastrophic penalty
                    score -= 500000.0
                elif dx < safe_w and dy < safe_h:
                    # Near-miss danger zone
                    proximity_factor = (1.0 - dx / safe_w) * (1.0 - dy / safe_h)
                    score -= proximity_factor * 15000.0

            # Check sand collection reward (incorporating individual speed variance)
            for sand in visible_sands:
                sand_spd_var = getattr(sand, "speed_variance", 1.0)
                sy_future = sand.y - (scroll_speed * sand_spd_var) * t
                sx_future = sand.x
                dx = abs(cur_x - sx_future)
                dy = abs(player_y - sy_future)

                sand_col_w = (player_w + sand.HITBOX_W) / 2.0
                sand_col_h = (player_h + sand.HITBOX_H) / 2.0

                if dx < sand_col_w and dy < sand_col_h:
                    # Sand collected!
                    score += 2500.0
                elif dy < sand_col_h * 2.0 and dx < 120.0:
                    # Close to reachable sand
                    score += (120.0 - dx) * 5.0

        return score

    def decide_chronos_input(self, state: StateManager, entities: EntityManager) -> Tuple[bool, bool]:
        """Determine (left, right) keypresses for current Chronos frame."""
        self.frame_counter += 1
        player = entities.player

        # Filter entities by vision handicap (bottom 20% invisible) and Envy vignette radius
        visible_shards = self.filter_visible_shards(
            entities.shards,
            entities.screen_h,
            player_x=player.x,
            player_y=player.y,
            vignette_radius=state.vignette_radius,
        )
        visible_sands = self.filter_visible_sands(
            entities.sands,
            entities.screen_h,
            player_x=player.x,
            player_y=player.y,
            vignette_radius=state.vignette_radius,
        )

        # GOFAI Trajectory Search
        # Evaluate 9 distinct 2-stage macro-actions over horizon (24 frames)
        # Stage 1: 8 frames, Stage 2: 16 frames
        horizon = self.config.horizon_frames
        stage1_len = 8
        stage2_len = horizon - stage1_len

        candidate_macro_actions = [
            (-1, -1),  # Full left
            (-1, 0),   # Left then coast
            (-1, 1),   # Left then right (evasion wiggle)
            (0, 0),    # Coast
            (0, -1),   # Coast then left
            (0, 1),    # Coast then right
            (1, 1),    # Full right
            (1, 0),    # Right then coast
            (1, -1),   # Right then left (evasion wiggle)
        ]

        best_score = -float("inf")
        best_first_act = 0

        for a1, a2 in candidate_macro_actions:
            actions = [a1] * stage1_len + [a2] * stage2_len
            score = self.evaluate_trajectory(
                actions=actions,
                start_x=player.x,
                start_vx=player.vx,
                player_y=player.y,
                visible_shards=visible_shards,
                visible_sands=visible_sands,
                scroll_speed=state.scroll_speed,
                hazard_speed_mod=state.sloth_hazard_speed_mod,
                player_speed_mod=state.sloth_player_speed_mod,
                screen_w=entities.screen_w,
            )

            if score > best_score:
                best_score = score
                best_first_act = a1

        # Convert best immediate action to (left, right)
        if best_first_act == -1:
            return (True, False)
        elif best_first_act == 1:
            return (False, True)
        else:
            return (False, False)

    def decide_kairos_choice(
        self,
        active_options: List[Tuple[SinType, any, int]],
        current_index: int,
        frames_remaining: Optional[int] = None,
    ) -> Tuple[bool, bool, bool]:
        """Determine (move_left, move_right, confirm) during Kairos time-freeze.

        Enforces bargain strategy:
        - Random choice BUT NEVER Greed.
        - Navigates immediately to target card, but WAITS until the very last moment
          (<= 6 frames remaining, ~0.2s before the 2.0s deadline) before confirming.
        """
        if not active_options:
            return (False, False, True)

        # If no target chosen yet for this Kairos round, pick one randomly (never Greed)
        if self.target_card_index is None or not (0 <= self.target_card_index < len(active_options)):
            valid_indices = [
                i for i, opt in enumerate(active_options)
                if opt[0] not in self.config.forbidden_sins
            ]
            if valid_indices:
                self.target_card_index = self.rng.choice(valid_indices)
            else:
                self.target_card_index = 0

        # Navigate cursor to target card index
        if current_index < self.target_card_index:
            return (False, True, False)  # move right
        elif current_index > self.target_card_index:
            return (True, False, False)  # move left
        else:
            # Reached target card: wait until the very last moment to seal pact
            if frames_remaining is not None and frames_remaining > 6:
                return (False, False, False)  # Hover over chosen card, hold off confirming
            return (False, False, True)  # Final moment reached: confirm choice

    def reset_kairos(self):
        """Clear Kairos target selection when resuming Chronos."""
        self.target_card_index = None

    def reset(self):
        """Reset bot internal state."""
        self.target_card_index = None
        self.frame_counter = 0
