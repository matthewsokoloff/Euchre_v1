import random
from .card import Card, Suit, Rank

class Deck:
    def __init__(self):
        self.cards = [Card(s, r) for s in Suit for r in Rank]

    def shuffle(self):
        random.shuffle(self.cards)

    def deal(self, n):
        return [self.cards.pop() for _ in range(n)]