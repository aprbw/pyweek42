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
        boon_name="Score Mult",
        curse_name="Descent Speed",
        boon_base=2.0,
        curse_base=2.0,
        boon_unit="x",
        curse_unit="x",
    ),
    SinType.GREED: BargainDefinition(
        sin=SinType.GREED,
        name="Greed",
        latin_name="Avaritia",
        boon_name="Harvest Bounty",
        curse_name="Kill-Timer Rate",
        boon_base=5.0,
        curse_base=1.5,
        boon_unit="pts/ent",
        curse_unit="x severity",
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
        boon_name="Hazard Drag",
        curse_name="Lateral Drag",
        boon_base=0.40,
        curse_base=0.25,
        boon_unit="drag",
        curse_unit="drag",
    ),
    SinType.ENVY: BargainDefinition(
        sin=SinType.ENVY,
        name="Envy",
        latin_name="Invidia",
        boon_name="Harvest Bypassed",
        curse_name="Sand Repel Field",
        boon_base=100.0,   # % of bypassed retrieved
        curse_base=140.0,  # radius in pixels (scaled for 600x800)
        boon_unit="%",
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
            # Score multiplier vs Speed multiplier
            state.score_multiplier += (boon_val * 0.5)
            state.speed_multiplier += (curse_val * 0.25)
            state.update_effective_scroll_speed()

        elif sin == SinType.GREED:
            # Accrued entities multiplier added to score
            accrued = state.total_sand_collected + state.total_shards_dodged
            harvest_score = int(accrued * boon_val * 10)
            state.score += harvest_score

            # Deterministic sudden death kill timer
            # Starts at 600 frames (20s), decreases by 1.5^k
            base_kill_frames = 600
            kill_frames = max(90, int(base_kill_frames / (1.50 ** k)))
            state.greed_timer_active = True
            if state.greed_kill_timer < 0 or kill_frames < state.greed_kill_timer:
                state.greed_kill_timer = kill_frames
                state.greed_initial_timer = kill_frames

            # Greed curse: Halve visual area (radius reduced to ~70.7%, e.g., 800 -> 566 ~ 600)
            state.vignette_radius = max(state.min_vignette_radius, state.vignette_radius * 0.7071)

        elif sin == SinType.WRATH:
            # Hazard wipe duration (boon) & zero yield duration (curse)
            frames_wipe = int(boon_val)
            frames_penalty = int(curse_val)
            state.wrath_wipe_timer = max(state.wrath_wipe_timer, frames_wipe)
            state.wrath_zero_yield_timer = max(state.wrath_zero_yield_timer, frames_penalty)
            if entities_manager:
                entities_manager.wipe_all_hazards()

        elif sin == SinType.SLOTH:
            # Hazard speed decrease vs Player lateral movement drag
            state.sloth_hazard_speed_mod = max(0.3, state.sloth_hazard_speed_mod - (boon_val * 0.3))
            state.sloth_player_speed_mod = max(0.35, state.sloth_player_speed_mod - (curse_val * 0.2))

        elif sin == SinType.ENVY:
            # Retroactively claim bypassed sand
            if entities_manager:
                reclaimed = entities_manager.reclaim_bypassed_sand()
                points = int(reclaimed * 100 * (boon_val / 100.0) * state.score_multiplier)
                state.score += points
            # Permanent sand repulsion field
            state.envy_repel_radius = max(state.envy_repel_radius, curse_val)

        elif sin == SinType.LUST:
            # Temporary sand magnet vs permanent hazard magnet
            state.lust_attract_timer = 300  # 10s
            state.lust_attract_radius = boon_val
            state.lust_hazard_attract_radius = max(state.lust_hazard_attract_radius, curse_val)

        # Shrink vignette as visual atmospheric consequence of borrowing time (gentle for non-Greed)
        if sin != SinType.GREED:
            state.vignette_radius = max(
                state.min_vignette_radius,
                state.vignette_radius - 12.0
            )

        self.selection_counts[sin] += 1
        self.history.append(sin)
        return summary
