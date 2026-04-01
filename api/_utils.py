"""
Shared utilities for the Vercel API: serialization, deserialization, and the
turn-advance state machine that drives the game between human decisions.
"""
import sys
import os

# Make the project root importable from inside api/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.card import Card, Suit, Rank
from game.game_state import GameState
from game.rules import (
    legal_moves, remove_worst_card, trick_winner, decide_move
)

SUIT_SYMBOLS = {"S": "♠", "H": "♥", "D": "♦", "C": "♣"}
SUIT_NAMES   = {"S": "Spades", "H": "Hearts", "D": "Diamonds", "C": "Clubs"}
RANK_NAMES   = {9: "9", 10: "10", 11: "J", 12: "Q", 13: "K", 14: "A"}


# ---------------------------------------------------------------------------
# Card helpers
# ---------------------------------------------------------------------------

def card_to_dict(card):
    if card is None:
        return None
    return {"suit": card.suit.value, "rank": card.rank.value}


def dict_to_card(d):
    if d is None:
        return None
    return Card(suit=Suit(d["suit"]), rank=Rank(d["rank"]))


def card_display(card):
    if card is None:
        return "?"
    return f"{RANK_NAMES[card.rank.value]}{SUIT_SYMBOLS[card.suit.value]}"


# ---------------------------------------------------------------------------
# Game (de)serialization
# ---------------------------------------------------------------------------

def _make_game(state_data=None):
    """
    Build an EuchreGame-like object either fresh (state_data=None) or
    reconstructed from a previously serialised state dict.
    """
    from game.euchre_game import EuchreGame
    from algorithm.ismcts import ISMCTS

    game = EuchreGame.__new__(EuchreGame)

    if state_data:
        game.state = GameState(
            hands=[[dict_to_card(c) for c in h] for h in state_data["hands"]],
            dealer=state_data["dealer"],
            trump=Suit(state_data["trump"]) if state_data["trump"] else None,
            trick=[(int(p), dict_to_card(c)) for p, c in state_data["trick"]],
            scores=[0, 0],
            current_player=state_data["current_player"],
            leader=state_data["leader"],
        )
        game.state.upcard    = dict_to_card(state_data.get("upcard"))
        game.team_scores     = list(state_data["team_scores"])
        game.makers_team     = state_data.get("makers_team")
        game.maker_index     = state_data.get("maker_index")
        game.alone           = state_data.get("alone", False)
        game.tricks_won      = list(state_data["tricks_won"])
    else:
        game.state = GameState(
            hands=[[] for _ in range(4)],
            # dealer=3 so that the very first call to deal_new_hand() (which does
            # dealer = (dealer+1)%4) produces dealer=0, making player 1 the first
            # bidder and giving the human (player 0) a full first hand as dealer.
            dealer=3,
            trump=None,
            trick=[],
            scores=[0, 0],
            current_player=0,
            leader=0,
        )
        game.state.upcard = None
        game.team_scores  = [0, 0]
        game.makers_team  = None
        game.maker_index  = None
        game.alone        = False
        game.tricks_won   = [0, 0]

    game.bot_types    = ["human", "ismcts", "ismcts", "ismcts"]
    game.human_player = 0
    game.debug        = False
    game.ismcts_bot   = ISMCTS(simulations=100, debug=False)

    # ISMCTS reads these from game.state via getattr
    game.state.maker_index  = game.maker_index
    game.state.makers_team  = game.makers_team
    game.state.alone        = game.alone

    return game


def _serialize(game, phase, bid_round=1, bid_pos=0, trick_num=0):
    return {
        "hands":        [[card_to_dict(c) for c in h] for h in game.state.hands],
        "dealer":       game.state.dealer,
        "trump":        game.state.trump.value if game.state.trump else None,
        "trick":        [[p, card_to_dict(c)] for p, c in game.state.trick],
        "current_player": game.state.current_player,
        "leader":       game.state.leader,
        "upcard":       card_to_dict(getattr(game.state, "upcard", None)),
        "team_scores":  list(game.team_scores),
        "makers_team":  game.makers_team,
        "maker_index":  game.maker_index,
        "alone":        game.alone,
        "tricks_won":   list(game.tricks_won),
        "phase":        phase,
        "bid_round":    bid_round,
        "bid_pos":      bid_pos,
        "trick_num":    trick_num,
    }


# ---------------------------------------------------------------------------
# Helpers shared by advance functions
# ---------------------------------------------------------------------------

