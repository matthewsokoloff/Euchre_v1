import random
from .card import Card, Suit, Rank

def is_right_bower(card: Card, trump: Suit) -> bool:
    # the right bower is the Jack of trump
    return card.rank == Rank.JACK and card.suit == trump

def is_left_bower(card: Card, trump: Suit) -> bool:
    # the left bower is the jack of the same color suit as trump
    if card.rank == Rank.JACK:
        if trump == Suit.HEARTS and card.suit == Suit.DIAMONDS:
            return True
        elif trump == Suit.DIAMONDS and card.suit == Suit.HEARTS:
            return True
        elif trump == Suit.CLUBS and card.suit == Suit.SPADES:
            return True
        elif trump == Suit.SPADES and card.suit == Suit.CLUBS:
            return True
    return False

def effective_suit(card: Card, trump: Suit) -> Suit:
    # Returns the suit the card acts as (accounts for left bower)
    if is_left_bower(card, trump):
        return trump
    return card.suit

def legal_moves(hand: list['Card'], trick: list[tuple[int,'Card']], trump: 'Suit') -> list['Card']:
    # returns a list of cards the player can legally play.
    if not trick:
        return hand[:]  # can lead anything

    lead_card = trick[0][1]
    lead_suit = effective_suit(lead_card, trump)

    # must follow suit if possible
    follow = [card for card in hand if effective_suit(card, trump) == lead_suit]
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
        base_value = 900  # same as right bower for ranking purposes
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
    # returns the index of the player (0-3) who won the trick


    lead_suit = effective_suit(trick[0], trump)
    best_index = 0
    best_val = -1

    for i, card in enumerate(trick):
        eff_suit = effective_suit(card, trump)

        if is_right_bower(card, trump):
            value = 100
        elif is_left_bower(card, trump):
            value = 90
        elif eff_suit == trump:
            value = 50 + card.rank.value
        elif eff_suit == lead_suit:
            value = 10 + card.rank.value
        else:
            value = 0

        if value > best_val:
            best_val = value
            best_index = i

    return best_index

def remove_worst_card(hand: list['Card'], upcard) -> list['Card']:
    # should return the hand including the upcard, having removed the worst card
    # should remove (in order of pref):
    # not a trump
    # a card to single suit
    # a low card
    return hand

def num_void_suits(hand: list['Card'], trump) -> int:
    # returns the number of void suits in a hand (not counting trump, so a max of 3)
    void_count = 0
    if trump!= Suit.SPADES and is_void_suit(hand, Suit.SPADES):
        void_count += 1
    if trump!= Suit.CLUBS and is_void_suit(hand, Suit.CLUBS):
        void_count += 1
    if trump!= Suit.HEARTS and is_void_suit(hand, Suit.HEARTS):
        void_count += 1
    if trump!= Suit.HEARTS and is_void_suit(hand, Suit.HEARTS):
        void_count += 1
    return void_count

def is_void_suit(hand: list['Card'], suit: Suit) -> bool:
    # returns whether a hand is void in a given suit
    for i, card in enumerate(hand):
        eff_suit = effective_suit(card, suit)
        if eff_suit == suit:
            return False
    return True

def hand_strength(trump: Suit, hand: list['Card'], upcard: 'Card', dealer: bool):
    # returns a numeric value for the strength of a hand for a given trump
    strength = 0

    void_suits = num_void_suits(hand, trump)

    if dealer and upcard: # if there's an upcard, add upcard to hand and remove the worst card
        hand = remove_worst_card(hand, upcard)

    for i, card in enumerate(hand):
        eff_suit = effective_suit(card, trump)

        if eff_suit == trump:
            if is_right_bower(card, trump):
                strength += 4
            elif is_left_bower(card, trump):
                strength += 3
            elif card.rank == Rank.ACE:
                strength += 2
            elif card.rank == Rank.KING:
                strength += 1
            else:
                if void_suits > 0:
                    strength += 1
        elif card.rank == Rank.ACE:
            strength += 1
    return strength

def card_to_remove():
    # empty for now, param empty too
    # NEEDS FIXING
    # must return a card for the dealer to remove from their hand
    # cannot be upcard
    # should consider what the trump is
    # discard either a junk card, or discard a card to get a void suit (trumpability)
    return None
