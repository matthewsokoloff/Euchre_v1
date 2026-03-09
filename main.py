from game.euchre_game import EuchreGame


def main():

    mode = input("Mode (normal/dev): ").strip().lower()

    game = EuchreGame(
        bot_types=["human", "ismcts", "ismcts", "ismcts"],
        human_player=0,
        mode=mode
    )

    while max(game.team_scores) < 10:

        game.play_hand()

        print("\nScore:")
        print(f"Team 0: {game.team_scores[0]}")
        print(f"Team 1: {game.team_scores[1]}")
        print("----------------------")

    winner = 0 if game.team_scores[0] > game.team_scores[1] else 1
    print(f"\nGame Over — Team {winner} wins!")


if __name__ == "__main__":
    main()