def _next_player(game, current):
    """Next active player, skipping the lone-maker's partner when going alone."""
    nxt = (current + 1) % 4
    if game.alone and game.maker_index is not None:
        partner = (game.maker_index + 2) % 4
        if nxt == partner:
            nxt = (nxt + 1) % 4
    return nxt


def _score_hand(game, messages):
    makers        = game.makers_team
    makers_tricks = game.tricks_won[makers]
    other         = 1 - makers

    if game.alone:
        if makers_tricks == 5:
            game.team_scores[makers] += 4
            messages.append(f"Went alone and swept all 5! Team {makers} +4 pts")
        else:
            game.team_scores[other] += 2
            messages.append(f"Alone bid failed — euchred! Team {other} +2 pts")
    elif makers_tricks == 5:
        game.team_scores[makers] += 2
        messages.append(f"Swept all 5 tricks! Team {makers} +2 pts")
    elif makers_tricks >= 3:
        game.team_scores[makers] += 1
        messages.append(f"Made the bid! Team {makers} +1 pt")
    else:
        game.team_scores[other] += 2
        messages.append(f"Euchred! Team {other} +2 pts")

    messages.append(
        f"Score → You+P2 (Team 0): {game.team_scores[0]}  |  "
        f"P1+P3 (Team 1): {game.team_scores[1]}"
    )


# ---------------------------------------------------------------------------
# State-machine: advance through bot bids until human's turn or bidding ends
# ---------------------------------------------------------------------------

def _advance_bidding(game, bid_round, bid_pos, messages):
    """
    Process bot bids in sequence until the human must act or trump is set.
    Returns (state_dict, messages, legal_card_indices_or_None).
    """
    dealer = game.state.dealer
    human  = game.human_player
    upcard = game.state.upcard

    while bid_pos <= 3:
        player = (dealer + 1 + bid_pos) % 4

        if player == human:
            # Human's turn — pause and wait
            return _serialize(game, "bidding", bid_round, bid_pos), messages, None

        # --- Bot bids ---
        if bid_round == 1:
            chosen_suit, alone = game.choose_trump(
                game.state.hands[player],
                round_number=1,
                upcard=upcard,
                dealer=(player == dealer),
            )
            # In round 1 the only legal call is the upcard's suit (ordering up).
            # choose_trump returns the best suit overall; any suit other than
            # upcard.suit is treated as a pass.
            suit = chosen_suit if chosen_suit == upcard.suit else None

            if suit == upcard.suit:
                messages.append(f"Player {player} orders it up!")
                _set_trump(game, suit, player, alone)

                if dealer == human:
                    # Human dealer must pick up and discard
                    game.state.hands[dealer].append(upcard)
                    state = _serialize(game, "discard", bid_round, bid_pos)
                    return state, messages, list(range(len(game.state.hands[dealer])))
                else:
                    game.state.hands[dealer] = remove_worst_card(
                        list(game.state.hands[dealer]), upcard, suit
                    )
                    messages.append(f"Player {dealer} (dealer) picks up and discards")
                    _start_play(game)
                    return _advance_playing(game, 0, messages)
            else:
                messages.append(f"Player {player} passes")

        else:  # bid_round == 2
            forbidden = upcard.suit
            is_stuck  = (bid_pos == 3)   # last bidder in round 2 = stuck dealer
            suit, alone = game.choose_trump(
                game.state.hands[player],
                forbidden=forbidden,
                round_number=3 if is_stuck else 2,
                dealer=(player == dealer),
            )

            if suit:
                messages.append(f"Player {player} calls {SUIT_NAMES[suit.value]}!")
                _set_trump(game, suit, player, alone)
                _start_play(game)
                return _advance_playing(game, 0, messages)
            else:
                messages.append(f"Player {player} passes")

        bid_pos += 1

    # All four players passed this round
    if bid_round == 1:
        messages.append("All passed — second round of bidding.")
        return _advance_bidding(game, 2, 0, messages)

    # Should not happen (dealer is forced in round 2), but guard anyway
    return _serialize(game, "error"), messages, None


def _set_trump(game, suit, player, alone):
    game.state.trump       = suit
    game.makers_team       = player % 2
    game.maker_index       = player
    game.alone             = alone
    # Mirror onto state so ISMCTS can read them
    game.state.maker_index = player
    game.state.makers_team = player % 2
    game.state.alone       = alone


