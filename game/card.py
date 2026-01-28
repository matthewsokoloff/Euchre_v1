from enum import Enum
from dataclasses import dataclass

class Suit(Enum):
    SPADES = "S"
    HEARTS = "H"
    DIAMONDS = "D"
    CLUBS = "C"

class Rank(Enum):
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14

@dataclass(frozen=True)
class Card:
    suit: Suit
    rank: Rank

    def __str__(self):
        return f"{self.rank.name} of {self.suit.name}"