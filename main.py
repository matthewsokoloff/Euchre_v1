from game.euchre_game import EuchreGame

def main():
    # Ask the user for mode
    mode = input("Enter mode (dev or normal): ").strip().lower()

    # Define bot types
    bots = ["human", "ismcts", "ismcts", "ismcts"]

    # Set debug based on input
    debug = True if mode == "dev" else False
    if debug:
        print("dev mode")
    else:
        print("normal mode")

    # Initialize game
    game = EuchreGame(bot_types=bots, human_player=0, debug=debug)

    # Play game
    game.play_game_human()


if __name__ == "__main__":
    main()