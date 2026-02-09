# tests for the functions in rules.py
from game.card import Card, Suit, Rank
from game.rules import (is_right_bower, is_left_bower, effective_suit, card_value,
    throw_junk, find_lowest_card, decide_move, sister_suit, trick_winner,
    find_worst_card, remove_worst_card, is_single_in_suit, num_void_suits,
    is_void_suit, hand_strength, cards_to_win_trick, legal_moves)

def test_all():
    print("=== Bower Tests ===")
    right = Card(Suit.HEARTS, Rank.JACK)
    left = Card(Suit.DIAMONDS, Rank.JACK)
    normal = Card(Suit.SPADES, Rank.ACE)
    trump = Suit.HEARTS

    assert is_right_bower(right, trump)
    assert not is_left_bower(right, trump)
    assert is_left_bower(left, trump)
    assert effective_suit(left, trump) == Suit.HEARTS
    assert card_value(right, trump) == 1000
    assert card_value(left, trump) == 900
    assert card_value(normal, trump) == 14
    print("Bower tests passed!")

    print("\n=== Legal Moves Tests ===")
    hand = [right, left, normal, Card(Suit.CLUBS, Rank.NINE)]
    trick = [(1, Card(Suit.HEARTS, Rank.ACE))]
    legal = legal_moves(hand, trick, trump)
    assert all(effective_suit(c, trump) == Suit.HEARTS for c in legal)
    print("Legal moves when following HEARTS lead:", legal)
    assert legal_moves(hand, [], trump) == hand
    print("Legal moves when leading:", hand)

    print("\n=== Throw Junk / Lowest Card Tests ===")
    singleton_hand = [Card(Suit.DIAMONDS, Rank.NINE), right, normal]
    junk_card = throw_junk(singleton_hand, trump)
    assert junk_card.suit == Suit.DIAMONDS  # singleton should be played
    lowest = find_lowest_card(hand, trump)
    print("Junk card chosen (singleton exists):", junk_card)
    print("Lowest card in hand:", lowest)

    print("\n=== Single / Void Suit Tests ===")
    assert is_single_in_suit(singleton_hand, Suit.DIAMONDS, singleton_hand[0], trump)
    assert num_void_suits(singleton_hand, trump) == 1
    assert is_void_suit(singleton_hand, Suit.CLUBS, trump)
    print("Single / void tests passed!")

    print("\n=== Trick Winner Test ===")
    trick_cards = [
        Card(Suit.HEARTS, Rank.NINE),
        Card(Suit.SPADES, Rank.ACE),
        Card(Suit.HEARTS, Rank.JACK),
        Card(Suit.CLUBS, Rank.ACE)
    ]
    winner = trick_winner(trick_cards, 0, trump)
    print("Trick winner index:", winner)
    assert winner == 2  # right bower wins

    print("\n=== Sister Suit Test ===")
    assert sister_suit(Suit.HEARTS) == Suit.DIAMONDS
    assert sister_suit(Suit.SPADES) == Suit.CLUBS
    print("Sister suit tests passed!")

    print("\n=== Find Worst Card Test ===")
    worst = find_worst_card(hand, trump)
    print("Worst card in hand:", worst)

    print("\n=== Remove Worst Card Test ===")
    upcard = Card(Suit.SPADES, Rank.TEN)
    new_hand = remove_worst_card(hand.copy(), upcard, trump)
    assert upcard in new_hand
    print("Hand after removing worst and adding upcard:", new_hand)

    print("\n=== Decide Move Test ===")
    trick = [(1, Card(Suit.HEARTS, Rank.NINE))]
    move = decide_move(hand, trick, trump, my_id=0)
    print("Decide move result:", move)

    print("\n=== Hand Strength Test ===")
    strength = hand_strength(trump, hand.copy(), upcard, dealer=True)
    print("Hand strength:", strength)

def test_edge_cases():
    print("\n=== Edge Case Tests ===")

    # Setup hand and trump
    trump = Suit.SPADES
    hand = [
        Card(Suit.SPADES, Rank.JACK),   # Right bower
        Card(Suit.CLUBS, Rank.JACK),    # Left bower
        Card(Suit.HEARTS, Rank.ACE),    # Off-suit ace
        Card(Suit.DIAMONDS, Rank.KING),
        Card(Suit.CLUBS, Rank.NINE)
    ]

    # Test card values
    assert card_value(hand[0], trump) == 1000
    assert card_value(hand[1], trump) == 900
    assert card_value(hand[2], trump) == 14
    assert card_value(hand[3], trump) == 13
    print("Card values test passed!")

    # Test legal moves following a lead
    trick = [(1, Card(Suit.HEARTS, Rank.KING))]
    legal = legal_moves(hand, trick, trump)
    assert all(effective_suit(c, trump) == Suit.HEARTS for c in legal)
    print("Legal moves following HEARTS lead:", legal)

    # Test throw_junk with no singletons (should pick lowest non-trump)
    junk = throw_junk(hand, trump)
    assert junk.suit in [Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS]
    print("Throw junk (no singletons) result:", junk)

    # Test cards_to_win_trick
    legal_plays = hand.copy()
    winning_cards = cards_to_win_trick(legal_plays, trick, trump)
    assert hand[0] in winning_cards  # Right bower should win
    print("Cards that can win the trick:", winning_cards)

    # Test trick winner when multiple trump played
    trick_cards = [
        Card(Suit.HEARTS, Rank.KING),
        Card(Suit.SPADES, Rank.NINE),
        Card(Suit.SPADES, Rank.JACK),   # Right bower
        Card(Suit.CLUBS, Rank.ACE)
    ]
    winner = trick_winner(trick_cards, leader=0, trump=trump)
    assert winner == 2
    print("Trick winner with trump cards:", winner)

    # Test find_worst_card
    worst = find_worst_card(hand, trump)
    print("Worst card in hand:", worst)

    # Test hand_strength with dealer and upcard
    upcard = Card(Suit.HEARTS, Rank.JACK)
    strength = hand_strength(trump, hand.copy(), upcard, dealer=True)
    print("Hand strength (with dealer and upcard):", strength)

    # Test sister suit function
    assert sister_suit(Suit.SPADES) == Suit.CLUBS
    assert sister_suit(Suit.HEARTS) == Suit.DIAMONDS
    print("Sister suit tests passed!")

if __name__ == "__main__":
    test_all()
    test_edge_cases()