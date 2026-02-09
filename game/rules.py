import random
from .card import Card, Suit, Rank



# current needs to fix: calculate card strength, decide card, cards_to_win_trick, and need to do tests on all logic and stuff
# and implement this funcs in the gameplay

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

def card_value(card: Card, trump: Suit) -> int:
    # returns val for a card
    # right bower is 1000
    # left bower is 900
    # trump is the value + 100
    # non trump is just the value of the card
    value = card.rank.value
    eff_suit = effective_suit(card, trump)
    if is_right_bower(card, trump):
        return 1000
    elif is_left_bower(card, trump):
        return 900
    elif eff_suit == trump:
        value += 100
    return value

def legal_moves(hand: list['Card'], trick: list[tuple[int,'Card']], trump: 'Suit') -> list['Card']:
    # returns a list of cards the player can legally play.
    if not trick:
        return hand[:]  # can lead anything

    lead_card = trick[0][1]
    lead_suit = effective_suit(lead_card, trump)

    # must follow suit if possible
    follow = [card for card in hand if effective_suit(card, trump) == lead_suit]
    return follow if follow else hand[:]

def cards_to_win_trick(legal_plays: list['Card'], trick: list[tuple[int,'Card']], trump: 'Suit') -> list['Card'] or None:
    # returns a list of cards in the hand that will win a given trick
    # if it returns None, no cards will win a given trick
    card_list = legal_plays
    cards_to_win: list['Card'] = []
    current_max: int = -1
    val_of_card: int = 0

    for i, card in enumerate(card_list):
        val_of_card = card_value(card, trump)
        if val_of_card > current_max:
            current_max = val_of_card
            cards_to_win.append(card)

    # if there are any cards that will win a trick, return them
    if len(card_list) > 0:
        return card_list

    # if not, return None
    return None

def throw_junk(legal_plays: list['Card']) -> Card:
    # returns a junk card

    # if singleton, then void a suit
    # if not, throw the lowest card (use find_lowest_card)
    return legal_plays[0]

def find_lowest_card(cards: list['Card'], trump) -> Card:
    # returns the lowest card out of a list of cards
    minimum = 100000
    card_val = 0
    card_chosen: Card = cards[0]

    for i, card in enumerate(cards):
        card_val = card_value(card, trump)
        if card_val < minimum:
            minimum = card_val
            card_chosen = card
    return card_chosen

def decide_move(hand: list['Card'], trick: list[tuple[int,'Card']], trump: 'Suit', my_id) -> Card:
    # returns the card the bot should play
    # my_id is the player id % 2

    legal_plays: list['Card'] = legal_moves(hand, trick, trump)

    # forced play
    if len(legal_plays) == 1:
        return legal_plays[0]

    # if leading, lead the strongest legal card
    if not trick:
        return max(legal_plays, key=lambda c: card_value(c, trump))

    # find lead suit
    lead_suit = effective_suit(trick[0][1], trump)

    # find who's winning the trick right now
    winning_player, winning_card = trick[0]
    # if the current trick winner is partner, throw junk
    # else take cards_to_win_trick() and return the min
    return hand[0]

def sister_suit(suit) -> Suit:
    if suit == Suit.SPADES:
        return Suit.CLUBS
    if suit == Suit.CLUBS:
        return Suit.SPADES
    if suit == Suit.HEARTS:
        return Suit.DIAMONDS
    if suit == Suit.DIAMONDS:
        return Suit.HEARTS

