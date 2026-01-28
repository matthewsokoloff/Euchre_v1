from dataclasses import dataclass
from typing import List, Optional
from .card import Card, Suit

@dataclass
class GameState:
    hands: List[List[Card]]
    dealer: int
    trump: Optional[Suit]
    trick: List[Card]
    scores: List[int]
    current_player: int
    leader: int
    upcard: Optional[Card] = None
