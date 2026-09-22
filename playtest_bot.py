"""Automated Headless Playtest Benchmark Suite for Grain of Doubt.

Executes headless game simulations with the GOFAI PlayTestingBot to verify
game balance, feasibility, and survivability under handicaps (80% speed, 20% bottom-blind).
"""
import argparse
import statistics
import time
from typing import List, Dict, Any

from engine.state import GameState, StateManager
from engine.entities import EntityManager
from engine.bargains import BargainManager, SinType
from engine.bot import PlayTestingBot, BotConfig


def run_single_episode(
    episode_idx: int,
    bot: PlayTestingBot,
    max_frames: int = 5400,  # 3.0 minutes at 30 FPS
    seed: int = 42,
) -> Dict[str, Any]:
    """Execute one full headless game until Game Over or max_frames."""
    state = StateManager()
    entities = EntityManager(screen_w=600, screen_h=800)
    bargains = BargainManager()
    bot.reset()

    state._bot_speed_handicap = bot.config.speed_handicap
    state.start_game()

    sins_chosen: List[SinType] = []
    active_options = []
    cursor_idx = 0

    for frame in range(max_frames):
        if state.current_state == GameState.CHRONOS:
            left, right = bot.decide_chronos_input(state, entities)
            state._input_left = left
            state._input_right = right
            state._bot_speed_handicap = bot.config.speed_handicap

            state.update_timers()
            entities.update(state)

            if state.current_state == GameState.KAIROS:
                active_options = bargains.draw_options(2)
                cursor_idx = 0
                bot.target_card_index = None

        elif state.current_state == GameState.KAIROS:
            # Bot decides Kairos selection
            m_left, m_right, confirm = bot.decide_kairos_choice(active_options, cursor_idx)
            if m_left and cursor_idx > 0:
                cursor_idx -= 1
            elif m_right and cursor_idx < len(active_options) - 1:
                cursor_idx += 1

            state.update_timers()

            if confirm or state.current_state == GameState.CHRONOS:
                if 0 <= cursor_idx < len(active_options):
                    chosen_sin, _, _ = active_options[cursor_idx]
                    assert chosen_sin != SinType.GREED, f"Bot violated policy: chosen Greed ({chosen_sin}) at frame {frame}!"
                    bargains.apply_bargain(chosen_sin, state, entities)
                    sins_chosen.append(chosen_sin)
                state.resume_chronos()
                bot.reset_kairos()
                active_options = []

        elif state.current_state == GameState.GAMEOVER:
            return {
                "episode": episode_idx,
                "survived_frames": frame,
                "survived_seconds": frame / 30.0,
                "score": state.score,
                "cycles": state.cycle_count,
                "sand_collected": state.total_sand_collected,
                "shards_dodged": state.total_shards_dodged,
                "death_reason": state.death_reason or "Hazard Collision",
                "sins_chosen": sins_chosen,
                "completed_full_time": False,
            }

    # Completed max_frames without dying!
    return {
        "episode": episode_idx,
        "survived_frames": max_frames,
        "survived_seconds": max_frames / 30.0,
        "score": state.score,
        "cycles": state.cycle_count,
        "sand_collected": state.total_sand_collected,
        "shards_dodged": state.total_shards_dodged,
        "death_reason": "Max Time Reached (Alive)",
        "sins_chosen": sins_chosen,
        "completed_full_time": True,
    }


def run_playtest_suite(episodes: int = 10, max_frames_per_ep: int = 4500) -> Dict[str, Any]:
    """Runs automated playtest suite across multiple episodes and reports statistics."""
    print("=" * 60)
    print("  GRAIN OF DOUBT - GOFAI PLAYTEST BENCHMARK SUITE")
    print(f"  Episodes: {episodes} | Max Duration: {max_frames_per_ep/30:.1f}s per run")
    print(f"  Handicaps: 80% Max Speed | Bottom 20% Blindness (y > 640)")
    print(f"  Strategy: Random Sins (STRICTLY NO GREED)")
    print("=" * 60)

    start_time = time.time()
    results = []
    config = BotConfig(speed_handicap=0.80, bottom_blind_ratio=0.20)
    bot = PlayTestingBot(config=config)

    for i in range(1, episodes + 1):
        ep_res = run_single_episode(i, bot, max_frames=max_frames_per_ep, seed=100 + i)
        results.append(ep_res)
        print(
            f"  [Ep {i:02d}] Survived: {ep_res['survived_seconds']:5.1f}s | "
            f"Cycles: {ep_res['cycles']:2d} | Score: {ep_res['score']:6d} | "
            f"Sands: {ep_res['sand_collected']:3d} | Shards Dodged: {ep_res['shards_dodged']:3d} | "
            f"Death: {ep_res['death_reason']}"
        )

    elapsed = time.time() - start_time
    scores = [r["score"] for r in results]
    lifetimes = [r["survived_seconds"] for r in results]
    cycles = [r["cycles"] for r in results]
    all_sins = [sin for r in results for sin in r["sins_chosen"]]

    greed_count = sum(1 for sin in all_sins if sin == SinType.GREED)

    sin_counts = {}
    for sin in all_sins:
        sin_counts[sin.name] = sin_counts.get(sin.name, 0) + 1

    print("-" * 60)
    print("PLAYTEST BENCHMARK SUMMARY:")
    print(f"  Simulated Real-Time  : {sum(lifetimes):.1f}s ({sum(lifetimes)/60.0:.2f} mins) in {elapsed:.2f}s execution")
    print(f"  Average Survival Time: {statistics.mean(lifetimes):.1f}s (Median: {statistics.median(lifetimes):.1f}s)")
    print(f"  Average Cycles Reached: {statistics.mean(cycles):.1f} (Max: {max(cycles)})")
    print(f"  Average Final Score  : {statistics.mean(scores):.0f} (Max: {max(scores)})")
    print(f"  Greed Chosen Count   : {greed_count} (Must be exactly 0)")
    print(f"  Sin Choices Breakdown: {sin_counts}")
    print("=" * 60)

    return {
        "results": results,
        "mean_score": statistics.mean(scores),
        "mean_lifetime": statistics.mean(lifetimes),
        "greed_count": greed_count,
        "sin_counts": sin_counts,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run headless playtest bot benchmark.")
    parser.add_argument("--episodes", type=int, default=10, help="Number of episodes to simulate")
    parser.add_argument("--frames", type=int, default=4500, help="Max frames per episode")
    args = parser.parse_args()

    run_playtest_suite(episodes=args.episodes, max_frames_per_ep=args.frames)
