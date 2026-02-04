from game.euchre_game import EuchreGame
from game.card import Card, Suit, Rank
from algorithm.ismcts import ISMCTS


def ismcts_decision_test():
    """
    Player 0 must decide what to lead.
    Trump = HEARTS
    Player 0 has:
      - Right bower
      - Ace of trump
      - Off-suit Ace
    ISMCTS should strongly prefer a trump lead.
    """

    game = EuchreGame(human_player=None)

    hands = [
        [  # Player 0 (decision-maker)
            Card(Suit.HEARTS, Rank.JACK),   # Right bower
            Card(Suit.HEARTS, Rank.ACE),    # Trump ace
            Card(Suit.SPADES, Rank.ACE),    # Off-suit ace
            Card(Suit.CLUBS, Rank.NINE),
            Card(Suit.DIAMONDS, Rank.NINE),
        ],
        [  # Player 1
            Card(Suit.CLUBS, Rank.ACE),
            Card(Suit.CLUBS, Rank.KING),
            Card(Suit.DIAMONDS, Rank.KING),
            Card(Suit.SPADES, Rank.TEN),
            Card(Suit.SPADES, Rank.NINE),
        ],
        [  # Player 2
            Card(Suit.HEARTS, Rank.KING),
            Card(Suit.HEARTS, Rank.QUEEN),
            Card(Suit.CLUBS, Rank.TEN),
            Card(Suit.SPADES, Rank.QUEEN),
            Card(Suit.DIAMONDS, Rank.TEN),
        ],
        [  # Player 3
            Card(Suit.SPADES, Rank.JACK),
            Card(Suit.SPADES, Rank.ACE),
            Card(Suit.DIAMONDS, Rank.ACE),
            Card(Suit.CLUBS, Rank.QUEEN),
            Card(Suit.CLUBS, Rank.TEN),
        ],
    ]

    game.set_hands(
        hands=hands,
        upcard=Card(Suit.HEARTS, Rank.NINE),
        dealer=3
    )

    game.state.trump = Suit.HEARTS
    game.state.current_player = 0
    game.state.leader = 0

    print("\n=== ISMCTS Decision Test ===")
    chosen = game.decide_card(
        player=0,
        legal=hands[0],
        trick=[]
    )
    print(f"\nISMCTS chose to lead: {chosen}")


if __name__ == "__main__":
    game = EuchreGame(human_player=None)
    ismcts_bot = ISMCTS(simulations=100)
    game.play_hand_with_ismcts(ismcts_bot)
