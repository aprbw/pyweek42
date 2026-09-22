"""Faustian Bargain Registry and Compounding Decay Curves."""
from dataclasses import dataclass
from enum import Enum, auto
import random
from typing import List, Tuple, Dict


class SinType(Enum):
    GLUTTONY = auto()
    PRIDE = auto()
    GREED = auto()
    WRATH = auto()
    SLOTH = auto()
    ENVY = auto()
    LUST = auto()


@dataclass
class BargainDefinition:
    sin: SinType
    name: str
    latin_name: str
    boon_name: str
    curse_name: str
    boon_base: float
    curse_base: float
    boon_unit: str
    curse_unit: str

    def get_boon_value(self, k: int) -> float:
        """Boon_i(k) = Boon_0 * (0.75)^k. Strictly monotonically decreasing."""
        return self.boon_base * (0.75 ** k)

    def get_curse_value(self, k: int) -> float:
        """Curse_i(k) = Curse_0 * (1.50)^k. Strictly monotonically increasing."""
        return self.curse_base * (1.50 ** k)


# Sin names are just the Sin, without "Sands of"
BARGAIN_REGISTRY: Dict[SinType, BargainDefinition] = {
    SinType.GLUTTONY: BargainDefinition(
        sin=SinType.GLUTTONY,
        name="Gluttony",
        latin_name="Gula",
        boon_name="+Sand Yield",
        curse_name="+Hazard Rate",
        boon_base=2.0,
        curse_base=2.0,
        boon_unit="x",
        curse_unit="x",
    ),
    SinType.PRIDE: BargainDefinition(
        sin=SinType.PRIDE,
        name="Pride",
        latin_name="Superbia",
        boon_name="Sand Clusters",
        curse_name="Descent Speed",
        boon_base=2.0,
        curse_base=2.0,
        boon_unit="cluster",
        curse_unit="x",
    ),
    SinType.GREED: BargainDefinition(
        sin=SinType.GREED,
        name="Greed",
        latin_name="Avaritia",
        boon_name="Bounty Harvest",
        curse_name="Borrowed Time",
        boon_base=5.0,
        curse_base=1.5,
        boon_unit="pts/ent",
        curse_unit="x tension",
    ),
    SinType.WRATH: BargainDefinition(
        sin=SinType.WRATH,
        name="Wrath",
        latin_name="Ira",
        boon_name="Hazard Purge",
        curse_name="Zero Yield Period",
        boon_base=300.0,  # 10.0 seconds (frames)
        curse_base=300.0,  # 10.0 seconds (frames)
        boon_unit="frames",
        curse_unit="frames",
    ),
    SinType.SLOTH: BargainDefinition(
        sin=SinType.SLOTH,
        name="Sloth",
        latin_name="Acedia",
        boon_name="Freeze Hazards",
        curse_name="Lateral Drag",
        boon_base=8.0,
        curse_base=0.25,
        boon_unit="s freeze",
        curse_unit="drag",
    ),
    SinType.ENVY: BargainDefinition(
        sin=SinType.ENVY,
        name="Envy",
        latin_name="Invidia",
        boon_name="Reap Screen Sands",
        curse_name="Vignette Vision",
        boon_base=1.0,
        curse_base=260.0,
        boon_unit="screen",
        curse_unit="px radius",
    ),
    SinType.LUST: BargainDefinition(
        sin=SinType.LUST,
        name="Lust",
        latin_name="Luxuria",
        boon_name="Sand Magnet Field",
        curse_name="Hazard Magnet Field",
        boon_base=220.0,  # radius in pixels (scaled for 600x800)
        curse_base=180.0,  # radius in pixels (scaled for 600x800)
        boon_unit="px radius",
        curse_unit="px radius",
    ),
}


