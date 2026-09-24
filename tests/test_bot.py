"""Unit and integration tests for GOFAI PlayTestingBot and handicaps."""
import pytest
from engine.state import GameState, StateManager
from engine.entities import HourglassPlayer, SandGrain, GlassShard, EntityManager, aabb_overlap
from engine.bargains import BargainManager, SinType, BARGAIN_REGISTRY
from engine.bot import PlayTestingBot, BotConfig
from playtest_bot import run_single_episode


def test_bottom_vision_handicap():
    """Verify bot cannot see entities in the bottom 20% of the screen (y > 640)."""
    bot = PlayTestingBot(BotConfig(bottom_blind_ratio=0.20))
    threshold = bot.get_vision_threshold_y(800)
    assert threshold == 640.0

    # Create shards at various y positions
    shard_visible = GlassShard(300, 500)
    shard_at_edge = GlassShard(300, 640)
    shard_blind_1 = GlassShard(300, 641)
    shard_blind_2 = GlassShard(300, 750)

    shards = [shard_visible, shard_at_edge, shard_blind_1, shard_blind_2]
    filtered_shards = bot.filter_visible_shards(shards, screen_h=800)

    assert shard_visible in filtered_shards
    assert shard_at_edge in filtered_shards
    assert shard_blind_1 not in filtered_shards
    assert shard_blind_2 not in filtered_shards

    # Create sands at various y positions
    sand_visible = SandGrain(300, 400)
    sand_blind = SandGrain(300, 700)
    filtered_sands = bot.filter_visible_sands([sand_visible, sand_blind], screen_h=800)

    assert sand_visible in filtered_sands
    assert sand_blind not in filtered_sands


def test_speed_handicap_and_effective_accel():
    """Verify 80% speed handicap is strictly configured and applied."""
    config = BotConfig(speed_handicap=0.80)
    bot = PlayTestingBot(config=config)
    assert bot.config.speed_handicap == 0.80

    # Test physics acceleration with handicap
    state = StateManager()
    state.start_game()
    entities = EntityManager(screen_w=600, screen_h=800)

    # Standard acceleration without handicap
    entities.player.reset()
    state._bot_speed_handicap = 1.0
    state._input_left = False
    state._input_right = True
    entities.update(state)
    vx_full = entities.player.vx

    # Acceleration with 80% handicap
    entities.player.reset()
    state._bot_speed_handicap = 0.80
    state._input_left = False
    state._input_right = True
    entities.update(state)
    vx_handicap = entities.player.vx

    assert vx_handicap == pytest.approx(vx_full * 0.80, rel=1e-3)


def test_bot_deterministic_hazard_evasion():
    """Verify bot evades oncoming glass shard directly ahead."""
    bot = PlayTestingBot(BotConfig(speed_handicap=0.80, bottom_blind_ratio=0.20))
    state = StateManager(initial_hearts=3)
    state.start_game()
    entities = EntityManager(screen_w=600, screen_h=800)

    # Place player at center (300, 200)
    entities.player.x = 300.0
    entities.player.vx = 0.0

    # Place lethal shard directly ahead on collision course
    # Shard at (300, 450) with 0 drift moving up at scroll_speed=10 px/frame
    shard = GlassShard(300.0, 450.0)
    shard.lateral_drift = 0.0
    entities.shards.append(shard)

    # Simulate frames until shard passes player y=200
    collided = False
    for frame in range(35):
        left, right = bot.decide_chronos_input(state, entities)
        state._input_left = left
        state._input_right = right
        state._bot_speed_handicap = bot.config.speed_handicap

        # Check collision before entity update
        px_box = entities.player.get_hitbox()
        for sh in entities.shards:
            shb = sh.get_hitbox()
            if aabb_overlap(px_box[0], px_box[1], px_box[2], px_box[3], shb[0], shb[1], shb[2], shb[3]):
                collided = True

        entities.update(state)

    # Bot must have steered away from x=300 and successfully evaded
    assert not collided, "Bot collided with incoming hazard!"
    assert state.hearts == 3, "Bot took damage!"
    assert abs(entities.player.x - 300.0) > 25.0, "Bot failed to steer laterally!"


def test_bot_deterministic_sand_collection():
    """Verify bot steers toward safe sand grain."""
    bot = PlayTestingBot(BotConfig(speed_handicap=0.80, bottom_blind_ratio=0.20))
    state = StateManager(initial_hearts=3)
    state.start_game()
    entities = EntityManager(screen_w=600, screen_h=800)

    # Place player at center (300, 200)
    entities.player.x = 300.0
    entities.player.vx = 0.0

    # Place sand grain to the right at (360, 420)
    sand = SandGrain(360.0, 420.0)
    entities.sands.append(sand)

    # Simulate until sand arrives
    collected = False
    for frame in range(30):
        left, right = bot.decide_chronos_input(state, entities)
        state._input_left = left
        state._input_right = right
        state._bot_speed_handicap = bot.config.speed_handicap
        entities.update(state)

        if state.score > 0:
            collected = True
            break

    assert collected, "Bot failed to steer and collect isolated sand grain!"
    assert state.score >= 1  # 1 sand is 1 point!


def test_bot_bargain_policy_never_greed():
    """Verify over 200 trials that bot NEVER selects SinType.GREED."""
    bargains = BargainManager()
    bot = PlayTestingBot()

    # Repeat 200 times
    for trial in range(200):
        # Force Greed into options
        options = [
            (SinType.GREED, BARGAIN_REGISTRY[SinType.GREED], 1),
            (SinType.GLUTTONY, BARGAIN_REGISTRY[SinType.GLUTTONY], 1),
            (SinType.PRIDE, BARGAIN_REGISTRY[SinType.PRIDE], 1),
        ]
        bot.reset()

        # Step through selection
        cursor = 1
        for _ in range(5):
            m_left, m_right, confirm = bot.decide_kairos_choice(options, cursor)
            if confirm:
                break
            if m_left:
                cursor -= 1
            elif m_right:
                cursor += 1

        chosen_sin = options[cursor][0]
        assert chosen_sin != SinType.GREED, f"Trial {trial}: Bot chose GREED!"


def test_bot_kairos_2_seconds_delay():
    """Verify bot waits 2.0s (60 frames) elapsed before confirming Kairos selection."""
    bot = PlayTestingBot()
    options = [
        (SinType.PRIDE, BARGAIN_REGISTRY[SinType.PRIDE], 1),
        (SinType.SLOTH, BARGAIN_REGISTRY[SinType.SLOTH], 1),
    ]
    bot.target_card_index = 0
    # Under 60 frames, bot will navigate but NOT confirm
    for elapsed in [0, 15, 30, 45, 59]:
        _, _, confirm = bot.decide_kairos_choice(options, current_index=0, frames_elapsed=elapsed)
        assert confirm is False, f"Bot should not confirm at elapsed frame {elapsed} (< 60)"

    # At 60+ frames, bot confirms selection
    _, _, confirm = bot.decide_kairos_choice(options, current_index=0, frames_elapsed=60)
    assert confirm is True


def test_headless_bot_simulation_survives():
    """Verify bot executes headless game for multiple cycles without crash."""
    bot = PlayTestingBot(BotConfig(speed_handicap=0.80, bottom_blind_ratio=0.20), seed=42)
    res = run_single_episode(1, bot, max_frames=600, seed=42)

    assert res["survived_frames"] > 100, f"Bot died too quickly: {res['survived_frames']} frames"
    for sin in res["sins_chosen"]:
        assert sin != SinType.GREED
