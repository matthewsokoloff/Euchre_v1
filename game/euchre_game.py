from .deck import Deck
from .game_state import GameState
from .card import Card, Suit, Rank
from algorithm.ismcts import ISMCTS
from .rules import is_right_bower, is_left_bower, effective_suit, legal_moves, decide_move, trick_winner, hand_strength

class EuchreGame:
    def __init__(self, human_player: int | None = None):

        self.state = GameState(
            hands = [[] for _ in range(4)],
            dealer = 3,   # so first deal goes to play 0
            trump = None,
            trick = [],
            scores = [0,0],
            current_player = 0,
            leader = 0)

        self.team_scores = [0,0] # team 0 and team 1
        self.human_player = human_player # store which player is human

        self.state.leader = self.state.current_player

        self.makers_team = None # team of the player who called trump
        self.maker_index = None # player index who called trump
        self.alone = False # whether maker called alone

    def deal_new_hand(self):
        # build and shuffle a new deck
        self.deck = Deck()
        self.deck.shuffle()

        self.state.hands = [self.deck.deal(5) for _ in range(4)]
        self.state.trick.clear()

        # make the dealer rotate
        self.state.dealer = (self.state.dealer + 1) % 4
        self.state.current_player = (self.state.dealer + 1) % 4
        self.state.leader = self.state.current_player

        # reset the trick counts
        self.tricks_won = [0,0]

        # get the upcard (next undealt card, to be bid on)
        self.state.upcard = self.deck.deal(1)[0]
        print(f"The upcard is {self.state.upcard}")

    def do_bidding(self):
        self.makers_team = None
        self.alone = False
        dealer = self.state.dealer

        print(f"Dealer is player {dealer}")
        print(f"Upcard is {self.state.upcard}\n")

        # --- Round 1: Order up ---
        for i in range(4):
            player = (dealer + 1 + i) % 4

            # Prepare hand to evaluate
            if player == dealer:
                hand_for_eval = self.state.hands[player] + [self.state.upcard]
            else:
                hand_for_eval = self.state.hands[player]

            # Evaluate trump for this hand
            suit, alone = self.choose_trump_heuristic(
                hand_for_eval,
                forbidden=None,
                player=player,
                round_number=1,
                upcard=self.state.upcard
            )

            if suit == self.state.upcard.suit:
                # This player orders up the upcard as trump
                self.state.trump = suit
                self.makers_team = player % 2
                self.maker_index = player
                self.alone = alone
                print(f"Player {player} orders up {self.state.trump.name}"
                    f"{' and goes alone!' if self.alone else ''}\n")

                # Dealer picks up upcard
                dealer_hand = self.state.hands[dealer]
                dealer_hand.append(self.state.upcard)
                print(f"Dealer (Player {dealer}) picks up upcard {self.state.upcard}")

                # Discard weakest card
                discard = min(dealer_hand, key=lambda c: (
                    1000 if is_right_bower(c, suit) else
                    900 if is_left_bower(c, suit) else
                    500 + c.rank.value if effective_suit(c, suit) == suit else
                    c.rank.value
                ))
                dealer_hand.remove(discard)
                print(f"Dealer (Player {dealer}) discards {discard}\n")

                return

            else:
                print(f"Player {player} passes\n")

        # --- Round 2: call trump (excluding upcard suit) ---
        for i in range(4):
            player = (dealer + 1 + i) % 4
            hand_for_eval = self.state.hands[player]

            suit, alone = self.choose_trump_heuristic(
                hand_for_eval,
                forbidden=self.state.upcard.suit,
                player=player,
                round_number=2
            )

            if suit:
                self.state.trump = suit
                self.makers_team = player % 2
                self.maker_index = player
                self.alone = alone
                print(f"Player {player} calls {self.state.trump.name}"
                    f"{' and goes alone!' if self.alone else ''}\n")
                return
            else:
                print(f"Player {player} passes\n")

        # --- Stick the dealer ---
        dealer_hand = self.state.hands[dealer]  # do NOT include upcard in round 2
        suit, alone = self.choose_trump_heuristic(dealer_hand, forbidden=None)
        if suit is None:
            # fallback: pick suit with most cards
            suit_counts = {s: 0 for s in Suit}
            for card in dealer_hand:
                eff_suit = effective_suit(card, Suit.HEARTS)  # HEARTS is safe as dummy trump
                if eff_suit in suit_counts:  # just to be safe
                    suit_counts[eff_suit] += 1
                else:
                    print(f"Warning: unexpected effective suit {eff_suit} for card {card}")
            suit = max(suit_counts, key=suit_counts.get)
            alone = False

        self.state.trump = suit
        self.makers_team = dealer % 2
        self.alone = alone
        print(f"Dealer (Player {dealer}) is forced to call {self.state.trump.name} "
            f"(RULE: Stick the Dealer{' and goes alone!' if self.alone else ''})")

    def choose_trump_heuristic(self, hand, forbidden=None, player=None, round_number=1, upcard=None):

        # NEEDS FIXING

        best_score = 0

        for suit in Suit:
            if suit == forbidden:
                continue

            trump_count = 0
            high_cards = 0
            for card in hand:
                eff_suit = effective_suit(card, suit)
                if eff_suit == suit:
                    trump_count += 1
                    if card.rank in [Rank.ACE, Rank.KING, Rank.QUEEN, Rank.JACK]:
                        high_cards += 1

            strength = trump_count + high_cards / 2
            if round_number == 1 and upcard and suit == upcard.suit:
                strength += 0.5

            if strength > best_score:
                best_score = strength
                best_suit = suit

        # Decide if going alone
        alone = False
        trump_cards = [c for c in hand if effective_suit(c, best_suit) == best_suit]
        high_trump = [c for c in trump_cards if c.rank in [Rank.ACE, Rank.KING, Rank.QUEEN, Rank.JACK]]
        if (len(trump_cards) >= 4 and len(high_trump) >= 2) or (len(trump_cards) >= 3 and len(high_trump) >= 3):
            alone = True

        # Round 1 requires stronger hands to order up
        min_strength = 4.5 if round_number == 1 else 3.5
        if best_score >= min_strength:
            return best_suit, alone
        return None, False

    def play_tricks(self):
        # plays all 5 tricks in the hand
        # skips partner if maker goes alone
        # returns a list of indices of winning players for each trick

        trump = self.state.trump
        leader = (self.state.dealer + 1) % 4  # first lead: left of dealer
        trick_winners = []

        for trick_num in range(5):
            print(f"\n--- Trick {trick_num + 1} ---")
            trick = []

            for offset in range(4):
                player = (leader + offset) % 4

                # skip partner if maker goes alone
                if (
                        self.alone
                        and player != self.maker_index
                        and player % 2 == self.makers_team
                ):
                    print(f"Player {player} sits out (partner is going alone)")
                    continue

                hand = self.state.hands[player]
                legal = legal_moves(hand, trick, trump)

                if not legal:
                    raise ValueError(f"No legal moves for player {player}")

                # ---------------- Player 0 (ISMCTS) ----------------
                if player == 0:
                    print(f"\n--- ISMCTS TURN (Player {player}) ---\nCurrent trick:")
                    if trick:
                        for p, c in trick:
                            print(f"  Player {p}: {c}")
                    else:
                        print("  (Lead)")

                    print("\nISMCTS hand:")
                    for c in hand:
                        print(f"  {c}")

                    input("\nPress ENTER to let ISMCTS choose a card...")

                    ismcts_bot = ISMCTS(simulations=300, debug=True)
                    chosen = ismcts_bot.choose_card(self, player)

                    # force legality
                    if chosen not in legal:
                        if len(legal) == 1:
                            chosen = legal[0]
                        else:
                            # fallback to heuristic
                            chosen = decide_move(hand, trick, trump, player % 2)

                    card_to_play = next(
                        c for c in hand
                        if c.suit == chosen.suit and c.rank == chosen.rank
                    )

                # ---------------- Heuristic Bots ----------------
                else:
                    card_to_play = decide_move(
                        hand=hand,
                        trick=trick,
                        trump=trump,
                        my_id=player % 2
                    )

                self.remove_card_from_hand(hand, card_to_play)
                trick.append((player, card_to_play))
                print(f"Player {player} plays {card_to_play}")

            # determine winner of the trick
            trick_cards = [c for _, c in trick]
            winner = trick_winner(trick_cards, leader, trump)

            print(f"Player {winner} wins the trick!")
            trick_winners.append(winner)

            # winner leads next trick
            leader = winner

        return trick_winners

    def score_hand(self, tricks: list[int]):
        # scores the hand (all 5 tricks)
        # makers = team that called trump
        # defenders = other team
        # if the makers get 5, 2 pts. 3-4, 1 pt. <3, 0 pts.
        # if the defenders get 0-2, 0 pts. >2, 2 pts. (euchre)
        if self.makers_team is None:
            raise ValueError("Maker team not set! Cannot score hand") # error catching

        makers = self.makers_team

        # count tricks won by each team
        team_tricks = [0, 0]
        for winner in tricks:
            team_tricks[winner % 2] += 1

        makers_tricks = team_tricks[makers]
        defenders_tricks = team_tricks[1 - makers]

        if self.alone:
            print(f"Team {makers}'s maker went alone!")

        if makers_tricks < 3:
            # Euchred
            self.team_scores[1 - makers] += 2
            print(f"Makers (team {makers}) euchred! Defenders get 2 points.")
        elif makers_tricks == 5:
            # Sweep (all)
            points = 4 if self.alone else 2 # loner sweep gets 4, normal sweep gets 2
            self.team_scores[makers] += points
            print(f"Makers (team {makers}) took all 5 tricks! +{points} points")
        else:
            # Normal
            self.team_scores[makers] += 1
            print(f"Makers (team {makers}) made their bid! +1 point.")
        return None

    def play_hand(self):
        self.deal_new_hand()  # deal cards and set upcard
        self.do_bidding()  # choose trump
        print(f"\nTrump is {self.state.trump}")
        # show hands
        for p, hand in enumerate(self.state.hands):
            print(f"Player {p} hand: " + ", ".join(str(c) for c in hand))
        # play tricks
        trick_winners = self.play_tricks()
        # score
        self.score_hand(trick_winners)
        print(f"Score: Team 0 = {self.team_scores[0]}, Team 1 = {self.team_scores[1]}")

    def sim_hand(self):
        # Only deal if hands/upcard not already set
        if not getattr(self.state, "hands", None) or not any(self.state.hands):
            self.deal_new_hand()

        if not getattr(self.state, "upcard", None):
            # fallback: deal upcard if missing
            self.state.upcard = self.deck.deal(1)[0]

        self.do_bidding()  # bot chooses trump
        print(f"\nTrump is {self.state.trump}\n")

        # Play hand
        trick_winners = self.play_tricks()
        self.score_hand(trick_winners)
        print(f"Score: Team 0 = {self.team_scores[0]}, Team 1 = {self.team_scores[1]}\n")
        return trick_winners

    def play_hand_with_ismcts(self, ismcts_bot):
        # Player 0 = ISMCTS
        self.deal_new_hand()
        self.do_bidding()
        print(f"\nTrump suit is {self.state.trump}")

        for p, hand in enumerate(self.state.hands):
            print(f"Player {p} hand: " + ", ".join(str(c) for c in hand))

        print("\n=== ISMCTS FULL HAND (AUTO SIMULATION) ===")
        leader = (self.state.dealer + 1) % 4
        trick_winners = []

        for trick_num in range(5):
            print(f"\n--- Trick {trick_num + 1} ---")
            trick = []

            for i in range(4):
                player = (leader + i) % 4
                hand = self.state.hands[player]

                # Skip partner if maker goes alone
                if self.alone and player != self.maker_index and player % 2 == self.makers_team:
                    print(f"Player {player} sits out (partner is going alone)")
                    continue

                legal = legal_moves(hand, trick, self.state.trump)
                if not legal:
                    legal = hand[:]  # safety fallback

                if player == 0:
                    # ISMCTS chooses card
                    chosen_card = ismcts_bot.choose_card(self, player)

                    # Ensure legality
                    if chosen_card not in legal:
                        chosen_card = decide_move(hand, trick, self.state.trump, player)

                    card_to_play = next(c for c in hand if c.suit == chosen_card.suit and c.rank == chosen_card.rank)
                else:
                    # Heuristic bots
                    # Use decide_move, which returns a Card from the hand
                    chosen_card = decide_move(hand, trick, self.state.trump, player)
                    card_to_play = next(c for c in hand if c.suit == chosen_card.suit and c.rank == chosen_card.rank)

                # Play the card
                self.remove_card_from_hand(hand, card_to_play)
                trick.append((player, card_to_play))
                print(f"Player {player} plays {card_to_play}{' (ISMCTS)' if player == 0 else ''}")

            # Determine trick winner
            trick_cards = [c for _, c in trick]
            winner_idx = trick_winner(trick_cards, 0, self.state.trump)
            leader = trick[winner_idx][0]
            print(f"Player {leader} wins the trick!")
            trick_winners.append(leader)

        # Score the hand
        self.score_hand(trick_winners)
        print(f"Score: Team 0 = {self.team_scores[0]}, Team 1 = {self.team_scores[1]}")

    def set_hands(self, hands: list[list['Card']], upcard: 'Card', dealer: int = 0):
        if len(hands) != 4:
            raise ValueError("Must provide 4 hands")
        for hand in hands:
            if len(hand) != 5:
                raise ValueError("Each hand must have 5 cards")

        self.state.hands = hands
        self.state.upcard = upcard
        self.state.dealer = dealer
        self.state.current_player = (dealer + 1) % 4
        self.state.leader = self.state.current_player

        # Reset scores for hand
        self.tricks_won = [0, 0]
        self.state.trump = None
        self.makers_team = None
        self.alone = False
        self.state.trick.clear()

        print(f"Test hands set. Dealer = Player {dealer}, Upcard = {upcard}")

    def remove_card_from_hand(self, hand: list['Card'], card: 'Card') -> None:
        for i, c in enumerate(hand):
            if c.suit == card.suit and c.rank == card.rank:
                del hand[i]
                return
        print("Hand contents:")
        for c in hand:
            print(f"  {c.rank} of {c.suit}")
        print("Card to remove:", card.rank, "of", card.suit)
        raise ValueError(f"Card {card} not found in hand!")

    def sim_game(self):
        print("=== Starting Euchre Simulation ===")
        while max(self.team_scores) < 10:  # a game plays to 10pts
            self.deal_new_hand()
            self.do_bidding()
            print(f"\nTrump suit is {self.state.trump}\n")

            # Play hand
            trick_winners = self.play_tricks()
            self.score_hand(trick_winners)
            print(f"Score: Team 0 = {self.team_scores[0]}, Team 1 = {self.team_scores[1]}\n")

        print("=== Game Over ===")
        if self.team_scores[0] > self.team_scores[1]:
            print("Team 0 wins!")
        else:
            print("Team 1 wins!")
