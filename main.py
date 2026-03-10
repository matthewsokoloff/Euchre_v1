from game.euchre_game import EuchreGame

def main():

    bots = ["human", "ismcts", "ismcts", "ismcts"]

    game = EuchreGame(bot_types=bots, human_player=0)

    game.play_game_human()


if __name__ == "__main__":
    main()
