"""Automated Unit Validation Suite for Grain of Doubt.
Verifies all 5 gates defined in p02.md / p03.md for 600x800 resolution and A/D controls.
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
    state = StateManager()  # Defaults to 5 hearts
    assert state.hearts == 5
    assert state.base_vignette_radius == 1000.0
    assert state.vignette_radius == 1000.0
    state.start_game()
    assert state.current_state == GameState.CHRONOS

    # 1. Assert continuous downward descent (scroll_speed > 0)
    assert state.scroll_speed > 0.0
    base_spd = state.scroll_speed

    # 2. Assert infinite lateral steering (A / D only - SkiFree style)
    player = HourglassPlayer(screen_w=600, screen_h=800)
    # Steer left hard for 100 frames: player moves infinitely left past 0
    for _ in range(100):
        player.apply_input(left=True, right=False)
    assert player.x < 0.0, "Player failed to steer into infinite left coordinates!"

    # Steer right hard for 200 frames: player moves infinitely right past 600
    for _ in range(200):
        player.apply_input(left=False, right=True)
    assert player.x > 600.0, "Player failed to steer into infinite right coordinates!"

    # 3. Assert collision with glass shards depletes hearts from 5
    # Damage 1
    hit = state.damage_player()
    assert hit is True
    assert state.hearts == 4
    assert state.invulnerable_timer == StateManager.INVULNERABLE_FRAMES
    assert state.shake_intensity > 0.0

    # Collision during invulnerability does not double damage
    hit_during_invuln = state.damage_player()
    assert hit_during_invuln is False
    assert state.hearts == 4

    # Expire invulnerability
    for _ in range(state.INVULNERABLE_FRAMES):
        state.update_timers()
    assert state.invulnerable_timer == 0

    # Deplete remaining hearts to 0
    for h in range(3, -1, -1):
        state.damage_player()
        for _ in range(state.INVULNERABLE_FRAMES):
            state.update_timers()

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

    # Test choice transition resumes Chronos with 2 bargain options
    bargains = BargainManager()
    options = bargains.draw_options(2)
    assert len(options) == 2
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
# Gate 4: Greed Borrowed Time Mechanics Gate
# ---------------------------------------------------------------------------
def test_greed_borrowed_time_mechanics_gate():
    """Verify Greed activates Borrowed Time without instant kill-timer, cuts vignette, and scales tension."""
    state = StateManager()
    state.start_game()
    bargains = BargainManager()

    assert not state.greed_active
    assert state.greed_level == 0
    initial_vignette = state.vignette_radius
    initial_spd = state.speed_multiplier
    initial_spawn = state.spawn_rate_multiplier

    # Apply Greed
    bargains.apply_bargain(SinType.GREED, state)
    assert state.greed_active is True
    assert state.greed_level == 1
    assert state.vignette_radius < initial_vignette  # 50% area cut (~70.7% radius)
    assert state.speed_multiplier > initial_spd      # Borrowed time pace escalation
    assert state.spawn_rate_multiplier > initial_spawn

    # Verify NO sudden death kill timer: advancing 1000 frames does NOT kill the player
    for _ in range(1000):
        state.update_timers()
        assert state.current_state != GameState.GAMEOVER, "Greed must not arbitrarily terminate game via kill timer!"


# ---------------------------------------------------------------------------
# Gate 5: Vignette Boundary Gate
# ---------------------------------------------------------------------------
class MockPyxel:
    def __init__(self):
        self.rect_calls = []
        self.dither_calls = []

    def rect(self, x, y, w, h, col):
        self.rect_calls.append((x, y, w, h, col))

    def dither(self, alpha):
        self.dither_calls.append(alpha)


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

    # Test render_vignette execution across varied boundary conditions (600x800)
    mock = MockPyxel()
    test_radii = [state.vignette_radius, state.min_vignette_radius, 0.0, -10.0, 150.0, 1500.0]
    for r in test_radii:
        mock.rect_calls.clear()
        # Should render without throwing any exceptions
        render_vignette(px=300.0, py=400.0, radius=r, screen_w=600, screen_h=800, pyxel_module=mock)
        if r <= 450.0:
            assert len(mock.rect_calls) > 0

    # Edge test: player near screen borders
    mock.rect_calls.clear()
    render_vignette(px=0.0, py=0.0, radius=200.0, screen_w=600, screen_h=800, pyxel_module=mock)
    assert len(mock.rect_calls) > 0


# ---------------------------------------------------------------------------
# Additional System Mechanics Tests
# ---------------------------------------------------------------------------
def test_wrath_entity_wipe_and_zero_yield():
    state = StateManager()
    state.start_game()
    entities = EntityManager(600, 800)
    # Spawn shards
    entities.shards.append(GlassShard(300, 700))
    entities.shards.append(GlassShard(350, 750))
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
    entities = EntityManager(600, 800)
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


def test_video_recorder_unique_filename():
    import os
    import tempfile
    from engine.video import VideoRecorder

    with tempfile.TemporaryDirectory() as tmpdir:
        base = os.path.join(tmpdir, "test.mp4")
        # File doesn't exist yet: returns base
        res1 = VideoRecorder._resolve_unique_filename(base)
        assert res1 == base

        # Create the file
        with open(base, "w") as f:
            f.write("dummy")

        # Now it increments to test_001.mp4 without overwriting
        res2 = VideoRecorder._resolve_unique_filename(base)
        assert res2 == os.path.join(tmpdir, "test_001.mp4")

        with open(res2, "w") as f:
            f.write("dummy2")

        # Next increment: test_002.mp4
        res3 = VideoRecorder._resolve_unique_filename(base)
        assert res3 == os.path.join(tmpdir, "test_002.mp4")


def test_video_recorder_produces_colored_frames():
    """Verify video frames are encoded with actual colors (not pitch black)."""
    import os
    import shutil
    import subprocess
    import tempfile
    import pyxel
    from engine.video import VideoRecorder

    if shutil.which("ffmpeg") is None:
        return  # Skip if ffmpeg not in test environment

    with tempfile.TemporaryDirectory() as tmpdir:
        out_mp4 = os.path.join(tmpdir, "color_test.mp4")
        recorder = VideoRecorder(output_path=out_mp4, width=600, height=800, fps=30)

        pyxel.init(600, 800, headless=True)
        pyxel.cls(7)  # Off-white
        pyxel.rect(50, 50, 200, 200, 8)  # Crimson Pink

        started = recorder.start(pyxel_module=pyxel, filename=out_mp4)
        assert started is True
        for _ in range(5):
            recorder.record_frame(pyxel)
        recorder.stop()

        assert os.path.exists(out_mp4)
        assert os.path.getsize(out_mp4) > 0

        # Decode 1 frame to rgb24 and assert colors are not all black (0, 0, 0)
        dec_cmd = ["ffmpeg", "-y", "-i", out_mp4, "-vframes", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
        proc = subprocess.Popen(dec_cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        raw_rgb, _ = proc.communicate()
        assert len(raw_rgb) == 600 * 800 * 3
        # Ensure we have high brightness colors (>15)
        bright_bytes = [b for b in raw_rgb if b > 50]
        assert len(bright_bytes) > 10000, "Recorded frame was pitch black! Pal8 layout failed!"


def test_dev_mode_toggle_and_mobile_touch_controls():
    """Verify dev mode toggle, home screen copy, and mobile touch button mechanics."""
    from main import GrainOfDoubtApp
    import pyxel

    app = GrainOfDoubtApp(headless=True)
    assert app.dev_mode is False
    assert app.touch_left is False
    assert app.touch_right is False

    # Verify title screen copy doesn't say "kairos timefreeze 2pact"
    import inspect
    title_src = inspect.getsource(app.draw_title_screen)
    assert "KAIROS TIME-FREEZE (2 PACTS)" not in title_src
    assert "kairos timefreeze 2pact" not in title_src.lower()

    # Simulate mobile touch input on left side
    pyxel.mouse_x = 100
    pyxel.mouse_y = 700
    # Mock btn to return True for MOUSE_BUTTON_LEFT
    orig_btn = pyxel.btn
    try:
        pyxel.btn = lambda k: (k == pyxel.MOUSE_BUTTON_LEFT)
        app.update_input()
        assert app.touch_left is True
        assert app.touch_right is False
        assert app.state._input_left is True
        assert app.state._input_right is False

        # Simulate mobile touch input on right side
        pyxel.mouse_x = 500
        pyxel.mouse_y = 700
        app.update_input()
        assert app.touch_left is False
        assert app.touch_right is True
        assert app.state._input_left is False
        assert app.state._input_right is True
    finally:
        pyxel.btn = orig_btn