def _start_play(game):
    """Reset trick and point current_player to the first player after dealer."""
    dealer = game.state.dealer
    game.state.current_player = (dealer + 1) % 4
    game.state.leader          = game.state.current_player
    game.state.trick           = []


# ---------------------------------------------------------------------------
# State-machine: advance through bot card plays until human's turn or hand ends
# ---------------------------------------------------------------------------

def _advance_playing(game, trick_num, messages):
    """
    Process bot card plays until the human must act or the hand/game ends.
    Returns (state_dict, messages, legal_card_indices_or_None).
    """
    human = game.human_player

    while True:
        current = game.state.current_player

        if current == human:
            hand  = game.state.hands[current]
            legal = legal_moves(hand, game.state.trick, game.state.trump)
            legal_indices = [hand.index(c) for c in legal]
            return _serialize(game, "playing", trick_num=trick_num), messages, legal_indices

        # --- Bot plays ---
        hand = game.state.hands[current]
        if not hand:
            game.state.current_player = _next_player(game, current)
            continue

        if game.bot_types[current] == "ismcts":
            # choose_card always returns a card object from the player's actual hand
            card = game.ismcts_bot.choose_card(game, current)
        else:
            card = decide_move(hand, game.state.trick, game.state.trump, current % 2)

        hand.remove(card)
        game.state.trick.append((current, card))
        messages.append(f"Player {current} plays {card_display(card)}")

        num_active = 3 if game.alone else 4
        if len(game.state.trick) == num_active:
            trick_num = _resolve_trick(game, trick_num, messages)
            if trick_num >= 5:
                return _finish_hand(game, trick_num, messages)
        else:
            game.state.current_player = _next_player(game, current)


def _resolve_trick(game, trick_num, messages):
    trick_cards = [c for _, c in game.state.trick]
    winner      = trick_winner(trick_cards, game.state.leader, game.state.trump)
    game.tricks_won[winner % 2] += 1

    if winner == game.human_player:
        messages.append("You win the trick!")
    else:
        messages.append(f"Player {winner} wins the trick!")

    game.state.trick          = []
    game.state.leader         = winner
    game.state.current_player = winner
    return trick_num + 1


def _finish_hand(game, trick_num, messages):
    _score_hand(game, messages)
    if max(game.team_scores) >= 10:
        w = 0 if game.team_scores[0] > game.team_scores[1] else 1
        messages.append(f"🎉 Team {w} wins the game!")
        return _serialize(game, "game_over", trick_num=trick_num), messages, None
    return _serialize(game, "hand_over", trick_num=trick_num), messages, None


# ---------------------------------------------------------------------------
# Main entry point called by the HTTP handler
# ---------------------------------------------------------------------------

