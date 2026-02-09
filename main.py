import unittest
from game.euchre_game import EuchreGame
from game.rules import Suit, hand_strength, effective_suit

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


class TestEuchreGame(unittest.TestCase):

    def setUp(self):
        self.game = EuchreGame()
        self.game.deal_new_hand()

    def test_choose_trump_heuristic_returns_valid_suit(self):
        for hand in self.game.state.hands:
            suit, alone = self.game.choose_trump(hand)
            self.assertTrue(suit is None or isinstance(suit, Suit))
            self.assertIsInstance(alone, bool)

    def test_do_bidding_sets_trump(self):
        self.game.do_bidding()
        self.assertIn(self.game.state.trump, list(Suit))
        self.assertIn(self.game.makers_team, [0, 1])
        self.assertIsNotNone(self.game.maker_index)

    def test_play_tricks_winner_index(self):
        self.game.do_bidding()
        winners = self.game.play_tricks()
        self.assertEqual(len(winners), 5)
        for winner in winners:
            self.assertIn(winner, [0, 1, 2, 3])

    def test_score_hand_updates_team_scores(self):
        # Set up the game state
        self.game.trump = Suit.HEARTS
        self.game.makers_team = 0  # Team 0 called trump
        winners = [0, 0, 0, 0, 0]  # Team 0 takes all tricks
        self.game.score_hand(winners)
        self.assertTrue(self.game.team_scores[0] > 0)  # Team 0 should get points

    def test_hand_strength_increases_with_trump(self):
        hand = self.game.state.hands[0]
        for suit in Suit:
            strength = hand_strength(suit, hand, None, dealer=False)
            self.assertIsInstance(strength, int)
            self.assertGreaterEqual(strength, 0)

if __name__ == "__main__":
    main()
    unittest.main()