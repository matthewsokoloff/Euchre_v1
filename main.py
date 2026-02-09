import unittest
from game import euchre_game, rules
from game.card import Card, Suit, Rank


class TestEuchreGame(unittest.TestCase):

    def setUp(self):
        # Create a game instance
        self.game = euchre_game.EuchreGame()
        self.game.team_scores = [0, 0]
        self.game.alone = False
        self.game.makers_team = 0

    # ---------- Test Rules Helpers ----------

    def test_right_left_bower(self):
        trump = Suit.HEARTS
        right_bower = Card(Suit.HEARTS, Rank.JACK)
        left_bower = Card(Suit.DIAMONDS, Rank.JACK)
        normal_card = Card(Suit.HEARTS, Rank.ACE)

        self.assertTrue(rules.is_right_bower(right_bower, trump))
        self.assertTrue(rules.is_left_bower(left_bower, trump))
        self.assertFalse(rules.is_right_bower(normal_card, trump))
        self.assertFalse(rules.is_left_bower(normal_card, trump))

    def test_effective_suit(self):
        trump = Suit.SPADES
        left_bower = Card(Suit.CLUBS, Rank.JACK)
        normal = Card(Suit.CLUBS, Rank.ACE)
        self.assertEqual(rules.effective_suit(left_bower, trump), trump)
        self.assertEqual(rules.effective_suit(normal, trump), Suit.CLUBS)

    def test_card_value_trump(self):
        trump = Suit.DIAMONDS
        right = Card(Suit.DIAMONDS, Rank.JACK)
        left = Card(Suit.HEARTS, Rank.JACK)
        ace_trump = Card(Suit.DIAMONDS, Rank.ACE)
        non_trump = Card(Suit.CLUBS, Rank.ACE)
        self.assertEqual(rules.card_value(right, trump), 1000)
        self.assertEqual(rules.card_value(left, trump), 900)
        self.assertTrue(rules.card_value(ace_trump, trump) > rules.card_value(non_trump, trump))

    # ---------- Test Choosing Trump / Bidding ----------

    def test_hand_strength(self):
        hand = [
            Card(Suit.SPADES, Rank.JACK),
            Card(Suit.HEARTS, Rank.ACE),
            Card(Suit.DIAMONDS, Rank.KING),
            Card(Suit.CLUBS, Rank.TEN),
            Card(Suit.HEARTS, Rank.KING)
        ]
        trump_strength = rules.hand_strength(Suit.HEARTS, hand, None, dealer=False)
        self.assertGreater(trump_strength, 0)
        non_trump_strength = rules.hand_strength(Suit.CLUBS, hand, None, dealer=False)
        self.assertGreater(trump_strength, 0)

    # ---------- Test Playing / Legal Moves ----------

    def test_legal_moves_follow_suit(self):
        hand = [
            Card(Suit.SPADES, Rank.ACE),
            Card(Suit.CLUBS, Rank.TEN),
            Card(Suit.HEARTS, Rank.JACK)
        ]
        trick = [(0, Card(Suit.SPADES, Rank.NINE))]
        legal = rules.legal_moves(hand, trick, Suit.HEARTS)
        # Only Spades card is legal to follow suit
        self.assertEqual(len(legal), 1)
        self.assertEqual(legal[0].suit, Suit.SPADES)

    def test_throw_junk(self):
        hand = [
            Card(Suit.SPADES, Rank.NINE),
            Card(Suit.CLUBS, Rank.TEN),
            Card(Suit.HEARTS, Rank.NINE)
        ]
        trump = Suit.HEARTS
        junk_card = rules.throw_junk(hand, trump)
        self.assertNotEqual(junk_card.suit, trump)

    # ---------- Test Scoring ----------

    def test_score_hand_basic(self):
        # Team 0 (makers) takes 3 tricks, should get 1 point
        self.game.makers_team = 0
        self.game.alone = False
        tricks = [0, 1, 0, 1, 0]
        self.game.score_hand(tricks)
        self.assertEqual(self.game.team_scores[0], 1)
        self.assertEqual(self.game.team_scores[1], 0)

    def test_score_hand_euchre(self):
        # Team 0 (makers) gets 2 tricks or fewer → opponents score 2
        self.game.makers_team = 0
        self.game.alone = False
        tricks = [1, 1, 0, 1, 1]
        self.game.score_hand(tricks)
        self.assertEqual(self.game.team_scores[0], 0)
        self.assertEqual(self.game.team_scores[1], 2)

    def test_score_hand_alone(self):
        # Team 0 goes alone and wins all 5 tricks → 4 points
        self.game.makers_team = 0
        self.game.alone = True
        tricks = [0, 0, 0, 0, 0]
        self.game.score_hand(tricks)
        self.assertEqual(self.game.team_scores[0], 4)

        # Team 0 goes alone and loses any trick → 0 points
        self.game.team_scores = [0, 0]
        tricks = [0, 1, 0, 0, 0]
        self.game.score_hand(tricks)
        self.assertEqual(self.game.team_scores[0], 0)


if __name__ == "__main__":
    unittest.main()
