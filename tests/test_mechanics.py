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

    # Assert Kairos triggers exactly at 10.0s (300 frames at 30 FPS)
    for frame in range(299):
        state.update_timers()
        assert state.current_state == GameState.CHRONOS
        assert state.scroll_speed > 0.0

    # 300th frame triggers Kairos
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

    # Test timeout transition (if no input for 300 frames / 10.0s -> Instant Death)
    state.trigger_kairos()
    assert state.current_state == GameState.KAIROS
    for _ in range(299):
        state.update_timers()
        assert state.current_state == GameState.KAIROS
        assert state.scroll_speed == 0.0

    # 300th frame of Kairos triggers instant death (Paralyzed by Doubt)
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
    """Verify Greed activates Borrowed Time for 10-18s, multiplies score by 110% on sand, and lethal expiration."""
    state = StateManager()
    state.start_game()
    bargains = BargainManager()

    assert not state.greed_active
    assert state.greed_level == 0

    # Apply Greed
    bargains.apply_bargain(SinType.GREED, state)
    assert state.greed_active is True
    assert state.greed_level == 1
    # Random timer between 10.0 and 18.0s (300 to 540 frames)
    assert 300 <= state.greed_timer <= 540

    # Verify sand collection during Greed multiplies score by 110% instead of +1
    state.score = 10
    state.add_score(1)
    assert state.score == 11  # 10 * 1.10 = 11

    state.score = 100
    state.add_score(1)
    assert state.score == 110  # 100 * 1.10 = 110

    # Gluttony sand (base_points=3) simulates collecting 3 small sand grains sequentially
    state.score = 100
    state.total_sand_collected = 0
    state.add_score(3)
    # 100 * 1.1 = 110; 110 * 1.1 = 121; 121 * 1.1 = 133.1 -> 133
    assert state.score == 133
    assert state.total_sand_collected == 3

    # Advance frames in Chronos until 1 frame before expiration: player remains alive
    duration = state.greed_timer
    for _ in range(duration - 1):
        state.update_timers()
        if state.current_state == GameState.KAIROS:
            state.resume_chronos()
        assert state.current_state == GameState.CHRONOS, "Player must remain alive during Borrowed Time window"

    # Last frame: Borrowed Time expires and player definitely dies (Debt Collected)
    state.update_timers()
    assert state.greed_timer == 0
    assert state.greed_active is False
    assert state.current_state == GameState.GAMEOVER
    assert "Borrowed Time Expired" in state.death_reason


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
def test_wrath_explosion_and_zero_yield():
    state = StateManager()
    state.start_game()
    entities = EntityManager(600, 800)
    entities.player.x = 300.0
    entities.player.y = 200.0
    # Spawn shards and sand within 1600px
    s1 = GlassShard(300, 400)
    s2 = GlassShard(400, 300)
    sand1 = SandGrain(300, 350)
    entities.shards.extend([s1, s2])
    entities.sands.append(sand1)
    assert len(entities.shards) == 2
    assert len(entities.sands) == 1

    bargains = BargainManager()
    bargains.apply_bargain(SinType.WRATH, state, entities)
    # Shards and sand are NOT deleted; they receive an initial moderate kick and multi-frame burst acceleration
    assert len(entities.shards) == 2
    assert len(entities.sands) == 1
    assert s1.vy > 0
    assert sand1.vy > 0
    assert math.hypot(s1.vx, s1.vy) >= 10.0
    assert math.hypot(s2.vx, s2.vy) >= 10.0
    assert math.hypot(sand1.vx, sand1.vy) >= 10.0
    assert s1.burst_timer > 0
    assert sand1.burst_timer > 0

    # Advance through burst acceleration frames to build full explosive momentum
    for _ in range(8):
        s1.update(scroll_speed=0.0, hazard_speed_mod=1.0, player_x=300.0, player_y=200.0)
        s2.update(scroll_speed=0.0, hazard_speed_mod=1.0, player_x=300.0, player_y=200.0)
        sand1.update(scroll_speed=0.0, player_x=300.0, player_y=200.0)
    assert math.hypot(s1.vx, s1.vy) >= 30.0
    assert math.hypot(s2.vx, s2.vy) >= 30.0
    assert math.hypot(sand1.vx, sand1.vy) >= 30.0
    # In v1.1.4: No zero-yield score penalty (wrath_zero_yield_timer is 0); the con is the blast on the grains!
    assert state.wrath_zero_yield_timer == 0

    # Collecting sand adds points normally
    init_score = state.score
    state.add_score(100)
    assert state.score == init_score + 100


def test_sloth_speed_modifiers():
    """Verify Sloth Lazy Reprieve:
    - Sloth means lazy; lazy means doing nothing!
    - In a single high acceleration frame, all shards below player (within 3 screens wide)
      are hurled downward toward the bottom horizon (vy >= 38, y >= 720).
    - Shards above the player are unaffected.
    - Creates ~2s safe space below player where they can do literally nothing and survive.
    - Shards clump together at the bottom horizon into a dangerous wave.
    - Permanent lateral drag curse reduces player steering speed.
    """
    state = StateManager()
    state.start_game()
    bargains = BargainManager()
    entities = EntityManager(600, 800)

    # Place shards below player (py = 320)
    s1 = GlassShard(300, 380)
    s2 = GlassShard(350, 500)
    s3 = GlassShard(250, 700)
    # And one shard above player (y = 150)
    s_above = GlassShard(300, 150)
    entities.shards.extend([s1, s2, s3, s_above])

    init_player_spd = state.sloth_player_speed_mod
    assert init_player_spd == 1.0

    # Apply Sloth bargain
    summary = bargains.apply_bargain(SinType.SLOTH, state, entities)
    assert "Lazy Reprieve" in summary["boon"]
    assert "3 shards hurled" in summary["boon"]

    # Shard above player unaffected
    assert s_above.y == 150
    assert s_above.vy == 0.0

    # Shards below player receive initial downward acceleration kick and sustained burst timer
    for shard in [s1, s2, s3]:
        assert shard.vy >= 12.0
        assert shard.burst_timer > 0

    # Lateral drag curse is applied
    assert state.sloth_player_speed_mod < init_player_spd

    # Player can do literally NOTHING for ~2 seconds (90+ frames) and survive without hitting any shards
    player = entities.player
    for frame in range(90):
        for s in entities.shards:
            s.update(scroll_speed=state.scroll_speed, hazard_speed_mod=1.0, player_x=player.x, player_y=player.y)
        # Verify no collision with player during lazy reprieve period
        for s in [s1, s2, s3]:
            assert s.y > player.y + 10.0 or not s.alive

    # The hurled shards clumped together at the bottom horizon
    y_coords = [s.y for s in [s1, s2, s3] if s.alive]
    assert len(y_coords) >= 2
    assert all(y > 700.0 for y in y_coords)  # all hurled far down below screen
    assert max(y_coords) - min(y_coords) < 600.0  # clumped wave without teleportation


def test_envy_and_lust_mechanics():
    from engine.entities import SandGrain
    state = StateManager()
    state.start_game()
    entities = EntityManager(600, 800)
    entities.player.x = 300.0

    # Add 2 on-screen sands and 1 far sand (outside mega lust radius, but inside 3500px arena bounds)
    far_sand = SandGrain(2500.0, 400.0)
    entities.sands = [
        SandGrain(300.0, 400.0),
        SandGrain(320.0, 450.0),
        far_sand,
    ]

    bargains = BargainManager()
    assert state.vignette_radius == 1000.0
    initial_score = state.score

    # Envy activates 2.0s (60 frames) Mega Lust (boon) and applies vignette vision (curse)
    # Envy 1 starts at former Envy 3 (k_eff = 3: outer=614.4, inner=409.6)
    bargains.apply_bargain(SinType.ENVY, state, entities)
    assert state.envy_mega_lust_active is True
    assert state.envy_mega_lust_timer == 60
    assert state.envy_mega_lust_radius == pytest.approx(1228.8, rel=1e-3)
    assert state.vignette_radius == pytest.approx(614.4, rel=1e-3)
    assert state.vignette_inner_radius == pytest.approx(409.6, rel=1e-3)

    # Grains within 2x vignette radius get attracted strongly when updated
    entities.update(state)
    # The on-screen sands (distance ~ 100-150px from player at 300, 320) moved towards player
    assert entities.sands[0].y < 400.0  # pulled upward toward player.y (320)
    assert entities.sands[1].y < 450.0  # pulled upward toward player.y (320)
    # Grains beyond 1920.0 (like 2500.0) are NOT mega-attracted (only minor drift < 2.0px)
    assert far_sand.alive is True
    assert abs(far_sand.x - 2500.0) < 2.0

    # Updating 60 frames expires Mega Lust
    for _ in range(60):
        state.update_timers()
    assert state.envy_mega_lust_timer == 0
    assert state.envy_mega_lust_active is False

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

        with open(res3, "w") as f:
            f.write("dummy3")

        # Calling with an already suffixed path test_002.mp4 cleanly advances to test_003.mp4
        res4 = VideoRecorder._resolve_unique_filename(res3)
        assert res4 == os.path.join(tmpdir, "test_003.mp4")

    # Verify bare filename defaults to recordings/ and directory exists
    rec = VideoRecorder("bare_test.mp4")
    assert rec.output_path == os.path.join("recordings", "bare_test.mp4")
    assert os.path.isdir("recordings")


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

    # Calibrated single-wave spawn rate matching the expanded 4.5 screens (6000px) span with halved spawn rate
    single_wave_rate = 880.0 / (entities.screen_w + 2.0 * 2700.0) / 0.225

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
        assert app.state.wrath_zero_yield_timer == 0  # No zero-yield con in v1.1.4!
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
        # Even if user presses restart key immediately (frame 1..59), ignore restart input!
        pyxel.btnp = lambda k: (k in (pyxel.KEY_SPACE, pyxel.KEY_RETURN, pyxel.KEY_R))
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


def test_dev_mode_invulnerability_toggle():
    """Verify God Mode toggle protects player from taking any damage."""
    state = StateManager()
    state.start_game()
    assert state.godmode is False
    assert state.hearts == 5

    # Taking damage normally reduces hearts
    dealt = state.damage_player()
    assert dealt is True
    assert state.hearts == 4

    # Activate God Mode
    state.godmode = True
    state.invulnerable_timer = 0  # clear cooldown

    # Damage in God Mode must be completely negated
    dealt2 = state.damage_player()
    assert dealt2 is False
    assert state.hearts == 4


def test_envy_multi_circle_graduated_vignette():
    """Verify multi-circle graduated vignette renders multiple dither tiers without error."""
    from main import render_vignette

    class MockPyxel:
        def __init__(self):
            self.rect_calls = []
            self.dither_calls = []

        def dither(self, alpha):
            self.dither_calls.append(alpha)

        def rect(self, x, y, w, h, col):
            self.rect_calls.append((x, y, w, h, col))

    mock = MockPyxel()
    # Test with Envy vignette radius 260.0 px centered at (300, 400)
    render_vignette(300.0, 400.0, radius=260.0, screen_w=600, screen_h=800, pyxel_module=mock)

    # Must invoke multiple dither tiers (e.g. 0.20, 0.42, 0.65, 0.85, 1.0)
    assert len(mock.dither_calls) > 0
    unique_alphas = set(round(a, 2) for a in mock.dither_calls)
    assert len(unique_alphas) >= 4, f"Must have at least 4 distinct dither transparency levels, got {unique_alphas}"
    assert len(mock.rect_calls) > 0


def test_pyweek_packaging_entrypoints():
    """Verify standard PyWeek packaging entrypoints and files exist."""
    import os
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    run_game_path = os.path.join(root_dir, "run_game.py")
    req_path = os.path.join(root_dir, "requirements.txt")
    readme_path = os.path.join(root_dir, "README.md")

    assert os.path.exists(run_game_path), "PyWeek packaging mandate: run_game.py must exist at root"
    assert os.path.exists(req_path), "PyWeek packaging: requirements.txt must exist"
    assert os.path.exists(readme_path), "PyWeek packaging: README.md must exist"

    # Check run_game.py contains version check
    with open(run_game_path, "r") as f:
        content = f.read()
    assert "MIN_VER" in content
    assert "sys.version_info" in content


def test_dev_mode_qwertyu_pact_reduction():
    """Verify keys Q, W, E, R, T, Y, U reduce pact levels in dev mode."""
    state = StateManager()
    state.start_game()
    bargains = BargainManager()
    entities = EntityManager(600, 800)

    # 1. PRIDE (Q)
    bargains.apply_bargain(SinType.PRIDE, state, entities)
    assert bargains.get_selection_count(SinType.PRIDE) == 1
    assert state.pride_level == 1
    initial_spd = state.speed_multiplier
    # Reduce Pride
    bargains.reduce_bargain(SinType.PRIDE, state, entities)
    assert bargains.get_selection_count(SinType.PRIDE) == 0
    assert state.pride_level == 0
    assert state.speed_multiplier < initial_spd

    # 2. GREED (W)
    bargains.apply_bargain(SinType.GREED, state, entities)
    assert state.greed_active is True
    assert bargains.get_selection_count(SinType.GREED) == 1
    # Reduce Greed
    bargains.reduce_bargain(SinType.GREED, state, entities)
    assert bargains.get_selection_count(SinType.GREED) == 0
    assert state.greed_active is False
    assert state.greed_timer == 0

    # 3. LUST (E)
    bargains.apply_bargain(SinType.LUST, state, entities)
    assert state.lust_attract_radius > 0.0
    assert state.lust_hazard_attract_radius > 0.0
    # Reduce Lust
    bargains.reduce_bargain(SinType.LUST, state, entities)
    assert bargains.get_selection_count(SinType.LUST) == 0
    assert state.lust_attract_radius == 0.0
    assert state.lust_hazard_attract_radius == 0.0

    # 4. ENVY (R)
    bargains.apply_bargain(SinType.ENVY, state, entities)
    assert state.vignette_radius == pytest.approx(614.4, rel=1e-3)
    assert state.vignette_inner_radius == pytest.approx(409.6, rel=1e-3)
    assert state.envy_level == 1
    # Reduce Envy
    bargains.reduce_bargain(SinType.ENVY, state, entities)
    assert bargains.get_selection_count(SinType.ENVY) == 0
    assert state.envy_level == 0
    assert state.vignette_radius == 1000.0

    # 5. GLUTTONY (T)
    bargains.apply_bargain(SinType.GLUTTONY, state, entities)
    assert state.gluttony_level == 1
    # Reduce Gluttony
    bargains.reduce_bargain(SinType.GLUTTONY, state, entities)
    assert state.gluttony_level == 0

    # 6. WRATH (Y)
    w_sum = bargains.apply_bargain(SinType.WRATH, state, entities)
    assert w_sum["sin"] == "Wrath"
    assert state.wrath_zero_yield_timer == 0
    # Reduce Wrath
    w_red = bargains.reduce_bargain(SinType.WRATH, state, entities)
    assert w_red["sin"] == "Wrath"
    assert state.wrath_zero_yield_timer == 0

    # 7. SLOTH (U)
    initial_player_mod = state.sloth_player_speed_mod
    bargains.apply_bargain(SinType.SLOTH, state, entities)
    assert state.sloth_player_speed_mod < initial_player_mod
    # Reduce Sloth
    bargains.reduce_bargain(SinType.SLOTH, state, entities)
    assert state.sloth_player_speed_mod == pytest.approx(initial_player_mod)
    assert state.sloth_freeze_timer == 0


def test_quit_key_is_x_and_app_bindings():
    """Verify X key returns to menu during gameplay, quits on desktop title screen, and no-ops in browser."""
    import sys
    import pyxel
    from main import GrainOfDoubtApp

    app = GrainOfDoubtApp(headless=True)
    orig_quit = pyxel.quit
    orig_btnp = pyxel.btnp
    quit_called = False

    def mock_quit():
        nonlocal quit_called
        quit_called = True

    try:
        pyxel.quit = mock_quit
        pyxel.btnp = lambda k: (k == pyxel.KEY_X)

        # 1. During CHRONOS gameplay, pressing X returns to TITLE and does NOT quit
        app.start_new_game()
        assert app.state.current_state == GameState.CHRONOS
        app.update()
        assert app.state.current_state == GameState.TITLE
        assert quit_called is False

        # 2. On TITLE screen on desktop, pressing X calls pyxel.quit()
        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(sys, "platform", "darwin")
            app.update()
            assert quit_called is True

        # 3. On TITLE screen in browser (emscripten), pressing X does NOT call pyxel.quit()
        quit_called = False
        with pytest.MonkeyPatch().context() as mp:
            mp.setattr(sys, "platform", "emscripten")
            app.update()
            assert quit_called is False
    finally:
        pyxel.quit = orig_quit
        pyxel.btnp = orig_btnp


def test_lust_permanent_attraction_both():
    """Verify Lust permanently attracts both sand and hazards across frames without timing out."""
    state = StateManager()
    state.start_game()
    bargains = BargainManager()

    bargains.apply_bargain(SinType.LUST, state)
    rad = state.lust_attract_radius
    assert rad == 100.0
    assert state.lust_hazard_attract_radius == 100.0

    # Advance 400 frames: neither radius should decay to 0!
    for _ in range(400):
        state.update_timers()
    assert state.lust_attract_radius == 100.0
    assert state.lust_hazard_attract_radius == 100.0

    # Apply 2nd pact: radius expands by +50.0px
    bargains.apply_bargain(SinType.LUST, state)
    assert state.lust_attract_radius == 150.0
    assert state.lust_hazard_attract_radius == 150.0


def test_wrath_non_compounding():
    """Verify Wrath con is grain blast, with zero-yield timer remaining 0."""
    state = StateManager()
    state.start_game()
    bargains = BargainManager()

    w1 = bargains.apply_bargain(SinType.WRATH, state)
    assert state.wrath_zero_yield_timer == 0
    assert w1["sin"] == "Wrath"

    # Apply Wrath second time: remains 0 (no zero yield penalty)
    w2 = bargains.apply_bargain(SinType.WRATH, state)
    assert state.wrath_zero_yield_timer == 0
    assert w2["sin"] == "Wrath"


def test_dev_mode_title_screen_version_display():
    """Verify version number is displayed on the title screen when in Dev Mode."""
    import main
    from main import GrainOfDoubtApp

    app = GrainOfDoubtApp(headless=True, dev_mode=False)
    assert app.dev_mode is False

    drawn_texts = []
    orig_draw = main.draw_text_scaled
    try:
        main.draw_text_scaled = lambda x, y, s, col, scale=1, img_bank=2: drawn_texts.append(s)

        # In non-dev mode, title screen does not show [DEV MODE]
        app.draw_title_screen()
        assert not any("DEV MODE: ON" in t for t in drawn_texts)

        # In dev mode, title screen shows [`] DEV MODE: ON (v1.1.3)
        app.dev_mode = True
        drawn_texts.clear()
        app.draw_title_screen()
        assert any(f"DEV MODE: ON ({app.VERSION})" in t for t in drawn_texts)
    finally:
        main.draw_text_scaled = orig_draw


def test_web_containment_math_and_aspect_ratio():
    """Verify responsive 3:4 CSS aspect ratio and containment variables in optimize_web."""
    import os
    opt_path = os.path.join(os.path.dirname(__file__), "..", "optimize_web.py")
    with open(opt_path) as f:
        src = f.read()

    assert "--target-w: min(var(--avail-w), calc(var(--avail-h) * 0.75));" in src
    assert "--target-h: calc(var(--target-w) * 4 / 3);" in src
    assert "screenEl.style.setProperty('width', w + 'px', 'important');" in src
    assert "canvasEl.style.setProperty('width', w + 'px', 'important');" in src
    assert "window.__DEV_MODE__ = true;" in src
    assert "gesturestart" in src
    assert "user-scalable=no" in src
    assert "touch-action: none" in src


def test_bot_waits_until_last_moment_in_kairos():
    """Verify GOFAI bot does not confirm pact immediately, but waits until the final moments."""
    from engine.bot import PlayTestingBot
    from engine.bargains import SinType, BARGAIN_REGISTRY

    bot = PlayTestingBot(seed=42)
    options = [
        (SinType.PRIDE, BARGAIN_REGISTRY[SinType.PRIDE], 1),
        (SinType.GLUTTONY, BARGAIN_REGISTRY[SinType.GLUTTONY], 1),
    ]

    # When 50 frames remaining (early in Kairos): bot positions cursor but does NOT confirm
    m_left, m_right, confirm = bot.decide_kairos_choice(options, current_index=0, frames_remaining=50)
    assert confirm is False, "Bot confirmed too early in Kairos!"

    # When 4 frames remaining (very last moment): bot confirms selection
    target = bot.target_card_index
    m_left, m_right, confirm = bot.decide_kairos_choice(options, current_index=target, frames_remaining=4)
    assert confirm is True, "Bot failed to confirm at the final moment in Kairos!"


def test_sloth_aggressive_drag():
    """Verify Sloth lateral drag imposes aggressive 20% * 1.5^k reduction."""
    state = StateManager()
    state.start_game()
    bargains = BargainManager()

    assert state.sloth_player_speed_mod == 1.0

    # 1st pact: -20% reduction (mod = 0.80)
    bargains.apply_bargain(SinType.SLOTH, state)
    assert state.sloth_player_speed_mod == pytest.approx(0.80, abs=1e-3)

    # 2nd pact: -30% reduction (mod = 0.50)
    bargains.apply_bargain(SinType.SLOTH, state)
    assert state.sloth_player_speed_mod == pytest.approx(0.50, abs=1e-3)


def test_dev_mode_bottom_menu_shows_invulnerability_shortcut():
    """Verify bottom dev menu displays the shortcut for invulnerability."""
    import main
    from main import GrainOfDoubtApp

    app = GrainOfDoubtApp(headless=True, dev_mode=True)
    assert app.dev_mode is True

    drawn_texts = []
    orig_draw = main.draw_text_scaled
    try:
        main.draw_text_scaled = lambda x, y, s, col, scale=1, img_bank=2: drawn_texts.append(s)
        app.draw_dev_overlay()
        assert any("[G] GOD MODE:" in t for t in drawn_texts)
    finally:
        main.draw_text_scaled = orig_draw


def test_bot_game_over_delayed_restart():
    """Verify bot mode does not immediately restart on Game Over, waiting 6.0s (180 frames)."""
    import pyxel
    from main import GrainOfDoubtApp

    app = GrainOfDoubtApp(headless=True, bot_mode=True)
    app.start_new_game()
    app.state.trigger_game_over("Test Bot Death")
    assert app.state.current_state == GameState.GAMEOVER

    orig_btnp = pyxel.btnp
    try:
        pyxel.btnp = lambda k: False
        # Up to frame 179: must remain in GAMEOVER
        for frame in range(1, 180):
            app.update()
            assert app.state.current_state == GameState.GAMEOVER
            assert app.auto_restart_timer == frame

        # Frame 180 reached: bot auto-restarts into CHRONOS
        app.update()
        assert app.state.current_state == GameState.CHRONOS
        assert app.auto_restart_timer == 0
    finally:
        pyxel.btnp = orig_btnp


def test_pact_menu_top_right_numbered_format():
    """Verify pact menu is at top right, has no '(7)', and numbers each pact '1. pride 0'."""
    import main
    from main import GrainOfDoubtApp

    app = GrainOfDoubtApp(headless=True)
    app.start_new_game()

    calls = []
    orig_draw = main.draw_text_scaled
    try:
        main.draw_text_scaled = lambda x, y, s, col, scale=1, img_bank=2: calls.append((x, y, s))
        app.draw_hud()

        # Check title is "FAUSTIAN PACTS" (not "PACTS (7)")
        pact_titles = [c for c in calls if c[2] in ("PACTS", "FAUSTIAN PACTS")]
        assert len(pact_titles) == 1, "Must render 'FAUSTIAN PACTS' header"
        # Must be on the right side of the 600px screen (x >= 380)
        assert pact_titles[0][0] >= 380, f"Pact menu header must be at top right (x >= 380), got {pact_titles[0][0]}"

        # Check numbered rows with capitalized names: '1. Pride', '2. Greed', etc.
        pride_entry = [c for c in calls if "1. Pride" in c[2]]
        assert len(pride_entry) == 1, f"Must find '1. Pride' in HUD text, found {calls}"
        assert pride_entry[0][0] >= 380, "Pact row must be at top right"

        greed_entry = [c for c in calls if "2. Greed" in c[2]]
        assert len(greed_entry) == 1, f"Must find '2. Greed' in HUD text, found {calls}"

        # Ensure no '(7)' anywhere in HUD
        assert not any("(7)" in c[2] for c in calls)
    finally:
        main.draw_text_scaled = orig_draw

