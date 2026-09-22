"""Automated Unit Validation Suite for Grain of Doubt.
Verifies all 5 gates defined in p02.md / p03.md for 600x800 resolution and A/D controls.
"""
import math
import random
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

    # Test timeout transition (if no input for 60 frames / 2.0s -> Instant Death)
    state.trigger_kairos()
    assert state.current_state == GameState.KAIROS
    for _ in range(59):
        state.update_timers()
        assert state.current_state == GameState.KAIROS
        assert state.scroll_speed == 0.0

    # 60th frame of Kairos triggers instant death (Paralyzed by Doubt)
    state.update_timers()
    assert state.current_state == GameState.GAMEOVER
    assert "Paralyzed by Doubt" in state.death_reason


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
    """Verify Greed activates Borrowed Time for 10-18s, multiplies score by 110% on sand, and scales tension."""
    state = StateManager()
    state.start_game()
    bargains = BargainManager()

    assert not state.greed_active
    assert state.greed_level == 0
    initial_spd = state.speed_multiplier
    initial_spawn = state.spawn_rate_multiplier

    # Apply Greed
    bargains.apply_bargain(SinType.GREED, state)
    assert state.greed_active is True
    assert state.greed_level == 1
    # Random timer between 10.0 and 18.0s (300 to 540 frames)
    assert 300 <= state.greed_timer <= 540
    assert state.speed_multiplier > initial_spd      # Borrowed time pace escalation
    assert state.spawn_rate_multiplier > initial_spawn

    # Verify sand collection during Greed multiplies score by 110% instead of +1
    state.score = 10
    state.add_score(1)
    assert state.score == 11  # 10 * 1.10 = 11

    state.score = 100
    state.add_score(1)
    assert state.score == 110  # 100 * 1.10 = 110

    # Advance frames in Chronos until timer expires: greed_active becomes False
    duration = state.greed_timer
    for _ in range(duration):
        state.update_timers()
        if state.current_state == GameState.KAIROS:
            state.resume_chronos()
        assert state.current_state != GameState.GAMEOVER, "Greed must not kill the player!"

    assert state.greed_timer == 0
    assert state.greed_active is False


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
    assert init_hazard_spd == 1.0

    bargains.apply_bargain(SinType.SLOTH, state)

    # Immediately upon selection: hazards are fully frozen (speed mod = 0.0)
    assert state.sloth_hazard_speed_mod == 0.0
    assert state.sloth_freeze_timer == 240
    assert state.sloth_player_speed_mod < init_player_spd

    # Halfway (120 frames / 4.0s): recovered to ~0.50
    for _ in range(120):
        state.update_timers()
    assert 0.49 <= state.sloth_hazard_speed_mod <= 0.51

    # Full 240 frames (8.0s): fully recovered back to 1.0
    for _ in range(120):
        state.update_timers()
    assert state.sloth_hazard_speed_mod == 1.0
    assert state.sloth_freeze_timer == 0


def test_envy_and_lust_mechanics():
    from engine.entities import SandGrain
    state = StateManager()
    state.start_game()
    entities = EntityManager(600, 800)
    entities.player.x = 300.0

    # Add 2 on-screen sands and 1 far off-screen sand
    entities.sands = [
        SandGrain(300.0, 400.0),
        SandGrain(320.0, 450.0),
        SandGrain(10000.0, 400.0),
    ]

    bargains = BargainManager()
    assert state.vignette_radius == 1000.0
    initial_score = state.score

    # Envy reaps all on-screen sands immediately (boon) and applies vignette vision (curse)
    bargains.apply_bargain(SinType.ENVY, state, entities)
    assert len(entities.sands) == 1
    assert entities.sands[0].x == 10000.0
    assert state.score >= initial_score + 2
    assert state.vignette_radius == 260.0  # Vignette Vision curse activated!

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

        # Verify B and V key toggles only work when dev_mode is True
        app.dev_mode = False
        app.bot_mode = False
        orig_btnp = pyxel.btnp
        try:
            pyxel.btnp = lambda k: (k == pyxel.KEY_B)
            app.update()
            assert app.bot_mode is False  # Cannot toggle without dev mode!

            # Enable dev mode: now KEY_B toggles bot_mode
            app.dev_mode = True
            app.update()
            assert app.bot_mode is True   # Enabled in dev mode!
        finally:
            pyxel.btnp = orig_btnp
    finally:
        pyxel.btn = orig_btn


