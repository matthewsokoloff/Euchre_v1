from .deck import Deck
from .game_state import GameState
from .card import Card, Suit, Rank
from algorithm.ismcts import ISMCTS
from .rules import (is_right_bower, is_left_bower, effective_suit, card_value, throw_junk, find_lowest_card, decide_move, sister_suit, trick_winner, find_worst_card, remove_worst_card, is_single_in_suit, num_void_suits, is_void_suit, hand_strength, cards_to_win_trick, legal_moves)

class EuchreGame:
    def __init__(self, bot_types=None, human_player: int | None = None, mode="normal"):
        self.state = GameState(hands=[[] for _ in range(4)], dealer=3, trump=None, trick=[], scores=[0, 0], current_player=0, leader=0)

        self.bot_types = bot_types or ["heuristic"] * 4
        self.mode = mode
        self.dev = mode == "dev"

        self.ismcts_bot = ISMCTS(simulations=300, debug=self.dev)

        self.team_scores = [0, 0]
        self.human_player = human_player
        self.state.leader = self.state.current_player
        self.makers_team = None
        self.maker_index = None
        self.alone = False
        self.tricks_won = [0, 0]

    def deal_new_hand(self):
        self.deck = Deck()
        self.deck.shuffle()
        self.state.hands = [self.deck.deal(5) for _ in range(4)]
        self.state.trick.clear()
        self.state.dealer = (self.state.dealer + 1) % 4
        self.state.current_player = (self.state.dealer + 1) % 4
        self.state.leader = self.state.current_player
        self.tricks_won = [0, 0]
        self.state.upcard = self.deck.deal(1)[0]
        print(f"\nDealer: Player {self.state.dealer}")
        print(f"Upcard: {self.state.upcard}")

        if self.dev:
            for p, hand in enumerate(self.state.hands):
                print(f"Player {p} hand: {', '.join(str(c) for c in hand)}")

    def choose_trump(self, hand: list[Card], forbidden: Suit | None = None, round_number: int = 1, upcard: Card | None = None, dealer: bool = False):
        # chooses trump
        # returns a tuple of the suit and the alone boolean
        best_suit = None
        best_score = 0

        # Evaluate each suit
        for suit in Suit:
            if suit == forbidden:
                continue

            # round 1, hand_strength handles upcard addition
            strength = hand_strength(trump = suit, hand = hand.copy(), upcard = upcard if round_number == 1 else None, dealer = dealer)

            if strength > best_score:
                best_score = strength
                best_suit = suit

        # Decide if player should go alone
        alone = best_score >= 14  # simple loner heuristic

        # Minimum strength required to pick a suit
        if round_number == 1:
            min_strength = 9
        elif round_number == 2:
            min_strength = 8
        else:
            min_strength = 7

        if best_score >= min_strength:
            return best_suit, alone
        else:
            if round_number == 3: # if the dealer is being stuck, force pick of the best suit
                return best_suit, alone
            return None, False

    def do_bidding(self):
        # bidding for euchre hand using functions from rules.py
        dealer = self.state.dealer

        # round 1 (bidding on upcard)
        for i in range(4):
            player = (dealer + 1 + i) % 4

            suit, alone = self.choose_trump(self.state.hands[player], forbidden = None, round_number = 1, upcard = self.state.upcard, dealer = (player == dealer))

            # player orders up the upcard suit
            if suit == self.state.upcard.suit:
                self.state.trump = suit
                self.makers_team = player % 2
                self.maker_index = player
                self.alone = alone
                print(f"Player {player} orders up {suit}")
                if alone:
                    print(f"Player {player} goes alone!")

                # dealer picks up upcard
                if player == dealer:
                    self.state.hands[dealer] = remove_worst_card(self.state.hands[dealer], self.state.upcard, suit)
                return # bidding done

        # round 2: if everyone passes on the upcard (trump can be called on any other suit)
        for i in range(4):
            player = (dealer + 1 + i) % 4
            suit, alone = self.choose_trump(self.state.hands[player], forbidden = self.state.upcard.suit, round_number = 2)
            if suit:
                self.state.trump = suit
                self.makers_team = player % 2
                self.maker_index = player
                self.alone = alone
                print(f"Player {player} calls {suit}")
                if alone:
                    print(f"Player {player} goes alone!")
                return # bidding done

        # if no one calls it, stick the dealer
        suit, alone = self.choose_trump(self.state.hands[dealer], forbidden = self.state.upcard.suit, round_number = 3)
        if suit:
            self.state.trump = suit
            self.makers_team = dealer % 2
            self.maker_index = dealer
            self.alone = alone
            if alone:
                print(f"Dealer {dealer} is stuck and goes alone in {suit}")
            else:
                print(f"Dealer {dealer} is stuck and calls {suit}")
            return # bidding done
        raise RuntimeError("No trump selected during bidding! This should never happen.")

    def play_tricks(self):
        trump = self.state.trump
        leader = (self.state.dealer + 1) % 4
        trick_winners = []

        for _ in range(5):
            trick = []
            print(f"--- Trick {len(trick_winners) + 1} ---")
            for offset in range(4):
                player = (leader + offset) % 4
                if self.alone and player != self.maker_index and player % 2 == self.makers_team:
                    continue
                hand = self.state.hands[player]
                if player == self.human_player:
                    legal = legal_moves(hand, trick, trump)
                    print("\nYour turn")
                    print("Hand:")
                    for i, c in enumerate(hand):
                        print(f"{i}: {c}")
                    if trick:
                        print("Current trick:", [str(c) for _, c in trick])
                    print("Legal moves:", [str(c) for c in legal])
                    while True:
                        try:
                            choice = int(input("Play card index: "))
                            card_to_play = hand[choice]
                            if card_to_play in legal:
                                break
                            print("Illegal move.")
                        except:
                            print("Invalid input.")
                elif self.bot_types[player] == "ismcts":
                    print(f"\nPlayer {player} (ISMCTS) thinking...")
                    card_to_play = self.ismcts_bot.choose_card(self, player)
                else:
                    card_to_play = decide_move(hand, trick, trump, player % 2)
                print(f"Player {player} plays {card_to_play}")
                hand.remove(card_to_play)
                trick.append((player, card_to_play))
            winner = trick_winner([c for _, c in trick], leader, trump)
            print(f"Player {winner} wins the trick\n")
            trick_winners.append(winner)
            leader = winner
        return trick_winners

    def score_hand(self, tricks: list[int]):
        makers = self.makers_team
        team_tricks = [0, 0]
        for winner in tricks:
            team_tricks[winner % 2] += 1
        makers_tricks = team_tricks[makers]
        if self.alone:
            points = 4 if makers_tricks == 5 else 0
            self.team_scores[makers] += points
        elif makers_tricks == 5:
            self.team_scores[makers] += 2
        elif makers_tricks >= 3:
            self.team_scores[makers] += 1
        else:
            self.team_scores[1 - makers] += 2
        # print(f"score: Team 0 = {self.team_scores[0]}, Team 1 = {self.team_scores[1]}")

    def play_hand(self):
        self.deal_new_hand()
        self.do_bidding()
        print(f"Trump is {self.state.trump}")
        if self.dev:
            for p, hand in enumerate(self.state.hands):
                print(f"Player {p} hand: {', '.join(str(c) for c in hand)}")
        trick_winners = self.play_tricks()
        self.score_hand(trick_winners)

    def sim_game(self, verbose: bool = False):
        """Play a full game to 10 points. Returns final scores and winning team."""
        if verbose:
            print("=== Starting Euchre Simulation ===")

        hand_stats = {
            "total_hands": 0,
            "ismcts_calls": 0,
            "ismcts_call_wins": 0,
            "ismcts_call_euchred": 0,
        }

        while max(self.team_scores) < 10:
            self.deal_new_hand()
            self.do_bidding()
            if verbose:
                print(f"\nTrump suit is {self.state.trump}\n")

            hand_stats["total_hands"] += 1

            trick_winners = self.play_tricks()
            makers = self.makers_team
            maker_index = self.maker_index

            # Count tricks
            team_tricks = [0, 0]
            for winner in trick_winners:
                team_tricks[winner % 2] += 1

            makers_tricks = team_tricks[makers]

            # Check if ISMCTS called
            if self.bot_types[maker_index] == "ismcts":
                hand_stats["ismcts_calls"] += 1

                if makers_tricks >= 3:
                    hand_stats["ismcts_call_wins"] += 1
                else:
                    hand_stats["ismcts_call_euchred"] += 1

            self.score_hand(trick_winners)
            if verbose:
                print(f"Score: Team 0 = {self.team_scores[0]}, Team 1 = {self.team_scores[1]}\n")

        winning_team = 0 if self.team_scores[0] > self.team_scores[1] else 1
        if verbose:
            print("=== Game Over ===")

        return self.team_scores, winning_team, hand_stats
