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


# Unique signature color for each Faustian Pact / Bargain Card
SIN_CARD_COLORS: Dict[SinType, int] = {
    SinType.PRIDE: 2,       # Imperial Purple
    SinType.GREED: 9,       # Amber Gold
    SinType.LUST: 14,       # Hot Passion Pink
    SinType.ENVY: 3,        # Dark Emerald Green
    SinType.GLUTTONY: 4,    # Clay / Earthy Brown
    SinType.WRATH: 8,       # Crimson Blood Red
    SinType.SLOTH: 1,       # Midnight Navy Blue
}


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
        boon_base=100.0,  # radius in pixels
        curse_base=100.0,  # radius in pixels
        boon_unit="px radius",
        curse_unit="px radius",
    ),
    SinType.ENVY: BargainDefinition(
        sin=SinType.ENVY,
        name="Envy",
        latin_name="Invidia",
        boon_name="Tidal Pull (2s)",
        curse_name="Vignette Vision",
        boon_base=1228.0,
        curse_base=614.4,
        boon_unit="px pull radius",
        curse_unit="px radius",
    ),
    SinType.GLUTTONY: BargainDefinition(
        sin=SinType.GLUTTONY,
        name="Gluttony",
        latin_name="Gula",
        boon_name="Fat Sand Grains (3x pts)",
        curse_name="Fat Glass Shards (10x area)",
        boon_base=10.0,
        curse_base=10.0,
        boon_unit="% fat grains",
        curse_unit="% fat shards",
    ),
    SinType.WRATH: BargainDefinition(
        sin=SinType.WRATH,
        name="Wrath",
        latin_name="Ira",
        boon_name="Wrath Blast (1200px)",
        curse_name="Zero Yield Period",
        boon_base=1200.0,  # radius in pixels
        curse_base=300.0,  # 10.0 seconds (frames)
        boon_unit="px blast radius",
        curse_unit="frames",
    ),
    SinType.SLOTH: BargainDefinition(
        sin=SinType.SLOTH,
        name="Sloth",
        latin_name="Acedia",
        boon_name="Lazy Reprieve",
        curse_name="Lateral Drag",
        boon_base=2.0,
        curse_base=0.20,
        boon_unit="s safe",
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
            # Permanently attracts both sand and hazards; starts at 100px, adds +50px per pact
            radius = 100.0 + k * 50.0
            state.lust_attract_radius = radius
            state.lust_hazard_attract_radius = radius
            summary = {
                "sin": defn.name,
                "boon": f"Sand Magnet: {radius:.0f}px (Permanent)",
                "curse": f"Hazard Magnet: {radius:.0f}px (Permanent)",
            }

        elif sin == SinType.ENVY:
            # Curse: Vignette Vision (dual-radius), starting at former Envy 3 (k_eff = k + 2)
            state.envy_level += 1
            k = state.envy_level
            k_eff = k + 2
            outer_r = round(1200.0 * (0.80 ** k_eff), 4)
            inner_r = round(1000.0 * (0.80 ** (k_eff + 1)), 4)
            state.vignette_radius = max(state.min_vignette_radius, outer_r)
            state.vignette_inner_radius = max(state.min_vignette_radius * 0.6, inner_r)

            # Boon: Temporary Tidal Pull for 2.0s (60 frames) attracting all grains within 2x vignette radius
            state.envy_mega_lust_timer = 60
            mega_r = 2.0 * state.vignette_radius
            summary = {
                "sin": defn.name,
                "boon": f"Tidal Pull: 2.0s pull ({mega_r:.0f}px radius)",
                "curse": f"Vignette: outer={state.vignette_radius:.0f}px inner={state.vignette_inner_radius:.0f}px",
            }

        elif sin == SinType.GLUTTONY:
            state.gluttony_level = getattr(state, "gluttony_level", 0) + 1
            k = state.gluttony_level
            fat_pct = (1.0 - (0.90 ** k)) * 100.0
            summary = {
                "sin": defn.name,
                "boon": f"Fat Grains: {fat_pct:.1f}% fat (3x pts, 10x area)",
                "curse": f"Fat Hazards: {fat_pct:.1f}% fat shards (10x area)",
            }

        elif sin == SinType.WRATH:
            # Wrath is an explosion! Everything (both sand and glass shards) within 1200px
            # is given an instant HUGE acceleration away from the player
            shards_hit = 0
            sands_hit = 0
            if entities_manager:
                shards_hit, sands_hit = entities_manager.wrath_explosion(explosion_radius=1200.0, impulse_strength=46.0)
            state.trigger_shake(duration=20, intensity=12.0)
            state.wrath_zero_yield_timer = 300
            summary = {
                "sin": defn.name,
                "boon": f"Wrath Blast: {shards_hit} shards & {sands_hit} sands detonated (1200px)",
                "curse": "Zero Yield: 10.0s (0 pts/sand)",
            }

        elif sin == SinType.SLOTH:
            # Boon: Sloth means lazy; lazy means doing nothing!
            # Single high acceleration frame throws all shards below player (within 3 screens wide) down to bottom
            thrown_count = 0
            if entities_manager:
                thrown_count = entities_manager.sloth_hurl_shards_downward()
            # Curse: Aggressive lateral drag: 0.20 * 1.5^k reduction, min 0.20
            drag_reduction = 0.20 * (1.5 ** k)
            state.sloth_player_speed_mod = max(0.20, state.sloth_player_speed_mod - drag_reduction)
            summary = {
                "sin": defn.name,
                "boon": f"Lazy Reprieve: {thrown_count} hazards hurled to bottom (~2s safe)",
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
                radius = 100.0 + (new_k - 1) * 50.0
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
                state.vignette_inner_radius = 1000.0
                state.envy_mega_lust_timer = 0
            else:
                k = state.envy_level
                k_eff = k + 2
                outer_r = round(1200.0 * (0.80 ** k_eff), 4)
                inner_r = round(1000.0 * (0.80 ** (k_eff + 1)), 4)
                state.vignette_radius = max(state.min_vignette_radius, outer_r)
                state.vignette_inner_radius = max(state.min_vignette_radius * 0.6, inner_r)
            summary = {
                "sin": defn.name,
                "boon": f"Envy Level: {state.envy_level}",
                "curse": f"Vignette: outer={state.vignette_radius:.0f}px inner={state.vignette_inner_radius:.0f}px",
            }

        elif sin == SinType.GLUTTONY:
            state.gluttony_level = max(0, getattr(state, "gluttony_level", 1) - 1)
            fat_pct = (1.0 - (0.90 ** state.gluttony_level)) * 100.0
            summary = {
                "sin": defn.name,
                "boon": f"Fat Grains: {fat_pct:.1f}% fat (3x pts)",
                "curse": f"Fat Hazards: {fat_pct:.1f}% fat shards (10x area)",
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

    def get_fat_chance(self, sin: SinType = SinType.GLUTTONY) -> float:
        """Calculates fat grain and shard probability: 1 - 0.9^k."""
        k = self.selection_counts.get(sin, 0)
        if k <= 0:
            return 0.0
        return 1.0 - (0.90 ** k)

    def get_envy_radii(self) -> Tuple[float, float]:
        """Calculates dual-radius vision bounds for Envy (outer, inner).
        Envy 1 starts at previous Envy 3 (k_eff = k + 2).
        """
        k = self.selection_counts.get(SinType.ENVY, 0)
        if k <= 0:
            return 1000.0, 900.0
        k_eff = k + 2
        outer_r = round(1200.0 * (0.80 ** k_eff), 4)
        inner_r = round(1000.0 * (0.80 ** (k_eff + 1)), 4)
        return outer_r, inner_r