class BargainManager:
    def __init__(self):
        self.selection_counts: Dict[SinType, int] = {sin: 0 for sin in SinType}
        self.history: List[SinType] = []

    def reset(self):
        self.selection_counts = {sin: 0 for sin in SinType}
        self.history.clear()

    def get_selection_count(self, sin: SinType) -> int:
        return self.selection_counts[sin]

    def draw_options(self, count: int = 3) -> List[Tuple[SinType, BargainDefinition, int]]:
        """Draw 3 distinct sins for Kairos circuit breaker."""
        sins = list(SinType)
        chosen = random.sample(sins, min(count, len(sins)))
        options = []
        for sin in chosen:
            defn = BARGAIN_REGISTRY[sin]
            k = self.selection_counts[sin]
            options.append((sin, defn, k))
        return options

    def apply_bargain(self, sin: SinType, state, entities_manager=None) -> Dict[str, str]:
        """Apply chosen Faustian bargain with compounding decay/increase."""
        defn = BARGAIN_REGISTRY[sin]
        k = self.selection_counts[sin]
        boon_val = defn.get_boon_value(k)
        curse_val = defn.get_curse_value(k)

        summary = {
            "sin": defn.name,
            "boon": f"{defn.boon_name}: +{boon_val:.1f}",
            "curse": f"{defn.curse_name}: +{curse_val:.1f}",
        }

        if sin == SinType.GLUTTONY:
            # Scale spawn rate
            state.spawn_rate_multiplier += (boon_val * 0.4)

        elif sin == SinType.PRIDE:
            # Sand Cluster increment (pair, triplet...) vs Speed multiplier
            state.pride_level += 1
            state.speed_multiplier += (curse_val * 0.25)
            state.update_effective_scroll_speed()

        elif sin == SinType.GREED:
            # Accrued entities multiplier added to score (1 sand = 1 pt)
            accrued = state.total_sand_collected + state.total_shards_dodged
            harvest_score = int(accrued * boon_val)
            state.score += harvest_score

            # Greed Borrowed Time:
            # - Random duration between 10.0 and 18.0 seconds (300 to 540 frames)
            # - During Borrowed Time: blood crimson sky, speed + spawn escalation,
            #   and collecting sand multiplies score by 110% instead of +1
            duration_sec = random.uniform(10.0, 18.0)
            duration_frames = int(duration_sec * 30.0)
            state.greed_active = True
            state.greed_level += 1
            state.greed_timer = duration_frames
            state.greed_duration = duration_frames
            state.speed_multiplier += 0.20 * curse_val
            state.spawn_rate_multiplier += 0.25 * curse_val
            state.update_effective_scroll_speed()

        elif sin == SinType.WRATH:
            # Hazard wipe duration (boon) & zero yield duration (curse)
            frames_wipe = int(boon_val)
            frames_penalty = int(curse_val)
            state.wrath_wipe_timer = max(state.wrath_wipe_timer, frames_wipe)
            state.wrath_zero_yield_timer = max(state.wrath_zero_yield_timer, frames_penalty)
            if entities_manager:
                entities_manager.wipe_all_hazards()

        elif sin == SinType.SLOTH:
            # Boon: Freeze hazards immediately, recovers linearly over 8.0s (240 frames)
            state.sloth_freeze_timer = state.SLOTH_FREEZE_FRAMES
            # Curse: Permanent lateral drag penalty
            state.sloth_player_speed_mod = max(0.35, state.sloth_player_speed_mod - (curse_val * 0.2))

        elif sin == SinType.ENVY:
            # Boon: Reap all sands currently visible on the screen
            collected = 0
            if entities_manager:
                cam_x = entities_manager.player.x - entities_manager.screen_w / 2.0
                collected = entities_manager.collect_all_screen_sands(cam_x)
                for _ in range(collected):
                    state.add_score(1)

            # Curse: Imposes the Vignette Vision tunnel vision mask
            state.envy_level += 1
            state.vignette_radius = max(
                state.min_vignette_radius,
                260.0 * (0.80 ** (state.envy_level - 1))
            )

        elif sin == SinType.LUST:
            # Temporary sand magnet vs permanent hazard magnet
            state.lust_attract_timer = 300  # 10s
            state.lust_attract_radius = boon_val
            state.lust_hazard_attract_radius = max(state.lust_hazard_attract_radius, curse_val)

        self.selection_counts[sin] += 1
        self.history.append(sin)
        return summary
