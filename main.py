import unittest
from game import euchre_game, rules
from game.card import Card, Suit, Rank
from game.euchre_game import EuchreGame
from algorithm.ismcts import ISMCTS
from game.rules import legal_moves
from algorithm.node import ISMCTSNode

class TestEuchreGame(unittest.TestCase):

    def test_card_win_rates(self):
        game = EuchreGame()
        game.deal_new_hand()
        player = 0
        hand = list(game.state.hands[player])

        bot = ISMCTS(simulations=1000, debug=False)

        # Build root node mid-game with mini-simulations
        root = bot.build_test_root(game, player, simulations_per_card=700)

        print(f"Player {player} hand: {[str(c) for c in hand]}")
        print("Estimated win rates for legal cards:")

        for child in root.children:
            win_rate = child.wins / child.visits if child.visits > 0 else 0
            print(f"{child.move}: {win_rate:.2f}")

"""
    def test_simulate_one_hand_debug(self):
        game = EuchreGame()
        try:
            # Deal
            game.deal_new_hand()
            assert game.state.upcard is not None, "Upcard was not dealt"

            # Bidding
            game.do_bidding()
            assert game.state.trump is not None, "Trump was not set"
            assert game.makers_team in (0, 1), "Invalid makers_team"
            assert game.maker_index in range(4), "Invalid maker_index"

            # Hands should still be valid
            for i, hand in enumerate(game.state.hands):
                assert len(hand) == 5, f"Player {i} does not have 5 cards after bidding"

            # Play tricks
            trick_winners = game.play_tricks()
            assert len(trick_winners) == 5, "Did not play exactly 5 tricks"

            # Trick winners should be valid players
            for w in trick_winners:
                assert w in range(4), f"Invalid trick winner: {w}"

            # Score
            pre_scores = game.team_scores.copy()
            game.score_hand(trick_winners)

            # Score should change
            score_diff = sum(game.team_scores) - sum(pre_scores)
            self.assertIn(score_diff, [0, 1, 2, 4], "Invalid score change after hand")

            print("One-hand simulation completed successfully")
            print("Trump:", game.state.trump)
            print("Makers team:", game.makers_team)
            print("Alone:", game.alone)
            print("Trick winners:", trick_winners)
            print("Scores:", game.team_scores)

        except Exception as e:
            print("Error during one-hand simulation")
            raise  # re-raise so you get full traceback

    def setUp(self):
        self.game = euchre_game.EuchreGame()
        self.game.team_scores = [0, 0]
        self.game.alone = False
        self.game.makers_team = 0
        self.game.state.dealer = 3

    # ---------- Rules: Card Identity / Suit Logic ----------

    def test_sister_suit(self):
        self.assertEqual(rules.sister_suit(Suit.HEARTS), Suit.DIAMONDS)
        self.assertEqual(rules.sister_suit(Suit.SPADES), Suit.CLUBS)

    def test_is_void_suit(self):
        hand = [
            Card(Suit.SPADES, Rank.ACE),
            Card(Suit.SPADES, Rank.KING)
        ]
        self.assertTrue(rules.is_void_suit(hand, Suit.HEARTS, trump=Suit.SPADES))
        self.assertFalse(rules.is_void_suit(hand, Suit.SPADES, trump=Suit.SPADES))

    def test_num_void_suits(self):
        hand = [
            Card(Suit.SPADES, Rank.ACE),
            Card(Suit.SPADES, Rank.KING),
            Card(Suit.HEARTS, Rank.ACE),
        ]
        voids = rules.num_void_suits(hand, trump=Suit.CLUBS)
        self.assertGreaterEqual(voids, 1)

    def test_is_single_in_suit(self):
        hand = [
            Card(Suit.SPADES, Rank.ACE),
            Card(Suit.HEARTS, Rank.ACE),
            Card(Suit.HEARTS, Rank.KING),
        ]
        spade_card = Card(Suit.SPADES, Rank.ACE)

        self.assertTrue(
            rules.is_single_in_suit(
                hand,
                Suit.SPADES,  # suit being checked
                spade_card,  # unused but required
                Suit.CLUBS  # trump
            )
        )

    # ---------- Rules: Card Selection Helpers ----------

    def test_find_lowest_card(self):
        hand = [
            Card(Suit.SPADES, Rank.ACE),
            Card(Suit.SPADES, Rank.NINE),
            Card(Suit.CLUBS, Rank.KING),
        ]
        lowest = rules.find_lowest_card(hand, trump=Suit.HEARTS)
        self.assertEqual(lowest.rank, Rank.NINE)

    def test_find_worst_card(self):
        hand = [
            Card(Suit.HEARTS, Rank.JACK),
            Card(Suit.SPADES, Rank.NINE),
            Card(Suit.CLUBS, Rank.TEN),
        ]
        worst = rules.find_worst_card(hand, trump=Suit.HEARTS)
        self.assertNotEqual(worst.suit, Suit.HEARTS)

    def test_remove_worst_card(self):
        hand = [
            Card(Suit.HEARTS, Rank.ACE),
            Card(Suit.SPADES, Rank.NINE),
            Card(Suit.CLUBS, Rank.TEN),
        ]
        upcard = Card(Suit.HEARTS, Rank.KING)
        new_hand = rules.remove_worst_card(hand.copy(), upcard, trump=Suit.HEARTS)
        self.assertIn(upcard, new_hand)
        self.assertEqual(len(new_hand), 5 if len(hand) == 5 else len(hand))

    def test_throw_junk(self):
        hand = [
            Card(Suit.HEARTS, Rank.ACE),
            Card(Suit.CLUBS, Rank.NINE),
            Card(Suit.SPADES, Rank.TEN),
        ]
        junk = rules.throw_junk(hand, trump=Suit.HEARTS)
        self.assertNotEqual(junk.suit, Suit.HEARTS)

    # ---------- Rules: Trick / Move Logic ----------

    def test_trick_winner(self):
        trump = Suit.HEARTS
        trick = [
            Card(Suit.SPADES, Rank.ACE),
            Card(Suit.HEARTS, Rank.NINE),
            Card(Suit.SPADES, Rank.KING),
            Card(Suit.CLUBS, Rank.ACE),
        ]
        winner = rules.trick_winner(trick, leader=0, trump=trump)
        self.assertEqual(winner, 1)

    def test_cards_to_win_trick(self):
        hand = [
            Card(Suit.SPADES, Rank.ACE),
            Card(Suit.SPADES, Rank.KING),
            Card(Suit.CLUBS, Rank.NINE),
        ]
        trick = [Card(Suit.SPADES, Rank.QUEEN)]
        winning = rules.cards_to_win_trick(hand, trick, trump=Suit.HEARTS)
        self.assertTrue(any(c.rank == Rank.ACE for c in winning))

    def test_decide_move(self):
        hand = [
            Card(Suit.SPADES, Rank.ACE),
            Card(Suit.HEARTS, Rank.NINE),
            Card(Suit.CLUBS, Rank.TEN),
        ]
        trick = [(0, Card(Suit.SPADES, Rank.KING))]
        move = rules.decide_move(hand, trick, Suit.HEARTS, 0)
        self.assertEqual(move.suit, Suit.SPADES)

    # ---------- Game Logic: Choosing Trump ----------

    def test_choose_trump_basic(self):
        hand = [
            Card(Suit.HEARTS, Rank.JACK),
            Card(Suit.HEARTS, Rank.ACE),
            Card(Suit.HEARTS, Rank.KING),
            Card(Suit.CLUBS, Rank.NINE),
            Card(Suit.SPADES, Rank.TEN),
        ]
        suit, alone = self.game.choose_trump(
            hand,
            round_number=1,
            upcard=Card(Suit.HEARTS, Rank.NINE),
            dealer=False
        )
        self.assertEqual(suit, Suit.HEARTS)
        self.assertTrue(alone)

    def test_choose_trump_pass(self):
        hand = [
            Card(Suit.CLUBS, Rank.NINE),
            Card(Suit.SPADES, Rank.NINE),
            Card(Suit.DIAMONDS, Rank.TEN),
            Card(Suit.CLUBS, Rank.TEN),
            Card(Suit.SPADES, Rank.TEN),
        ]
        suit, alone = self.game.choose_trump(hand, round_number=1, upcard=Card(Suit.HEARTS, Rank.ACE))
        self.assertIsNone(suit)
        self.assertFalse(alone)

    # ---------- Game Logic: Deterministic Bidding ----------

    def test_do_bidding_forced(self):
        self.game.state.hands = [
            [Card(Suit.HEARTS, Rank.ACE)] * 5,
            [Card(Suit.CLUBS, Rank.NINE)] * 5,
            [Card(Suit.SPADES, Rank.NINE)] * 5,
            [Card(Suit.DIAMONDS, Rank.NINE)] * 5,
        ]
        self.game.state.upcard = Card(Suit.HEARTS, Rank.NINE)
        self.game.state.dealer = 3

        self.game.do_bidding()
        self.assertEqual(self.game.state.trump, Suit.HEARTS)
        self.assertEqual(self.game.makers_team, 0)

    # ---------- Game Logic: Play Tricks ----------

    def test_play_tricks_runs(self):
        self.game.state.trump = Suit.HEARTS
        self.game.makers_team = 0
        self.game.maker_index = 0
        self.game.alone = False

        self.game.state.hands = [
            [Card(Suit.HEARTS, Rank.ACE)] * 5,
            [Card(Suit.CLUBS, Rank.NINE)] * 5,
            [Card(Suit.SPADES, Rank.NINE)] * 5,
            [Card(Suit.DIAMONDS, Rank.NINE)] * 5,
        ]

        winners = self.game.play_tricks()
        self.assertEqual(len(winners), 5)

    # ---------- Scoring ----------

    def test_score_hand_all_cases(self):
        self.game.makers_team = 0
        self.game.alone = False
        self.game.score_hand([0, 0, 0, 1, 1])
        self.assertEqual(self.game.team_scores[0], 1)

        self.game.team_scores = [0, 0]
        self.game.score_hand([1, 1, 1, 0, 1])
        self.assertEqual(self.game.team_scores[1], 2)
"""

if __name__ == "__main__":
    unittest.main()
