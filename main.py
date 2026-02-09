from game.euchre_game import EuchreGame

def main():
    # Initialize Euchre game w/o human player
    game = EuchreGame(human_player=None)

    # Run a full game to 10 points with verbose output
    final_scores, winning_team = game.sim_game(verbose=True)

    # Print final results
    print("\n=== Final Game Results ===")
    print(f"Team 0 Score: {final_scores[0]}")
    print(f"Team 1 Score: {final_scores[1]}")
    print(f"Winning Team: Team {winning_team}")

if __name__ == "__main__":
    main()