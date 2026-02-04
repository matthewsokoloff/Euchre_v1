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
        # empty for now
        # should deal, bid, print hands (optional), play tricks, and score
        print("empty")

    def sim_hand(self):
        # this should be for if you set the hand. or, could put this into play_hand
        print("empty")

    def set_hands(self):
        # empty for now
        # set the hands for testing/simulations
        print("empty")

    def remove_card_from_hand(self):
        # empty for now
        # if dealer is ordered up, will remove the card from their hand
        # should call card_to_remove from rules.py
        print("empty")

    def sim_game(self):
        # empty for now
        print("emtpy")
        # a game goes until one team gets 10 or more points