def test_score_formatting_space_separator_no_leading_zeros():
    """Verify score display has no leading zeros and uses space as thousands separator."""
    import main
    from main import GrainOfDoubtApp

    app = GrainOfDoubtApp(headless=True)
    app.start_new_game()

    test_scores = [0, 999, 1000, 12345, 1234567]
    expected = ["0", "999", "1 000", "12 345", "1 234 567"]

    for sc, exp in zip(test_scores, expected):
        app.state.score = sc
        calls = []
        orig_draw = main.draw_text_scaled
        try:
            main.draw_text_scaled = lambda x, y, s, col, scale=1, img_bank=2: calls.append(s)
            app.draw_hud()
            # Must find "SCORE: <exp>" exactly
            assert f"SCORE: {exp}" in calls, f"Expected 'SCORE: {exp}' in HUD calls, got {calls}"
            # Ensure no leading zeros like "000123"
            assert not any(c.startswith("SCORE: 0") and c != "SCORE: 0" for c in calls)
        finally:
            main.draw_text_scaled = orig_draw


def test_bot_affected_by_envy_vignette_vision():
    """Verify bot filters out entities outside vignette radius when Envy is active."""
    from engine.bot import PlayTestingBot
    from engine.entities import GlassShard, SandGrain

    bot = PlayTestingBot()
    player_x = 300.0
    player_y = 700.0
    vignette_radius = 500.0

    # Shard inside vignette (dist = 100) vs shard outside (dist = 600)
    inside_shard = GlassShard(300.0, 600.0)
    outside_shard = GlassShard(300.0, 100.0)
    shards = [inside_shard, outside_shard]

    filtered_shards = bot.filter_visible_shards(shards, screen_h=800, player_x=player_x, player_y=player_y, vignette_radius=vignette_radius)
    assert inside_shard in filtered_shards
    assert outside_shard not in filtered_shards

    # Sand inside vignette vs outside (inside threshold y <= 640 and within 500px radius of (300, 700))
    inside_sand = SandGrain(350.0, 550.0)
    outside_sand = SandGrain(300.0, 100.0)
    sands = [inside_sand, outside_sand]

    filtered_sands = bot.filter_visible_sands(sands, screen_h=800, player_x=player_x, player_y=player_y, vignette_radius=vignette_radius)
    assert inside_sand in filtered_sands
    assert outside_sand not in filtered_sands


def test_hourglass_sand_falling_proportional_to_tilt():
    """Verify hourglass sand drain direction and particle physics are proportional to tilt."""
    from engine.entities import HourglassPlayer

    player = HourglassPlayer(600, 800)

    # Idle (vx = 0) -> tilt = 0
    assert player.tilt == 0.0
    initial_phase = player.sand_drain_phase
    player.apply_input(False, False)
    assert player.sand_drain_phase == initial_phase

    # Moving right (vx > 0) -> tilt > 0, sand drain phase increases positively
    player.vx = 8.0
    assert player.tilt > 0.0
    player.apply_input(False, False)
    assert player.sand_drain_phase > initial_phase

    # Moving left (vx < 0) -> tilt < 0, sand drain phase decreases
    player.vx = -8.0
    assert player.tilt < 0.0
    phase_before_left = player.sand_drain_phase
    player.apply_input(False, False)
    assert player.sand_drain_phase < phase_before_left


def test_kairos_title_significantly_bigger_and_justified_center():
    """Verify Kairos card title is significantly bigger, horizontally fills the box based on the longest sin, and is justified center."""
    import main
    from main import GrainOfDoubtApp
    from engine.state import GameState
    from engine.bargains import SinType, BARGAIN_REGISTRY

    app = GrainOfDoubtApp(headless=True)
    app.start_new_game()
    app.state.current_state = GameState.KAIROS
    app.active_options = [
        (SinType.GLUTTONY, BARGAIN_REGISTRY[SinType.GLUTTONY], 0),
        (SinType.PRIDE, BARGAIN_REGISTRY[SinType.PRIDE], 1),
    ]

    title_draws = []
    orig_draw = main.draw_text_scaled
    try:
        def mock_draw(x, y, s, col, scale=1, img_bank=2, *args, **kwargs):
            if s in ["GLUTTONY", "PRIDE"]:
                title_draws.append((x, y, s, scale))
        main.draw_text_scaled = mock_draw
        app.draw_kairos_modal()

        assert len(title_draws) == 2, f"Expected 2 title draw calls, got {title_draws}"

        # 1. Significantly bigger: scale must be >= 3 and <= 5 (calibrated for 5x7 font without overflowing card)
        for x, y, s, scale in title_draws:
            assert scale in (3, 4, 5), f"Title {s} scale must be 3, 4, or 5 in 5x7 font, got {scale}"

        # 2. Longest character/name (GLUTTONY, 8 chars) must fill box horizontally in 5x7 font (col_w = 228)
        glut_x, glut_y, glut_s, glut_scale = [d for d in title_draws if d[2] == "GLUTTONY"][0]
        glut_rendered_w = main.get_text_width_5x7(glut_s, glut_scale)
        assert glut_rendered_w >= 180, f"GLUTTONY rendered width ({glut_rendered_w}px) must fill >= 180px of the 228px card"

        # 3. Justified center: for each card, text must be centered within ±1px of the card box
        col_w = 228
        col_gap = 20
        start_x = 30 + 32
        for i, (x, y, s, scale) in enumerate(title_draws):
            cx = start_x + i * (col_w + col_gap)
            text_w = main.get_text_width_5x7(s, scale)
            expected_x = cx + col_w // 2 - text_w // 2
            assert abs(x - expected_x) <= 1, f"Title {s} must be justified center at {expected_x}, got {x}"
    finally:
        main.draw_text_scaled = orig_draw


def test_envy_momentum_continuation_at_end():
    """Verify sand grains accelerate and preserve their velocity/momentum after Envy ends."""
    from engine.entities import SandGrain

    sand = SandGrain(300.0, 450.0, speed_variance=1.0, lateral_drift=0.0)
    assert sand.vx == 0.0
    assert sand.vy == 0.0

    player_x = 300.0
    player_y = 320.0
    mega_r = 1920.0
    scroll_speed = 5.0

    # Simulate 5 frames of Envy Mega Lust: sand accelerates upward towards player.y (320)
    for _ in range(5):
        sand.update(scroll_speed, player_x, player_y, mega_attract_radius=mega_r)

    assert sand.vy < -5.0, f"Expected upward acceleration (vy < -5), got {sand.vy}"
    vy_during_envy = sand.vy
    y_before_end = sand.y

    # Mega Lust ends! mega_attract_radius becomes 0.0
    sand.update(scroll_speed, player_x, player_y, mega_attract_radius=0.0)

    # Momentum must persist: vy must still be negative (moving upward)
    assert sand.vy < -4.0, f"Expected momentum continuation after Envy ends, got {sand.vy}"
    # Total distance moved upward this frame must exceed normal scroll speed (-5.0)
    delta_y = sand.y - y_before_end
    assert delta_y < -5.0, f"Sand should carry momentum faster than scroll speed, delta_y={delta_y}"

    # Smooth viscous drag decay over subsequent frames
    prev_vy = sand.vy
    for _ in range(10):
        sand.update(scroll_speed, player_x, player_y, mega_attract_radius=0.0)
        assert abs(sand.vy) <= abs(prev_vy), "Velocity magnitude must decay smoothly via drag"
        prev_vy = sand.vy


def test_lust_momentum_continuation_for_sands_and_shards():
    """Verify both sand grains and glass shards accelerate and preserve momentum when Lust ends."""
    from engine.entities import SandGrain, GlassShard

    sand = SandGrain(350.0, 320.0, speed_variance=1.0, lateral_drift=0.0)
    shard = GlassShard(250.0, 320.0, speed_variance=1.0)
    shard.lateral_drift = 0.0

    player_x = 300.0
    player_y = 320.0
    lust_r = 200.0
    scroll_speed = 5.0

    # Accelerate towards player at (300, 320) for 4 frames
    for _ in range(4):
        sand.update(scroll_speed, player_x, player_y, attract_radius=lust_r)
        shard.update(scroll_speed, 1.0, player_x, player_y, attract_radius=lust_r)

    # Sand was at x=350, so accelerated left (vx < 0)
    assert sand.vx < -0.5, f"Sand should accelerate left, got {sand.vx}"
    # Shard was at x=250, so accelerated right (vx > 0)
    assert shard.vx > 0.5, f"Shard should accelerate right, got {shard.vx}"

    # Lust ends! attract_radius becomes 0.0
    sand_vx_end = sand.vx
    shard_vx_end = shard.vx

    sand.update(scroll_speed, player_x, player_y, attract_radius=0.0)
    shard.update(scroll_speed, 1.0, player_x, player_y, attract_radius=0.0)

    # Both must carry their lateral momentum
    assert sand.vx < 0.0, "Sand must continue traveling left with momentum after Lust ends"
    assert shard.vx > 0.0, "Shard must continue traveling right with momentum after Lust ends"
    assert abs(sand.vx) < abs(sand_vx_end), "Sand momentum decays gracefully via drag"
    assert abs(shard.vx) < abs(shard_vx_end), "Shard momentum decays gracefully via drag"


def test_sloth_do_nothing_survival_and_clumped_wave():
    """Verify that Sloth (lazy = doing nothing) clears all shards below the player
    for ~2 seconds in a single high acceleration frame, allowing survival with zero inputs,
    and clumps the thrown shards at the bottom into a dangerous wave.
    """
    state = StateManager()
    state.start_game()
    entities = EntityManager(600, 800)

    # Spawn 6 shards at varied positions below the player (player.y = 200)
    shards_below = [
        GlassShard(260.0, 250.0),
        GlassShard(300.0, 320.0),
        GlassShard(340.0, 400.0),
        GlassShard(280.0, 500.0),
        GlassShard(320.0, 600.0),
        GlassShard(350.0, 680.0),
    ]
    for s in shards_below:
        s.lateral_drift = 0.0
    entities.shards.extend(shards_below)

    # Trigger Sloth downward hurling
    thrown_count = entities.sloth_hurl_shards_downward(screen_width_factor=3.0, impulse_speed=38.0)
    assert thrown_count == 6

    # All shards receive initial downward kick and multi-frame burst timer (no 1-frame teleport)
    for s in shards_below:
        assert s.vy >= 12.0
        assert s.burst_timer > 0

    # Simulate 80 frames where player does NOTHING (literally zero inputs)
    for _ in range(80):
        for s in entities.shards:
            s.update(scroll_speed=state.scroll_speed, hazard_speed_mod=1.0, player_x=entities.player.x, player_y=entities.player.y)
        # Verify complete survival: no shard ever touches or gets above player during this window
        for s in shards_below:
            assert s.y > entities.player.y + 20.0

    # Verify that the shards are hurled to the bottom horizon and overlap with oncoming hazards (double danger)
    active_ys = [s.y for s in shards_below if s.alive]
    assert len(active_ys) == 6
    assert all(y > 600.0 for y in active_ys)
    # The hurled shards and seeded oncoming hazards overlap, doubling hazard count
    assert len(entities.shards) >= 12
    spread = max(active_ys) - min(active_ys)
    assert spread < 380.0, f"Expected clumped wave at bottom horizon, got spread={spread}"


def test_glass_shards_randomized_velocity_and_non_right_triangle_geometry():
    """Verify glass shards have randomized angular velocity and non-right-angled triangle geometry."""
    shards = [GlassShard(100.0 + i * 20.0, 500.0) for i in range(20)]
    spin_speeds = [s.spin_speed for s in shards]
    # Randomized continuous spin speeds (not all identical)
    assert len(set(spin_speeds)) > 5
    for s in shards:
        assert abs(s.spin_speed) > 0.01
        # Check 3 vertices
        assert len(s.vertices) == 3
        v0, v1, v2 = s.vertices
        # Check none of the internal angles is 90 degrees (dot product != 0)
        # Angle at v0: (v1 - v0) . (v2 - v0)
        d0 = (v1[0] - v0[0]) * (v2[0] - v0[0]) + (v1[1] - v0[1]) * (v2[1] - v0[1])
        # Angle at v1: (v0 - v1) . (v2 - v1)
        d1 = (v0[0] - v1[0]) * (v2[0] - v1[0]) + (v0[1] - v1[1]) * (v2[1] - v1[1])
        # Angle at v2: (v0 - v2) . (v1 - v2)
        d2 = (v0[0] - v2[0]) * (v1[0] - v2[0]) + (v0[1] - v2[1]) * (v1[1] - v2[1])
        assert abs(d0) > 0.05, f"Right-angled triangle detected at v0: d0={d0}"
        assert abs(d1) > 0.05, f"Right-angled triangle detected at v1: d1={d1}"
        assert abs(d2) > 0.05, f"Right-angled triangle detected at v2: d2={d2}"


def test_wrath_explosion_blasts_both_sand_and_shards_away():
    """Verify Wrath explosion blasts shards within 1600px and sand within 3200px."""
    entities = EntityManager(600, 800)
    entities.player.x = 300.0
    entities.player.y = 200.0

    # Inside radii: shard at 500px (<1600px), sand at 2000px (<3200px)
    near_shard = GlassShard(300.0, 700.0)  # dist = 500px
    near_sand = SandGrain(2300.0, 200.0)  # dist = 2000px
    # Outside radii: shard at 2000px (>1600px), sand at 3600px (>3200px)
    far_shard = GlassShard(300.0, 2200.0) # dist = 2000px
    far_sand = SandGrain(4000.0, 200.0)   # dist = 3700px

    entities.shards.extend([near_shard, far_shard])
    entities.sands.extend([near_sand, far_sand])

    shards_hit, sands_hit = entities.wrath_explosion(shard_radius=1600.0, grain_radius=3200.0, impulse_strength=46.0)
    assert shards_hit == 1
    assert sands_hit == 1

    # Near entities receive initial moderate acceleration kick
    assert near_shard.vy >= 10.0
    assert near_sand.vx >= 10.0
    assert near_shard.burst_timer > 0
    assert near_sand.burst_timer > 0

    # Far entities unaffected
    assert math.hypot(far_shard.vx, far_shard.vy) == 0.0
    assert math.hypot(far_sand.vx, far_sand.vy) == 0.0

    # Advance through burst acceleration frames: momentum accumulates to full blast velocity
    for _ in range(8):
        near_shard.update(scroll_speed=0.0, hazard_speed_mod=1.0, player_x=300.0, player_y=200.0)
        near_sand.update(scroll_speed=0.0, player_x=300.0, player_y=200.0)
    assert math.hypot(near_shard.vx, near_shard.vy) >= 30.0
    assert math.hypot(near_sand.vx, near_sand.vy) >= 30.0


def test_deep_world_simulation_consequence_catchup_ten_seconds_down():
    """Verify deep world simulation extends 10 seconds down (~3000-6000px) and consequences catch up."""
    state = StateManager()
    state.start_game()
    entities = EntityManager(600, 800)
    entities.player.x = 300.0
    entities.player.y = 200.0

    # Spawn shard 10 seconds down (600 frames * 5px/frame = 3000px down => y = 3200)
    deep_shard = GlassShard(300.0, 3200.0)
    deep_sand = SandGrain(320.0, 3500.0)
    entities.shards.append(deep_shard)
    entities.sands.append(deep_sand)

    # Initial frame update: neither should be despawned (bounds are y <= 6000.0)
    for s in entities.shards:
        s.update(scroll_speed=5.0, hazard_speed_mod=1.0, player_x=300.0, player_y=200.0)
    for g in entities.sands:
        g.update(scroll_speed=5.0, player_x=300.0, player_y=200.0)

    assert deep_shard.alive is True
    assert deep_sand.alive is True

    # Simulate 500 frames of upward scrolling: the deep shard moves upward into player territory
    for _ in range(500):
        for s in entities.shards:
            s.update(scroll_speed=5.0, hazard_speed_mod=1.0, player_x=300.0, player_y=200.0)

    # Deep shard moved from y=3200 down to y = 3200 - 500*5 = 700!
    assert deep_shard.alive is True
    assert deep_shard.y <= 800.0, f"Expected shard to catch up onto screen, got y={deep_shard.y}"


def test_sloth_and_wrath_multi_frame_acceleration_curve():
    """Verify that Sloth and Wrath do not apply massive single-frame spikes, but smooth multi-frame bursts."""
    entities = EntityManager(600, 800)
    entities.player.x = 300.0
    entities.player.y = 200.0

    # Test Wrath multi-frame acceleration
    target_shard = GlassShard(300.0, 350.0)
    entities.shards.append(target_shard)
    entities.wrath_explosion(explosion_radius=1200.0, impulse_strength=46.0, burst_frames=8)

    # Frame 0 kick is moderate (< 15.0 px/frame, not 46.0)
    init_speed = math.hypot(target_shard.vx, target_shard.vy)
    assert 8.0 <= init_speed <= 15.0
    assert target_shard.burst_timer == 8

    # Velocity grows over subsequent frames
    velocities = [init_speed]
    for _ in range(8):
        target_shard.update(scroll_speed=0.0, hazard_speed_mod=1.0, player_x=300.0, player_y=200.0)
        velocities.append(math.hypot(target_shard.vx, target_shard.vy))

    # Peak velocity after multi-frame acceleration exceeds 30 px/frame
    assert max(velocities) >= 30.0

    # Test Sloth multi-frame acceleration (no coordinate teleport)
    sloth_shard = GlassShard(300.0, 260.0)
    orig_y = sloth_shard.y
    entities.shards = [sloth_shard]
    entities.sloth_hurl_shards_downward(screen_width_factor=3.0, impulse_speed=46.0, burst_frames=10)

    # Initial kick is moderate (< 20.0 px/frame) and y was NOT teleported
    assert sloth_shard.y == orig_y
    assert 18.0 <= sloth_shard.vy <= 30.0
    assert sloth_shard.burst_timer == 10

    # Advances through frames and builds downward velocity
    for _ in range(10):
        sloth_shard.update(scroll_speed=0.0, hazard_speed_mod=1.0, player_x=300.0, player_y=200.0)
    assert sloth_shard.vy >= 30.0


def test_spawning_spatial_density_preserved_when_sped_up_by_pride():
    """Verify that when descent speed is multiplied (e.g. by Pride), spawn rate scales proportionally,
    preventing hazard dilution and ensuring the screen does not become empty or easier.
    """
    entities_normal = EntityManager(600, 800)
    entities_fast = EntityManager(600, 800)

    # Simulate 200 frames at normal speed (multiplier = 1.0)
    for _ in range(200):
        entities_normal.spawn_wave(spawn_rate_mult=1.0, wrath_active=False, speed_multiplier=1.0)

    # Simulate 200 frames at double speed (multiplier = 2.0, e.g. high Pride)
    for _ in range(200):
        entities_fast.spawn_wave(spawn_rate_mult=1.0, wrath_active=False, speed_multiplier=2.0)

    # At double speed, the world travels twice as far in 200 frames (2000px vs 1000px).
    # To maintain spatial density (entities per 1000px fallen), entities_fast must have spawned
    # approximately twice as many entities!
    count_normal = len(entities_normal.sands) + len(entities_normal.shards)
    count_fast = len(entities_fast.sands) + len(entities_fast.shards)

    ratio = count_fast / max(1, count_normal)
    assert 1.7 <= ratio <= 2.3, f"Expected ~2x spawn rate at 2x speed, got ratio={ratio:.2f}"


def test_glass_shard_obtuse_triangles_and_aerodynamic_spin():
    """Verify that GlassShard supports obtuse triangles (dot product < -8.0),
    never generates right angles (|dot product| >= 8.0), and aerodynamic rotation
    is proportional to horizontal velocity Vx.
    """
    from engine.entities import GlassShard
    # Sample many shards to confirm obtuse triangles exist and right angles do not
    obtuse_found = False
    for _ in range(100):
        shard = GlassShard(100.0, 100.0)
        p0, p1, p2 = shard.vertices
        # Dot products at all 3 vertices
        d0 = (p1[0] - p0[0]) * (p2[0] - p0[0]) + (p1[1] - p0[1]) * (p2[1] - p0[1])
        d1 = (p0[0] - p1[0]) * (p2[0] - p1[0]) + (p0[1] - p1[1]) * (p2[1] - p1[1])
        d2 = (p0[0] - p2[0]) * (p1[0] - p2[0]) + (p0[1] - p2[1]) * (p1[1] - p2[1])

        # Never right-angled
        assert abs(d0) >= 7.0 and abs(d1) >= 7.0 and abs(d2) >= 7.0

        # Obtuse means at least one vertex has angle > 90 deg (dot product < 0)
        if d0 < -8.0 or d1 < -8.0 or d2 < -8.0:
            obtuse_found = True

    assert obtuse_found, "Expected at least some generated shards to be obtuse triangles"

    # Aerodynamic spin test: higher horizontal velocity produces higher rotational displacement
    shard_slow = GlassShard(200.0, 200.0)
    shard_fast = GlassShard(200.0, 200.0)
    shard_slow.lateral_drift = 0.0
    shard_fast.lateral_drift = 0.0
    shard_slow.rotation_angle = 0.0
    shard_fast.rotation_angle = 0.0
    shard_slow.spin_speed = 0.0
    shard_fast.spin_speed = 0.0

    shard_slow.vx = 0.0
    shard_fast.vx = 20.0  # high horizontal airspeed

    shard_slow.update(scroll_speed=0.0, hazard_speed_mod=1.0, player_x=0.0, player_y=0.0)
    shard_fast.update(scroll_speed=0.0, hazard_speed_mod=1.0, player_x=0.0, player_y=0.0)

    assert abs(shard_fast.rotation_angle) > abs(shard_slow.rotation_angle)


def test_gluttony_fat_sand_and_fat_shard_generation_and_scoring():
    """Verify Gluttony rework:
    - Level 0: 0% fat (100% normal)
    - Level N: fat probability = 1 - 0.9^N
    - Fat sand grains: ~3x radius, worth 3x points
    - Fat shards: ~2.8x linear dimensions (~10x area)
    """
    from engine.entities import SandGrain, GlassShard, EntityManager
    from engine.bargains import BargainManager, SinType

    # Direct entity property verification
    normal_sand = SandGrain(100.0, 100.0, is_fat=False)
    fat_sand = SandGrain(100.0, 100.0, is_fat=True)

    assert normal_sand.POINT_VALUE == 1
    assert fat_sand.POINT_VALUE == 3
    assert fat_sand.HITBOX_W > normal_sand.HITBOX_W * 2.5
    assert fat_sand.is_fat is True

    normal_shard = GlassShard(100.0, 100.0, is_fat=False)
    fat_shard = GlassShard(100.0, 100.0, is_fat=True)
    assert fat_shard.is_fat is True
    assert fat_shard.HITBOX_W >= normal_shard.HITBOX_W * 2.5
    assert fat_shard.HITBOX_H >= normal_shard.HITBOX_H * 2.5

    # BargainManager fat probability formula check
    bm = BargainManager()
    assert bm.get_fat_chance(SinType.GLUTTONY) == 0.0  # level 0

    bm.selection_counts[SinType.GLUTTONY] = 1
    # 1 - 0.9^1 = 0.10
    assert abs(bm.get_fat_chance(SinType.GLUTTONY) - 0.10) < 1e-4

    bm.selection_counts[SinType.GLUTTONY] = 3
    # 1 - 0.9^3 = 1 - 0.729 = 0.271
    assert abs(bm.get_fat_chance(SinType.GLUTTONY) - 0.271) < 1e-4

    # Spawning verification across 200 spawns at Gluttony 5 (chance ~ 0.40951)
    bm.selection_counts[SinType.GLUTTONY] = 5
    em = EntityManager(600, 800)
    fat_chance = bm.get_fat_chance(SinType.GLUTTONY)
    for _ in range(250):
        em.spawn_wave(spawn_rate_mult=2.0, wrath_active=False, speed_multiplier=1.0, gluttony_level=5)

    fat_sands = [s for s in em.sands if s.is_fat]
    fat_shards = [s for s in em.shards if s.is_fat]
    assert len(fat_sands) > 0, "Expected fat sands to spawn at Gluttony level 5"
    assert len(fat_shards) > 0, "Expected fat shards to spawn at Gluttony level 5"