def process_action(body):
    """
    Dispatch a game action and return a response dict with keys:
      state, messages, legal_cards, error
    """
    action   = body.get("action")
    messages = []

    # ------------------------------------------------------------------ new_game
    if action == "new_game":
        game = _make_game()
        game.deal_new_hand()
        state, msgs, legal = _advance_bidding(game, 1, 0, messages)
        return {"state": state, "messages": msgs, "legal_cards": legal, "error": None}

    # ------------------------------------------------------------------ restore state
    state_data = body.get("state")
    if not state_data:
        return _err("No game state provided", None)

    game      = _make_game(state_data)
    phase     = state_data.get("phase", "bidding")
    bid_round = state_data.get("bid_round", 1)
    bid_pos   = state_data.get("bid_pos", 0)
    trick_num = state_data.get("trick_num", 0)

    # ------------------------------------------------------------------ next_hand
    if action == "next_hand":
        game.deal_new_hand()
        game.makers_team        = None
        game.maker_index        = None
        game.alone              = False
        game.tricks_won         = [0, 0]
        game.state.maker_index  = None
        game.state.makers_team  = None
        game.state.alone        = False
        state, msgs, legal = _advance_bidding(game, 1, 0, messages)
        return {"state": state, "messages": msgs, "legal_cards": legal, "error": None}

    # ------------------------------------------------------------------ bid
    if action == "bid":
        if phase != "bidding":
            return _err("Not in bidding phase", state_data)

        if bid_round == 1:
            order_up = body.get("order_up", False)
            alone    = body.get("alone", False)

            if order_up:
                upcard = game.state.upcard
                dealer = game.state.dealer
                messages.append("You order it up!")
                _set_trump(game, upcard.suit, game.human_player, alone)

                if dealer == game.human_player:
                    game.state.hands[dealer].append(upcard)
                    state = _serialize(game, "discard", bid_round, bid_pos)
                    return {"state": state, "messages": messages,
                            "legal_cards": list(range(len(game.state.hands[dealer]))),
                            "error": None}
                else:
                    game.state.hands[dealer] = remove_worst_card(
                        list(game.state.hands[dealer]), upcard, upcard.suit
                    )
                    messages.append(f"Player {dealer} (dealer) picks up and discards")
                    _start_play(game)
                    state, msgs, legal = _advance_playing(game, 0, messages)
                    return {"state": state, "messages": msgs, "legal_cards": legal, "error": None}
            else:
                messages.append("You pass")
                state, msgs, legal = _advance_bidding(game, 1, bid_pos + 1, messages)
                return {"state": state, "messages": msgs, "legal_cards": legal, "error": None}

        else:  # bid_round == 2
            suit_str = body.get("suit")   # "H" | "D" | "C" | "S" | None for pass
            alone    = body.get("alone", False)

            # Stuck-dealer guard: bid_pos==3 AND dealer==human
            is_stuck = (bid_pos == 3 and game.state.dealer == game.human_player)

            if suit_str:
                suit = Suit(suit_str)
                if game.state.upcard and suit == game.state.upcard.suit:
                    return _err("Cannot call the upcard's suit", state_data)
                messages.append(f"You call {SUIT_NAMES[suit_str]}!")
                _set_trump(game, suit, game.human_player, alone)
                _start_play(game)
                state, msgs, legal = _advance_playing(game, 0, messages)
                return {"state": state, "messages": msgs, "legal_cards": legal, "error": None}
            else:
                if is_stuck:
                    return _err("You're the dealer — you must call a suit!", state_data)
                messages.append("You pass")
                state, msgs, legal = _advance_bidding(game, 2, bid_pos + 1, messages)
                return {"state": state, "messages": msgs, "legal_cards": legal, "error": None}

    # ------------------------------------------------------------------ discard
    if action == "discard":
        if phase != "discard":
            return _err("Not in discard phase", state_data)
        card_idx = body.get("card_idx")
        hand     = game.state.hands[game.human_player]
        if card_idx is None or not (0 <= card_idx < len(hand)):
            return _err("Invalid card index", state_data)
        discarded = hand.pop(card_idx)
        messages.append(f"You discard {card_display(discarded)}")
        _start_play(game)
        state, msgs, legal = _advance_playing(game, 0, messages)
        return {"state": state, "messages": msgs, "legal_cards": legal, "error": None}

    # ------------------------------------------------------------------ play
    if action == "play":
        if phase != "playing":
            return _err("Not in playing phase", state_data)
        card_idx = body.get("card_idx")
        hand     = game.state.hands[game.human_player]
        legal    = legal_moves(hand, game.state.trick, game.state.trump)

        if card_idx is None or not (0 <= card_idx < len(hand)):
            return _err("Invalid card index", state_data)
        card = hand[card_idx]
        if card not in legal:
            legal_indices = [hand.index(c) for c in legal]
            return {"state": state_data, "messages": [],
                    "legal_cards": legal_indices,
                    "error": "Must follow suit — pick a highlighted card"}

        hand.remove(card)
        game.state.trick.append((game.human_player, card))
        messages.append(f"You play {card_display(card)}")

        num_active = 3 if game.alone else 4
        if len(game.state.trick) == num_active:
            trick_num = _resolve_trick(game, trick_num, messages)
            if trick_num >= 5:
                return _r(*_finish_hand(game, trick_num, messages))
            state, msgs, legal_c = _advance_playing(game, trick_num, messages)
            return {"state": state, "messages": msgs, "legal_cards": legal_c, "error": None}
        else:
            game.state.current_player = _next_player(game, game.human_player)
            state, msgs, legal_c = _advance_playing(game, trick_num, messages)
            return {"state": state, "messages": msgs, "legal_cards": legal_c, "error": None}

    return _err(f"Unknown action: {action}", state_data)


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def _err(msg, state):
    return {"state": state, "messages": [], "legal_cards": None, "error": msg}


def _r(state, messages, legal):
    """Unpack _finish_hand tuple into response dict."""
    return {"state": state, "messages": messages, "legal_cards": legal, "error": None}
