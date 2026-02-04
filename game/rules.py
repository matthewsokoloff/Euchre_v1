import random
from .card import Card, Suit, Rank

def is_right_bower(card: Card, trump: Suit) -> bool:
    # the right bower is the Jack of trump
    return card.rank == Rank.JACK and card.suit == trump

def is_left_bower(card: Card, trump: Suit) -> bool:
    # the left bower is the jack of the same color suit as trump
    if trump in [Suit.HEARTS, Suit.DIAMONDS]:
        return card.rank == Rank.JACK and card.suit == (Suit.DIAMONDS if trump == Suit.HEARTS else Suit.HEARTS)
    else:
        return card.rank == Rank.JACK and card.suit == (Suit.CLUBS if trump == Suit.SPADES else Suit.SPADES)

def effective_suit(card: Card, trump: Suit) -> Suit:
    # Returns the suit the card acts as (accounts for left bower)
    if is_left_bower(card, trump):
        return trump
    return card.suit

def legal_moves(hand: list['Card'], trick: list[tuple[int,'Card']], trump: 'Suit') -> list['Card']:
    # Returns a list of cards the player can legally play.
    if not trick:
        return hand[:]  # can lead anything

    lead_card = trick[0][1]
    lead_suit = effective_suit(lead_card, trump)

    # Must follow suit if possible
    follow = [c for c in hand if effective_suit(c, trump) == lead_suit]
    return follow if follow else hand[:]

def decide_card(card: Card, lead_suit: Suit, trump: Suit, trick: list[Card] = None) -> float:

    # NEEDS FIXING

    # should return the card the user should play
    # should take a list of the legal moves based on the player's hand
    # if forced to play, play
    # otherwise, should decide what to play based on the current trick state
    # if the trick is lost, throw junk (separate func?)
    # must decide whether to take trick from partner or not
    # otherwise, play winning card

    # should return a numeric strength for comparing cards in a trick.
    eff_suit = effective_suit(card, trump)

    # Base strength
    if is_right_bower(card, trump):
        base_value = 1000
    elif is_left_bower(card, trump):
        base_value = 1000  # same as right bower for ranking purposes
    elif eff_suit == trump:
        base_value = 500 + card.rank.value * 10
    elif trick and eff_suit == effective_suit(trick[0], trump):
        base_value = 300 + card.rank.value * 5
    else:
        base_value = card.rank.value  # off-suit junk

    # Adjust based on trick state
    if trick:
        # Highest card in the trick so far
        def card_rank_for_trick(c: Card) -> int:
            c_eff = effective_suit(c, trump)
            if is_right_bower(c, trump):
                return 1000
            elif is_left_bower(c, trump):
                return 1000
            elif c_eff == trump:
                return 500 + c.rank.value * 10
            elif c_eff == effective_suit(trick[0], trump):
                return 300 + c.rank.value * 5
            else:
                return c.rank.value

        highest_so_far = max(card_rank_for_trick(c) for c in trick)

        # Determine if card can win
        if base_value >= highest_so_far:
            # Winning card - prefer low  winning cards
            base_value = 400 + card.rank.value
        else:
            # Losing card: junk slightly higher than absolute losing
            if eff_suit == trump or eff_suit == effective_suit(trick[0], trump):
                # mid-strength losing card: keep modest value
                base_value = 200 + card.rank.value
            else:
                # pure junk: very low
                base_value = 50 + card.rank.value / 10

    return base_value

def trick_winner(trick: list[Card], leader: int, trump: Suit) -> int:
    """Returns the index (0-3) of the winner of the trick."""

    # should return the int of the player (0-3) who won the trick
    # highest number card wins. assign right bower 100, left 90, trump + 50
    # if not trump go by card #

    lead_suit = effective_suit(trick[0], trump)
    best_idx = 0
    best_value = -1

    for i, card in enumerate(trick):
        eff_suit = effective_suit(card, trump)

        # Assign numeric value for comparison
        if is_right_bower(card, trump):
            value = 1000
        elif is_left_bower(card, trump):
            value = 900
        elif eff_suit == trump:
            value = 500 + card.rank.value
        elif eff_suit == lead_suit:
            value = 100 + card.rank.value
        else:
            value = 0

        if value > best_value:
            best_value = value
            best_idx = i

    return best_idx

def hand_strength():
    # empty, param empty
    # NEEDS FIXING
    # should return the strength of the hand for a given trump suit
    # decide based on num of trump, ranking of trump, off suit aces
    # maybe based on void suits and or singles if dealer (discardability?)
    # will be used for bidding
    # (in bidding, in euchre, will decide if player should go alone based off of value)
    return None

def card_to_remove():
    # empty for now, param empty too
    # NEEDS FIXING
    # must return a card for the dealer to remove from their hand
    # cannot be upcard
    # should consider what the trump is
    # discard either a junk card, or discard a card to get a void suit (trumpability)
    return None