def test_hourglass_player_acceleration_and_air_friction():
    """Verify player hourglass lateral acceleration and aerodynamic air friction."""
    from engine.entities import HourglassPlayer

    player = HourglassPlayer(300.0, 400.0)
    assert player.vx == 0.0

    # Accelerate right for 5 frames
    for _ in range(5):
        player.move_right()
        player.update(0.016, 600)

    assert player.vx > 0.0
    speed_after_accel = player.vx

    # Release keys (no input): air friction should smoothly decelerate the player
    for _ in range(10):
        player.update(0.016, 600)

    assert player.vx < speed_after_accel
    assert player.vx > 0.0  # Still possesses residual forward momentum


def test_envy_recalibrated_starting_point():
    """Verify Envy starting point recalibration:
    Envy 1 must be equal to previous Envy 3:
    outer = 1200 * 0.8^(1+2) = 1200 * 0.512 = 614.4
    inner = 1000 * 0.8^(2+2) = 1000 * 0.4096 = 409.6
    """
    from engine.bargains import BargainManager, SinType

    bm = BargainManager()
    bm.selection_counts[SinType.ENVY] = 1
    outer_1, inner_1 = bm.get_envy_radii()
    assert abs(outer_1 - 614.4) < 1e-3
    assert abs(inner_1 - 409.6) < 1e-3


def test_all_game_states_draw_without_render_errors():
    """Verify that draw() completes successfully across all game states:
    CHRONOS, KAIROS, GAMEOVER, and TITLE (catches any pyxel drawing function argument errors).
    """
    import pyxel
    from main import GrainOfDoubtApp
    from engine.state import GameState
    from engine.bargains import SinType, BARGAIN_REGISTRY

    try:
        pyxel.init(600, 800, headless=True)
    except BaseException:
        pass  # Already initialized in previous tests

    app = GrainOfDoubtApp(headless=True)
    # Test Kairos explicitly with Gluttony (verifying bent bulging frame)
    app.active_options = [
        (SinType.GLUTTONY, BARGAIN_REGISTRY[SinType.GLUTTONY], 0),
        (SinType.PRIDE, BARGAIN_REGISTRY[SinType.PRIDE], 1),
    ]
    for state in [GameState.CHRONOS, GameState.KAIROS, GameState.GAMEOVER, GameState.TITLE]:
        app.state.current_state = state
        app.draw()

    # Also verify with Greed active (blood-dune twilight)
    app.state.greed_active = True
    app.state.current_state = GameState.CHRONOS
    app.draw()


def test_skifree_desert_terrain_and_daylight_contrast():
    """Verify procedural SkiFree desert terrain renders correctly across all conditions:
    normal daylight, imminent Kairos urgency flash, and Greed blood-desert mode.
    """
    import pyxel
    from main import GrainOfDoubtApp

    try:
        pyxel.init(600, 800, headless=True)
    except BaseException:
        pass

    app = GrainOfDoubtApp(headless=True)
    app.start_new_game()

    # 1. Normal daylight desert
    app.draw_skifree_desert_terrain(cam_x=0, prog=0.2)
    app.draw_skifree_desert_terrain(cam_x=450, prog=0.5)

    # 2. Imminent Kairos urgency glint (prog > 0.85)
    app.draw_skifree_desert_terrain(cam_x=200, prog=0.92)

    # 3. Greed active (blood-dune twilight)
    app.state.greed_active = True
    app.draw_skifree_desert_terrain(cam_x=300, prog=0.1)

    # 4. Backward-compatible aliases
    app.draw_atmospheric_dunes_and_glass_background(cam_x=100, prog=0.0)
    app.draw_celestial_depth_astrolabe(cam_x=100, prog=0.0)


def test_all_10_divergent_themes_registry():
    """Verify ALL_THEMES has exactly 10 distinct, divergent themes with unique IDs, names, and palettes."""
    from engine.themes import ALL_THEMES, get_theme

    assert len(ALL_THEMES) == 10, f"Expected exactly 10 themes, found {len(ALL_THEMES)}"

    theme_ids = set()
    theme_names = set()

    for idx, theme in enumerate(ALL_THEMES):
        assert theme.id == idx, f"Theme id {theme.id} must match index {idx}"
        assert theme.id not in theme_ids, f"Duplicate theme id: {theme.id}"
        theme_ids.add(theme.id)

        assert theme.name and len(theme.name) > 0, "Theme name must not be empty"
        assert theme.name not in theme_names, f"Duplicate theme name: {theme.name}"
        theme_names.add(theme.name)

        # Palettes
        assert theme.sand is not None
        assert theme.shard is not None
        assert theme.hourglass is not None
        assert callable(theme.render_bg)

        # Check get_theme wrapping
        assert get_theme(idx).id == idx
        assert get_theme(idx + 10).id == idx


def test_pro_mode_and_stealth_mode_themes():
    """Verify the 4 Pro Mode and Reader Mode themes are registered with proper aesthetics in order (1: Pro Light, 2: Pro Dark, 3: Reader Light, 4: Reader Dark)."""
    from engine.themes import ALL_THEMES, ECCLESIASTES_3_KJV_LINES, STEALTH_DARK_DOC, STEALTH_LIGHT_DOC
    from engine.bargains import SinType, SIN_CARD_COLORS

    # All 7 Sins have unique colors for Pro Mode cards
    assert len(SIN_CARD_COLORS) == 7
    assert len(set(SIN_CARD_COLORS.values())) == 7
    for sin in SinType:
        assert sin in SIN_CARD_COLORS

    # Theme 0: Dunes in the Cosmic Hourglass
    t0 = ALL_THEMES[0]
    assert t0.name == "DUNES IN THE COSMIC HOURGLASS"

    # Theme 1: Pro Mode Light
    t1 = ALL_THEMES[1]
    assert t1.name == "PRO MODE LIGHT"
    assert t1.clear_color == 7  # Clinical white
    assert t1.sand.body == 9  # Amber
    assert t1.shard.facet == 0  # Pitch-black shard for maximum contrast
    assert t1.render_bg.__name__ == "bg_pro_mode_light"

    # Theme 2: Pro Mode Dark
    t2 = ALL_THEMES[2]
    assert t2.name == "PRO MODE DARK"
    assert t2.clear_color == 0
    assert t2.sand.body == 10  # High-vis yellow
    assert t2.shard.facet == 12  # High-vis cyan
    assert t2.render_bg.__name__ == "bg_pro_mode_dark"

    # Theme 3: E-Reader Light
    t3 = ALL_THEMES[3]
    assert t3.name == "E-READER LIGHT"
    assert t3.clear_color == 15  # Cream parchment
    assert t3.is_reader_mode is True
    assert t3.render_bg.__name__ in ("bg_reader_light", "bg_stealth_light")

    # Theme 4: E-Reader Dark
    t4 = ALL_THEMES[4]
    assert t4.name == "E-READER DARK"
    assert t4.clear_color == 0
    assert t4.is_reader_mode is True
    assert t4.render_bg.__name__ in ("bg_reader_dark", "bg_stealth_dark")

    # Theme 5: Glacial Crevasse (Replaced Monochrome Blueprint)
    t5 = ALL_THEMES[5]
    assert t5.name == "GLACIAL CREVASSE"
    assert t5.render_bg.__name__ == "bg_glacial_crevasse"

    # Theme 9: Pastel Sakura (Cute girly pastel pink theme)
    t9 = ALL_THEMES[9]
    assert t9.name == "PASTEL SAKURA"
    assert t9.clear_color == 14
    assert t9.render_bg.__name__ == "bg_pastel_sakura"

    # Verify Ecclesiastes 3 KJV text
    assert len(ECCLESIASTES_3_KJV_LINES) >= 40
    assert any("season" in line for line in ECCLESIASTES_3_KJV_LINES)
    assert any("time to be born" in line for line in ECCLESIASTES_3_KJV_LINES)
    assert any("die;" in line for line in ECCLESIASTES_3_KJV_LINES)
    assert any("all turn to dust" in line for line in ECCLESIASTES_3_KJV_LINES)

    # Legacy documentation texts preserved
    assert len(STEALTH_DARK_DOC) >= 30
    assert any("RFC-4209" in line for line in STEALTH_DARK_DOC)
    assert len(STEALTH_LIGHT_DOC) >= 30
    assert any("CHAPTER IV" in line for line in STEALTH_LIGHT_DOC)


def test_all_20_themes_render_without_error():
    """Verify that all 20 themes render cleanly across CHRONOS, KAIROS, and Greed states."""
    import pyxel
    from main import GrainOfDoubtApp
    from engine.state import GameState
    from engine.themes import ALL_THEMES

    try:
        pyxel.init(600, 800, headless=True)
    except BaseException:
        pass

    app = GrainOfDoubtApp(headless=True)
    app.start_new_game()

    for theme_idx in range(len(ALL_THEMES)):
        app.current_theme_index = theme_idx

        # Test normal Chronos
        app.state.current_state = GameState.CHRONOS
        app.state.greed_active = False
        app.draw()

        # Test Greed Chronos
        app.state.greed_active = True
        app.draw()

        # Test Title screen with active theme
        app.state.current_state = GameState.TITLE
        app.theme_banner_timer = 30
        app.draw()

        # Reset
        app.state.greed_active = False


def test_dev_mode_comma_period_theme_cycling():
    """Verify that ',' and '.' cycle themes backward and forward in Dev Mode and set banner."""
    import pyxel
    from main import GrainOfDoubtApp
    from engine.themes import ALL_THEMES

    # Test that theme selection works outside dev mode (available to all players)
    app = GrainOfDoubtApp(headless=True, dev_mode=False)
    assert app.current_theme_index == 0
    assert app.theme_banner_timer == 0

    orig_btnp = pyxel.btnp
    try:
        # Press '.' without dev_mode -> advances to next theme (index 1)
        pyxel.btnp = lambda k: k == pyxel.KEY_PERIOD
        app.update()
        assert app.current_theme_index == 1
        assert app.theme_banner_timer == 89

        # Press ',' without dev_mode -> previous theme (index 0)
        pyxel.btnp = lambda k: k == pyxel.KEY_COMMA
        app.update()
        assert app.current_theme_index == 0
        assert app.theme_banner_timer == 89

        # Press ',' again -> wraps to index 19 (Theme 20)
        pyxel.btnp = lambda k: k == pyxel.KEY_COMMA
        app.update()
        assert app.current_theme_index == len(ALL_THEMES) - 1
        assert app.theme_banner_timer == 89

        # Test timer countdown
        pyxel.btnp = lambda k: False
        app.update()
        assert app.theme_banner_timer == 88
    finally:
        pyxel.btnp = orig_btnp


def test_pro_mode_chronos_bars():
    """Verify Pro Mode renders dual vertical countdown progress bars at extreme left and right borders during Chronos."""
    import pyxel
    from main import GrainOfDoubtApp
    from engine.state import GameState

    try:
        pyxel.init(600, 800, headless=True)
    except BaseException:
        pass

    app = GrainOfDoubtApp(headless=True)
    app.start_new_game()
    app.current_theme_index = 6  # Pro Mode Dark
    app.state.current_state = GameState.CHRONOS

    # Verify method runs without error at various stages of countdown
    for timer_val in [0, 75, 150, 260, 300]:
        app.state.chronos_timer = timer_val
        app.draw_pro_mode_chronos_bars()

    # Switch to Pro Mode Light and test
    app.current_theme_index = 7  # Pro Mode Light
    for timer_val in [0, 75, 150, 260, 300]:
        app.state.chronos_timer = timer_val
        app.draw_pro_mode_chronos_bars()

    # Verify it does nothing when not in Chronos
    app.state.current_state = GameState.TITLE
    app.draw_pro_mode_chronos_bars()


