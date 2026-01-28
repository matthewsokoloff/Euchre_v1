import random
from .card import Card, Suit, Rank

def is_right_bower(card: Card, trump: Suit) -> bool:
    # the right bower is the Jack of trump
    # empty for now
    return False;

def is_left_bower(card: Card, trump: Suit) -> bool:
    # the left bower is the jack of the same color suit as trump
    # empty for now
    return False;

def effective_suit(card: Card, trump: Suit) -> Suit:
    # Returns the suit the card acts as (accounts for left bower)
    if is_left_bower(card, trump):
        return trump
    return card.suit

def legal_moves():
    # empty for now, parameters also empty
    # should return a list of cards the player can play (-> list['Card'])
    return None

def decide_card():
    # empty for now, param also empty
    # should return the card the user should play
    # should take a list of the legal moves based on the player's hand
    # if forced to play, play
    # otherwise, should decide what to play based on the current trick state
    # if the trick is lost, throw junk (separate func?)
    # must decide whether to take trick from partner or not
    # otherwise, play winning card
    return None

def trick_winner():
    # empty, param empty
    # should return the int of the player (0-3) who won the trick
    # highest number card wins. assign right bower 100, left 90, trump + 50
    # if not trump go by card #
    return None

def hand_strength():
    # empty, param empty
    # should return the strength of the hand for a given trump suit
    # decide based on num of trump, ranking of trump, off suit aces
    # maybe based on void suits and or singles if dealer (discardability?)
    # will be used for bidding
    # (in bidding, in euchre, will decide if player should go alone based off of value)
    return None

def card_to_remove():
    # empty for now, param empty too
    # must return a card for the dealer to remove from their hand
    # cannot be upcard
    # should consider what the trump is
    # discard either a junk card, or discard a card to get a void suit (trumpability)
    return None
