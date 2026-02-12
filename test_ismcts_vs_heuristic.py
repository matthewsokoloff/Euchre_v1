import time
import statistics
from game.euchre_game import EuchreGame


def run_match(num_games=200, sims=200):
    start_time = time.time()

    total_ismcts_calls = 0
    total_ismcts_call_wins = 0
    total_ismcts_call_euchred = 0
    total_hands_played = 0


    win_results = []
    score_diffs = []

    for i in range(num_games):
        # Rotate ISMCTS seat every game
        seat = i % 4
        bots = ["heuristic"] * 4
        bots[seat] = "ismcts"

        game = EuchreGame(bot_types=bots)
        game.ismcts_bot.simulations = sims

        scores, winner, hand_stats = game.sim_game(verbose=False)

        ismcts_team = seat % 2
        score_diff = scores[ismcts_team] - scores[1 - ismcts_team]

        win_results.append(1 if winner == ismcts_team else 0)
        score_diffs.append(score_diff)

        total_ismcts_calls += hand_stats["ismcts_calls"]
        total_ismcts_call_wins += hand_stats["ismcts_call_wins"]
        total_ismcts_call_euchred += hand_stats["ismcts_call_euchred"]
        total_hands_played += hand_stats["total_hands"]

        print(f"Game {i+1}/{num_games} complete")

    duration = time.time() - start_time

    win_rate = sum(win_results) / num_games
    avg_score_diff = sum(score_diffs) / num_games
    std_dev = statistics.stdev(score_diffs)

    print("\n===== RESULTS =====")
    print(f"Games played: {num_games}")
    print(f"Simulations per move: {sims}")
    print(f"Win rate: {win_rate:.2%}")
    print(f"Average score diff: {avg_score_diff:.2f}")
    print(f"Score diff std dev: {std_dev:.2f}")
    print(f"Total runtime: {duration:.2f} seconds")
    print(f"Avg seconds per game: {duration / num_games:.3f}")

    print("\n===== ISMCTS CALL STATS =====")

    if total_ismcts_calls > 0:
        call_win_rate = total_ismcts_call_wins / total_ismcts_calls
        euchre_rate = total_ismcts_call_euchred / total_ismcts_calls
        call_frequency = total_ismcts_calls / total_hands_played
        print(f"call frequency: {call_frequency}")

        print(f"Total hands played: {total_hands_played}")
        print(f"Total times ISMCTS called trump: {total_ismcts_calls}")
        print(f"Call frequency: {call_frequency:.2%}")
        print(f"Win rate when calling: {call_win_rate:.2%}")
        print(f"Euchred rate when calling: {euchre_rate:.2%}")
    else:
        print("ISMCTS never called trump.")


if __name__ == "__main__":
    run_match(num_games=100, sims=500)