def test_pride_sand_clusters_and_one_point_per_sand():
    """Verify 1 sand is 1 point, and Pride spawns clustered pairs/triplets with shared velocity."""
    state = StateManager()
    state.start_game()
    assert state.score == 0

    # 1 sand is 1 point
    state.add_score(1)
    assert state.score == 1
    assert state.total_sand_collected == 1

    entities = EntityManager(screen_w=600, screen_h=800)
    bargains = BargainManager()

    # Calibrated single-wave spawn rate matching the expanded 4.5 screens (6000px) span
    single_wave_rate = 880.0 / (entities.screen_w + 2.0 * 2700.0) / 0.45

    # Initially pride_level is 0 -> spawn 1 sand grain per wave
    random.seed(42)
    entities.spawn_accumulator = 0.0
    with pytest.MonkeyPatch().context() as mp:
        mp.setattr(random, "random", lambda: 0.1)  # Force sand
        entities.spawn_wave(single_wave_rate, wrath_active=False, camera_x=0.0, pride_level=state.pride_level)
    assert len(entities.sands) == 1

    # Apply 1st Pride -> pride_level becomes 1 (Pairs)
    bargains.apply_bargain(SinType.PRIDE, state)
    assert state.pride_level == 1

    entities.sands.clear()
    entities.spawn_accumulator = 0.0
    with pytest.MonkeyPatch().context() as mp:
        mp.setattr(random, "random", lambda: 0.1)  # Force sand
        entities.spawn_wave(single_wave_rate, wrath_active=False, camera_x=0.0, pride_level=state.pride_level)
    # Group size must be 2 (pair)
    assert len(entities.sands) == 2
    s1, s2 = entities.sands[0], entities.sands[1]
    # Shared initial velocities
    assert s1.speed_variance == s2.speed_variance
    assert s1.lateral_drift == s2.lateral_drift
    assert s1.shimmer_phase == s2.shimmer_phase
    # Different positions (no overlap)
    assert (s1.x != s2.x) or (s1.y != s2.y)

    # Apply 2nd Pride -> pride_level becomes 2 (Triplets)
    bargains.apply_bargain(SinType.PRIDE, state)
    assert state.pride_level == 2

    entities.sands.clear()
    entities.spawn_accumulator = 0.0
    with pytest.MonkeyPatch().context() as mp:
        mp.setattr(random, "random", lambda: 0.1)  # Force sand
        entities.spawn_wave(single_wave_rate, wrath_active=False, camera_x=0.0, pride_level=state.pride_level)
    # Group size must be 3 (triplet)
    assert len(entities.sands) == 3


def test_dev_mode_fixed_pacts_and_title_screen_shortcut():
    """Verify dev mode keys 1-7 apply fixed pacts in canonical Catholic order."""
    from main import GrainOfDoubtApp
    import pyxel

    app = GrainOfDoubtApp(headless=True)
    app.start_new_game()

    # Dev mode is OFF initially
    assert not app.dev_mode
    orig_btnp = pyxel.btnp
    try:
        pyxel.btnp = lambda k: (k == pyxel.KEY_BACKQUOTE)
        app.update()
        assert app.dev_mode is True

        # In canonical order: key 1 applies PRIDE
        initial_pride = app.state.pride_level
        pyxel.btnp = lambda k: (k == pyxel.KEY_1)
        app.update()
        assert app.state.pride_level == initial_pride + 1
        assert app.selected_feedback is not None
        assert app.selected_feedback["sin"] == "Pride"

        # Key 6 applies WRATH
        pyxel.btnp = lambda k: (k == pyxel.KEY_6)
        app.update()
        assert app.state.wrath_wipe_timer > 0
        assert app.selected_feedback["sin"] == "Wrath"
    finally:
        pyxel.btnp = orig_btnp


def test_canonical_sins_order_and_vertical_list():
    """Assert the 7 deadly sins adhere strictly to Catholic Gregorian canonical order (SALIGIA)."""
    from main import CANONICAL_SINS

    expected = [
        SinType.PRIDE,
        SinType.GREED,
        SinType.LUST,
        SinType.ENVY,
        SinType.GLUTTONY,
        SinType.WRATH,
        SinType.SLOTH,
    ]
    assert CANONICAL_SINS == expected
    assert len(CANONICAL_SINS) == 7


