from .deck import Deck
from .game_state import GameState
from .card import Card, Suit, Rank
from .rules import is_right_bower, is_left_bower, effective_suit, legal_moves, decide_card, trick_winner, hand_strength, card_to_remove

class EuchreGame:
    def __init__(self, human_player: int | None = None):

        self.state = GameState(
            hands=[[] for _ in range(4)],
            dealer=3,   # so first deal goes to play 0
            trump=None,
            trick=[],
            scores=[0,0],
            current_player=0,
            leader=0)

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
        # empty for now, to hold bidding code
        # will use files from rules.py to bid
        # go through round 1 and 2 bidding

        print("Nothing here for bidding yet")

    def choose_trump_heuristic(self) -> 'Suit | None':
        # empty for now, for round 2 bidding
        # a param must be the forbidden suit
        # should use hand_strength from rules.py to decide
        # if the dealer is stuck, must include that
        # dealer stuck = must call trump even if bad cards
        # dealer stuck could go in bidding, if choose_trump
        # returns None to stuck dealer, choose on max # trump
        print("empty")
        return None

    def play_tricks(self):
        # empty for now
        # should return the trick winners
        # must account for loners
        return None

    def score_hand(self, tricks: list[int]):
        # empty for now
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
