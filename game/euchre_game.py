from .deck import Deck
from .game_state import GameState
from .card import Card, Suit, Rank
from algorithm.ismcts import ISMCTS
from .rules import (is_right_bower, is_left_bower, effective_suit, card_value, throw_junk, find_lowest_card, decide_move, sister_suit, trick_winner, find_worst_card, remove_worst_card, is_single_in_suit, num_void_suits, is_void_suit, hand_strength, cards_to_win_trick, legal_moves)

class EuchreGame:
    def __init__(self, bot_types=None, human_player: int | None = None, debug=False):
        """ Initializes a Euchre game instance.

        Sets up the starting game state, bot configuration, scoring, and game tracking
        variables used during play.

        bot_types (list[str] | None): A list describing the type of
            player for each seat (length 4). Examples include
            "human", "heuristic", or "ismcts". If None, all players
            default to heuristic bots.

        human_player (int | None): The player index (0–3) that is
            controlled by a human. If None, all players are bots.

        debug (bool): If True, enables debugging output such as ISMCTS
        stats and internal game information."""

        self.state = GameState(hands=[[] for _ in range(4)], dealer=3, trump=None, trick=[], scores=[0, 0], current_player=0, leader=0) # dealer = 3 sends first deal to player 0

        self.bot_types = bot_types or ["heuristic"] * 4
        self.debug = debug
        self.ismcts_bot = ISMCTS(simulations=600, debug=debug)

        self.team_scores = [0, 0]
        self.human_player = human_player
        self.state.leader = self.state.current_player
        self.makers_team = None
        self.maker_index = None
        self.alone = False
        self.tricks_won = [0, 0]

    def deal_new_hand(self):
        """deals a new hand"""
        self.deck = Deck()
        self.deck.shuffle()
        self.state.hands = [self.deck.deal(5) for _ in range(4)]
        self.state.trick.clear()
        self.state.dealer = (self.state.dealer + 1) % 4
        self.state.current_player = (self.state.dealer + 1) % 4
        self.state.leader = self.state.current_player
        self.tricks_won = [0, 0]
        self.state.upcard = self.deck.deal(1)[0]

    def choose_trump(self, hand: list[Card], forbidden: Suit | None = None, round_number: int = 1, upcard: Card | None = None, dealer: bool = False):
        """chooses trump. returns a tuple of the suit and the alone boolean"""
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
        """handles the bidding for both round one and two. prints"""
        dealer = self.state.dealer

        print(f"\nUpcard: {self.state.upcard}")

        # ROUND 1
        for i in range(4):
            player = (dealer + 1 + i) % 4
            print(f"Player {player} bidding...")

            if player == self.human_player:
                suit, alone = self.human_bid(player, 1)

            else:
                suit, alone = self.choose_trump(self.state.hands[player], round_number=1, upcard=self.state.upcard, dealer=(player == dealer),)

            if suit == self.state.upcard.suit:
                print(f"Player {player} orders it up!")

                self.state.trump = suit
                self.makers_team = player % 2
                self.maker_index = player
                self.alone = alone

                if player == dealer:

                    if dealer == self.human_player:
                        self.state.hands[dealer].append(self.state.upcard)
                        self.human_discard(dealer)
                    else:
                        self.state.hands[dealer] = remove_worst_card(self.state.hands[dealer], self.state.upcard,suit,)
                return
            else:
                print("Pass")

        # ROUND 2
        print("\nSecond round of bidding")

        for i in range(4):
            player = (dealer + 1 + i) % 4
            print(f"Player {player} bidding...")

            if player == self.human_player:
                suit, alone = self.human_bid(player, 2, forbidden=self.state.upcard.suit)

            else:
                suit, alone = self.choose_trump(
                    self.state.hands[player],
                    forbidden=self.state.upcard.suit,
                    round_number=2,
                )

            if suit:
                print(f"Player {player} calls {suit}")

                self.state.trump = suit
                self.makers_team = player % 2
                self.maker_index = player
                self.alone = alone
                return
            else:
                print("Pass")

        # Stick the dealer
        print("\nDealer is stuck!")

        dealer = self.state.dealer

        if dealer == self.human_player:
            suit, alone = self.human_bid(dealer, 2, forbidden=self.state.upcard.suit)
        else:
            suit, alone = self.choose_trump(
                self.state.hands[dealer],
                forbidden=self.state.upcard.suit,
                round_number=3,
            )

        print(f"Dealer calls {suit}")

        self.state.trump = suit
        self.makers_team = dealer % 2
        self.maker_index = dealer
        self.alone = alone

    def play_tricks(self):
        """handles trick play. returns player number of the trick winners"""
        trump = self.state.trump
        leader = (self.state.dealer + 1) % 4
        trick_winners = []

        for _ in range(5):
            trick = []
            for offset in range(4):
                player = (leader + offset) % 4
                if self.alone and player != self.maker_index and player % 2 == self.makers_team:
                    continue
                hand = self.state.hands[player]
                if self.bot_types[player] == "ismcts":
                    card_to_play = self.ismcts_bot.choose_card(self, player)
                else:
                    card_to_play = decide_move(hand, trick, trump, player % 2)
                hand.remove(card_to_play)
                trick.append((player, card_to_play))
            winner = trick_winner([c for _, c in trick], leader, trump)
            trick_winners.append(winner)
            leader = winner
        return trick_winners

    def score_hand(self, tricks: list[int]):
        """handles scoring. updates the score"""
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

    def play_hand(self):
        """plays a hand (5 tricks)"""
        self.deal_new_hand()
        self.do_bidding()
        print(f"Trump is {self.state.trump}")
        for p, hand in enumerate(self.state.hands):
            print(f"Player {p} hand: {', '.join(str(c) for c in hand)}")
        trick_winners = self.play_tricks()
        self.score_hand(trick_winners)

    def sim_game(self, verbose: bool = False):
        """plays a full game to 10 points. returns final scores and winning team."""
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

    def human_choose_card(self, player, trick):
        """handles choosing cards. returns the card the human chose"""
        hand = self.state.hands[player]
        trump = self.state.trump

        legal = legal_moves(hand, trick, trump)

        print("\nYour hand:")
        for i, c in enumerate(hand):
            marker = ""
            if c in legal:
                marker = "(legal)"
            print(f"{i}: {c} {marker}")

        while True:
            choice = input("Choose card index: ")

            if not choice.isdigit():
                print("Enter a number.")
                continue

            idx = int(choice)

            if idx < 0 or idx >= len(hand):
                print("Invalid index.")
                continue

            card = hand[idx]

            if card not in legal:
                print("You must follow suit.")
                continue

            return card

    def play_tricks_human(self):
        """handles human playing tricks. returns the player number of the trick winners."""
        trump = self.state.trump
        leader = (self.state.dealer + 1) % 4
        trick_winners = []

        for t in range(5):
            print(f"\n=== Trick {t + 1} ===")

            trick = []

            for offset in range(4):
                player = (leader + offset) % 4
                self.state.current_player = player

                if self.alone and player != self.maker_index and player % 2 == self.makers_team:
                    continue

                hand = self.state.hands[player]

                if player == self.human_player:
                    card = self.human_choose_card(player, trick)

                elif self.bot_types[player] == "ismcts":
                    card = self.ismcts_bot.choose_card(self, player)

                else:
                    card = decide_move(hand, trick, trump, player % 2)

                hand.remove(card)
                trick.append((player, card))
                self.state.trick.append((player, card))

                print(f"Player {player} plays {card}")

            winner = trick_winner([c for _, c in trick], leader, trump)
            self.state.trick.clear()
            print(f"Player {winner} wins the trick")

            trick_winners.append(winner)
            leader = winner

        return trick_winners

    def play_game_human(self):
        """handles full gameplay"""
        print("Starting Euchre!")

        while max(self.team_scores) < 10:

            self.deal_new_hand()

            print("\n==========================")
            print(f"Dealer: Player {self.state.dealer}")
            print(f"Upcard: {self.state.upcard}")
            print("==========================")

            print("\nYour hand:")
            for c in self.state.hands[self.human_player]:
                print(c)

            self.do_bidding()

            print(f"\nTrump is {self.state.trump}")

            trick_winners = self.play_tricks_human()

            self.score_hand(trick_winners)

            print("\nScore:")
            print(f"Team 0: {self.team_scores[0]}")
            print(f"Team 1: {self.team_scores[1]}")

        winner = 0 if self.team_scores[0] > self.team_scores[1] else 1
        print(f"\nTeam {winner} wins!")

    def human_bid(self, player, round_number, forbidden=None):
        """allows the human player to bid and returns their choice"""
        print("\nYour hand:")
        for c in self.state.hands[player]:
            print(c)

        if round_number == 1:
            print(f"\nUpcard is {self.state.upcard}")
            choice = input("Order it up? (y/n): ").lower()

            if choice == "y":
                alone = input("Go alone? (y/n): ").lower() == "y"
                return self.state.upcard.suit, alone
            return None, False

        else:
            print("\nCall a suit or pass.")
            print("Options: hearts, diamonds, clubs, spades, pass")

            while True:
                choice = input("Your call: ").lower()

                if choice == "pass":
                    return None, False

                suit_map = {
                    "hearts": Suit.HEARTS,
                    "diamonds": Suit.DIAMONDS,
                    "clubs": Suit.CLUBS,
                    "spades": Suit.SPADES,
                }

                if choice in suit_map:
                    suit = suit_map[choice]

                    if suit == forbidden:
                        print("Cannot choose the upcard suit.")
                        continue

                    alone = input("Go alone? (y/n): ").lower() == "y"
                    return suit, alone

                print("Invalid input.")

    def human_discard(self, dealer):
        """allows the human player to discard. returns (nothing) when the human player has discarded."""
        hand = self.state.hands[dealer]

        print("\nYou picked up the upcard.")
        print("Choose a card to discard:\n")

        for i, c in enumerate(hand):
            print(f"{i}: {c}")

        while True:
            choice = input("Discard index: ")

            if not choice.isdigit():
                continue

            idx = int(choice)

            if 0 <= idx < len(hand):
                hand.pop(idx)
                return