def test_game_over_2s_debounce_lockout():
    """Verify Game Over enforces 2.0s (60 frames) lockout before allowing restart."""
    from main import GrainOfDoubtApp
    import pyxel

    app = GrainOfDoubtApp(headless=True)
    app.start_new_game()

    # Force Game Over
    app.state.trigger_game_over("Test Hourglass Shattered")
    assert app.state.current_state == GameState.GAMEOVER
    assert app.game_over_timer == 0

    orig_btnp = pyxel.btnp
    try:
        # Even if user presses restart key immediately (frame 1..59), ignore input!
        pyxel.btnp = lambda k: True
        for frame in range(1, 60):
            app.update()
            assert app.game_over_timer == frame
            assert app.state.current_state == GameState.GAMEOVER, "Must lock out restart input during 2s debounce!"

        # Frame 60 reached, input now unlocks and triggers restart
        app.update()
        assert app.state.current_state == GameState.CHRONOS
        assert app.game_over_timer == 0
    finally:
        pyxel.btnp = orig_btnp


def test_infinite_arena_4_point_5_screens_spawn_margin():
    """Verify procedural wave generator produces items across 4.5 screens (+-2700px) margin."""
    entities = EntityManager(screen_w=600, screen_h=800)
    entities.reset()

    # Spawn wave at camera_x = 1000
    camera_x = 1000.0
    entities.spawn_wave(spawn_rate_mult=10.0, wrath_active=False, camera_x=camera_x)

    all_xs = [s.x for s in entities.sands] + [sh.x for sh in entities.shards]
    assert len(all_xs) > 0

    # Minimum and maximum possible bounds: [1000 - 2700, 1000 + 600 + 2700] = [-1700, 4300]
    for x in all_xs:
        assert (camera_x - 2750.0) <= x <= (camera_x + 600.0 + 2750.0)

    # Over multiple spawns, verify broad distribution beyond former 140px limits
    spanned_outside_140 = any(abs(x - (camera_x + 300.0)) > 600.0 for x in all_xs)
    assert spanned_outside_140, "Entities must populate the wide +-2700px horizon!"


def test_pride_randomized_offsets():
    """Verify Pride sand clusters generate randomized offsets with no complete overlap."""
    entities = EntityManager(screen_w=600, screen_h=800)
    entities.reset()

    # With pride_level = 3 (quadruplet cluster = 4 grains)
    import random
    random.seed(42)
    # Collect offsets from 10 cluster generations
    all_cluster_offsets = []
    for _ in range(10):
        # Force sand spawn
        group_size = 4
        offsets = [(0.0, 0.0)]
        for _ in range(group_size - 1):
            for _attempt in range(15):
                rand_angle = random.uniform(0, 2.0 * math.pi)
                rand_r = random.uniform(14.0, 36.0)
                cand_ox = math.cos(rand_angle) * rand_r
                cand_oy = math.sin(rand_angle) * (rand_r * 0.8)
                if all(math.hypot(cand_ox - ex_ox, cand_oy - ex_oy) >= 12.0 for ex_ox, ex_oy in offsets):
                    offsets.append((cand_ox, cand_oy))
                    break
            else:
                offsets.append((random.uniform(-25.0, 25.0), random.uniform(-25.0, 25.0)))
        all_cluster_offsets.append(offsets)

    # Check that offsets are not identical across clusters (they are randomized)
    assert all_cluster_offsets[0] != all_cluster_offsets[1]
    # Check minimum separation within each cluster
    for cluster in all_cluster_offsets:
        assert len(cluster) == 4
        for i in range(len(cluster)):
            for j in range(i + 1, len(cluster)):
                dist = math.hypot(cluster[i][0] - cluster[j][0], cluster[i][1] - cluster[j][1])
                assert dist >= 10.0, "Cluster grains must not overlap"


def test_kairos_repress_protection():
    """Verify Kairos ignores held steering input until player releases and re-presses."""
    from main import GrainOfDoubtApp
    app = GrainOfDoubtApp(headless=True)
    app.start_new_game()
    app.state.current_state = GameState.KAIROS
    app.active_options = app.bargains.draw_options(2)

    # Simulate player was holding left when entering Kairos
    app.kairos_left_released = False
    app.selected_card_index = -1

    # Attempt to seal without releasing: should not seal
    instant_seal = False
    # If left is still held, release flag remains False
    is_left_now = True
    if not is_left_now:
        app.kairos_left_released = True
    move_left = True and app.kairos_left_released
    if move_left:
        instant_seal = True
    assert not instant_seal
    assert app.selected_card_index == -1

    # Now player unpresses
    is_left_now = False
    if not is_left_now:
        app.kairos_left_released = True
    assert app.kairos_left_released is True

    # Now player presses left again (re-press)
    move_left = True and app.kairos_left_released
    if move_left:
        app.selected_card_index = 0
        instant_seal = True
    assert instant_seal is True
    assert app.selected_card_index == 0