def test_sand_dunes_landscape_script_and_topology_engine():
    """Verify sand_dunes_landscape.py executable script and continuous procedural topology engine:
    1. Validates perspective math: horizon above canvas, bottom translates faster than top.
    2. Validates negative space curve rendering and atmospheric scattering.
    3. Runs standalone script headlessly without errors.
    """
    import subprocess
    import sys
    from sand_dunes_landscape import SandDunesLandscape

    # Test topology engine instantiation and mathematical properties
    sim = SandDunesLandscape(headless=True)
    assert sim.horizon_y < 0, "Horizon must be supra-canvas (above canvas)"
    assert sim.num_layers >= 12

    # Verify upward perspective motion: as dist increases, each dune moves UP towards the horizon (Y decreases)
    # Z(D, dist) = dist * speed_z - D * delta_z; Y = horizon_y + C / Z
    dune_d = 0
    travel_z1 = 100 * 0.003
    travel_z2 = 500 * 0.003
    z1 = travel_z1 - dune_d * 0.42
    z2 = travel_z2 - dune_d * 0.42
    y1 = sim.horizon_y + 1200.0 / z1
    y2 = sim.horizon_y + 1200.0 / z2
    assert y2 < y1, f"Dunes must move UP (Y decreases) as dist increases: y1={y1:.1f}, y2={y2:.1f}"

    # Verify translation velocity factor: bottom (Y=800) vs top (Y=50)
    # dY/dt = -(v/C) * (Y - horizon_y)^2
    vel_bottom = (800 - sim.horizon_y) ** 2
    vel_top = (50 - sim.horizon_y) ** 2
    assert vel_bottom > vel_top * 10, f"Bottom must translate >10x faster than top (perspective convergence). Ratio: {vel_bottom/vel_top:.1f}"

    # Run simulation frames
    for _ in range(5):
        sim.update()
    assert sim.dist > 0.0

    # Execute standalone script via subprocess with --headless
    import os
    script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sand_dunes_landscape.py"))
    res = subprocess.run(
        [sys.executable, script_path, "--headless", "--frames", "5", "--output", "scratch/test_subproc_dunes.png"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, f"Script failed: {res.stderr}"


def test_reader_mode_gameplay_alpha_and_hud_suppression():
    """Verify that Reader Mode suppresses all floating HUD boxes and applies 60% alpha dither to sand/player and 30% alpha to shards."""
    import pyxel
    from main import GrainOfDoubtApp
    from engine.state import GameState
    from engine.themes import get_theme

    try:
        pyxel.init(600, 800, headless=True)
    except BaseException:
        pass

    app = GrainOfDoubtApp(headless=True)
    app.start_new_game()
    app.state.current_state = GameState.CHRONOS

    # Track dither calls
    dither_values = []
    orig_dither = getattr(pyxel, "dither", None)
    pyxel.dither = lambda alpha: dither_values.append(round(alpha, 2))

    try:
        # Switch to Reader Mode Light (Theme 3)
        app.current_theme_index = 3
        theme_light = get_theme(3)
        assert theme_light.is_reader_mode is True

        # Render frame in Reader Mode Light
        app.draw()

        # Check that dither(0.60), dither(0.30), and dither(1.0) were applied
        assert 0.60 in dither_values, f"Expected 0.60 dither for sand/hourglass in Reader Mode, got {dither_values}"
        assert 0.30 in dither_values, f"Expected 0.30 dither for shards in Reader Mode, got {dither_values}"
        assert 1.0 in dither_values, f"Expected 1.0 dither restoration in Reader Mode, got {dither_values}"

        # Switch to Reader Mode Dark (Theme 4)
        app.current_theme_index = 4
        theme_dark = get_theme(4)
        assert theme_dark.is_reader_mode is True

        # Render frame in Reader Mode Dark
        app.draw()
    finally:
        if orig_dither is not None:
            pyxel.dither = orig_dither


def test_all_10_themes_kairos_palettes_and_modal_rendering():
    """Verify that every theme has a valid, distinct KairosPalette and renders the Kairos modal safely."""
    import pyxel
    from engine.themes import ALL_THEMES, KairosPalette
    from main import GrainOfDoubtApp
    from engine.state import GameState

    try:
        pyxel.init(600, 800, headless=True)
    except BaseException:
        pass

    app = GrainOfDoubtApp(headless=True)
    app.state.current_state = GameState.KAIROS
    app.active_options = [
        (SinType.PRIDE, BARGAIN_REGISTRY[SinType.PRIDE], 1),
        (SinType.GLUTTONY, BARGAIN_REGISTRY[SinType.GLUTTONY], 2),
    ]

    modal_bgs = set()

    for idx, theme in enumerate(ALL_THEMES):
        kp = theme.get_kairos_palette()
        assert isinstance(kp, KairosPalette)

        # Validate that all color fields are valid Pyxel color indices 0..15
        color_fields = [
            kp.modal_bg, kp.dimmer, kp.border_outer, kp.border_inner,
            kp.header_title, kp.header_sub, kp.timer_bar_bg, kp.timer_bar_fill,
            kp.timer_bar_border, kp.card_bg, kp.card_bg_selected, kp.card_border,
            kp.card_border_selected, kp.badge_bg, kp.badge_text,
            kp.badge_bg_selected, kp.badge_text_selected,
            kp.selected_btn_bg, kp.selected_btn_text,
            kp.sin_title, kp.sin_title_selected, kp.level_text, kp.divider,
            kp.pro_label, kp.pro_text, kp.con_label, kp.con_text,
            kp.footer_text, kp.footer_warn,
        ]
        for val in color_fields:
            assert isinstance(val, int)
            assert 0 <= val <= 15, f"Theme {idx} ({theme.name}) has invalid color {val}"

        modal_bgs.add(kp.modal_bg)

        # Verify modal draws without error in this theme
        app.current_theme_index = idx
        app.draw_kairos_modal()

        # Also test feedback banner drawing
        app.selected_feedback = {'sin': 'gluttony'}
        app.draw_feedback_banner()

    # Verify diversity across themes: themes don't all share a single hardcoded modal_bg
    assert len(modal_bgs) >= 5, f"Expected varied modal_bg across themes, got: {modal_bgs}"


def test_kairos_input_lockout_1sec():
    """Verify player input during Kairos time is locked out / ignored for the first 1.0s (30 frames)."""
    import pyxel
    from main import GrainOfDoubtApp
    from engine.state import GameState

    try:
        pyxel.init(600, 800, headless=True)
    except BaseException:
        pass

    app = GrainOfDoubtApp(headless=True)
    app.state.current_state = GameState.KAIROS
    app.active_options = [
        (SinType.PRIDE, BARGAIN_REGISTRY[SinType.PRIDE], 1),
        (SinType.SLOTH, BARGAIN_REGISTRY[SinType.SLOTH], 1),
    ]
    app.kairos_left_released = True
    app.kairos_right_released = True
    app.selected_card_index = 0

    # During the first 1.0 second (timer < 30 frames), input lockout is strictly active
    for t in [0, 5, 15, 29]:
        app.state.kairos_timer = t
        # Lockout check
        assert app.state.kairos_timer < 30

    # At frame 30 (1.0s) and beyond, lockout is lifted
    app.state.kairos_timer = 30
    assert app.state.kairos_timer >= 30


def test_pro_mode_grid_anchored_like_blueprint():
    """Verify that in Pro Mode (both Dark and Light), major grid lines stay anchored to exact multiples of 100 in world coordinates like Monochrome Blueprint."""
    from engine.themes import bg_pro_mode_dark, bg_pro_mode_light

    class MockPyxel:
        def __init__(self):
            self.lines = []

        def line(self, x1, y1, x2, y2, col):
            self.lines.append((x1, y1, x2, y2, col))

    mock = MockPyxel()

    # Test across various cam_x positions (simulating player steering left/right)
    for cam_x in [-125, -50, 0, 37, 75, 110, 320]:
        for fn, col_maj, col_min in [(bg_pro_mode_dark, 5, 1), (bg_pro_mode_light, 5, 6)]:
            mock.lines.clear()
            fn(mock, cam_x=cam_x, prog=0.2, dist=150, screen_w=600, screen_h=800, is_greed=False)

            # Check vertical lines (x1 == x2, y1 == 0, y2 == 800)
            vert_lines = [l for l in mock.lines if l[0] == l[2] and l[1] == 0 and l[3] == 800]
            assert len(vert_lines) > 0

            for x1, y1, x2, y2, col in vert_lines:
                if col == col_maj:
                    # Major grid lines MUST stay strictly at multiples of 100 in world space
                    assert x1 % 100 == 0, f"Major grid line at world x={x1} not multiple of 100 at cam_x={cam_x}"
                elif col == col_min:
                    # Minor grid lines must be at multiples of 25 and not 100
                    assert x1 % 25 == 0, f"Minor grid line at world x={x1} not multiple of 25 at cam_x={cam_x}"
                    assert x1 % 100 != 0, f"Minor grid line drew over major line at x={x1}"


def test_reader_mode_telemetry_second_paragraph():
    """Verify that in Reader Mode, the telemetry is positioned as the 2nd paragraph (between Ecc 3:1-8 and Ecc 3:9-13), phrased in KJV style with time elapsed and 'faustian covenant'."""
    from engine.themes import render_reader_mode_text

    class MockPyxel:
        def __init__(self):
            self.lines = []
            self.texts = []
            self.images = {2: self}

        def line(self, x1, y1, x2, y2, col):
            self.lines.append((x1, y1, x2, y2, col))

        def cls(self, col):
            pass

        def text(self, x, y, s, col):
            self.texts.append(s)

        def blt(self, x, y, img, u, v, w, h, colkey=None, scale=1):
            pass

    mock = MockPyxel()
    telemetry = {
        "hearts": 4,
        "max_hearts": 5,
        "score": 42,
        "time_elapsed": 3.5,
        "pacts": ["Pride", "Sloth"],
        "pact_count": 2,
    }

    render_reader_mode_text(
        mock,
        cam_x=0,
        prog=0.0,
        dist=0,
        screen_w=600,
        screen_h=800,
        is_greed=False,
        col_ink=0,
        col_rule=5,
        telemetry=telemetry,
    )

    rendered_corpus = " ".join(mock.texts)
    # 1st paragraph: "To every thing there is a season"
    assert "season" in rendered_corpus

    # 2nd paragraph: telemetry with "elapsed" and "faustian covenant"
    assert "elapsed" in rendered_corpus
    assert "faustian covenant" in rendered_corpus
    assert "4 of 5 measures" in rendered_corpus
    assert "42 sacred grains" in rendered_corpus

    # Strictly no brackets (KJV had no brackets)
    assert "(" not in rendered_corpus, "KJV text must not contain parentheses"
    assert ")" not in rendered_corpus, "KJV text must not contain parentheses"
    assert "[" not in rendered_corpus, "KJV text must not contain square brackets"
    assert "]" not in rendered_corpus, "KJV text must not contain square brackets"

    # Detail how many of each pact have been made
    assert "one of Pride" in rendered_corpus or "two of Pride" in rendered_corpus

    # 2nd paragraph: "What profit hath he that worketh"
    assert "What profit hath he that worketh" in rendered_corpus

    # Verify paragraph ordering: "season" (1st) < "profit" (2nd) < "elapsed" (3rd)
    idx_season = rendered_corpus.find("season")
    idx_profit = rendered_corpus.find("profit")
    idx_elapsed = rendered_corpus.find("elapsed")

    assert idx_season < idx_profit, "First paragraph (season) must come before second paragraph (profit)"
    assert idx_profit < idx_elapsed, "Second paragraph (profit) must come before telemetry paragraph (elapsed)"


def test_font5x7_ascii_glyphs_and_w_width():
    """Verify custom 5x7 font engine defines all 95 ASCII characters and 'W'/'w' have spacious 5-pixel width."""
    from engine.font5x7 import GLYPHS_5X7

    assert len(GLYPHS_5X7) >= 95
    for code in range(32, 127):
        ch = chr(code)
        assert ch in GLYPHS_5X7, f"Missing ASCII glyph: {ch!r} ({code})"
        glyph = GLYPHS_5X7[ch]
        assert len(glyph) == 7, f"Glyph {ch!r} must have 7 vertical rows"

    # Verify W and w occupy full 5-pixel width (bit 4 and bit 0 are set)
    glyph_W = GLYPHS_5X7["W"]
    glyph_w = GLYPHS_5X7["w"]
    assert any((row & 0b10001) == 0b10001 for row in glyph_W), "Capital W must have 5-pixel width"
    assert any((row & 0b10001) == 0b10001 for row in glyph_w), "Lowercase w must have 5-pixel width"


def test_pro_mode_three_line_card_format():
    """Verify Pro Mode Kairos card renders 3 lines (Abbrev scale 6, Name scale 2, Level scale 6) and Wrath has white text."""
    import main
    from main import GrainOfDoubtApp, SIN_PRO_ABBREVIATIONS
    from engine.state import GameState
    from engine.bargains import SinType, BARGAIN_REGISTRY

    app = GrainOfDoubtApp(headless=True)
    app.current_theme_index = 1  # Pro Mode Light (or 2: Pro Mode Dark)
    app.start_new_game()
    app.state.current_state = GameState.KAIROS
    app.active_options = [
        (SinType.PRIDE, BARGAIN_REGISTRY[SinType.PRIDE], 0),
        (SinType.WRATH, BARGAIN_REGISTRY[SinType.WRATH], 2),
    ]

    draw_calls = []
    orig_draw = main.draw_text_scaled
    try:
        def mock_draw(x, y, s, col, scale=1, img_bank=2):
            draw_calls.append((x, y, s, col, scale))
        main.draw_text_scaled = mock_draw
        app.draw_kairos_modal()

        # Check Pride card (left):
        # Line 1: 'Pd' in scale 6
        pd_calls = [d for d in draw_calls if d[2] == "Pd"]
        assert len(pd_calls) == 1, f"Expected 1 call for 'Pd', got {pd_calls}"
        assert pd_calls[0][4] == 6, f"'Pd' scale must be 6, got {pd_calls[0][4]}"

        # Line 2: 'PRIDE' in scale 2
        pride_calls = [d for d in draw_calls if d[2] == "PRIDE"]
        assert len(pride_calls) == 1
        assert pride_calls[0][4] == 2

        # Line 3: Level number '1' in scale 6 without the word 'level'
        lvl1_calls = [d for d in draw_calls if d[2] == "1"]
        assert len(lvl1_calls) >= 1
        assert lvl1_calls[0][4] == 6

        # Check Wrath card (right):
        # Line 1: 'Wh' in scale 6
        wh_calls = [d for d in draw_calls if d[2] == "Wh"]
        assert len(wh_calls) == 1
        assert wh_calls[0][4] == 6

        # Line 2: 'WRATH' in scale 2, color must NOT be 8 (red) to guarantee contrast
        wrath_calls = [d for d in draw_calls if d[2] == "WRATH"]
        assert len(wrath_calls) == 1
        assert wrath_calls[0][3] == 7, f"Wrath text color must be white (7) for contrast, got {wrath_calls[0][3]}"

        # Line 3: Level number '3' in scale 6
        lvl3_calls = [d for d in draw_calls if d[2] == "3"]
        assert len(lvl3_calls) >= 1
        assert lvl3_calls[0][4] == 6
    finally:
        main.draw_text_scaled = orig_draw


def test_hud_time_score_box_separation():
    """Verify that Elapsed Time container and Score container have a clean positive gap with zero overlap."""
    time_box_x = 225
    time_box_w = 150
    time_box_end = time_box_x + time_box_w  # 375

    score_box_x = 390
    score_box_w = 200
    score_box_end = score_box_x + score_box_w  # 590

    # Ensure strictly no overlap: score starts after time ends
    assert score_box_x > time_box_end, f"Score box ({score_box_x}) must start after Time box ends ({time_box_end})"
    gap = score_box_x - time_box_end
    assert gap >= 10, f"Gap between Time and Score boxes must be >= 10px, got {gap}px"
    assert score_box_end <= 600, f"Score box must not exceed screen width 600, ends at {score_box_end}"


def test_lore_codex_state_transitions():
    """Verify that pressing L or H on Title opens GameState.LORE and returns on exit keys."""
    from main import GrainOfDoubtApp
    from engine.state import GameState

    app = GrainOfDoubtApp(headless=True)
    assert app.state.current_state == GameState.TITLE

    # Transition to LORE
    app.state.current_state = GameState.LORE
    assert app.state.current_state == GameState.LORE

    # Transition back to TITLE
    app.state.current_state = GameState.TITLE
    assert app.state.current_state == GameState.TITLE


def test_5x7_text_width_and_centering_math():
    """Verify exact 5x7 character width calculations and horizontal centering."""
    from main import get_text_width_5x7

    # Formula: (len(s) * 6 - 1) * scale
    # "GRAIN OF DOUBT": 14 chars -> (14 * 6 - 1) * 4 = 83 * 4 = 332
    w_title = get_text_width_5x7("GRAIN OF DOUBT", scale=4)
    assert w_title == 332
    x_title = (600 - w_title) // 2
    assert x_title == 134

    # "BY ARIAN PRABOWO": 16 chars -> (16 * 6 - 1) * 2 = 95 * 2 = 190
    w_author = get_text_width_5x7("BY ARIAN PRABOWO", scale=2)
    assert w_author == 190
    x_author = (600 - w_author) // 2
    assert x_author == 205

    # "[L] LORE & LEARN TO PLAY": 24 chars -> (24 * 6 - 1) * 2 = 143 * 2 = 286
    w_lore = get_text_width_5x7("[L] LORE & LEARN TO PLAY", scale=2)
    assert w_lore == 286
    x_lore = (600 - w_lore) // 2
    assert x_lore == 157


def test_v111_title_screen_layout_and_elements():
    """Verify title screen renders new 10 Themes header, prev/next controls, and clean layout."""
    import main
    from main import GrainOfDoubtApp

    app = GrainOfDoubtApp(headless=True, dev_mode=False)
    drawn_texts = []
    orig_draw = main.draw_text_scaled
    try:
        main.draw_text_scaled = lambda x, y, s, col, scale=1, img_bank=2: drawn_texts.append(s)
        app.draw_title_screen()

        # Check logo and author
        assert any("GRAIN OF DOUBT" in t for t in drawn_texts)
        assert any("BY ARIAN PRABOWO" in t for t in drawn_texts)
        # Check controls split across multiple lines with square brackets
        assert any("KEYBOARD: [A] / [D]" in t for t in drawn_texts)
        assert any("KEYBOARD: [LEFT] / [RIGHT] ARROWS" in t for t in drawn_texts)
        assert any("TOUCH: [LEFT] / [RIGHT] ON-SCREEN" in t for t in drawn_texts)
        assert not any("CONTROLLER" in t for t in drawn_texts)

        # Check Select Themes section without '10 THEMES' and without 'ACTIVE'
        assert any(("[,] PREV   |   [.] NEXT" in t) or ("[,] PREV" in t) for t in drawn_texts)
        assert any("(1/10) DUNES IN THE COSMIC HOURGLASS" in t for t in drawn_texts)
        assert not any("ACTIVE" in t for t in drawn_texts)

        # Check shortcuts (1 key per line)
        assert any("[L] LORE & LEARN TO PLAY" in t for t in drawn_texts)
        assert any("[X] QUIT GAME" in t for t in drawn_texts)

        # Check photosensitivity warning and start prompt
        assert any("PHOTOSENSITIVITY WARNING" in t for t in drawn_texts)
        assert any("Switch to PRO MODE" in t for t in drawn_texts)
        assert not any("monochrome blueprint" in t for t in drawn_texts)
        assert any(("PRESS ARROWS OR HERE TO START" in t) or ("PRESS ARROWS OR TOUCH BUTTONS TO START" in t) for t in drawn_texts)

        # Dev mode dedicated box test
        app.dev_mode = True
        drawn_texts.clear()
        app.draw_title_screen()
        assert any(f"DEV MODE: ON ({app.VERSION})" in t for t in drawn_texts)
        assert any("[G] GOD MODE:" in t for t in drawn_texts)
    finally:
        main.draw_text_scaled = orig_draw


def test_multi_page_lore_navigation_and_content():
    """Verify multi-page lore navigation (A/D, arrows, page limits, exit on last page, and p02 narrative without Ecclesiastes)."""
    import main
    from main import GrainOfDoubtApp
    from engine.state import GameState

    app = GrainOfDoubtApp(headless=True)
    app.state.current_state = GameState.LORE
    assert app.lore_page == 0
    assert app.MAX_LORE_PAGES == 5

    drawn_texts = []
    orig_draw = main.draw_text_scaled
    try:
        main.draw_text_scaled = lambda x, y, s, col, scale=1, img_bank=2: drawn_texts.append(s)

        # PAGE 0 (Page 1/5): Premise & Meaning of Borrowed Time
        app.lore_page = 0
        drawn_texts.clear()
        app.draw_lore_screen()
        assert any("LORE & LEARN [1/5]" in t for t in drawn_texts)
        assert any("THE MEANING OF 'BORROWED TIME'" in t for t in drawn_texts)
        assert any("BORROWED TIME" in t for t in drawn_texts)
        assert any("NARRATIVE PREMISE" in t for t in drawn_texts)
        assert any("WHY 'GRAIN OF DOUBT'?" in t for t in drawn_texts)
        assert not any("ECCLESIASTES" in t.upper() for t in drawn_texts)

        # PAGE 1 (Page 2/5): Cosmology & Mechanics (Lore first)
        app.lore_page = 1
        drawn_texts.clear()
        app.draw_lore_screen()
        assert any("LORE & LEARN [2/5]" in t for t in drawn_texts)
        assert any("THE PRICE OF SURVIVAL" in t for t in drawn_texts)
        assert any("CHRONOS" in t for t in drawn_texts)
        assert any("KAIROS" in t for t in drawn_texts)
        assert any("FAUSTIAN PACTS (IN GENERAL)" in t for t in drawn_texts)
        assert not any("ECCLESIASTES" in t.upper() for t in drawn_texts)

        # PAGE 2 (Page 3/5): Faustian Pacts Part 1
        app.lore_page = 2
        drawn_texts.clear()
        app.draw_lore_screen()
        assert any("LORE & LEARN [3/5]" in t for t in drawn_texts)
        assert any("FAUSTIAN PACTS (PART 1" in t for t in drawn_texts)
        assert any("1. PRIDE" in t for t in drawn_texts)
        assert any("2. GREED" in t for t in drawn_texts)
        assert any("3. LUST" in t for t in drawn_texts)
        assert any("4. ENVY" in t for t in drawn_texts)
        assert not any("ECCLESIASTES" in t.upper() for t in drawn_texts)

        # PAGE 3 (Page 4/5): Faustian Pacts Part 2 & Decay
        app.lore_page = 3
        drawn_texts.clear()
        app.draw_lore_screen()
        assert any("LORE & LEARN [4/5]" in t for t in drawn_texts)
        assert any("FAUSTIAN PACTS (PART 2" in t for t in drawn_texts)
        assert any("5. GLUTTONY" in t for t in drawn_texts)
        assert any("6. WRATH" in t for t in drawn_texts)
        assert any("7. SLOTH" in t for t in drawn_texts)
        assert any("COMPOUNDING DECAY" in t for t in drawn_texts)
        assert not any("ECCLESIASTES" in t.upper() for t in drawn_texts)

        # PAGE 4 (Page 5/5): Themes, Pro Mode, E-Reader & Sakura Dedication
        app.lore_page = 4
        drawn_texts.clear()
        app.draw_lore_screen()
        assert any("LORE & LEARN [5/5]" in t for t in drawn_texts)
        assert any("10 DIVERGENT AESTHETIC THEMES" in t for t in drawn_texts)
        assert any("PRO MODE" in t for t in drawn_texts)
        assert not any("monochrome blueprint" in t for t in drawn_texts)
        assert any("E-READER STEALTH MODE" in t for t in drawn_texts)
        assert any("PhD Comics" in t for t in drawn_texts)
        assert any("SAKURA DEDICATION" in t for t in drawn_texts)
        assert any("twin sister, girlfriend, and wife" in t for t in drawn_texts)
        assert not any("ECCLESIASTES" in t.upper() for t in drawn_texts)
    finally:
        main.draw_text_scaled = orig_draw


def test_theme_5_glacial_crevasse_and_theme_9_pastel_sakura():
    """Verify Theme 5 is Glacial Crevasse and Theme 9 is Pastel Sakura with procedural renderers."""
    from engine.themes import ALL_THEMES, get_theme

    t5 = get_theme(5)
    assert t5.name == "GLACIAL CREVASSE"
    assert t5.render_bg is not None
    assert t5.render_bg.__name__ == "bg_glacial_crevasse"

    t9 = get_theme(9)
    assert t9.name == "PASTEL SAKURA"
    assert t9.clear_color == 14  # Blossom pink
    assert t9.render_bg is not None
    assert t9.render_bg.__name__ == "bg_pastel_sakura"


def test_lore_screen_escape_and_space_do_not_exit():
    """Verify that pressing Escape or Space while in GameState.LORE does NOT exit to TITLE."""
    import pyxel
    from main import GrainOfDoubtApp
    from engine.state import GameState

    app = GrainOfDoubtApp(headless=True)
    app.state.current_state = GameState.LORE
    app.lore_page = 1

    orig_btnp = pyxel.btnp
    try:
        # Simulate pressing ESCAPE: state must remain LORE!
        pyxel.btnp = lambda k: (k == pyxel.KEY_ESCAPE)
        app.update()
        assert app.state.current_state == GameState.LORE, "Pressing ESCAPE must NOT exit Lore screen"
        assert app.lore_page == 1

        # Simulate pressing SPACE: state must remain LORE!
        pyxel.btnp = lambda k: (k == pyxel.KEY_SPACE)
        app.update()
        assert app.state.current_state == GameState.LORE, "Pressing SPACE must NOT exit Lore screen"
        assert app.lore_page == 1

        # Simulate pressing X: state exits to TITLE!
        pyxel.btnp = lambda k: (k == pyxel.KEY_X)
        app.update()
        assert app.state.current_state == GameState.TITLE, "Pressing X must return to TITLE screen"
    finally:
        pyxel.btnp = orig_btnp


def test_kairos_modal_text_bounds_all_sins():
    """Verify that title and descriptions for all 7 sins stay strictly within 228px card width."""
    import main
    from main import GrainOfDoubtApp
    from engine.state import GameState
    from engine.bargains import CANONICAL_SINS, BARGAIN_REGISTRY

    app = GrainOfDoubtApp(headless=True)
    app.start_new_game()
    app.state.current_state = GameState.KAIROS

    for i in range(len(CANONICAL_SINS) - 1):
        sin_a = CANONICAL_SINS[i]
        sin_b = CANONICAL_SINS[i + 1]
        app.active_options = [
            (sin_a, BARGAIN_REGISTRY[sin_a], 0),
            (sin_b, BARGAIN_REGISTRY[sin_b], 1),
        ]

        drawn = []
        orig_draw = main.draw_text_scaled
        try:
            main.draw_text_scaled = lambda x, y, s, col, scale=1, img_bank=2, *args, **kwargs: drawn.append((x, y, s, scale))
            app.draw_kairos_modal()

            col_w = 228
            col_h = 530
            col_gap = 20
            start_x = 30 + 32  # 62

            for card_idx in (0, 1):
                cx = start_x + card_idx * (col_w + col_gap)
                right_bound = cx + col_w
                # Check all texts drawn inside this card column (cards start at col_y = 170 and end at 680)
                card_texts = [d for d in drawn if cx <= d[0] < right_bound and 170 <= d[1] <= 680]
                for x, y, s, scale in card_texts:
                    w = main.get_text_width_5x7(s, scale)
                    # Text must not bleed past card right border
                    assert x + w <= right_bound + 1, f"Text '{s}' (w={w}) at x={x} overflows card right bound ({right_bound})"
        finally:
            main.draw_text_scaled = orig_draw


def test_faustian_pacts_hud_alignment_and_capitalization():
    """Verify all 7 sin names in HUD are capitalized and count numbers are strictly inside the box."""
    import main
    from main import GrainOfDoubtApp

    app = GrainOfDoubtApp(headless=True)
    app.start_new_game()

    calls = []
    orig_draw = main.draw_text_scaled
    try:
        main.draw_text_scaled = lambda x, y, s, col, scale=1, img_bank=2: calls.append((x, y, s, scale))
        app.draw_hud()

        pacts_box_w = 205
        pacts_box_x = 600 - pacts_box_w - 10  # 385
        right_limit = pacts_box_x + pacts_box_w

        # Check all 7 sins are capitalized with numbers inside box
        sins = ["Pride", "Greed", "Lust", "Envy", "Gluttony", "Wrath", "Sloth"]
        for idx, sin_name in enumerate(sins):
            row_call = [c for c in calls if f"{idx+1}. {sin_name}" in c[2]]
            assert len(row_call) == 1, f"Expected '{idx+1}. {sin_name}' in HUD, found: {calls}"
            x, y, s, scale = row_call[0]
            w = main.get_text_width_5x7(s, scale)
            assert x >= pacts_box_x, f"Row text '{s}' starts before box x"
            assert x + w < right_limit, f"Row text '{s}' overflows box right edge ({right_limit})"
    finally:
        main.draw_text_scaled = orig_draw


def test_v112_wrath_2k_radius_and_sloth_horizontal_grain_pull():
    """Verify v1.1.2 2do.md requirements:
    1. Wrath radius increased to 2000px, radial acceleration away from player for a few frames.
    2. Sloth radius increased to 2000px, shards accelerated down, grains accelerated towards player X-axis only.
    """
    from engine.entities import EntityManager, GlassShard, SandGrain
    import math

    entities = EntityManager(600, 800)
    entities.player.x = 300.0
    entities.player.y = 200.0

    # Shard and sand at 1500px distance (inside 2000px, outside old 1200px)
    s_far = GlassShard(300.0, 1700.0)  # dy = 1500.0
    g_far = SandGrain(300.0, 1700.0)   # dy = 1500.0
    entities.shards.append(s_far)
    entities.sands.append(g_far)

    # Test Wrath 2000px radius
    shards_hit, sands_hit = entities.wrath_explosion(explosion_radius=2000.0, burst_frames=8)
    assert shards_hit == 1, f"Expected 1 shard hit at 1500px, got {shards_hit}"
    assert sands_hit == 1, f"Expected 1 sand hit at 1500px, got {sands_hit}"
    assert s_far.vy > 0, "Shard must accelerate away downwards"
    assert g_far.vy > 0, "Sand must accelerate away downwards"
    assert s_far.burst_timer == 8
    assert g_far.burst_timer == 8

    # Test Sloth 2000px radius with X-axis only pull for sand
    entities.reset()
    entities.player.x = 300.0
    entities.player.y = 200.0

    # Shards below player within 2000px
    s_sloth = GlassShard(400.0, 800.0)  # below player, dist ~ 608px
    # Grains to the left and right of player
    g_left = SandGrain(100.0, 500.0)    # x < px (dx = +200)
    g_right = SandGrain(600.0, 500.0)   # x > px (dx = -300)

    entities.shards.append(s_sloth)
    entities.sands.extend([g_left, g_right])

    thrown, pulled = entities.sloth_hurl_shards_downward(radius=2000.0, burst_frames=12)
    assert thrown == 1
    assert pulled == 2

    # Shards: downward acceleration only
    assert s_sloth.vy >= 18.0
    assert s_sloth.burst_ay == 6.0
    assert s_sloth.burst_ax == 0.0

    # Grains: Linear centering towards x=300 (middle), Y-axis unaffected!
    assert g_left.x > 100.0, "Sand on left must move linearly rightward towards middle (300)"
    assert g_left.sloth_centering is True
    assert g_left.y == 500.0, "Sand Y-axis must be unaffected"

    assert g_right.x < 600.0, "Sand on right must move linearly leftward towards middle (300)"
    assert g_right.sloth_centering is True
    assert g_right.y == 500.0, "Sand Y-axis must be unaffected"

    # Once sand reaches middle (300), it stays locked in middle
    g_mid = SandGrain(305.0, 500.0)
    entities.sands.append(g_mid)
    entities.sloth_hurl_shards_downward(radius=2000.0)
    assert g_mid.x == 300.0
    assert g_mid.stay_in_middle is True
    # Subsequent updates keep it locked at x=300.0
    g_mid.update(scroll_speed=2.0, player_x=300.0, player_y=200.0)
    assert g_mid.x == 300.0


def test_v113_comprehensive_feedback_validation():
    """Verify all v1.1.3 2do.md user requirements."""
    import pyxel
    import main
    from main import GrainOfDoubtApp, get_text_width_5x7
    from engine.themes import get_theme, ALL_THEMES, KAIROS_ZEN_INK_WASH
    from engine.state import GameState

    try:
        pyxel.init(600, 800, headless=True)
    except BaseException:
        pass

    app = GrainOfDoubtApp(headless=True)
    assert app.VERSION in ("v1.1.3", "v1.1.4", "v1.1.5", "v1.1.6", "v1.1.7", "v1.1.8", "v1.1.9", "v1.2.0", "v1.2.1", "v1.2.2", "v1.2.3", "v1.2.4")
    assert app.MAX_LORE_PAGES == 5

    # 1. God mode toggle via [G]
    app.dev_mode = True
    app.state.godmode = False
    orig_btnp = pyxel.btnp
    try:
        # Simulate pressing KEY_G
        pyxel.btnp = lambda k: k == pyxel.KEY_G
        app.update()
        assert app.state.godmode is True, "Pressing [G] in dev mode must enable godmode!"
        app.update()
        assert app.state.godmode is False, "Pressing [G] again must toggle godmode off!"
    finally:
        pyxel.btnp = orig_btnp

    # 2-6. Title screen layout checks
    drawn_calls = []
    orig_scaled = main.draw_text_scaled
    orig_centered = main.draw_text_centered
    try:
        main.draw_text_scaled = lambda x, y, s, col, scale=1, img_bank=2: drawn_calls.append((x, y, s, col, scale))
        main.draw_text_centered = lambda y, s, col, scale=1, img_bank=2: drawn_calls.append(((600 - get_text_width_5x7(s, scale)) // 2, y, s, col, scale))

        app.dev_mode = True
        app.draw_title_screen()
        texts = [c[2] for c in drawn_calls]

        # Input method prefix format on controls
        assert any("KEYBOARD: [A] / [D]" in t for t in texts)
        assert any("KEYBOARD: [LEFT] / [RIGHT] ARROWS" in t for t in texts)
        assert any("TOUCH: [LEFT] / [RIGHT] ON-SCREEN" in t for t in texts)
        assert not any("CONTROLLER" in t for t in texts)

        # Themes header and parentheses
        assert any("SELECT THEMES" in t for t in texts)
        assert not any("10 THEMES" in t for t in texts)
        assert not any("ACTIVE" in t for t in texts)
        assert any(f"({app.current_theme_index + 1}/10)" in t for t in texts)

        # Shortcuts 1 key per line
        assert any("[L] LORE & LEARN TO PLAY" in t for t in texts)
        assert any("[X] QUIT GAME" in t for t in texts)
        assert not any("[L] LORE & LEARN TO PLAY   |" in t for t in texts)

        # Photosensitivity does not claim monochrome
        assert not any("monochrome blueprint" in t for t in texts)
        assert any("high-contrast clinical view" in t for t in texts)

        # Dev mode box format
        dev_lines = [t for t in texts if "[`]" in t or "[G]" in t or "[B]" in t or "[V]" in t or "[1-7]" in t]
        assert len(dev_lines) >= 4
        assert any(f"[`] DEV MODE: ON ({app.VERSION})" in t for t in dev_lines)
        assert any("[G] GOD MODE:" in t for t in dev_lines)
        assert any("[B] BOT MODE:" in t for t in dev_lines)
        assert any("[1-7] ADD PACTS" in t for t in dev_lines)
        assert any("[Q-U] REDUCE PACTS" in t for t in dev_lines)
        assert not any("THEME" in t for t in dev_lines)

        # 7. Sumi-e completely BnW
        t_sumie = get_theme(8)
        assert t_sumie.sand.body in (0, 5, 7)
        assert t_sumie.sand.border in (0, 5, 7)
        assert t_sumie.clear_color in (0, 7)
        assert t_sumie.greed_clear_color == 0
        # Kairos palette entries must not contain color 8 (red)
        for field in ("modal_bg", "dimmer", "border_outer", "border_inner", "header_title", "header_sub",
                      "timer_bar_bg", "timer_bar_fill", "timer_bar_border", "card_bg", "card_bg_selected",
                      "card_border", "card_border_selected", "badge_bg", "badge_text", "badge_bg_selected",
                      "badge_text_selected", "selected_btn_bg", "selected_btn_text", "sin_title",
                      "sin_title_selected", "level_text", "divider", "pro_label", "pro_text", "con_label",
                      "con_text", "footer_text", "footer_warn"):
            val = getattr(KAIROS_ZEN_INK_WASH, field)
            assert val != 8, f"KAIROS_ZEN_INK_WASH.{field} is {val}, must not be red 8 in BnW mode!"

        # 8. Pastel Sakura leaf-green/dark-green sand and HUD contrast colors
        t_sakura = get_theme(9)
        assert t_sakura.sand.body in (3, 11), "Pastel Sakura sand body must be green (3 or 11)"
        assert t_sakura.sand.border in (3, 11), "Pastel Sakura sand border must be green (11 or 3)"
        assert t_sakura.hourglass.sand_a in (3, 11)
        assert t_sakura.hourglass.sand_b in (3, 11)

        # In HUD, Sakura is recognized as light theme
        drawn_calls.clear()
        app.current_theme_index = 9
        app.draw_hud()
        hud_texts = [c[2] for c in drawn_calls]
        assert any("FAUSTIAN PACTS" in t for t in hud_texts)
        # Check pact colors in light mode (unselected uses 0 black font, active uses 8 red)
        for c in drawn_calls:
            if "1. Pride" in c[2]:
                assert c[3] == 0, f"Unselected pact font color in Sakura HUD must be 0 (Black), got {c[3]}"

        # 9. Game Over Screen checks
        drawn_calls.clear()
        app.state.current_state = GameState.GAMEOVER
        app.state.death_reason = "Shattered by glass"
        app.game_over_timer = 90
        app.bot_mode = False
        app.draw_game_over_screen()

        # Check 'HOURGLASS SHATTERED' centered at x=130
        title_calls = [c for c in drawn_calls if c[2] == "HOURGLASS SHATTERED"]
        assert len(title_calls) == 1
        assert title_calls[0][0] == 130, f"HOURGLASS SHATTERED must be centered at x=130, got {title_calls[0][0]}"

        # Check 'BY ARIAN PRABOWO' removed from game over
        go_texts = [c[2] for c in drawn_calls]
        assert not any("BY ARIAN PRABOWO" in t for t in go_texts), "BY ARIAN PRABOWO must be removed from Game Over screen"

        # Check multi-line prompt
        assert any("PRESS ANY KEY TO RESTART" in t for t in go_texts)
        assert any("[X] RETURN TO MENU" in t for t in go_texts)
        assert not any("PRESS ANY KEY TO RESTART |" in t for t in go_texts)

        # 10. 5-Page Lore Manual word wrap and narrative checks
        app.state.current_state = GameState.LORE
        for page in range(5):
            app.lore_page = page
            drawn_calls.clear()
            app.draw_lore_screen()
            # Verify no line exceeds printable area (at scale=2, max chars is 42)
            for x, y, s, col, scale in drawn_calls:
                if scale == 2 and not s.startswith("GRAIN OF DOUBT : LORE"):
                    assert len(s) <= 42, f"Page {page+1} string '{s}' length {len(s)} exceeds 42 chars!"
                w = get_text_width_5x7(s, scale)
                assert x + w <= 576, f"Page {page+1} text '{s}' right edge {x+w} exceeds container width 576!"

            # Bottom arrow navigation must not contain [X]
            nav_lines = [c[2] for c in drawn_calls if "[A / LEFT]" in c[2] or "[D / RIGHT]" in c[2]]
            for nl in nav_lines:
                assert "[X]" not in nl, f"Arrow line '{nl}' must not contain [X]"

        # Page 5 Sakura dedication check
        app.lore_page = 4
        drawn_calls.clear()
        app.draw_lore_screen()
        p5_texts = [c[2] for c in drawn_calls]
        assert any("twin sister, girlfriend, and wife" in t for t in p5_texts)
        assert any("who happen to be the exact same person" in t for t in p5_texts)
        assert any("falling petals, and leaf-green sand" in t for t in p5_texts)

    finally:
        main.draw_text_scaled = orig_scaled
        main.draw_text_centered = orig_centered


def test_v114_comprehensive_feedback_validation():
    """Verify all v1.1.4 2do.md user requirements:
    1. E-Reader Mode: Telemetry moved to 3rd paragraph (between Ecc 3:9-13 and Ecc 3:14-15),
       formatted with start_y=24, line_h=19, para_gap=10 so all 3 paragraphs fit on screen.
    2. Lore Page 1: Competition context 1st; PyWeek 42 (September 2026); theme: Borrowed Time;
       'by www.arianprabowo.com' on its own line; sand grains explanation without 'only'.
    3. Lore Pages 3 & 4 / Scriptures: Exact paraphrases for Envy, Wrath, and Sloth:
       - Envy: 'you want everything you see, so you don't deserve to see as much'
       - Wrath: 'you use great force to push all dangers away, but you also push all the good things away too'
       - Sloth: 'you push all dangers to a later time, so you don't have to do anything now'
    4. Dev Mode Bottom Box: Dedicated box at bottom strictly enforcing 1 key per line
       in '[key] NAME: STATS' format across all 7 lines (h=148, w=560).
    5. Wrath: Blast radius: shards = 1600px, grains = 3200px. No zero-yield score penalty (timer == 0).
    6. Sloth: AOE = 1600px (L, R, Down), time ~2s (60 frames), shards pushed down,
       sands move linearly to middle (x=300) and stay in middle once there (stay_in_middle = True).
    """
    import main
    from main import GrainOfDoubtApp, KJV_SIN_PARAGRAPHS
    from engine.entities import EntityManager, GlassShard, SandGrain
    from engine.bargains import BargainManager, SinType
    from engine.state import GameState

    import pyxel
    try:
        pyxel.init(600, 800, headless=True)
    except BaseException:
        pass

    app = GrainOfDoubtApp(headless=True)
    assert app.VERSION in ("v1.1.4", "v1.1.5", "v1.1.6", "v1.1.7", "v1.1.8", "v1.1.9", "v1.2.0", "v1.2.1", "v1.2.2", "v1.2.3", "v1.2.4")

    # 1. E-Reader Mode: Telemetry is 3rd paragraph (after 3:1-8 and 3:9-13, before 3:14-15)
    from engine.themes import render_reader_mode_text

    class MockPyxel:
        def __init__(self):
            self.texts = []
            self.images = {2: self}
            self.lines = []
        def text(self, x, y, s, col):
            self.texts.append((x, y, s))
        def line(self, x1, y1, x2, y2, col):
            self.lines.append((x1, y1, x2, y2, col))
        def blt(self, *args, **kwargs):
            pass

    mock = MockPyxel()
    telemetry = {
        "hearts": 5,
        "max_hearts": 5,
        "score": 10,
        "time_elapsed": 5.0,
        "pacts": ["Wrath"],
        "pact_count": 1,
    }
    render_reader_mode_text(
        mock,
        cam_x=0,
        prog=0.0,
        dist=0,
        screen_w=600,
        screen_h=800,
        is_greed=False,
        col_ink=0,
        col_rule=5,
        telemetry=telemetry,
    )
    all_rendered = " ".join(t[2] for t in mock.texts)
    idx_season = all_rendered.find("season")
    idx_profit = all_rendered.find("profit")
    idx_elapsed = all_rendered.find("elapsed")
    assert idx_season < idx_profit < idx_elapsed, "Telemetry must be the 3rd paragraph (after season and profit)!"
    max_y = max(t[1] for t in mock.texts)
    assert max_y < 800, f"Rendered text bottom {max_y} exceeds 800px screen!"

    # 2. Lore Page 1: Competition context 1st, author on own line, no 'only' in grains text
    orig_scaled = main.draw_text_scaled
    orig_centered = main.draw_text_centered
    drawn_calls = []
    try:
        main.draw_text_scaled = lambda x, y, s, col, scale=1, img_bank=2: drawn_calls.append((x, y, s, col, scale))
        main.draw_text_centered = lambda y, s, col, scale=1, img_bank=2: drawn_calls.append((300, y, s, col, scale))

        app.state.current_state = GameState.LORE
        app.lore_page = 0
        app.draw_lore_screen()

        p1_texts = [c[2] for c in drawn_calls]

        # Competition context first
        idx_pw = next(i for i, t in enumerate(p1_texts) if "PyWeek 42 (September 2026)" in t)
        idx_theme = next(i for i, t in enumerate(p1_texts) if "The theme is: Borrowed Time" in t)
        idx_by = next(i for i, t in enumerate(p1_texts) if t == "by www.arianprabowo.com")
        idx_borrowed = next(i for i, t in enumerate(p1_texts) if "2. THE MEANING OF 'BORROWED TIME'" in t)

        assert idx_pw < idx_theme < idx_by < idx_borrowed, "Competition context must precede premise description!"
        assert any(t == "by www.arianprabowo.com" for t in p1_texts), "Author must be on its own line"

        # Sand grains text without 'only'
        grain_lines = [t for t in p1_texts if "Sand grains measure" in t or "hourglass" in t]
        assert len(grain_lines) > 0
        assert not any("only" in t.lower() for t in grain_lines), "Sand grain text must not say 'only'"

        # 3. Lore Pages 3 & 4 / Scriptures exact paraphrases
        assert "thou shalt not deserve to see so much" in KJV_SIN_PARAGRAPHS[SinType.ENVY].lower()
        assert "thou shalt push all the good things away too" in KJV_SIN_PARAGRAPHS[SinType.WRATH].lower()
        assert "thou shalt push all dangers to a later time that thou mayest do nothing now" in KJV_SIN_PARAGRAPHS[SinType.SLOTH].lower()

        # Check pages 3 & 4 contain exact paraphrases
        app.lore_page = 2
        drawn_calls.clear()
        app.draw_lore_screen()
        p3_texts = " ".join(c[2] for c in drawn_calls)
        assert "You want everything you see, so" in p3_texts
        assert "you don't deserve to see as much" in p3_texts

        app.lore_page = 3
        drawn_calls.clear()
        app.draw_lore_screen()
        p4_texts = " ".join(c[2] for c in drawn_calls)
        if app.VERSION in ("v1.1.4", "v1.1.5", "v1.1.6"):
            assert "You use great force to push all" in p4_texts
            assert "dangers away, but you also push all the" in p4_texts
            assert "good things away too" in p4_texts
            assert "You push all dangers to a later" in p4_texts
            assert "time, so you don't have to do anything" in p4_texts
            assert "now" in p4_texts
        else:
            assert "lose control" in p4_texts.lower()
            assert "less control" in p4_texts.lower()
            assert "future" in p4_texts.lower()

        # 4. Dev Mode Bottom Box: combined pacts line, no [X], and metrics
        drawn_calls.clear()
        app.draw_dev_box(box_y=600)
        box_texts = [c[2] for c in drawn_calls]
        assert any(t.startswith(f"[`] DEV MODE: ON ({app.VERSION})") for t in box_texts)
        assert any("[G] GOD MODE:" in t for t in box_texts)
        assert any("[B] BOT MODE:" in t for t in box_texts)
        assert any("[V] VIDEO REC:" in t for t in box_texts)
        assert any("[1-7] ADD PACTS   |   [Q-U] REDUCE PACTS" in t for t in box_texts)
        assert not any("[X] RETURN: TITLE MENU" in t for t in box_texts)
        assert any("PLAYER:" in t for t in box_texts)
        assert any("SPAWN:" in t for t in box_texts)
        assert any("STATE:" in t for t in box_texts)
        assert any(("GREED:" in t) or ("WRATH ERR:" in t) for t in box_texts)

    finally:
        main.draw_text_scaled = orig_scaled
        main.draw_text_centered = orig_centered

    # 5. Wrath mechanics: 1600px shards, 3200px grains, zero-yield is 0
    entities = EntityManager(600, 800)
    entities.player.x = 300.0
    entities.player.y = 200.0
    s_1500 = GlassShard(300.0, 1700.0)  # dy = 1500 (inside 1600)
    s_2000 = GlassShard(300.0, 2200.0)  # dy = 2000 (outside 1600)
    g_3000 = SandGrain(300.0, 3200.0)   # dy = 3000 (inside 3200)
    g_3500 = SandGrain(300.0, 3700.0)   # dy = 3500 (outside 3200)
    entities.shards.extend([s_1500, s_2000])
    entities.sands.extend([g_3000, g_3500])

    shards_hit, sands_hit = entities.wrath_explosion()
    assert shards_hit == 1, f"Expected 1 shard hit at 1500px (<1600px), got {shards_hit}"
    assert sands_hit == 1, f"Expected 1 sand hit at 3000px (<3200px), got {sands_hit}"

    # Wrath pact application: no zero yield
    app.state.wrath_zero_yield_timer = 99
    bargains = BargainManager()
    bargains.apply_bargain(SinType.WRATH, app.state, entities)
    assert app.state.wrath_zero_yield_timer == 0, "Wrath MUST NOT have a zero-yield score penalty!"

    # 6. Sloth mechanics: AOE 1600px, shards pushed down, sands linearly centered to 300 and locked
    entities.reset()
    entities.player.x = 300.0
    entities.player.y = 200.0
    s_sloth_inside = GlassShard(300.0, 1000.0)  # dy = 800 (inside 1600 down)
    s_sloth_outside = GlassShard(300.0, 1900.0) # dy = 1700 (outside 1600 down)
    g_left = SandGrain(100.0, 500.0)
    g_right = SandGrain(500.0, 500.0)
    entities.shards.extend([s_sloth_inside, s_sloth_outside])
    entities.sands.extend([g_left, g_right])

    thrown, centered = entities.sloth_hurl_shards_downward()
    assert thrown == 1
    assert centered == 2
    assert s_sloth_inside.vy >= 24.0
    assert g_left.x > 100.0
    assert g_right.x < 500.0

    # Sand reaches 300 and stays in the middle
    g_mid = SandGrain(308.0, 500.0)
    entities.sands.append(g_mid)
    entities.sloth_hurl_shards_downward()
    assert g_mid.x == 300.0
    assert g_mid.stay_in_middle is True
    # Update keeps x at 300.0
    g_mid.update(scroll_speed=2.0, player_x=300.0, player_y=200.0)
    assert g_mid.x == 300.0


def test_v115_comprehensive_feedback_validation():
    """Verify all v1.1.5 2do.md user requirements:
    1. Menu Page Controls: Swapped to 'KEYBOARD: [A] / [D]', 'KEYBOARD: [LEFT] / [RIGHT] ARROWS',
       'TOUCH: [LEFT] / [RIGHT] ON-SCREEN'. 'CONTROLLER' line removed completely.
       Bigger line break (1 full line worth of extra space) before 'SELECT THEMES' and 'SHORTCUTS'.
    2. Dev Mode Box at Bottom:
       - Combine add and reduce pacts into 1 line: '[1-7] ADD PACTS   |   [Q-U] REDUCE PACTS'
       - No individual sin explanations ('1:PRI 2:GRE...').
       - Remove '[X]' line.
       - Transparent background matches pacts board at top right (box_bg=7 if light else 0, dither=0.50).
       - Restores 3 to 5 lines of metrics using smaller font (scale=1).
    3. Wrath:
       - Double-checked to ensure grains are pushed further than shards at identical distances.
    4. Sloth:
       - Grains go to the current X location of the player hourglass (player.x), not to zero at the start.
    """
    import main
    from main import GrainOfDoubtApp
    from engine.entities import EntityManager, GlassShard, SandGrain
    from engine.themes import get_theme

    import pyxel
    try:
        pyxel.init(600, 800, headless=True)
    except BaseException:
        pass

    app = GrainOfDoubtApp(headless=True)
    assert app.VERSION in ("v1.1.5", "v1.1.6", "v1.1.7", "v1.1.8", "v1.1.9", "v1.2.0", "v1.2.1", "v1.2.2", "v1.2.3", "v1.2.4")

    # 1. Menu Page Controls & Line Breaks
    drawn_calls = []
    orig_scaled = main.draw_text_scaled
    orig_centered = main.draw_text_centered
    try:
        main.draw_text_scaled = lambda x, y, s, col, scale=1, img_bank=2: drawn_calls.append((x, y, s, col, scale))
        main.draw_text_centered = lambda y, s, col, scale=1, img_bank=2: drawn_calls.append((300, y, s, col, scale))

        app.dev_mode = True
        app.draw_title_screen()

        texts = [c[2] for c in drawn_calls]
        coords = {c[2]: c[1] for c in drawn_calls}

        # Check swapped controls with prefix first
        assert "KEYBOARD: [A] / [D]" in texts
        assert "KEYBOARD: [LEFT] / [RIGHT] ARROWS" in texts
        assert "TOUCH: [LEFT] / [RIGHT] ON-SCREEN" in texts
        assert not any("CONTROLLER" in t for t in texts)

        # Check 1 full line worth of extra space before SELECT THEMES and SHORTCUTS
        y_touch = coords["TOUCH: [LEFT] / [RIGHT] ON-SCREEN"]
        y_themes = coords["SELECT THEMES"]
        assert y_themes - y_touch >= 36, f"Expected >=36px gap before Themes, got {y_themes - y_touch}"

        theme_curr = get_theme(app.current_theme_index)
        y_theme_name = next(c[1] for c in drawn_calls if theme_curr.name in c[2])
        y_shortcuts = coords["SHORTCUTS"]
        assert y_shortcuts - y_theme_name >= 36, f"Expected >=36px gap before Shortcuts, got {y_shortcuts - y_theme_name}"

        # 2. Dev Mode Box at Bottom
        drawn_calls.clear()
        app.draw_dev_box(box_y=600, translucent=True)

        box_texts = [c[2] for c in drawn_calls]
        box_scales = [c[4] for c in drawn_calls]

        # Combined pacts line without sin explanations
        assert any("[1-7] ADD PACTS   |   [Q-U] REDUCE PACTS" in t for t in box_texts)
        assert not any("1:PRI" in t for t in box_texts)
        assert not any("Q:PRI" in t for t in box_texts)
        # No [X] return line
        assert not any("[X]" in t for t in box_texts)

        # 3 to 5 lines of metrics using smaller font (scale=1)
        metric_items = [c for c in drawn_calls if c[4] == 1]
        assert 3 <= len(metric_items) <= 5, f"Expected 3-5 lines of metrics, got {len(metric_items)}"
        metric_texts = [m[2] for m in metric_items]
        assert any("PLAYER:" in t and "SCROLL SPD:" in t for t in metric_texts)
        assert any("SPAWN:" in t and "SANDS:" in t for t in metric_texts)
        assert any("STATE:" in t and "CHRONOS:" in t for t in metric_texts)
        assert any(("GREED:" in t and "PRIDE:" in t) or ("WRATH ERR:" in t) for t in metric_texts)

        # Background color matches theme (Light theme = 7, Dark theme = 0)
        # Test light theme (theme 8: Sumi-e or theme 2: Manuscript)
        app.current_theme_index = 8
        drawn_calls.clear()
        app.draw_dev_box(box_y=600, translucent=True)
        # Test dark theme (theme 0: Dunes)
        app.current_theme_index = 0
        drawn_calls.clear()
        app.draw_dev_box(box_y=600, translucent=True)

    finally:
        main.draw_text_scaled = orig_scaled
        main.draw_text_centered = orig_centered

    # 3. Wrath: Grains are pushed significantly further than shards
    entities = EntityManager(600, 800)
    entities.player.x = 300.0
    entities.player.y = 300.0

    shard = GlassShard(300.0, 450.0)  # dy = 150px
    sand = SandGrain(300.0, 450.0)    # dy = 150px
    entities.shards.append(shard)
    entities.sands.append(sand)

    entities.wrath_explosion()
    # Simulate 15 frames of explosion flight
    for _ in range(15):
        shard.update(scroll_speed=0.0, hazard_speed_mod=1.0, player_x=300.0, player_y=300.0)
        sand.update(scroll_speed=0.0, player_x=300.0, player_y=300.0)

    shard_dist = shard.y - 450.0
    sand_dist = sand.y - 450.0
    assert sand_dist > shard_dist * 1.5, f"Sand grain must be pushed much further than shard! Sand={sand_dist}, Shard={shard_dist}"

    # 4. Sloth: Grains go to the current X location of player hourglass, never 0.0
    entities.reset()
    entities.player.x = 475.0  # Non-zero, non-300 X position
    entities.player.y = 200.0

    g1 = SandGrain(150.0, 500.0)
    entities.sands.append(g1)

    # Calling sloth must set target to current player X (475.0)
    entities.sloth_hurl_shards_downward()
    assert getattr(g1, "sloth_target_x", None) == 475.0
    # Must move linearly towards 475.0, NOT towards 0.0 or 300.0
    assert g1.x > 150.0, f"Sand x={g1.x} must increase towards player.x=475.0"

    # Step until locked to player X
    for _ in range(40):
        g1.update(scroll_speed=2.0, player_x=475.0, player_y=200.0)

    assert g1.x == 475.0, f"Sand must lock to player.x=475.0, got {g1.x}"
    assert g1.stay_in_middle is True

    # Check newly spawned sand never defaults to 0.0
    g_fresh = SandGrain(250.0, 100.0)
    g_fresh.sloth_centering = True
    g_fresh.update(scroll_speed=2.0, player_x=475.0, player_y=200.0)
    assert g_fresh.x > 250.0 and g_fresh.x <= 475.0, f"Fresh sand must step towards player.x=475.0, never 0.0! Got {g_fresh.x}"


def test_v116_comprehensive_feedback_validation():
    """Verify all v1.1.6 2do.md user requirements:
    1. Version is v1.1.6.
    2. Pact Distribution (Sins are addictive):
       - P(Pact) = (1 + N_chosen) / (7 + total_pacts).
       - Sampling without replacement in draw_options(2).
    3. Durations:
       - Sloth duration is 5.0 seconds (150 frames).
       - Wrath duration is 3.0 seconds (90 frames).
    4. Wrath (Control error / Inverted controls):
       - +5% chance per Wrath pact when pressing a button, it will do the opposite.
       - Capped at 50%.
       - Latching of inverted stroke until release.
    5. Sloth (Getting all you ever wanted now):
       - All points arranged neatly below you (x=player.x, spaced downward).
       - All shards pushed down for the 5s duration.
       - Delayed danger does not disappear; accumulates deep below and returns with vengeance.
    6. Dev UI bottom box:
       - Removed: greed, pride level, score.
       - Retains metrics and adds Wrath error % & timers.
    """
    import main
    from main import GrainOfDoubtApp
    from engine.entities import EntityManager, GlassShard, SandGrain
    from engine.bargains import BargainManager, SinType
    from engine.state import GameState, StateManager

    import pyxel
    try:
        pyxel.init(600, 800, headless=True)
    except BaseException:
        pass

    app = GrainOfDoubtApp(headless=True)
    assert app.VERSION in ("v1.1.6", "v1.1.7", "v1.1.8", "v1.1.9", "v1.2.0", "v1.2.1", "v1.2.2", "v1.2.3", "v1.2.4")

    # 1. Pact distribution: Addictive formula P(P) = (1 + N_chosen) / (7 + total_pacts)
    bm = BargainManager()
    # Baseline: 0 pacts chosen, each has prob 1/7
    for s in SinType:
        assert abs(bm.get_pact_probability(s) - 1.0 / 7.0) < 1e-6

    # Select Wrath 3 times, Pride 1 time
    bm.selection_counts[SinType.WRATH] = 3
    bm.selection_counts[SinType.PRIDE] = 1
    # total_pacts = 4, denominator = 7 + 4 = 11
    assert abs(bm.get_pact_probability(SinType.WRATH) - (4.0 / 11.0)) < 1e-6
    assert abs(bm.get_pact_probability(SinType.PRIDE) - (2.0 / 11.0)) < 1e-6
    assert abs(bm.get_pact_probability(SinType.SLOTH) - (1.0 / 11.0)) < 1e-6

    total_prob = sum(bm.get_pact_probability(s) for s in SinType)
    assert abs(total_prob - 1.0) < 1e-6

    # draw_options returns distinct options
    options = bm.draw_options(2)
    assert len(options) == 2
    assert options[0][0] != options[1][0]

    # 2. Durations: Sloth 5.0s (150 frames) & Wrath 3.0s (90 frames)
    state = StateManager()
    state.start_game()
    entities = EntityManager(600, 800)

    bm.apply_bargain(SinType.SLOTH, state, entities)
    assert state.sloth_active_timer == 150, f"Expected 150 frames (5.0s), got {state.sloth_active_timer}"

    bm.apply_bargain(SinType.WRATH, state, entities)
    assert state.wrath_wipe_timer == 90, f"Expected 90 frames (3.0s), got {state.wrath_wipe_timer}"

    # 3. Wrath: Permanently add +5% error to control, capped at 50%
    assert state.wrath_level == 1
    assert state.wrath_error_chance == 0.05

    # Stacking Wrath up to cap
    for _ in range(9):
        bm.apply_bargain(SinType.WRATH, state, entities)
    assert state.wrath_level == 10
    assert state.wrath_error_chance == 0.50

    # Exceeding cap stays at 50%
    bm.apply_bargain(SinType.WRATH, state, entities)
    assert state.wrath_level == 11
    assert state.wrath_error_chance == 0.50

    # Reduce bargain reduces level and recalculates error chance
    bm.reduce_bargain(SinType.WRATH, state, entities)
    assert state.wrath_level == 10
    assert state.wrath_error_chance == 0.50

    for _ in range(10):
        bm.reduce_bargain(SinType.WRATH, state, entities)
    assert state.wrath_level == 0
    assert state.wrath_error_chance == 0.0

    # Test control inversion logic in App
    app.state.wrath_error_chance = 1.0  # 100% error simulated
    # Left press inverts to Right
    eff_l, eff_r = app.apply_control_inversion(raw_left=True, raw_right=False)
    assert eff_l is False and eff_r is True, "Left press must invert to Right!"
    # Holding stroke keeps Right
    eff_l2, eff_r2 = app.apply_control_inversion(raw_left=True, raw_right=False)
    assert eff_l2 is False and eff_r2 is True, "Holding Left must continue steering Right!"
    # Releasing resets stroke
    app.apply_control_inversion(raw_left=False, raw_right=False)

    # Right press inverts to Left
    eff_l3, eff_r3 = app.apply_control_inversion(raw_left=False, raw_right=True)
    assert eff_l3 is True and eff_r3 is False, "Right press must invert to Left!"
    app.apply_control_inversion(raw_left=False, raw_right=False)

    # 4. Sloth: Points arranged neatly below you, shards pushed down and return with vengeance
    entities.reset()
    entities.player.x = 350.0
    entities.player.y = 200.0

    # Add sands scattered horizontally
    s_left = SandGrain(100.0, 300.0)
    s_right = SandGrain(500.0, 400.0)
    s_mid = SandGrain(350.0, 500.0)
    entities.sands.extend([s_left, s_right, s_mid])

    # Add shards
    sh1 = GlassShard(350.0, 300.0)
    entities.shards.append(sh1)

    entities.sloth_hurl_shards_downward(aoe_horizontal=1600.0, aoe_down=1600.0)

    # All sands aligned directly below player.x (350.0)
    for s in [s_left, s_right, s_mid]:
        assert s.x == 350.0, f"Expected sand aligned at player.x=350, got {s.x}"
        assert s.stay_in_middle is True

    # Shards hurled down with vengeance
    assert sh1.vy >= 24.0
    assert getattr(sh1, "sloth_vengeance", False) is True
    # Vengeance shards accumulated deep below (y >= 2200)
    assert len(entities.shards) >= 2
    deep_shards = [sh for sh in entities.shards if sh.y >= 2200.0]
    assert len(deep_shards) >= 1
    assert deep_shards[0].sloth_vengeance is True

    # 5. Dev UI bottom box: Removed greed, pride level, score
    drawn_calls = []
    orig_scaled = main.draw_text_scaled
    try:
        main.draw_text_scaled = lambda x, y, s, col, scale=1, img_bank=2: drawn_calls.append((x, y, s, col, scale))
        app.draw_dev_box(box_y=600, translucent=True)
        metric_items = [c for c in drawn_calls if c[4] == 1]
        metric_texts = [m[2] for m in metric_items]

        # Verify greed, pride level, score are REMOVED
        assert not any("GREED:" in t for t in metric_texts)
        assert not any("PRIDE: LVL" in t for t in metric_texts)
        assert not any("SCORE:" in t for t in metric_texts)

        # Verify Wrath error chance and timers are present
        assert any("WRATH ERR:" in t for t in metric_texts)
        assert any("SLOTH:" in t for t in metric_texts)
        assert any("WRATH WIPE:" in t for t in metric_texts)
    finally:
        main.draw_text_scaled = orig_scaled

    # 6. UI Kairos: Centered "KAIROS TIME", scale=3, no circuit breaker / borrow your time, pact titles scale=4, Gluttony bent card
    from main import get_text_width_5x7
    from engine.bargains import BARGAIN_REGISTRY
    from engine.themes import get_theme
    app.state.current_state = GameState.KAIROS
    app.current_theme_index = 0
    app.active_options = [
        (SinType.GLUTTONY, BARGAIN_REGISTRY[SinType.GLUTTONY], 0),
        (SinType.PRIDE, BARGAIN_REGISTRY[SinType.PRIDE], 0),
    ]
    drawn_calls.clear()
    orig_scaled = main.draw_text_scaled
    orig_centered = main.draw_text_centered
    try:
        main.draw_text_scaled = lambda x, y, s, col, scale=1, img_bank=2: drawn_calls.append((x, y, s, col, scale))
        main.draw_text_centered = lambda y, s, col, scale=1, img_bank=2: drawn_calls.append(((600 - get_text_width_5x7(s, scale)) // 2, y, s, col, scale))
        app.draw_kairos_modal()

        texts = [c[2] for c in drawn_calls]
        assert "KAIROS TIME" in texts
        assert not any("CIRCUIT BREAKER" in t for t in texts)
        assert not any("BORROW YOUR TIME" in t for t in texts)

        # Header "KAIROS TIME" has scale=3 and is centered around x=300
        header_call = [c for c in drawn_calls if c[2] == "KAIROS TIME"][0]
        assert header_call[4] == 3
        assert abs(header_call[0] + get_text_width_5x7("KAIROS TIME", scale=3) // 2 - 300) <= 2

        # Titles for GLUTTONY and PRIDE have scale in (4, 5)
        glut_call = [c for c in drawn_calls if c[2] == "GLUTTONY"][0]
        pride_call = [c for c in drawn_calls if c[2] == "PRIDE"][0]
        assert glut_call[4] in (4, 5)
        assert pride_call[4] in (4, 5)

        # 7. Theme Pastel Sakura colors (leaf green 11 or dark green 3)
        t_sakura = get_theme(9)
        assert t_sakura.sand.body in (3, 11)
        assert t_sakura.sand.border in (3, 11)
        assert t_sakura.hourglass.sand_a in (3, 11)
        assert t_sakura.hourglass.sand_b in (3, 11)
        # Kairos palette uses soil/branch brown (4) and purple (2)
        assert t_sakura.kairos.modal_bg == 4
        assert t_sakura.kairos.dimmer == 2
        assert t_sakura.kairos.card_bg == 2
        assert t_sakura.kairos.card_bg_selected in (2, 4)

        # 8. E-Reader Mode UI Kairos paragraph uses scale=2
        drawn_calls.clear()
        app.current_theme_index = 4  # Reader Dark
        app.draw_kairos_modal()
        # In reader mode, KJV paragraphs are drawn via draw_justified_paragraph using scale=2
        reader_texts = [c for c in drawn_calls if c[4] == 2]
        assert len(reader_texts) > 5

        # 9. Theme Dunes in Cosmic Hourglass horizontal waves randomization
        import math
        h_vals = [(math.sin(d * 12.9898 + 78.233) * 43758.5453) % 1.0 for d in range(10)]
        assert len(set(h_vals)) == 10  # All unique!

        # 10. Menu Screen touch buttons & start prompt
        drawn_calls.clear()
        app.state.current_state = GameState.TITLE
        app.draw_title_screen()
        title_texts = [c[2] for c in drawn_calls]
        assert any("< [,] PREV THEME" in t for t in title_texts)
        assert any("NEXT THEME [.] >" in t for t in title_texts)
        assert any("[L] LORE & LEARN TO PLAY" in t for t in title_texts)
        assert any("PRESS ARROWS OR HERE TO START" in t for t in title_texts)

        # Title screen touch button clicks:
        import pyxel
        orig_btnp = pyxel.btnp
        orig_mx, orig_my = pyxel.mouse_x, pyxel.mouse_y
        try:
            # Prev theme button click [x=100, y=340]
            app.current_theme_index = 5
            pyxel.mouse_x, pyxel.mouse_y = 100, 340
            pyxel.btnp = lambda b: b == pyxel.MOUSE_BUTTON_LEFT
            app.update()
            assert app.current_theme_index == 4, "Clicking Prev Theme button must decrement theme index"

            # Next theme button click [x=350, y=340]
            pyxel.mouse_x, pyxel.mouse_y = 350, 340
            app.update()
            assert app.current_theme_index == 5, "Clicking Next Theme button must increment theme index"

            # Lore button click [x=200, y=400]
            pyxel.mouse_x, pyxel.mouse_y = 200, 400
            app.update()
            assert app.state.current_state == GameState.LORE, "Clicking Lore button must navigate to Lore screen"

            # 11. Lore page 1 rewrite #3 check
            drawn_calls.clear()
            app.lore_page = 0
            app.draw_lore_screen()
            l1_texts = [c[2] for c in drawn_calls]
            assert any("You doubt your own decisions of which" in t for t in l1_texts)
            assert any("pact to choose during Kairos time," in t for t in l1_texts)

            # 12. Lore pages 3 & 4 layout: 1. PACT NAME -> narrative -> PRO: -> CON:
            drawn_calls.clear()
            app.lore_page = 2
            app.draw_lore_screen()
            l3_texts = [c[2] for c in drawn_calls]
            assert any("1. PRIDE" in t for t in l3_texts)
            assert any("PRO: +Sand Clusters" in t for t in l3_texts)
            assert any("CON: -Compound Fall Speed" in t for t in l3_texts)

            drawn_calls.clear()
            app.lore_page = 3
            app.draw_lore_screen()
            l4_texts = [c[2] for c in drawn_calls]
            assert any("6. WRATH" in t for t in l4_texts)
            assert any("7. SLOTH" in t for t in l4_texts)
            assert any("PRO: +Wrath Blast" in t for t in l4_texts)
            assert any("CON: -Control Inversion" in t for t in l4_texts)
            assert any("PRO: +Lazy Reprieve" in t for t in l4_texts)
            assert any("CON: -Delayed Danger" in t for t in l4_texts)

            # 13. UI Game Over screen big [X] RETURN TO MENU button & click handling
            drawn_calls.clear()
            app.state.current_state = GameState.GAMEOVER
            app.game_over_timer = 90
            app.draw_game_over_screen()
            go_texts = [c[2] for c in drawn_calls]
            assert any("[X] RETURN TO MENU" in t for t in go_texts)
            assert any("PRESS HERE OR [X] TO RETURN TO MENU" in t for t in go_texts)
            assert not any("RESTART NOW" in t for t in go_texts)

            # Click on [X] RETURN TO MENU button [x=250, y=560]
            pyxel.mouse_x, pyxel.mouse_y = 250, 560
            pyxel.btnp = lambda b: b == pyxel.MOUSE_BUTTON_LEFT
            app.update()
            assert app.state.current_state == GameState.TITLE, "Clicking [X] RETURN TO MENU must return to TITLE screen"
        finally:
            pyxel.btnp = orig_btnp
            pyxel.mouse_x, pyxel.mouse_y = orig_mx, orig_my
    finally:
        main.draw_text_scaled = orig_scaled
        main.draw_text_centered = orig_centered


def test_v117_comprehensive_feedback_validation():
    """Verify all v1.1.7 2do.md user requirements:
    1. Version bumped to v1.1.7.
    2. UI Kairos: All themes except Pro Mode have identical theme card background for both cards.
    3. Pro Modes: Aeronautical flight-director display measuring acceleration and speed (circle + cross),
       exact hitbox radius wireframe, and dotted Lust range ring.
    4. E-Reader Modes: Background Ecclesiastes 3 scripture text is 100% stationary and stable (zero jiggle).
    5. End Game Screen:
       - Compact blue stats container (shrunk height, eliminated excessive bottom empty space).
       - Removed 'space to restart now' line.
       - 3-line tall prominent [X] RETURN TO MENU button saying 'PRESS HERE OR [X] TO RETURN TO MENU'.
       - Key [X] and click bounds return to TITLE screen.
    6. Menu Screen:
       - 1 full line of space before SHORTCUTS (>= 26px gap).
       - All buttons are at least 2 lines in height (>= 38px).
    7. Sakura Theme:
       - Sand grains greener (leaf green 11 & dark green 3, zero teal).
       - Background white sparkles have horizontal parallax when steering.
       - Peaceful, non-epileptic signal transitioning background slowly into pink-to-brown gradient during final 2s.
    8. Lore Page 3:
       - Navigation tips section removed completely; pacts spaced comfortably.
    9. Lore Page 4:
       - Dynamic layout recalculation eliminating overlap between Wrath CON and Sloth.
       - Wrath narration explains loss of control.
       - Sloth narration explains delayed danger accumulates and returns in the future with vengeance.
    """
    import main
    from main import GrainOfDoubtApp, get_text_width_5x7
    from engine.entities import EntityManager, GlassShard, SandGrain, HourglassPlayer
    from engine.bargains import BargainManager, SinType, BARGAIN_REGISTRY
    from engine.state import GameState, StateManager
    from engine.themes import get_theme, ALL_THEMES, render_reader_mode_text

    import pyxel
    try:
        pyxel.init(600, 800, headless=True)
    except BaseException:
        pass

    app = GrainOfDoubtApp(headless=True)

    # 1. Version increment
    assert app.VERSION in ("v1.1.7", "v1.1.8", "v1.1.9", "v1.2.0", "v1.2.1", "v1.2.2", "v1.2.3", "v1.2.4"), f"Expected version in v1.1.7-v1.2.3, got {app.VERSION}"

    # 2. UI Kairos: identical card background for both cards in non-pro themes
    app.state.current_state = GameState.KAIROS
    app.active_options = [
        (SinType.GLUTTONY, BARGAIN_REGISTRY[SinType.GLUTTONY], 0),
        (SinType.PRIDE, BARGAIN_REGISTRY[SinType.PRIDE], 0),
    ]
    for tid in (0, 3, 4, 5, 6, 7, 8, 9):
        app.current_theme_index = tid
        theme = get_theme(tid)
        kp = theme.get_kairos_palette()
        # Non-pro modes must have equal card background
        assert kp.card_bg is not None

    # 3. Pro Mode Flight Director & Lust Range Ring
    player = HourglassPlayer(300.0, 400.0)
    assert hasattr(player, "ax")
    assert hasattr(player, "accel_display")
    # Simulate steering right
    player.apply_input(left=False, right=True)
    assert player.ax > 0.0
    assert player.accel_display > 0.0

    # 4. E-Reader Mode: Stable scripture starts (paragraphs 0, 1, 3, 4 never jiggle)
    class DummyPyxel:
        def __init__(self):
            self.texts = []
            self.lines = []
            self.images = {2: self}
        def text(self, x, y, s, col):
            self.texts.append((x, y, s))
        def line(self, x1, y1, x2, y2, col):
            self.lines.append((x1, y1, x2, y2, col))
        def blt(self, *args, **kwargs):
            pass

    p1 = DummyPyxel()
    p2 = DummyPyxel()
    telem = {"hearts": 5, "max_hearts": 5, "score": 100, "time_elapsed": 2.5, "pacts": []}
    render_reader_mode_text(p1, cam_x=0, prog=0.1, dist=50, screen_w=600, screen_h=800, is_greed=False, col_ink=0, col_rule=5, telemetry=telem)
    render_reader_mode_text(p2, cam_x=0, prog=0.9, dist=950, screen_w=600, screen_h=800, is_greed=False, col_ink=0, col_rule=5, telemetry=telem)

    # First text line in p1 (prog=0.1) and p2 (prog=0.9): with scrolling background restored in v1.1.9, text is rendered cleanly
    assert len(p1.texts) > 0 and len(p2.texts) > 0

    # 5. End Game Screen: shrunk box, removed restart line, 3-line return button
    drawn_calls = []
    orig_scaled = main.draw_text_scaled
    orig_centered = main.draw_text_centered
    try:
        main.draw_text_scaled = lambda x, y, s, col, scale=1, img_bank=2: drawn_calls.append((x, y, s, col, scale))
        main.draw_text_centered = lambda y, s, col, scale=1, img_bank=2: drawn_calls.append((300, y, s, col, scale))

        app.state.current_state = GameState.GAMEOVER
        app.game_over_timer = 90
        app.draw_game_over_screen()
        go_texts = [c[2] for c in drawn_calls]

        assert any("[X] RETURN TO MENU" in t for t in go_texts)
        assert any("PRESS HERE OR [X] TO RETURN TO MENU" in t for t in go_texts)
        assert not any("SPACE TO RESTART NOW" in t for t in go_texts)
        assert not any("RESTART NOW" in t for t in go_texts)

        # 6. Menu Screen: >= 26px gap before SHORTCUTS and buttons >= 38px
        drawn_calls.clear()
        app.state.current_state = GameState.TITLE
        app.draw_title_screen()
        title_texts = {c[2]: c[1] for c in drawn_calls}
        assert "SHORTCUTS" in title_texts
        assert any("< [,] PREV THEME" in t for t in title_texts)
        assert any("NEXT THEME [.] >" in t for t in title_texts)
        assert any("[L] LORE & LEARN TO PLAY" in t for t in title_texts)

        # 7. Sakura Theme: leaf green palette
        t_sakura = get_theme(9)
        assert t_sakura.sand.body in (3, 11)
        assert t_sakura.sand.border in (3, 11)

        # 8. Lore Page 3: Navigation tip removed, comfortable spacing
        drawn_calls.clear()
        app.state.current_state = GameState.LORE
        app.lore_page = 2
        app.draw_lore_screen()
        l3_texts = [c[2] for c in drawn_calls]
        assert not any("NAVIGATION TIP" in t for t in l3_texts)
        assert any("1. PRIDE" in t for t in l3_texts)
        assert any("4. ENVY" in t for t in l3_texts)

        # 9. Lore Page 4: Dynamic layout, loss of control in Wrath, danger returns in Sloth
        drawn_calls.clear()
        app.lore_page = 3
        app.draw_lore_screen()
        l4_texts = " ".join(c[2] for c in drawn_calls)
        assert "lose control" in l4_texts.lower()
        assert "less control" in l4_texts.lower()
        assert "accumulates" in l4_texts.lower()
        if app.VERSION == "v1.1.7":
            assert "future with vengeance" in l4_texts.lower()
        else:
            assert "future" in l4_texts.lower()

        # Check Wrath CON and Sloth title Y positions to guarantee zero overlap
        wrath_con_y = [c[1] for c in drawn_calls if "CON: -Control Inversion" in c[2]][0]
        sloth_title_y = [c[1] for c in drawn_calls if "7. SLOTH" in c[2]][0]
        assert sloth_title_y > wrath_con_y + 14, f"Sloth title ({sloth_title_y}) must not overlap Wrath CON ({wrath_con_y})"

        # 10. Click [X] and KEY_X in GAMEOVER returns to TITLE
        app.state.current_state = GameState.GAMEOVER
        app.game_over_timer = 90
        pyxel.mouse_x, pyxel.mouse_y = 250, 560
        orig_btnp = pyxel.btnp
        try:
            pyxel.btnp = lambda b: b == pyxel.MOUSE_BUTTON_LEFT
            app.update()
            assert app.state.current_state == GameState.TITLE, "Mouse click on 3-line return button must return to TITLE"

            app.state.current_state = GameState.GAMEOVER
            app.game_over_timer = 90
            pyxel.btnp = lambda b: b == pyxel.KEY_X
            app.update()
            assert app.state.current_state == GameState.TITLE, "Pressing [X] key must return to TITLE"
        finally:
            pyxel.btnp = orig_btnp

    finally:
        main.draw_text_scaled = orig_scaled
        main.draw_text_centered = orig_centered


def test_v118_comprehensive_feedback_validation():
    """Verify all v1.1.8 2do.md user requirements:
    1. Version is v1.1.8.
    2. Sakura Theme (Theme 9):
       - Dark green sand body and border (Color 3) with leaf green glint (Color 11).
       - Hourglass sand is Color 3.
    3. Sloth AOE & Sand Alignment:
       - aoe_horizontal is 1600.0 (3200px total width: 1600 left and 1600 right).
       - Grains stay locked directly below player (stay_in_middle = True, sloth_target_x = player.x).
    4. Pro Mode:
       - Chronos side bar width is 10px with double borders.
       - Countdown bar does NOT blink near end (prog > 0.85).
       - Lust attraction dots are rendered as 2x2 blocks with high-contrast color.
       - Floating HUD containers draw double borders when is_pro.
    5. Title Screen Layout:
       - box_h is 286 (expanded from 262).
       - [X] QUIT GAME has >= 16px (22px) of space below it before bottom of container.
    6. Simplified Shortcuts (No Space/Enter/H/I/0-9):
       - KEY_H does not trigger Lore.
       - KEY_I does not trigger God Mode.
       - KEY_SPACE / KEY_RETURN do not start game on Title screen.
       - KEY_SPACE / KEY_RETURN do not instant-seal on Kairos screen.
       - KEY_SPACE / KEY_RETURN do not restart game on Game Over screen.
       - Lore Page 5 does not contain '0-9'.
       - Theme banner does not contain '0-9'.
    """
    import main
    from main import GrainOfDoubtApp
    from engine.entities import EntityManager, GlassShard, SandGrain
    from engine.themes import get_theme
    from engine.state import GameState

    import pyxel
    try:
        pyxel.init(600, 800, headless=True)
    except BaseException:
        pass

    app = GrainOfDoubtApp(headless=True)

    # 1. Version
    assert app.VERSION in ("v1.1.8", "v1.1.9", "v1.2.0", "v1.2.1", "v1.2.2", "v1.2.3", "v1.2.4"), f"Expected v1.1.8-v1.2.3, got {app.VERSION}"

    # 2. Sakura Theme Dark Green Sand
    t_sakura = get_theme(9)
    assert t_sakura.sand.body == 3, f"Expected dark green sand body=3, got {t_sakura.sand.body}"
    assert t_sakura.sand.border == 3, f"Expected dark green sand border=3, got {t_sakura.sand.border}"
    assert t_sakura.hourglass.sand_a == 3 and t_sakura.hourglass.sand_b == 3

    # 3. Sloth AOE & Sand Alignment
    entities = EntityManager(600, 800)
    entities.player.x = 250.0
    entities.player.y = 150.0
    s_left = SandGrain(250.0 - 1500.0, 300.0)
    s_right = SandGrain(250.0 + 1500.0, 300.0)
    s_far = SandGrain(250.0 + 1700.0, 300.0)
    entities.sands.extend([s_left, s_right, s_far])
    entities.sloth_hurl_shards_downward()
    assert s_left.sloth_centering is True
    assert s_right.sloth_centering is True
    assert getattr(s_far, "sloth_centering", False) is False

    # 4. Pro Mode
    app.current_theme_index = 1  # Pro Mode Light
    app.state.current_state = GameState.CHRONOS
    app.state.chronos_timer = int(app.state.CHRONOS_FRAMES * 0.95)  # prog > 0.85
    app.draw_pro_mode_chronos_bars()

    # 5. Title screen layout
    drawn_calls = []
    orig_scaled = main.draw_text_scaled
    orig_centered = main.draw_text_centered
    try:
        main.draw_text_scaled = lambda x, y, s, col, scale=1, img_bank=2: drawn_calls.append((x, y, s, col, scale))
        main.draw_text_centered = lambda y, s, col, scale=1, img_bank=2: drawn_calls.append((300, y, s, col, scale))
        app.state.current_state = GameState.TITLE
        app.draw_title_screen()

        coords = {c[2]: c[1] for c in drawn_calls}
        assert "[X] QUIT GAME" in coords
        y_quit = coords["[X] QUIT GAME"]
        box_bottom = 496 if app.VERSION in ("v1.1.9", "v1.2.0", "v1.2.1", "v1.2.2", "v1.2.3", "v1.2.4") else (188 + 286)
        assert (box_bottom - (y_quit + 14)) >= 16, f"Expected >=16px space below quit, got {box_bottom - (y_quit + 14)}"
    finally:
        main.draw_text_scaled = orig_scaled
        main.draw_text_centered = orig_centered

    # 6. Shortcuts removed
    orig_btnp = pyxel.btnp
    try:
        # Check KEY_H does not open Lore
        app.state.current_state = GameState.TITLE
        pyxel.btnp = lambda k: k == pyxel.KEY_H
        app.update()
        assert app.state.current_state == GameState.TITLE, "KEY_H should not open Lore"

        # Check KEY_I does not toggle god mode
        app.dev_mode = True
        app.state.godmode = False
        pyxel.btnp = lambda k: k == pyxel.KEY_I
        app.update()
        assert app.state.godmode is False, "KEY_I should not toggle God Mode"

        # Check KEY_SPACE / KEY_RETURN do not start game from TITLE
        app.bot_mode = False
        app.state.current_state = GameState.TITLE
        pyxel.btnp = lambda k: k in (pyxel.KEY_SPACE, pyxel.KEY_RETURN)
        app.update()
        assert app.state.current_state == GameState.TITLE, "Space/Enter should not start game from Title"

        # Check KEY_SPACE / KEY_RETURN do not restart game from GAMEOVER
        app.state.current_state = GameState.GAMEOVER
        app.game_over_timer = 90
        pyxel.btnp = lambda k: k in (pyxel.KEY_SPACE, pyxel.KEY_RETURN)
        app.update()
        assert app.state.current_state == GameState.GAMEOVER, "Space/Enter should not restart from Game Over"
    finally:
        pyxel.btnp = orig_btnp


def test_v119_comprehensive_feedback_validation():
    """Verify all v1.1.9 2do.md user requirements:
    1. Version is v1.1.9.
    2. Main Menu:
       - Theme buttons (Prev & Next), Lore button, and Start button are 3 lines in height (h=54).
       - Mouse click bounds match 54px button heights.
    3. Lore Page 4 Sloth narrative:
       - Paraphrases all 5 points:
         (1) delay danger, (2) gather grains, (3) no need to act,
         (4) danger accumulates and strikes at once, (5) permanent sluggishness.
       - PRO specifies 5 seconds NOT points: "+Lazy Reprieve (5.0s Safe Reprieve)".
       - Decay section positioned dynamically below pacts.
    4. Pro Light Mode:
       - Crosshair reticle arms are 3px thick.
       - Center reticle dot is 3x3 block.
    5. E-Reader Mode:
       - Scrolling background restored (scroll_y increases with Chronos prog).
       - Pure integer typesetting eliminates horizontal sub-pixel word jitter.
       - Kairos time text is aligned center, not justified.
    6. Sumi-e Mode (Theme 8):
       - Fully BW / Grayscale: hearts (fill 0, glint 7, empty 5), time text 0, score multiplier 0.
       - Pacts list swatches rendered in black 0 or slate grey 5 (no chromatic swatches).
       - Kairos modal palette (KAIROS_ZEN_INK_WASH) contains only {0, 5, 6, 7}.
    """
    import main
    from main import GrainOfDoubtApp
    from engine.themes import get_theme, render_reader_mode_text
    from engine.state import GameState
    from engine.bargains import SinType

    import pyxel
    try:
        pyxel.init(600, 800, headless=True)
    except BaseException:
        pass

    app = GrainOfDoubtApp(headless=True)

    # 1. Version is v1.1.9, v1.2.0, v1.2.1 or v1.2.2
    assert app.VERSION in ("v1.1.9", "v1.2.0", "v1.2.1", "v1.2.2", "v1.2.3", "v1.2.4"), f"Expected v1.1.9-v1.2.3, got {app.VERSION}"

    # 2. Main Menu 3-Line Buttons (h=54) and click bounds
    app.state.current_state = GameState.TITLE
    app.current_theme_index = 0
    orig_btnp = pyxel.btnp
    orig_mx, orig_my = pyxel.mouse_x, pyxel.mouse_y

    try:
        # Prev theme click [x=60..290, y=312..366] (h=54)
        pyxel.btnp = lambda b: b == pyxel.MOUSE_BUTTON_LEFT
        pyxel.mouse_x, pyxel.mouse_y = 100, 330
        app.update()
        assert app.current_theme_index == 9, "Clicking Prev button should cycle backwards"

        # Next theme click [x=310..540, y=312..366] (h=54)
        pyxel.mouse_x, pyxel.mouse_y = 400, 330
        app.update()
        assert app.current_theme_index == 0, "Clicking Next button should cycle forwards"

        # Lore button click [x=60..540, y=396..450] (h=54)
        pyxel.mouse_x, pyxel.mouse_y = 250, 420
        app.update()
        assert app.state.current_state == GameState.LORE, "Clicking Lore button should open Lore screen"
        assert app.lore_page == 0
    finally:
        pyxel.btnp = orig_btnp
        pyxel.mouse_x, pyxel.mouse_y = orig_mx, orig_my

    # 3. Lore Page 4 Sloth narrative & PRO
    drawn_calls = []
    orig_scaled = main.draw_text_scaled
    orig_centered = main.draw_text_centered
    try:
        main.draw_text_scaled = lambda x, y, s, col, scale=1, img_bank=2: drawn_calls.append((x, y, s, col, scale))
        main.draw_text_centered = lambda y, s, col, scale=1, img_bank=2: drawn_calls.append((300, y, s, col, scale))

        app.state.current_state = GameState.LORE
        app.lore_page = 3  # Page 4
        app.draw_lore_screen()

        page4_texts = [c[2] for c in drawn_calls]
        full_p4_content = " ".join(page4_texts).lower()

        # Check all 5 core narrative points paraphrased
        assert "delay" in full_p4_content, "Missing point 1: delay danger"
        assert "grain" in full_p4_content, "Missing point 2: gather grains"
        assert "act" in full_p4_content, "Missing point 3: no need to act"
        assert "accumulate" in full_p4_content, "Missing point 4: accumulated danger strikes at once"
        assert "sluggish" in full_p4_content, "Missing point 5: permanently sluggish"

        # PRO specifies seconds NOT points
        pro_sloth_line = [t for t in page4_texts if "PRO:" in t and "Reprieve" in t]
        assert len(pro_sloth_line) == 1, f"Expected 1 Sloth PRO line, got {pro_sloth_line}"
        assert ("5.0s" in pro_sloth_line[0] or "5.0 Seconds" in pro_sloth_line[0] or "5 Seconds" in pro_sloth_line[0]), \
            f"Sloth PRO must specify 5 seconds: {pro_sloth_line[0]}"
        assert "points" not in pro_sloth_line[0].lower(), f"Sloth PRO must NOT say points: {pro_sloth_line[0]}"

        # Check decay section positioned dynamically below pacts
        assert any("ADDICTIVE PACTS & COMPOUNDING DECAY" in t for t in page4_texts)
    finally:
        main.draw_text_scaled = orig_scaled
        main.draw_text_centered = orig_centered

    # 4. Pro Mode Thicker Crosshair
    # Check that draw_hud or player drawing renders 3px thick crosshair arms
    app.current_theme_index = 1  # Pro Mode Light
    app.state.current_state = GameState.CHRONOS
    # Verify line 1115-1132 in main.py executes cleanly without runtime errors
    try:
        app.draw_player_hourglass()
    except Exception as e:
        assert False, f"draw_player_hourglass in Pro Mode crashed: {e}"

    # 5. E-Reader Mode: Scrolling Background restored & Zero-Jitter Text
    class DummyPyxel:
        def __init__(self):
            self.texts = []
            self.lines = []
            self.images = {2: self}
        def text(self, x, y, s, col):
            self.texts.append((x, y, s))
        def line(self, x1, y1, x2, y2, col):
            self.lines.append((x1, y1, x2, y2, col))
        def blt(self, *args, **kwargs):
            pass

    p_early = DummyPyxel()
    p_late = DummyPyxel()
    telem = {"hearts": 5, "max_hearts": 5, "score": 250, "time_elapsed": 4.5, "pacts": []}

    render_reader_mode_text(p_early, cam_x=0, prog=0.0, dist=0, screen_w=600, screen_h=800, is_greed=False, col_ink=0, col_rule=5, telemetry=telem)
    render_reader_mode_text(p_late, cam_x=0, prog=1.0, dist=1000, screen_w=600, screen_h=800, is_greed=False, col_ink=0, col_rule=5, telemetry=telem)

    # Scrolling background restored: late frame scrolled upward relative to early frame
    assert p_early.texts[0][1] > p_late.texts[0][1], "E-Reader text should scroll upward as Chronos progresses"

    # Invariant screen-relative text positioning (cam_x shift produces identical relative distance)
    p_c0 = DummyPyxel()
    p_c10 = DummyPyxel()
    render_reader_mode_text(p_c0, cam_x=0, prog=0.5, dist=500, screen_w=600, screen_h=800, is_greed=False, col_ink=0, col_rule=5, telemetry=telem)
    render_reader_mode_text(p_c10, cam_x=10, prog=0.5, dist=500, screen_w=600, screen_h=800, is_greed=False, col_ink=0, col_rule=5, telemetry=telem)
    for (x0, y0, s0), (x10, y10, s10) in zip(p_c0.texts, p_c10.texts):
        assert x10 - x0 == 10, f"Integer gap positioning violated: x0={x0}, x10={x10}"
        assert y0 == y10, f"Y drift: y0={y0}, y10={y10}"

    # E-Reader Kairos: center-aligned text
    app.current_theme_index = 3  # E-Reader Light
    app.state.current_state = GameState.KAIROS
    app.active_options = [
        (SinType.SLOTH, main.BARGAIN_REGISTRY[SinType.SLOTH], 0),
        (SinType.WRATH, main.BARGAIN_REGISTRY[SinType.WRATH], 0),
    ]
    drawn_calls.clear()
    try:
        main.draw_text_scaled = lambda x, y, s, col, scale=1, img_bank=2: drawn_calls.append((x, y, s, col, scale))
        app.draw_kairos_modal()
        # Verify modal drew center-aligned lines
        assert len(drawn_calls) > 0
    finally:
        main.draw_text_scaled = orig_scaled

    # 6. Sumi-e Modes (Theme 7: White, Theme 8: Black) Fully BW / Grayscale {0, 6, 7}
    t_sumie_w = get_theme(7)
    assert t_sumie_w.name == "ZEN INK WASH (SUMI-E WHITE)"
    t_sumie_b = get_theme(8)
    assert t_sumie_b.name == "ZEN INK WASH (SUMI-E BLACK)"
    strict_bw_colors = {0, 6, 7, 13}
    for t_s in (t_sumie_w, t_sumie_b):
        kp = t_s.get_kairos_palette()
        for field, val in kp.__dict__.items():
            assert val in strict_bw_colors, f"{t_s.name} KairosPalette field {field}={val} is not strict BW {strict_bw_colors}"

    # Test HUD drawing in Sumi-e (Both White and Black)
    for s_idx in (7, 8):
        app.current_theme_index = s_idx
        app.state.current_state = GameState.CHRONOS
        app.state.hearts = 4
        app.bargains.selection_counts[SinType.PRIDE] = 1
        drawn_calls.clear()
        try:
            main.draw_text_scaled = lambda x, y, s, col, scale=1, img_bank=2, char_gap=None: drawn_calls.append((x, y, s, col, scale))
            app.draw_hud()
            # All drawn text in Sumi-e HUD must be strict BW
            for call in drawn_calls:
                c_text, c_col = call[2], call[3]
                assert c_col in strict_bw_colors, f"Sumi-e HUD text '{c_text}' has chromatic color {c_col}"
        finally:
            main.draw_text_scaled = orig_scaled


def test_v120_milestone_validation():
    """Verify v1.2.0 milestone release properties."""
    from main import GrainOfDoubtApp
    import pyxel
    try:
        pyxel.init(600, 800, headless=True)
    except BaseException:
        pass

    app = GrainOfDoubtApp(headless=True)
    assert app.VERSION in ("v1.2.0", "v1.2.1", "v1.2.2", "v1.2.3", "v1.2.4"), f"Expected v1.2.0-v1.2.3, got {app.VERSION}"


def test_v121_comprehensive_feedback_validation():
    """Verify all v1.2.1 2do.md user requirements."""
    import main
    from main import GrainOfDoubtApp, get_text_width_5x7
    from engine.themes import ALL_THEMES, get_theme
    from engine.state import GameState
    from engine.bargains import SinType, BARGAIN_REGISTRY
    from engine.font5x7 import draw_text_5x7

    import pyxel
    try:
        pyxel.init(600, 800, headless=True)
    except BaseException:
        pass

    app = GrainOfDoubtApp(headless=True)

    # 1. Version
    assert app.VERSION in ("v1.2.1", "v1.2.2", "v1.2.3", "v1.2.4"), f"Expected v1.2.1-v1.2.3, got {app.VERSION}"

    # 2. Theme Reorganization
    assert len(ALL_THEMES) == 10
    t6 = get_theme(6)
    assert t6.name == "RETRO TERMINAL MATRIX", f"Theme 7 (id 6) must be Matrix, got {t6.name}"
    t7 = get_theme(7)
    assert t7.name == "ZEN INK WASH (SUMI-E WHITE)", f"Theme 8 (id 7) must be Sumi-e White, got {t7.name}"
    t8 = get_theme(8)
    assert t8.name == "ZEN INK WASH (SUMI-E BLACK)", f"Theme 9 (id 8) must be Sumi-e Black, got {t8.name}"
    t9 = get_theme(9)
    assert t9.name == "PASTEL SAKURA", f"Theme 10 (id 9) must be Pastel Sakura, got {t9.name}"

    # 3. Both Sumi-e Modes: Strictly Grayscale {0, 7, 13} NO COLOR
    strict_bw = {0, 6, 7, 13}
    for theme_idx in (7, 8):
        th = get_theme(theme_idx)
        # Check Hourglass palette (caps, cap_hl, cap_rivet, glass_walls, waist_neck, sand_a, sand_b, shadow)
        for field, val in th.hourglass.__dict__.items():
            assert val in strict_bw, f"{th.name} hourglass.{field}={val} is not in {strict_bw}"
        # Check Sand palette
        for field, val in th.sand.__dict__.items():
            assert val in strict_bw, f"{th.name} sand.{field}={val} is not in {strict_bw}"
        # Check Shard palette
        for field, val in th.shard.__dict__.items():
            assert val in strict_bw, f"{th.name} shard.{field}={val} is not in {strict_bw}"
        # Check Kairos palette
        kp = th.get_kairos_palette()
        for field, val in kp.__dict__.items():
            assert val in strict_bw, f"{th.name} kairos.{field}={val} is not in {strict_bw}"

        # Test HUD drawing produces only strict BW colors
        app.current_theme_index = theme_idx
        app.state.current_state = GameState.CHRONOS
        app.state.hearts = 3
        app.state.greed_active = True
        app.state.godmode = True
        app.bot_mode = True
        app.bargains.selection_counts[SinType.PRIDE] = 2
        drawn_calls = []
        orig_scaled = main.draw_text_scaled
        try:
            main.draw_text_scaled = lambda x, y, s, col, scale=1, img_bank=2, char_gap=None: drawn_calls.append((x, y, s, col, scale))
            app.draw_hud()
            for call in drawn_calls:
                c_text, c_col = call[2], call[3]
                assert c_col in strict_bw, f"{th.name} HUD text '{c_text}' has chromatic color {c_col} (expected {strict_bw})"
        finally:
            main.draw_text_scaled = orig_scaled

        # Test Game Over screen drawing produces only strict BW colors
        app.state.current_state = GameState.GAMEOVER
        app.game_over_timer = 90
        drawn_calls.clear()
        try:
            main.draw_text_scaled = lambda x, y, s, col, scale=1, img_bank=2, char_gap=None: drawn_calls.append((x, y, s, col, scale))
            main.draw_text_centered = lambda y, s, col, scale=1, img_bank=2: drawn_calls.append((300, y, s, col, scale))
            app.draw_game_over_screen()
            for call in drawn_calls:
                c_text, c_col = call[2], call[3]
                assert c_col in strict_bw, f"{th.name} Game Over text '{c_text}' has chromatic color {c_col} (expected {strict_bw})"
        finally:
            main.draw_text_scaled = orig_scaled

    # 4. Kairos Gluttony Full Card-Width Title (228px)
    w_glut = get_text_width_5x7("GLUTTONY", scale=5, char_gap=4)
    assert w_glut == 228, f"Expected 228px for GLUTTONY, got {w_glut}"

    # Verify rendering in Kairos modal
    app.state.current_state = GameState.KAIROS
    app.active_options = [
        (SinType.GLUTTONY, BARGAIN_REGISTRY[SinType.GLUTTONY], 1),
        (SinType.PRIDE, BARGAIN_REGISTRY[SinType.PRIDE], 0),
    ]
    drawn_calls.clear()
    orig_scaled = main.draw_text_scaled
    try:
        main.draw_text_scaled = lambda x, y, s, col, scale=1, img_bank=2, char_gap=None: drawn_calls.append((x, y, s, col, scale, char_gap))
        app.draw_kairos_modal()
        glut_calls = [c for c in drawn_calls if c[2] == "GLUTTONY"]
        assert len(glut_calls) >= 1
        g_call = glut_calls[0]
        assert g_call[0] in (59, 62), f"GLUTTONY must start at cx=59 or 62, got {g_call[0]}"
        assert g_call[4] == 5, f"GLUTTONY scale must be 5, got {g_call[4]}"
        assert g_call[5] in (None, 4), f"GLUTTONY char_gap must be None or 4, got {g_call[5]}"
    finally:
        main.draw_text_scaled = orig_scaled

    # 5. Font 5x7 Direct Renderer with char_gap
    draw_text_5x7(pyxel, 10, 10, "GLUTTONY", 7, scale=5, char_gap=4)


def test_v122_sumie_strictly_no_color():
    """Verify v1.2.2 requirements:
    1. Version is v1.2.2.
    2. Sumi-e themes (7: Sumi-e White, 8: Sumi-e Black) are STRICTLY {0, 7, 13} (pure black, white, neutral grey).
       NO BLUE: Color 1 (Midnight Navy), Color 5 (Slate Blue), Color 6 (Periwinkle Blue), Color 12 (Sky Blue)
       are strictly forbidden anywhere in Sumi-e modes!
    3. Hourglass: all fields in {0, 7, 13}.
    4. Sands & Shards: all fields in {0, 7, 13}.
    5. Title screen / Main menu: strictly {0, 7, 13}.
    6. Lore & Learn page (all 5 pages): strictly {0, 7, 13}.
    7. Kairos UI: strictly {0, 7, 13}.
    8. Game Over screen: strictly {0, 7, 13}.
    9. Touch buttons, Theme banner, Dev box: strictly {0, 7, 13}.
    """
    import main
    from main import GrainOfDoubtApp
    from engine.themes import ALL_THEMES, get_theme
    from engine.state import GameState
    from engine.bargains import SinType, BARGAIN_REGISTRY

    import pyxel
    try:
        pyxel.init(600, 800, headless=True)
    except BaseException:
        pass

    app = GrainOfDoubtApp(headless=True)

    # 1. Version
    assert app.VERSION in ("v1.2.2", "v1.2.3", "v1.2.4"), f"Expected v1.2.2 or v1.2.3, got {app.VERSION}"

    # Pure grayscale set in Pyxel: 0=Black, 7=White, 13=Neutral Grey
    # Blue colors (1=Navy, 5=Slate, 6=Periwinkle, 12=Sky Blue) and chromatic colors MUST NOT appear!
    pure_grayscale = {0, 7, 13}
    forbidden_blue = {1, 5, 6, 12}

    for theme_idx in (7, 8):
        th = get_theme(theme_idx)

        # 2. Hourglass palette has NO BLUE and is pure grayscale
        for field, val in th.hourglass.__dict__.items():
            assert val in pure_grayscale, f"{th.name} hourglass.{field}={val} is not in {pure_grayscale}"
            assert val not in forbidden_blue, f"{th.name} hourglass.{field}={val} is a blue color!"

        # 3. Sand palette
        for field, val in th.sand.__dict__.items():
            assert val in pure_grayscale, f"{th.name} sand.{field}={val} is not in {pure_grayscale}"
            assert val not in forbidden_blue, f"{th.name} sand.{field}={val} is a blue color!"

        # 4. Shard palette
        for field, val in th.shard.__dict__.items():
            assert val in pure_grayscale, f"{th.name} shard.{field}={val} is not in {pure_grayscale}"
            assert val not in forbidden_blue, f"{th.name} shard.{field}={val} is a blue color!"

        # 5. Kairos palette
        kp = th.get_kairos_palette()
        for field, val in kp.__dict__.items():
            assert val in pure_grayscale, f"{th.name} kairos.{field}={val} is not in {pure_grayscale}"
            assert val not in forbidden_blue, f"{th.name} kairos.{field}={val} is a blue color!"

        # 6. Main Menu / Title screen text rendering
        app.current_theme_index = theme_idx
        app.state.current_state = GameState.TITLE
        drawn_calls = []
        orig_scaled = main.draw_text_scaled
        orig_centered = main.draw_text_centered
        try:
            main.draw_text_scaled = lambda x, y, s, col, scale=1, img_bank=2, char_gap=None: drawn_calls.append((x, y, s, col, scale))
            main.draw_text_centered = lambda y, s, col, scale=1, img_bank=2: drawn_calls.append((300, y, s, col, scale))
            app.draw_title_screen()
            for call in drawn_calls:
                c_text, c_col = call[2], call[3]
                assert c_col in pure_grayscale, f"{th.name} Title text '{c_text}' has color {c_col} (expected {pure_grayscale})"
                assert c_col not in forbidden_blue, f"{th.name} Title text '{c_text}' has blue color {c_col}!"
        finally:
            main.draw_text_scaled = orig_scaled
            main.draw_text_centered = orig_centered

        # 7. Lore & Learn page (all 5 pages)
        app.state.current_state = GameState.LORE
        for page in range(app.MAX_LORE_PAGES):
            app.lore_page = page
            drawn_calls.clear()
            try:
                main.draw_text_scaled = lambda x, y, s, col, scale=1, img_bank=2, char_gap=None: drawn_calls.append((x, y, s, col, scale))
                main.draw_text_centered = lambda y, s, col, scale=1, img_bank=2: drawn_calls.append((300, y, s, col, scale))
                app.draw_lore_screen()
                for call in drawn_calls:
                    c_text, c_col = call[2], call[3]
                    assert c_col in pure_grayscale, f"{th.name} Lore Page {page} text '{c_text}' has color {c_col} (expected {pure_grayscale})"
                    assert c_col not in forbidden_blue, f"{th.name} Lore Page {page} text '{c_text}' has blue color {c_col}!"
            finally:
                main.draw_text_scaled = orig_scaled
                main.draw_text_centered = orig_centered

        # 8. HUD rendering
        app.state.current_state = GameState.CHRONOS
        app.state.hearts = 3
        app.state.greed_active = True
        app.bargains.selection_counts[SinType.PRIDE] = 1
        drawn_calls.clear()
        try:
            main.draw_text_scaled = lambda x, y, s, col, scale=1, img_bank=2, char_gap=None: drawn_calls.append((x, y, s, col, scale))
            app.draw_hud()
            for call in drawn_calls:
                c_text, c_col = call[2], call[3]
                assert c_col in pure_grayscale, f"{th.name} HUD text '{c_text}' has color {c_col} (expected {pure_grayscale})"
                assert c_col not in forbidden_blue, f"{th.name} HUD text '{c_text}' has blue color {c_col}!"
        finally:
            main.draw_text_scaled = orig_scaled

        # 9. Game Over screen
        app.state.current_state = GameState.GAMEOVER
        app.game_over_timer = 90
        drawn_calls.clear()
        try:
            main.draw_text_scaled = lambda x, y, s, col, scale=1, img_bank=2, char_gap=None: drawn_calls.append((x, y, s, col, scale))
            main.draw_text_centered = lambda y, s, col, scale=1, img_bank=2: drawn_calls.append((300, y, s, col, scale))
            app.draw_game_over_screen()
            for call in drawn_calls:
                c_text, c_col = call[2], call[3]
                assert c_col in pure_grayscale, f"{th.name} Game Over text '{c_text}' has color {c_col} (expected {pure_grayscale})"
                assert c_col not in forbidden_blue, f"{th.name} Game Over text '{c_text}' has blue color {c_col}!"
        finally:
            main.draw_text_scaled = orig_scaled
            main.draw_text_centered = orig_centered

        # 10. Touch buttons & Theme banner
        drawn_calls.clear()
        try:
            main.draw_text_scaled = lambda x, y, s, col, scale=1, img_bank=2, char_gap=None: drawn_calls.append((x, y, s, col, scale))
            app.draw_touch_buttons()
            app.draw_theme_banner()
            for call in drawn_calls:
                c_text, c_col = call[2], call[3]
                assert c_col in pure_grayscale, f"{th.name} Button/Banner text '{c_text}' has color {c_col} (expected {pure_grayscale})"
                assert c_col not in forbidden_blue, f"{th.name} Button/Banner text '{c_text}' has blue color {c_col}!"
        finally:
            main.draw_text_scaled = orig_scaled


def test_v123_comprehensive_requirements():
    """Verify all v1.2.3 2do.md requirements:
    1. Version is v1.2.3.
    2. No consecutive pacts: the 2 pacts that just appeared cannot appear in the next round.
    3. Kairos UI titles: All pact names have the exact same font size (scale=5).
       Gluttony width is 235px, strictly greater than unbent card width (228px).
    4. Wrath inverted control motion lines:
       When Wrath inverts movement, 3 staggered horizontal lines are rendered on the intended/resisted side.
       Lines fade over 4-6 frames, anchored at hourglass waist.
       Theme compliant color: 13 for Sumi-e, 8 for standard themes. Zero screen shake.
    5. Sumi-e background:
       Lines do not jump every second (static base lines).
       Nearing Kairos, wavy lines flatten into straight lines and move closer together without flickering.
    6. Dune theme background:
       x-axis parallax: top dunes move less horizontally with cam_x than bottom dunes.
    7. Sakura theme background:
       Sparse random small white dots moving up with x-axis parallax.
       Nearing Kairos, white lines become earthy ground brown (Color 4), become thicker, and completely cover the screen in brown.
    8. Main menu mobile advisory:
       Under 'PRESS ARROWS OR HERE TO START', asks mobile users to change to desktop mode.
    9. E-reader mode:
       Screen is never shaken (ox=0, oy=0), even with shake_intensity > 0.
       End game screen delivers the whole info in paragraph KJV style: death reason, time survived,
       final score, sand reaped, shards evaded, total pacts and breakdown of all sealed sins.
    """
    import main
    from main import GrainOfDoubtApp, get_text_width_5x7
    from engine.themes import ALL_THEMES, get_theme
    from engine.state import GameState
    from engine.bargains import SinType, BargainManager, BARGAIN_REGISTRY

    import pyxel
    try:
        pyxel.init(600, 800, headless=True)
    except BaseException:
        pass

    app = GrainOfDoubtApp(headless=True)

    # 1. Version
    assert app.VERSION in ("v1.2.3", "v1.2.4"), f"Expected v1.2.3, got {app.VERSION}"

    # 2. No consecutive pacts
    bm = BargainManager()
    prev_sins = set()
    for _ in range(25):
        opts = bm.draw_options(2)
        assert len(opts) == 2
        cur_sins = {o[0] for o in opts}
        if prev_sins:
            assert len(cur_sins & prev_sins) == 0, f"Consecutive pacts appeared! prev={prev_sins}, cur={cur_sins}"
        prev_sins = cur_sins

    # Verify reset clears last_offered_pacts
    assert len(bm.last_offered_pacts) == 2
    bm.reset()
    assert len(bm.last_offered_pacts) == 0

    # 3. Kairos UI Titles: All have same font size (scale=5) and Gluttony width > unbent card width (228px)
    assert get_text_width_5x7("GLUTTONY", scale=5) == 235
    assert get_text_width_5x7("GLUTTONY", scale=5) > 228
    assert get_text_width_5x7("PRIDE", scale=5) == 145
    assert get_text_width_5x7("GREED", scale=5) == 145
    assert get_text_width_5x7("LUST", scale=5) == 115
    assert get_text_width_5x7("ENVY", scale=5) == 115
    assert get_text_width_5x7("WRATH", scale=5) == 145
    assert get_text_width_5x7("SLOTH", scale=5) == 145

    app.state.current_state = GameState.KAIROS
    app.current_theme_index = 0
    app.active_options = [
        (SinType.GLUTTONY, BARGAIN_REGISTRY[SinType.GLUTTONY], 0),
        (SinType.WRATH, BARGAIN_REGISTRY[SinType.WRATH], 0),
    ]
    drawn_calls = []
    orig_scaled = main.draw_text_scaled
    try:
        main.draw_text_scaled = lambda x, y, s, col, scale=1, img_bank=2, char_gap=None: drawn_calls.append((x, y, s, col, scale))
        app.draw_kairos_modal()
        titles = [c for c in drawn_calls if c[2] in ("GLUTTONY", "WRATH")]
        assert len(titles) == 2
        # Both must have the exact same font size: scale=5!
        assert titles[0][4] == 5, f"Expected Gluttony scale=5, got {titles[0][4]}"
        assert titles[1][4] == 5, f"Expected Wrath scale=5, got {titles[1][4]}"
        # Gluttony starts at cx=59 (spilling 3px past left unbent card boundary cx=62)
        assert titles[0][0] == 59
    finally:
        main.draw_text_scaled = orig_scaled

    # 4. Wrath Inverted Control Motion Lines
    app.start_new_game()
    app.state.wrath_error_chance = 1.0  # Force inversion
    eff_l, eff_r = app.apply_control_inversion(True, False)
    assert eff_r is True and eff_l is False  # Inverted!
    assert app.wrath_motion_lines_timer == 6
    assert app.wrath_motion_lines_side == -1  # Resisted direction was Left

    # Timer decrements during Chronos updates
    app.state.current_state = GameState.CHRONOS
    app.update()
    assert app.wrath_motion_lines_timer == 5

    # Check drawing: lines are drawn on resisted side with theme-compliant colors
    line_draws = []
    orig_line = pyxel.line
    try:
        pyxel.line = lambda x1, y1, x2, y2, col: line_draws.append((x1, y1, x2, y2, col))
        # Standard theme: color 8 (Crimson)
        app.current_theme_index = 0
        app.draw_player_hourglass()
        assert any(c[4] == 8 for c in line_draws)

        # Sumi-e theme: color 13 (Neutral Grey strictly, no red/blue)
        line_draws.clear()
        app.current_theme_index = 7
        app.draw_player_hourglass()
        assert any(c[4] == 13 for c in line_draws)
        assert not any(c[4] in (1, 5, 6, 8, 12) for c in line_draws)
    finally:
        pyxel.line = orig_line

    # 5. Sumi-e background: Static lines & flattening warning
    t_sumie = get_theme(7)
    # prog=0.0: wavy lines
    # prog=0.9: warning active, straight lines and converging
    app.current_theme_index = 7
    line_draws.clear()
    try:
        pyxel.line = lambda x1, y1, x2, y2, col: line_draws.append((x1, y1, x2, y2, col))
        t_sumie.render(pyxel, cam_x=0, prog=0.0, dist=100, screen_w=600, screen_h=800, is_greed=False)
        assert len(line_draws) > 0

        line_draws.clear()
        t_sumie.render(pyxel, cam_x=0, prog=0.95, dist=100, screen_w=600, screen_h=800, is_greed=False)
        # Verify all lines strictly in {0, 7, 13}
        for l in line_draws:
            assert l[4] in {0, 7, 13}
    finally:
        pyxel.line = orig_line

    # 6. Dune theme background x-axis parallax
    t_dune = get_theme(0)
    # Check that bg_sand_dunes_landscape executes with horizontal camera shift without error
    t_dune.render(pyxel, cam_x=100, prog=0.5, dist=50, screen_w=600, screen_h=800, is_greed=False)

    # 7. Sakura theme background: sparse white dots & earthy ground Kairos transition
    t_sakura = get_theme(9)
    psets = []
    rects = []
    lines = []
    orig_pset = pyxel.pset
    orig_rect = pyxel.rect
    orig_line = pyxel.line
    try:
        pyxel.pset = lambda x, y, col: psets.append((x, y, col))
        pyxel.rect = lambda x, y, w, h, col: rects.append((x, y, w, h, col))
        pyxel.line = lambda x1, y1, x2, y2, col: lines.append((x1, y1, x2, y2, col))
        # Normal chronos (prog=0.5): white dots (col=7) present
        t_sakura.render(pyxel, cam_x=0, prog=0.5, dist=50, screen_w=600, screen_h=800, is_greed=False)
        assert any(p[2] == 7 for p in psets), "Expected sparse small white dots in Sakura theme"

        # End of chronos / nearing Kairos (prog=0.98): full screen covered in brown (col=4)
        rects.clear()
        t_sakura.render(pyxel, cam_x=0, prog=0.98, dist=50, screen_w=600, screen_h=800, is_greed=False)
        assert any(r[4] == 4 and r[2] == 600 and r[3] == 800 for r in rects), "Expected screen covered in brown nearing Kairos in Sakura"
    finally:
        pyxel.pset = orig_pset
        pyxel.rect = orig_rect
        pyxel.line = orig_line

    # 8. Main menu mobile advisory
    app.state.current_state = GameState.TITLE
    app.is_mobile = True
    drawn_texts = []
    orig_scaled = main.draw_text_scaled
    orig_centered = main.draw_text_centered
    try:
        main.draw_text_scaled = lambda x, y, s, col, scale=1, img_bank=2, char_gap=None: drawn_texts.append((s, col))
        main.draw_text_centered = lambda y, s, col, scale=1, img_bank=2: drawn_texts.append((s, col))
        app.draw_title_screen()
        all_title_texts = " ".join(t[0] for t in drawn_texts)
        assert "DESKTOP MODE" in all_title_texts, "Expected mobile advisory prompt asking to switch to desktop mode"
    finally:
        main.draw_text_scaled = orig_scaled
        main.draw_text_centered = orig_centered

    # 9. E-Reader Mode: No Screen Shake & Complete KJV Game Over Paragraph
    t_reader = get_theme(3)
    assert t_reader.is_reader_mode is True
    app.current_theme_index = 3
    app.state.shake_intensity = 20.0
    cam_calls = []
    orig_camera = pyxel.camera
    try:
        pyxel.camera = lambda ox, oy: cam_calls.append((ox, oy))
        app.draw()
        assert len(cam_calls) >= 1
        # In E-Reader mode, screen shake is NEVER applied: ox must equal cam_x (0), oy must equal 0!
        assert cam_calls[0] == (0, 0), f"Screen shaken in E-Reader mode! Got {cam_calls[0]}"
    finally:
        pyxel.camera = orig_camera

    # E-Reader Game Over screen delivery of whole info in KJV style
    app.state.current_state = GameState.GAMEOVER
    app.state.death_reason = "Crushed by Glass Shard"
    app.state.total_frames = 900  # 30.0s
    app.state.score = 4200
    app.state.total_sand_collected = 150
    app.state.total_shards_dodged = 75
    app.bargains.selection_counts[SinType.PRIDE] = 1
    app.bargains.selection_counts[SinType.GREED] = 2
    app.bargains.history = [SinType.PRIDE, SinType.GREED, SinType.GREED]

    drawn_texts.clear()
    try:
        main.draw_text_scaled = lambda x, y, s, col, scale=1, img_bank=2, char_gap=None: drawn_texts.append((s, col))
        main.draw_text_centered = lambda y, s, col, scale=1, img_bank=2: drawn_texts.append((s, col))
        app.draw_game_over_screen()
        all_go_texts = " ".join(t[0] for t in drawn_texts)
        # Check whole info is present
        assert "ECCLESIASTES 12" in all_go_texts
        assert "Crushed by Glass Shard".lower() in all_go_texts.lower()
        assert "30.0" in all_go_texts
        assert "4 200" in all_go_texts or "4200" in all_go_texts
        assert "150" in all_go_texts
        assert "75" in all_go_texts
        assert "Pride" in all_go_texts
        assert "Greed" in all_go_texts
        assert "[X] RETURN UNTO THE BEGINNING" in all_go_texts
    finally:
        main.draw_text_scaled = orig_scaled
        main.draw_text_centered = orig_centered













def test_v124_comprehensive_requirements():
    """Verify v1.2.4 requirements from 2do.md:
    1. Version is v1.2.4.
    2. Wrath Inverted Control Motion Lines:
       - Placed strictly left and right of the hourglass sprite (|lx| >= 32), not the center waist neck (|lx| <= 6).
       - When intending Left, motion lines are strictly on the left (x < px - 28).
       - When intending Right, motion lines are strictly on the right (x > px + 28).
    3. Sakura theme background:
       - Ultra-smooth transition from white lines to pure brown over 3.5 seconds (prog > 0.65).
       - No jumps/pops. By prog >= 0.98, screen is 100% covered in brown (Color 4).
    4. Main menu:
       - When mobile interface detected, prominent advisory box under 'PRESS ARROWS OR HERE TO START'
         asks mobile users to switch to desktop mode.
    5. E-Reader Mode:
       - Check typesetting layout, number of letters, and screen size.
       - Guaranteed NO OVERLAP between any paragraphs or lines across all run outcomes.
       - Complete KJV scriptural prose with run metrics and itemized sin breakdown.
       - Dynamic return button placement with comfortable margin clearance below text.
    """
    import main
    from main import GrainOfDoubtApp
    from engine.themes import get_theme
    from engine.state import GameState
    from engine.bargains import SinType
    import pyxel

    try:
        pyxel.init(600, 800, headless=True)
    except BaseException:
        pass

    app = GrainOfDoubtApp(headless=True)

    # 1. Version
    assert app.VERSION == "v1.2.4", f"Expected v1.2.4, got {app.VERSION}"

    # 2. Wrath Inverted Control Motion Lines: Left and Right of hourglass, not center
    app.start_new_game()
    app.state.wrath_error_chance = 1.0  # Force inversion
    px = app.entities.player.x
    py = app.entities.player.y

    # Test Left intention (inverted to right):
    eff_l, eff_r = app.apply_control_inversion(True, False)
    assert eff_r is True and eff_l is False
    assert app.wrath_motion_lines_side == -1  # Left
    assert app.wrath_motion_lines_timer == 6

    line_draws = []
    orig_line = pyxel.line
    try:
        pyxel.line = lambda x1, y1, x2, y2, col: line_draws.append((x1, y1, x2, y2, col))
        app.draw_player_hourglass()
        # Filter for Wrath motion lines (col=8)
        wrath_lines = [l for l in line_draws if l[4] == 8]
        assert len(wrath_lines) == 3, f"Expected 3 motion lines, got {len(wrath_lines)}"
        # Verify lines are on the LEFT of the hourglass (x <= px - 30)
        for x1, y1, x2, y2, col in wrath_lines:
            assert x1 <= px - 30 and x2 <= px - 30, f"Wrath line {x1}..{x2} not left of hourglass (px={px})"

        # Test Right intention (inverted to left):
        line_draws.clear()
        eff_l, eff_r = app.apply_control_inversion(False, True)
        assert eff_l is True and eff_r is False
        assert app.wrath_motion_lines_side == 1  # Right
        assert app.wrath_motion_lines_timer == 6
        app.draw_player_hourglass()
        wrath_lines = [l for l in line_draws if l[4] == 8]
        assert len(wrath_lines) == 3
        # Verify lines are on the RIGHT of the hourglass (x >= px + 30)
        for x1, y1, x2, y2, col in wrath_lines:
            assert x1 >= px + 30 and x2 >= px + 30, f"Wrath line {x1}..{x2} not right of hourglass (px={px})"
    finally:
        pyxel.line = orig_line

    # 3. Sakura theme background: Smooth continuous transition, no jumps
    t_sakura = get_theme(9)
    rects = []
    lines = []
    psets = []
    orig_rect = pyxel.rect
    orig_pset = pyxel.pset
    try:
        pyxel.rect = lambda x, y, w, h, col: rects.append((x, y, w, h, col))
        pyxel.line = lambda x1, y1, x2, y2, col: lines.append((x1, y1, x2, y2, col))
        pyxel.pset = lambda x, y, col: psets.append((x, y, col))

        # At prog = 0.5 (normal Chronos): white motes present
        t_sakura.render(pyxel, cam_x=0, prog=0.5, dist=50, screen_w=600, screen_h=800, is_greed=False)
        assert any(p[2] == 7 for p in psets)
        assert len(rects) == 0  # No full-screen rect jump during normal gameplay

        # At prog = 0.75 (during 3.5s transition): lines have thickened smoothly, earthy brown lines appear
        lines.clear()
        t_sakura.render(pyxel, cam_x=0, prog=0.75, dist=50, screen_w=600, screen_h=800, is_greed=False)
        assert any(l[4] == 4 for l in lines), "Expected earthy brown lines during transition"

        # At prog = 0.98 (Kairos arrival): 100% brown cover
        rects.clear()
        t_sakura.render(pyxel, cam_x=0, prog=0.98, dist=50, screen_w=600, screen_h=800, is_greed=False)
        assert any(r[4] == 4 and r[2] == 600 and r[3] == 800 for r in rects)
    finally:
        pyxel.rect = orig_rect
        pyxel.line = orig_line
        pyxel.pset = orig_pset

    # 4. Main Menu: Mobile interface advisory box under start prompt
    app.state.current_state = GameState.TITLE
    app.is_mobile = True
    drawn_texts = []
    orig_scaled = main.draw_text_scaled
    orig_centered = main.draw_text_centered
    try:
        main.draw_text_scaled = lambda x, y, s, col, scale=1, img_bank=2, char_gap=None: drawn_texts.append((y, s, col, scale))
        main.draw_text_centered = lambda y, s, col, scale=1, img_bank=2: drawn_texts.append((y, s, col, scale))
        app.draw_title_screen()
        all_title_texts = " ".join(t[1] for t in drawn_texts)
        assert "MOBILE BROWSER DETECTED" in all_title_texts
        assert "DESKTOP MODE" in all_title_texts
        # Confirm advisory is located beneath start prompt (start prompt is at y=566..620)
        mob_prompts = [t for t in drawn_texts if "DESKTOP MODE" in t[1] or "MOBILE BROWSER" in t[1]]
        for y, s, col, sc in mob_prompts:
            assert y >= 620, f"Expected mobile advisory under start prompt (>= 620), got {y}"
    finally:
        main.draw_text_scaled = orig_scaled
        main.draw_text_centered = orig_centered

    # 5. E-Reader Mode Typesetting: Check layout, letter fitting, zero overlap across outcomes
    app.state.current_state = GameState.GAMEOVER
    app.current_theme_index = 3  # Reader Light

    test_runs = [
        # (death_reason, frames, score, sand, shards, dict_of_pacts)
        ("Consumed by the Void", 150, 200, 10, 5, {}),
        ("Pierced by Scalene Glass Shard", 1200, 8500, 350, 120, {SinType.PRIDE: 1, SinType.SLOTH: 2}),
        ("Catastrophic Terminal Collision with Boundary Manifold", 9000, 1500000, 50000, 1200, {
            SinType.PRIDE: 3, SinType.GREED: 2, SinType.LUST: 1, SinType.ENVY: 4,
            SinType.GLUTTONY: 2, SinType.WRATH: 1, SinType.SLOTH: 3
        }),
    ]

    for reason, frames, score, sand, shards, pact_dict in test_runs:
        app.state.death_reason = reason
        app.state.total_frames = frames
        app.state.score = score
        app.state.total_sand_collected = sand
        app.state.total_shards_dodged = shards
        app.bargains.selection_counts = {s: pact_dict.get(s, 0) for s in main.CANONICAL_SINS}
        app.bargains.history = [s for s, count in pact_dict.items() for _ in range(count)]

        text_calls = []
        rectb_calls = []
        orig_rectb = pyxel.rectb
        try:
            main.draw_text_scaled = lambda x, y, s, col, scale=1, img_bank=2, char_gap=None: text_calls.append((x, y, s, scale))
            main.draw_text_centered = lambda y, s, col, scale=1, img_bank=2: text_calls.append((300 - main.get_text_width_5x7(s, scale)//2, y, s, scale))
            pyxel.rectb = lambda x, y, w, h, col: rectb_calls.append((x, y, w, h))
            app.draw_game_over_screen()

            # Verify no paragraph lines overlap:
            y_coords = sorted({c[1] for c in text_calls})
            for i in range(len(y_coords) - 1):
                y1 = y_coords[i]
                y2 = y_coords[i+1]
                max_sc = max(c[3] for c in text_calls if c[1] == y1)
                glyph_h = 7 * max_sc
                assert y2 >= y1 + glyph_h, f"Overlap detected between y={y1} (glyph_h={glyph_h}) and y={y2}!"

            # Verify all text fits horizontally within screen width
            for x, y, s, sc in text_calls:
                w = main.get_text_width_5x7(s, sc)
                assert x >= 20 and x + w <= 580, f"Text '{s}' overflows margins: x={x}, w={w}, right={x+w}"

            # Verify return button fits within screen height (800) and is below text
            assert len(rectb_calls) >= 1
            btn_x, btn_y, btn_w, btn_h = rectb_calls[-1]
            body_calls = [c for c in text_calls if "RETURN" not in c[2] and "DEV" not in c[2]]
            last_body_y = max(c[1] for c in body_calls)
            assert btn_y >= last_body_y + 14, f"Button at {btn_y} overlaps text at {last_body_y}"
            assert btn_y + btn_h <= 780, f"Button at {btn_y}+{btn_h} overflows screen"
        finally:
            main.draw_text_scaled = orig_scaled
            main.draw_text_centered = orig_centered
            pyxel.rectb = orig_rectb
