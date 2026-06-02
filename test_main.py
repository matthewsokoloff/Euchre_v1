import unittest

from game.card import Card, Rank, Suit
from game.rules import card_value, find_lowest_card, legal_moves, trick_winner


class TestCoreEuchreLogic(unittest.TestCase):
    def test_success_right_bower_is_strongest(self):
        self.assertEqual(card_value(Card(Suit.HEARTS, Rank.JACK), Suit.HEARTS), 1000)

    def test_legal_moves_follow_suit(self):
        hand = [
            Card(Suit.SPADES, Rank.ACE),
            Card(Suit.HEARTS, Rank.KING),
        ]
        self.assertEqual(legal_moves(hand, [(0, Card(Suit.SPADES, Rank.NINE))], Suit.HEARTS), [hand[0]])

    def test_trump_wins_trick(self):
        trick = [
            Card(Suit.SPADES, Rank.ACE),
            Card(Suit.HEARTS, Rank.NINE),
        ]
        self.assertEqual(trick_winner(trick, leader=0, trump=Suit.HEARTS), 1)

    def test_error_empty_hand(self):
        with self.assertRaises(IndexError):
            find_lowest_card([], trump=Suit.CLUBS)


if __name__ == "__main__":
    unittest.main()
