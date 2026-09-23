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
    SinType.PRIDE: BargainDefinition(
        sin=SinType.PRIDE,
        name="Pride",
        latin_name="Superbia",
        boon_name="Sand Clusters",
        curse_name="Descent Speed",
        boon_base=1.0,
        curse_base=25.0,
        boon_unit="grain",
        curse_unit="%",
    ),
    SinType.GREED: BargainDefinition(
        sin=SinType.GREED,
        name="Greed",
        latin_name="Avaritia",
        boon_name="Bounty Multiplier (x110%)",
        curse_name="Borrowed Time (Lethal)",
        boon_base=110.0,
        curse_base=14.0,  # 10.0 to 18.0 seconds window
        boon_unit="%",
        curse_unit="s",
    ),
    SinType.LUST: BargainDefinition(
        sin=SinType.LUST,
        name="Lust",
        latin_name="Luxuria",
        boon_name="Sand Magnet Field",
        curse_name="Hazard Magnet Field",
        boon_base=180.0,  # radius in pixels
        curse_base=180.0,  # radius in pixels
        boon_unit="px radius",
        curse_unit="px radius",
    ),
    SinType.ENVY: BargainDefinition(
        sin=SinType.ENVY,
        name="Envy",
        latin_name="Invidia",
        boon_name="Mega Lust (2s)",
        curse_name="Vignette Vision",
        boon_base=1920.0,
        curse_base=960.0,
        boon_unit="px pull radius",
        curse_unit="px radius",
    ),
    SinType.GLUTTONY: BargainDefinition(
        sin=SinType.GLUTTONY,
        name="Gluttony",
        latin_name="Gula",
        boon_name="+Sand Spawn Rate",
        curse_name="+Hazard Spawn Rate",
        boon_base=50.0,
        curse_base=50.0,
        boon_unit="%",
        curse_unit="%",
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
        curse_base=0.20,
        boon_unit="s freeze",
        curse_unit="drag",
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
        """Apply chosen Faustian bargain."""
        defn = BARGAIN_REGISTRY[sin]
        k = self.selection_counts[sin]

        if sin == SinType.PRIDE:
            # Boon: +1 sand grain per level (pairs, triplets...)
            state.pride_level += 1
            # Curse: +25% descent speed flat
            state.speed_multiplier += 0.25
            state.update_effective_scroll_speed()
            summary = {
                "sin": defn.name,
                "boon": f"Sand Clusters: {state.pride_level + 1} grains/wave",
                "curse": f"Descent Speed: +25% (x{state.speed_multiplier:.2f})",
            }

        elif sin == SinType.GREED:
            # Greed Borrowed Time:
            # - Randomized window of 10.0 to 18.0 seconds (300 to 540 frames)
            # - Boon: Each sand multiplies current score by 110%
            # - Curse: At the end, you definitely die (Debt Collected)
            duration_sec = random.uniform(10.0, 18.0)
            duration_frames = int(duration_sec * 30.0)
            state.greed_active = True
            state.greed_level += 1
            state.greed_timer = duration_frames
            state.greed_duration = duration_frames
            summary = {
                "sin": defn.name,
                "boon": "Bounty Multiplier: x110% per sand",
                "curse": f"Borrowed Time: {duration_sec:.1f}s (Debt Collected on Expiry)",
            }

        elif sin == SinType.LUST:
            # Permanently attracts both sand and hazards; subsequent pacts increase radius
            radius = 180.0 + k * 60.0
            state.lust_attract_radius = radius
            state.lust_hazard_attract_radius = radius
            summary = {
                "sin": defn.name,
                "boon": f"Sand Magnet: {radius:.0f}px (Permanent)",
                "curse": f"Hazard Magnet: {radius:.0f}px (Permanent)",
            }

        elif sin == SinType.ENVY:
            # Curse: Vignette Vision (dual-radius)
            state.envy_level += 1
            k = state.envy_level
            outer_r = round(1200.0 * (0.80 ** k), 4)
            inner_r = round(1000.0 * (0.80 ** (k + 1)), 4)
            state.vignette_radius = max(state.min_vignette_radius, outer_r)
            state.vignette_inner_radius = max(state.min_vignette_radius * 0.6, inner_r)

            # Boon: Temporary Mega Lust for 2.0s (60 frames) attracting all grains within 2x vignette radius
            state.envy_mega_lust_timer = 60
            mega_r = 2.0 * state.vignette_radius
            summary = {
                "sin": defn.name,
                "boon": f"Mega Lust: 2.0s pull ({mega_r:.0f}px radius)",
                "curse": f"Vignette: outer={state.vignette_radius:.0f}px inner={state.vignette_inner_radius:.0f}px",
            }

        elif sin == SinType.GLUTTONY:
            # Symmetric language & numbers: +50% sand spawn rate, +50% hazard spawn rate
            state.gluttony_level = getattr(state, "gluttony_level", 0) + 1
            state.spawn_rate_multiplier += 0.50
            summary = {
                "sin": defn.name,
                "boon": f"+Sand Spawn Rate: +50% (x{state.spawn_rate_multiplier:.2f})",
                "curse": f"+Hazard Spawn Rate: +50% (x{state.spawn_rate_multiplier:.2f})",
            }

        elif sin == SinType.WRATH:
            # Non-compounding: flat 10.0s wipe, flat 10.0s zero-yield
            state.wrath_wipe_timer = 300
            state.wrath_zero_yield_timer = 300
            if entities_manager:
                entities_manager.wipe_all_hazards()
            summary = {
                "sin": defn.name,
                "boon": "Hazard Purge: 10.0s (Screen Cleared)",
                "curse": "Zero Yield: 10.0s (0 pts/sand)",
            }

        elif sin == SinType.SLOTH:
            # Boon: Freeze hazards immediately, linear recovery over 8.0s (240 frames)
            state.sloth_freeze_timer = state.SLOTH_FREEZE_FRAMES
            # Curse: Aggressive lateral drag: 0.20 * 1.5^k reduction, min 0.20
            drag_reduction = 0.20 * (1.5 ** k)
            state.sloth_player_speed_mod = max(0.20, state.sloth_player_speed_mod - drag_reduction)
            summary = {
                "sin": defn.name,
                "boon": "Freeze Hazards: 8.0s linear recovery",
                "curse": f"Lateral Drag: -{drag_reduction * 100:.1f}% steering (mod={state.sloth_player_speed_mod:.2f})",
            }

        self.selection_counts[sin] += 1
        self.history.append(sin)
        return summary

    def reduce_bargain(self, sin: SinType, state, entities_manager=None) -> Dict[str, str]:
        """Reduce chosen Faustian bargain level (Q-U in Dev Mode)."""
        current_k = self.selection_counts[sin]
        if current_k <= 0:
            return {
                "sin": BARGAIN_REGISTRY[sin].name,
                "boon": "Already at 0",
                "curse": "Already at 0",
            }

        self.selection_counts[sin] -= 1
        new_k = self.selection_counts[sin]
        defn = BARGAIN_REGISTRY[sin]

        if sin == SinType.PRIDE:
            state.pride_level = max(0, state.pride_level - 1)
            state.speed_multiplier = max(1.0, state.speed_multiplier - 0.25)
            state.update_effective_scroll_speed()
            summary = {
                "sin": defn.name,
                "boon": f"Pride Level: {state.pride_level} ({state.pride_level + 1} grains)",
                "curse": f"Descent Speed: x{state.speed_multiplier:.2f}",
            }

        elif sin == SinType.GREED:
            state.greed_level = max(0, state.greed_level - 1)
            if new_k == 0:
                state.greed_active = False
                state.greed_timer = 0
                state.greed_duration = 0
            summary = {
                "sin": defn.name,
                "boon": f"Greed Level: {state.greed_level}",
                "curse": "Borrowed Time Cleared" if new_k == 0 else f"Timer: {state.greed_timer / 30.0:.1f}s",
            }

        elif sin == SinType.LUST:
            if new_k == 0:
                state.lust_attract_radius = 0.0
                state.lust_hazard_attract_radius = 0.0
            else:
                radius = 180.0 + (new_k - 1) * 60.0
                state.lust_attract_radius = radius
                state.lust_hazard_attract_radius = radius
            summary = {
                "sin": defn.name,
                "boon": f"Sand Magnet: {state.lust_attract_radius:.0f}px",
                "curse": f"Hazard Magnet: {state.lust_hazard_attract_radius:.0f}px",
            }

        elif sin == SinType.ENVY:
            state.envy_level = max(0, state.envy_level - 1)
            if state.envy_level == 0:
                state.vignette_radius = state.base_vignette_radius
                state.vignette_inner_radius = 900.0
                state.envy_mega_lust_timer = 0
            else:
                k = state.envy_level
                outer_r = round(1200.0 * (0.80 ** k), 4)
                inner_r = round(1000.0 * (0.80 ** (k + 1)), 4)
                state.vignette_radius = max(state.min_vignette_radius, outer_r)
                state.vignette_inner_radius = max(state.min_vignette_radius * 0.6, inner_r)
            summary = {
                "sin": defn.name,
                "boon": f"Envy Level: {state.envy_level}",
                "curse": f"Vignette: outer={state.vignette_radius:.0f}px inner={state.vignette_inner_radius:.0f}px",
            }

        elif sin == SinType.GLUTTONY:
            state.gluttony_level = max(0, getattr(state, "gluttony_level", 1) - 1)
            state.spawn_rate_multiplier = max(1.0, state.spawn_rate_multiplier - 0.50)
            summary = {
                "sin": defn.name,
                "boon": f"Gluttony Level: {state.gluttony_level}",
                "curse": f"Spawn Rate: x{state.spawn_rate_multiplier:.2f}",
            }

        elif sin == SinType.WRATH:
            state.wrath_wipe_timer = 0
            state.wrath_zero_yield_timer = 0
            summary = {
                "sin": defn.name,
                "boon": "Wrath Reset",
                "curse": "Zero Yield Ended",
            }

        elif sin == SinType.SLOTH:
            speed_mod = 1.0
            for i in range(new_k):
                speed_mod -= 0.20 * (1.5 ** i)
            state.sloth_player_speed_mod = max(0.20, speed_mod)
            if new_k == 0:
                state.sloth_freeze_timer = 0
            summary = {
                "sin": defn.name,
                "boon": f"Sloth Level: {new_k}",
                "curse": f"Steering Speed Mod: {state.sloth_player_speed_mod:.2f}",
            }

        return summary
