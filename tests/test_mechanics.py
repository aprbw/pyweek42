"""Automated Unit Validation Suite for Grain of Doubt.
Verifies all 5 gates defined in p02.md section 07.
"""
import math
import pytest
from engine.state import GameState, StateManager
from engine.entities import HourglassPlayer, SandGrain, GlassShard, EntityManager, aabb_overlap
from engine.bargains import BargainManager, SinType, BARGAIN_REGISTRY
from engine.audio import AudioManager
from main import render_vignette


# ---------------------------------------------------------------------------
# Gate 1: Chronos Descent & Hazard Gate
# ---------------------------------------------------------------------------
def test_chronos_descent_and_hazard_gate():
    state = StateManager(initial_hearts=3)
    state.start_game()
    assert state.current_state == GameState.CHRONOS

    # 1. Assert continuous downward descent (scroll_speed > 0)
    assert state.scroll_speed > 0.0

    # Test Dive increases speed by 50%
    base_spd = state.scroll_speed
    state.dive_active = True
    state.update_effective_scroll_speed()
    assert state.scroll_speed == pytest.approx(base_spd * 1.50)

    # Test Brake decreases speed by 25%
    state.dive_active = False
    state.brake_active = True
    state.update_effective_scroll_speed()
    assert state.scroll_speed == pytest.approx(base_spd * 0.75)
    state.brake_active = False
    state.update_effective_scroll_speed()

    # 2. Assert lateral steering bounds
    player = HourglassPlayer(screen_w=160, screen_h=120)
    # Steer left hard for 100 frames
    for _ in range(100):
        player.apply_input(left=True, right=False, up=False, down=False)
    assert player.x >= player.min_x
    assert player.x == pytest.approx(player.min_x, abs=0.01)

    # Steer right hard for 200 frames
    for _ in range(200):
        player.apply_input(left=False, right=True, up=False, down=False)
    assert player.x <= player.max_x
    assert player.x == pytest.approx(player.max_x, abs=0.01)

    # 3. Assert collision with glass shards depletes hearts
    # Damage 1
    hit = state.damage_player()
    assert hit is True
    assert state.hearts == 2
    assert state.invulnerable_timer == StateManager.INVULNERABLE_FRAMES
    assert state.shake_intensity > 0.0

    # Collision during invulnerability does not double damage
    hit_during_invuln = state.damage_player()
    assert hit_during_invuln is False
    assert state.hearts == 2

    # Expire invulnerability
    for _ in range(state.INVULNERABLE_FRAMES):
        state.update_timers()
    assert state.invulnerable_timer == 0

    # Damage 2
    state.damage_player()
    assert state.hearts == 1

    for _ in range(state.INVULNERABLE_FRAMES):
        state.update_timers()

    # Damage 3: lethal hit -> Game Over
    state.damage_player()
    assert state.hearts == 0
    assert state.current_state == GameState.GAMEOVER
    assert state.scroll_speed == 0.0


# ---------------------------------------------------------------------------
# Gate 2: Kairos Timing Gate
# ---------------------------------------------------------------------------
def test_kairos_timing_gate():
    state = StateManager()
    state.start_game()
    assert state.current_state == GameState.CHRONOS

    # Assert Kairos triggers exactly at 8.0s (240 frames at 30 FPS)
    for frame in range(239):
        state.update_timers()
        assert state.current_state == GameState.CHRONOS
        assert state.scroll_speed > 0.0

    # 240th frame triggers Kairos
    state.update_timers()
    assert state.current_state == GameState.KAIROS
    assert state.scroll_speed == 0.0  # Freezes kinematics

    # Test choice transition resumes Chronos
    bargains = BargainManager()
    options = bargains.draw_options(3)
    assert len(options) == 3
    # Apply first option
    bargains.apply_bargain(options[0][0], state)
    state.resume_chronos()
    assert state.current_state == GameState.CHRONOS
    assert state.scroll_speed > 0.0
    assert state.chronos_timer == 0

    # Test timeout transition (if no input for 60 frames / 2.0s)
    state.trigger_kairos()
    assert state.current_state == GameState.KAIROS
    for _ in range(59):
        state.update_timers()
        assert state.current_state == GameState.KAIROS
        assert state.scroll_speed == 0.0

    # 60th frame of Kairos triggers timeout back to Chronos
    state.update_timers()
    assert state.current_state == GameState.CHRONOS
    assert state.scroll_speed > 0.0


# ---------------------------------------------------------------------------
# Gate 3: Compounding Math Gate
# ---------------------------------------------------------------------------
def test_compounding_math_gate():
    """Verify bargain Boon(k) strictly decreases and Curse(k) strictly increases monotonically for k in {0, 1, 2, 3}."""
    for sin_type, defn in BARGAIN_REGISTRY.items():
        boons = [defn.get_boon_value(k) for k in range(4)]
        curses = [defn.get_curse_value(k) for k in range(4)]

        # Verify strict monotonicity
        for k in range(3):
            assert boons[k + 1] < boons[k], f"{sin_type} Boon failed strict monotonic decrease at k={k}"
            assert curses[k + 1] > curses[k], f"{sin_type} Curse failed strict monotonic increase at k={k}"

        # Verify exact mathematical scaling: Boon(k) = Boon(0) * (0.75)^k, Curse(k) = Curse(0) * (1.50)^k
        for k in range(4):
            expected_boon = defn.boon_base * (0.75 ** k)
            expected_curse = defn.curse_base * (1.50 ** k)
            assert boons[k] == pytest.approx(expected_boon, rel=1e-5)
            assert curses[k] == pytest.approx(expected_curse, rel=1e-5)