# decide_card needs to be fixed
def decide_card(card: Card, lead_suit: Suit, trump: Suit, trick: list[Card] = None) -> float:

    # should return the best *legal* card that the user can play
    # get list of legal plays
    # if only one, play it
    # if the trick is lost, throw junk (separate func?)
    # if the trick is won by your partner, throw junk (try to single suit -> separate func?)
    # don't trump partner ace
    # if you made it, you should lead trump
    # otherwise you should try to win the trick


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
    # returns index 0-3 of player who won trick

    lead_suit = effective_suit(trick[0], trump)

    best_index = 0
    best_card = trick[0]

    for i in range(1, len(trick)):
        card = trick[i]

        best_suit = effective_suit(best_card, trump)
        card_suit = effective_suit(card, trump)

        # trump beats non-trump
        if card_suit == trump and best_suit != trump:
            best_card = card
            best_index = i
            continue

        if card_suit != trump and best_suit == trump:
            continue

        # both trump OR both non-trump
        if card_suit == best_suit:
            if card_value(card, trump) > card_value(best_card, trump):
                best_card = card
                best_index = i
            continue

        # neither trump → lead suit wins
        if card_suit == lead_suit and best_suit != lead_suit:
            best_card = card
            best_index = i
            continue

        # otherwise, best_card stays

    return (leader + best_index) % 4

def find_worst_card(hand: list['Card'], trump: Suit) -> Card:
    # returns the worst card in a hand (probably a card that should be discarded or thrown as junk)
    lowest_rank = 1000
    worst_card = hand[0]

    trump_count = 0
    for card in hand:
        if effective_suit(card, trump) == trump:
            trump_count += 1

    # if 5 trump, lowest trump is worst
    if trump_count == 5:
        for card in hand:
            if card.rank.value < lowest_rank:
                lowest_rank = card.rank.value
                worst_card = card
        return worst_card

    # if 4 trump → throw the lone non-trump
    if trump_count == 4:
        for card in hand:
            if effective_suit(card, trump) != trump:
                return card

    # try to void a non-trump suit
    for card in hand:
        eff_suit = effective_suit(card, trump)
        if eff_suit != trump and is_single_in_suit(hand, card.suit, card, trump):
            return card

    # otherwise throw lowest non-trump
    for card in hand:
        eff_suit = effective_suit(card, trump)
        if eff_suit != trump and card.rank.value < lowest_rank:
            lowest_rank = card.rank.value
            worst_card = card

    return worst_card

def remove_worst_card(hand: list['Card'], upcard: Card, trump: Suit) -> list['Card']:
    # returns the hand with the upcard, having removed the worst card
    worst_card = find_worst_card(hand, trump)
    hand.remove(worst_card)
    hand.append(upcard)
    return hand

def is_single_in_suit(hand: list['Card'], suit: Suit, card: Card, trump: Suit) -> bool:
    # returns a boolean for whether a card in a hand is the only one in the suit or not

    count_in_suit = 0

    for i, card in enumerate(hand):
        eff_suit = effective_suit(card, trump)
        if eff_suit == suit:
            count_in_suit += 1
    if count_in_suit == 1:
        return True
    return False

def num_void_suits(hand: list['Card'], trump) -> int:
    # returns the number of void suits in a hand (not counting trump, so a max of 3)
    void_count = 0
    if trump!= Suit.SPADES and is_void_suit(hand, Suit.SPADES, trump):
        void_count += 1
    if trump!= Suit.CLUBS and is_void_suit(hand, Suit.CLUBS, trump):
        void_count += 1
    if trump!= Suit.HEARTS and is_void_suit(hand, Suit.HEARTS, trump):
        void_count += 1
    if trump!= Suit.DIAMONDS and is_void_suit(hand, Suit.DIAMONDS, trump):
        void_count += 1
    return void_count

def is_void_suit(hand: list['Card'], suit: Suit, trump: Suit) -> bool:
    # returns whether a hand is void in a given suit
    for card in hand:
        eff_suit = effective_suit(card, trump)
        if eff_suit == suit:
            return False
    return True

def hand_strength(trump: Suit, hand: list['Card'], upcard: Card, dealer: bool):
    # returns a numeric value for the strength of a hand for a given trump
    strength = 0

    void_suits = num_void_suits(hand, trump)

    if dealer and upcard: # if there's an upcard, add upcard to hand and remove the worst card
        hand = remove_worst_card(hand, upcard, trump)

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
