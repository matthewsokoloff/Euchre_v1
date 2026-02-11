import time
import statistics
from game.euchre_game import EuchreGame


def run_match(num_games=200, sims=200):
    start_time = time.time()

    win_results = []
    score_diffs = []

    for i in range(num_games):
        # Rotate ISMCTS seat every game
        seat = i % 4
        bots = ["heuristic"] * 4
        bots[seat] = "ismcts"

        game = EuchreGame(bot_types=bots)
        game.ismcts_bot.simulations = sims

        scores, winner = game.sim_game(verbose=False)

        ismcts_team = seat % 2
        score_diff = scores[ismcts_team] - scores[1 - ismcts_team]

        win_results.append(1 if winner == ismcts_team else 0)
        score_diffs.append(score_diff)

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


if __name__ == "__main__":
    run_match(num_games=50, sims=200)