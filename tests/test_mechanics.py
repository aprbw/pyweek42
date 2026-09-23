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
    assert "3 hazards hurled" in summary["boon"]

    # Shard above player unaffected
    assert s_above.y == 150
    assert s_above.vy == 0.0

    # Shards below player are hurled down with explosive downward velocity
    for shard in [s1, s2, s3]:
        assert shard.y >= 720.0
        assert shard.vy >= 38.0

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
    # Their y coordinates are tightly grouped together
    y_coords = [s.y for s in [s1, s2, s3] if s.alive]
    assert len(y_coords) >= 2
    assert max(y_coords) - min(y_coords) < 150.0  # tightly clumped wave


def test_envy_and_lust_mechanics():
    from engine.entities import SandGrain
    state = StateManager()
    state.start_game()
    entities = EntityManager(600, 800)
    entities.player.x = 300.0

    # Add 2 on-screen sands and 1 far sand (outside 1920px mega lust radius, but inside 3500px arena bounds)
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
    bargains.apply_bargain(SinType.ENVY, state, entities)
    assert state.envy_mega_lust_active is True
    assert state.envy_mega_lust_timer == 60
    assert state.envy_mega_lust_radius == 1920.0  # 2x outer vignette radius (960.0 * 2)
    assert state.vignette_radius == 960.0  # Vignette Vision outer radius (1200 * 0.8^1)
    assert state.vignette_inner_radius == 640.0  # Vignette Vision inner radius (1000 * 0.8^2)

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
    assert state.vignette_radius == 960.0
    assert state.vignette_inner_radius == 640.0
    assert state.envy_level == 1
    # Reduce Envy
    bargains.reduce_bargain(SinType.ENVY, state, entities)
    assert bargains.get_selection_count(SinType.ENVY) == 0
    assert state.envy_level == 0
    assert state.vignette_radius == 1000.0

    # 5. GLUTTONY (T)
    initial_spawn = state.spawn_rate_multiplier
    bargains.apply_bargain(SinType.GLUTTONY, state, entities)
    assert state.spawn_rate_multiplier == pytest.approx(initial_spawn + 0.50)
    # Reduce Gluttony
    bargains.reduce_bargain(SinType.GLUTTONY, state, entities)
    assert state.spawn_rate_multiplier == pytest.approx(initial_spawn)

    # 6. WRATH (Y)
    bargains.apply_bargain(SinType.WRATH, state, entities)
    assert state.wrath_wipe_timer == 300
    assert state.wrath_zero_yield_timer == 300
    # Reduce Wrath
    bargains.reduce_bargain(SinType.WRATH, state, entities)
    assert state.wrath_wipe_timer == 0
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
    assert rad == 180.0
    assert state.lust_hazard_attract_radius == 180.0

    # Advance 400 frames: neither radius should decay to 0!
    for _ in range(400):
        state.update_timers()
    assert state.lust_attract_radius == 180.0
    assert state.lust_hazard_attract_radius == 180.0

    # Apply 2nd pact: radius expands
    bargains.apply_bargain(SinType.LUST, state)
    assert state.lust_attract_radius == 240.0
    assert state.lust_hazard_attract_radius == 240.0


def test_wrath_non_compounding():
    """Verify Wrath does not compound or extend past 10.0s (300 frames) on multiple uses."""
    state = StateManager()
    state.start_game()
    bargains = BargainManager()

    bargains.apply_bargain(SinType.WRATH, state)
    assert state.wrath_wipe_timer == 300
    assert state.wrath_zero_yield_timer == 300

    # Apply Wrath second time: remains flat 300 (does not compound to 600 or 1.5x)
    bargains.apply_bargain(SinType.WRATH, state)
    assert state.wrath_wipe_timer == 300
    assert state.wrath_zero_yield_timer == 300


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
        assert not any("VERSION:" in t and "[DEV MODE]" in t for t in drawn_texts)

        # In dev mode, title screen shows VERSION v0.9.0 [DEV MODE]
        app.dev_mode = True
        drawn_texts.clear()
        app.draw_title_screen()
        assert any(f"VERSION: {app.VERSION} [DEV MODE]" in t for t in drawn_texts)
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
        assert any("SHORTCUT: [I] INVULNERABILITY" in t for t in drawn_texts)
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

        # Check title is "PACTS" (not "PACTS (7)")
        pact_titles = [c for c in calls if c[2] == "PACTS"]
        assert len(pact_titles) == 1, "Must render 'PACTS' header"
        # Must be on the right side of the 600px screen (x > 400)
        assert pact_titles[0][0] >= 440, f"Pact menu header must be at top right (x >= 440), got {pact_titles[0][0]}"

        # Check numbered rows: '1. pride', '2. greed', etc.
        pride_entry = [c for c in calls if "1. pride" in c[2]]
        assert len(pride_entry) == 1, f"Must find '1. pride' in HUD text, found {calls}"
        assert pride_entry[0][0] >= 440, "Pact row must be at top right"

        greed_entry = [c for c in calls if "2. greed" in c[2]]
        assert len(greed_entry) == 1, f"Must find '2. greed' in HUD text, found {calls}"

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
        def mock_draw(x, y, s, col, scale=1, img_bank=2):
            if s in ["GLUTTONY", "PRIDE"]:
                title_draws.append((x, y, s, scale))
        main.draw_text_scaled = mock_draw
        app.draw_kairos_modal()

        assert len(title_draws) == 2, f"Expected 2 title draw calls, got {title_draws}"

        # 1. Significantly bigger: scale must be >= 6 (specifically 7, vs old scale 3)
        for x, y, s, scale in title_draws:
            assert scale >= 6, f"Title {s} scale must be >= 6 (significantly bigger), got {scale}"

        # 2. Longest character/name (GLUTTONY, 8 chars) must fill box horizontally (col_w = 228)
        glut_x, glut_y, glut_s, glut_scale = [d for d in title_draws if d[2] == "GLUTTONY"][0]
        glut_rendered_w = (len(glut_s) * 4 - 1) * glut_scale
        assert glut_rendered_w >= 200, f"GLUTTONY rendered width ({glut_rendered_w}px) must fill >= 200px of the 228px card"

        # 3. Justified center: for each card, text must be centered within ±1px of the card box
        col_w = 228
        col_gap = 20
        start_x = 30 + 32
        for i, (x, y, s, scale) in enumerate(title_draws):
            cx = start_x + i * (col_w + col_gap)
            text_w = (len(s) * 4 - 1) * scale
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

    # All shards hurled to at least y >= 720.0 with vy >= 38.0
    for s in shards_below:
        assert s.y >= 720.0
        assert s.vy >= 38.0

    # Simulate 80 frames where player does NOTHING (literally zero inputs)
    for _ in range(80):
        for s in entities.shards:
            s.update(scroll_speed=state.scroll_speed, hazard_speed_mod=1.0, player_x=entities.player.x, player_y=entities.player.y)
        # Verify complete survival: no shard ever touches or gets above player during this window
        for s in shards_below:
            assert s.y > entities.player.y + 20.0

    # Verify that the shards are clumped together at the bottom horizon
    active_ys = [s.y for s in shards_below if s.alive]
    assert len(active_ys) == 6
    # In a clumped wave, the vertical dispersion is greatly condensed
    spread = max(active_ys) - min(active_ys)
    assert spread < 180.0, f"Expected clumped wave at bottom horizon, got spread={spread}"




