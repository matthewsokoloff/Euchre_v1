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
        dealer = self.state.dealer
        upcard = self.state.upcard
        print(f"Dealer: Player {dealer}")
        print(f"Upcard: {upcard}")

        # Show human hand
        hand_str = ', '.join(str(c) for c in self.state.hands[self.human_player])
        print(f"Your hand: {hand_str}")

        # --- ROUND 1: bidding on upcard ---
        for i in range(4):
            player = (dealer + 1 + i) % 4

            if player == self.human_player:
                print(f"\nYour turn to bid. Upcard: {upcard}")
                choice = input(f"Order up {upcard.suit.name}? (y/n): ").strip().lower()
                if choice == "y":
                    suit = upcard.suit
                    alone = input("Go alone? (y/n): ").strip().lower() == "y"
                    self.state.trump = suit
                    self.makers_team = player % 2
                    self.maker_index = player
                    self.alone = alone
                    print(f"You ordered up {suit.name}")

                    # Dealer must pick up the upcard
                    if player == dealer:
                        print(f"You must pick up the upcard: {upcard}")
                        discard_choices = self.state.hands[player][:]
                        discard = get_human_card_choice(self.state.hands[player], discard_choices)
                        self.state.hands[player].remove(discard)
                        self.state.hands[player].append(upcard)
                        print(f"You picked up {upcard} and discarded {discard}")
                    return
                else:
                    print("You pass.")
                    continue

            # BOT players
            suit, alone = self.choose_trump(
                self.state.hands[player],
                forbidden=None,
                round_number=1,
                upcard=upcard,
                dealer=(player == dealer)
            )

            if suit == upcard.suit:
                print(f"Player {player} orders up {suit.name}")
                if alone:
                    print(f"Player {player} goes alone!")
                self.state.trump = suit
                self.makers_team = player % 2
                self.maker_index = player
                self.alone = alone

                # Dealer picks up upcard if needed
                if player == dealer:
                    if player == self.human_player:
                        discard_choices = self.state.hands[player][:]
                        discard = get_human_card_choice(self.state.hands[player], discard_choices)
                        self.state.hands[player].remove(discard)
                        self.state.hands[player].append(upcard)
                        print(f"You picked up {upcard} and discarded {discard}")
                    else:
                        self.state.hands[dealer] = remove_worst_card(self.state.hands[dealer], upcard, suit)
                return
            else:
                print(f"Player {player} passes")

        # --- ROUND 2: calling a different suit ---
        for i in range(4):
            player = (dealer + 1 + i) % 4

            if player == self.human_player:
                print(f"\nYour turn to call trump (cannot be {upcard.suit.name})")
                choice = input("Call a suit? (or enter to pass): ").strip().upper()
                if choice in [s.name for s in Suit if s != upcard.suit]:
                    suit = Suit[choice]
                    alone = input("Go alone? (y/n): ").strip().lower() == "y"
                    self.state.trump = suit
                    self.makers_team = player % 2
                    self.maker_index = player
                    self.alone = alone
                    print(f"You called {suit.name}")
                    if alone:
                        print("You go alone!")
                    return
                else:
                    print("You pass.")
                    continue

            suit, alone = self.choose_trump(
                self.state.hands[player],
                forbidden=upcard.suit,
                round_number=2
            )
            if suit:
                print(f"Player {player} calls {suit.name}")
                if alone:
                    print(f"Player {player} goes alone!")
                self.state.trump = suit
                self.makers_team = player % 2
                self.maker_index = player
                self.alone = alone
                return
            else:
                print(f"Player {player} passes")

        # --- ROUND 3: dealer forced to pick ---
        suit, alone = self.choose_trump(
            self.state.hands[dealer],
            forbidden=upcard.suit,
            round_number=3
        )
        self.state.trump = suit
        self.makers_team = dealer % 2
        self.maker_index = dealer
        self.alone = alone

        if dealer == self.human_player:
            print(f"\nYou are stuck and must call {suit.name}")
            discard_choices = self.state.hands[dealer][:]
            discard = get_human_card_choice(self.state.hands[dealer], discard_choices)
            self.state.hands[dealer].remove(discard)
            self.state.hands[dealer].append(upcard)  # optional: dealer could pick up upcard if desired
            print(f"You discarded {discard}")
        else:
            print(f"Dealer {dealer} is stuck and calls {suit.name}")
            if alone:
                print(f"Player {dealer} goes alone!")
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
                legal = legal_moves(hand, trick, trump)
                if player == self.human_player:
                    card_to_play = get_human_card_choice(hand, legal)
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
            if points > 0:
                print(f"Team {makers} scores {points} (alone!)")
            else:
                print(f"Team {1 - makers} euchres them for 2!")
        elif makers_tricks == 5:
            self.team_scores[makers] += 2
            print(f"Team {makers} scores 2")
        elif makers_tricks >= 3:
            self.team_scores[makers] += 1
            print(f"Team {makers} scores 1")
        else:
            self.team_scores[1 - makers] += 2
        print(f"Score: Team 0 = {self.team_scores[0]}, Team 1 = {self.team_scores[1]}")

    def play_hand(self):
        self.deal_new_hand()
        self.do_bidding()
        print(f"Trump is {self.state.trump.name}")
        if self.dev:
            for p, hand in enumerate(self.state.hands):
                print(f"Player {p} hand: {', '.join(str(c) for c in hand)}")
        else:
            # show only player 0's hand
            hand = self.state.hands[0]
            print(f"Your hand: {', '.join(str(c) for c in hand)}")
        # reset trick counts
        self.tricks_won = [0, 0]
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


def get_human_card_choice(hand: list['Card'], legal_moves: list['Card']) -> 'Card':
    # let human player pick a card from legal moves
    print("Your turn")
    print("Hand:")
    for i, card in enumerate(hand):
        print(f"{i}: {card}")
    print(f"Cards you can play: {[str(c) for c in legal_moves]}")

    while True:
        try:
            choice = int(input("Play card index: "))
            if 0 <= choice < len(hand) and hand[choice] in legal_moves:
                return hand[choice]
            else:
                print("Invalid choice. Must be a legal card from your hand.")
        except ValueError:
            print("Invalid input. Enter a number corresponding to your card index.")