# ---------------------------------------------------------------------------
# Gate 4: Greed Deterministic Kill-Timer Gate
# ---------------------------------------------------------------------------
def test_greed_deterministic_kill_timer_gate():
    """Verify Sands of Greed initializes deterministic kill-timer terminating game upon expiration."""
    state = StateManager()
    state.start_game()
    bargains = BargainManager()

    assert not state.greed_timer_active
    assert state.greed_kill_timer == -1

    # Apply Greed
    bargains.apply_bargain(SinType.GREED, state)
    assert state.greed_timer_active is True
    assert state.greed_kill_timer > 0
    initial_timer = state.greed_kill_timer

    # Advance timer until 1 frame before death
    for _ in range(initial_timer - 1):
        state.update_timers()
        assert state.current_state != GameState.GAMEOVER

    # Last tick triggers sudden death
    state.update_timers()
    assert state.current_state == GameState.GAMEOVER
    assert "Greed" in state.death_reason


# ---------------------------------------------------------------------------
# Gate 5: Vignette Boundary Gate
# ---------------------------------------------------------------------------
class MockPyxel:
    def __init__(self):
        self.rect_calls = []

    def rect(self, x, y, w, h, col):
        self.rect_calls.append((x, y, w, h, col))


def test_vignette_boundary_gate():
    """Assert R_vignette > 0 and clamps cleanly without rendering exceptions."""
    state = StateManager()
    assert state.vignette_radius > 0.0
    assert state.min_vignette_radius > 0.0

    # Test contracting vignette radius with bargains
    bargains = BargainManager()
    for _ in range(30):
        bargains.apply_bargain(SinType.GLUTTONY, state)
    assert state.vignette_radius >= state.min_vignette_radius
    assert state.vignette_radius > 0.0

    # Test render_vignette execution across varied boundary conditions
    mock = MockPyxel()
    test_radii = [state.vignette_radius, state.min_vignette_radius, 0.0, -10.0, 50.0, 300.0]
    for r in test_radii:
        mock.rect_calls.clear()
        # Should render without throwing any exceptions
        render_vignette(px=80.0, py=60.0, radius=r, screen_w=160, screen_h=120, pyxel_module=mock)
        if r <= 100.0:
            assert len(mock.rect_calls) > 0

    # Edge test: player near screen borders
    mock.rect_calls.clear()
    render_vignette(px=0.0, py=0.0, radius=40.0, screen_w=160, screen_h=120, pyxel_module=mock)
    assert len(mock.rect_calls) > 0


# ---------------------------------------------------------------------------
# Additional System Mechanics Tests
# ---------------------------------------------------------------------------
def test_wrath_entity_wipe_and_zero_yield():
    state = StateManager()
    state.start_game()
    entities = EntityManager(160, 120)
    # Spawn shards
    entities.shards.append(GlassShard(80, 100))
    entities.shards.append(GlassShard(90, 110))
    assert len(entities.shards) == 2

    bargains = BargainManager()
    bargains.apply_bargain(SinType.WRATH, state, entities)
    assert len(entities.shards) == 0
    assert state.wrath_wipe_timer > 0
    assert state.wrath_zero_yield_timer > 0

    # In zero yield, collecting sand adds 0 points
    init_score = state.score
    state.add_score(100)
    assert state.score == init_score


def test_sloth_speed_modifiers():
    state = StateManager()
    state.start_game()
    bargains = BargainManager()

    init_hazard_spd = state.sloth_hazard_speed_mod
    init_player_spd = state.sloth_player_speed_mod
    bargains.apply_bargain(SinType.SLOTH, state)

    assert state.sloth_hazard_speed_mod < init_hazard_spd
    assert state.sloth_player_speed_mod < init_player_spd


def test_envy_and_lust_mechanics():
    state = StateManager()
    state.start_game()
    entities = EntityManager(160, 120)
    entities.bypassed_sand_pool = 10

    bargains = BargainManager()
    # Envy claims bypassed sand
    bargains.apply_bargain(SinType.ENVY, state, entities)
    assert entities.bypassed_sand_pool == 0
    assert state.score > 0
    assert state.envy_repel_radius > 0.0

    # Lust activates sand and hazard magnetic fields
    bargains.apply_bargain(SinType.LUST, state, entities)
    assert state.lust_attract_radius > 0.0
    assert state.lust_hazard_attract_radius > 0.0


def test_audio_manager_safe_without_pyxel():
    audio = AudioManager()
    # Shouldn't raise any exceptions when uninitialized
    audio.play_collect()
    audio.play_impact()
    audio.play_kairos()
    audio.play_death()
