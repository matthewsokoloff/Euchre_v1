import random
import copy
from algorithm.node import ISMCTSNode
from game.rules import legal_moves, decide_card_heuristic, trick_winner, effective_suit
from game.card import Card, Suit, Rank


class ISMCTS:
    def __init__(self, simulations=300, debug=False):
        self.simulations = simulations
        self.debug = debug

    # ======================================================
    # PUBLIC ENTRY POINT
    # ======================================================
    def choose_card(self, game, player):
        if player != 0:
            raise ValueError("ISMCTS can only be used for player 0")

        real_hand = list(game.state.hands[player])
        if not real_hand:
            raise ValueError("Player 0 has an empty hand!")

        root = ISMCTSNode()

        def get_legal_moves(hand, trick, trump):
            moves = legal_moves(hand, trick, trump)
            return moves if moves else list(hand)  # fallback to all cards

        for _ in range(self.simulations):
            state = copy.deepcopy(game.state)
            state.hands[player] = list(real_hand)
            state.trick = list(state.trick)

            node = root

            while True:
                current_player = state.current_player
                alone = getattr(game, "alone", False)
                makers_team = getattr(game, "makers_team", None)
                maker_index = getattr(game, "maker_index", None)

                # Skip partner if maker is going alone
                if alone and current_player != maker_index and makers_team is not None:
                    if current_player % 2 == makers_team:
                        state.current_player = (state.current_player + 1) % 4
                        continue

                hand = state.hands[current_player]
                if not hand:
                    # No cards left, skip
                    state.current_player = (state.current_player + 1) % 4
                    continue

                legal = get_legal_moves(hand, state.trick, state.trump)
                if not legal:
                    legal = hand[:]  # safety fallback

                if current_player == player:
                    untried = [c for c in node.untried_moves(legal) if c in legal]
                    move = random.choice(untried) if untried else random.choice(legal)
                    node = node.add_child(move)
                    hand.remove(move)
                    state.trick.append((player, move))
                    state.current_player = (state.current_player + 1) % 4
                else:
                    # Heuristic play with fallback
                    if legal:
                        card = max(
                            legal,
                            key=lambda c: decide_card_heuristic(
                                c,
                                effective_suit(state.trick[0][1], state.trump) if state.trick else None,
                                state.trump,
                                [c2 for _, c2 in state.trick] if state.trick else None
                            )
                        )
                    else:
                        card = random.choice(hand)
                    hand.remove(card)
                    state.trick.append((current_player, card))
                    state.current_player = (state.current_player + 1) % 4

                # Complete trick if 4 cards
                if len(state.trick) == 4:
                    winner_idx = trick_winner([c for _, c in state.trick], 0, state.trump)
                    winner = state.trick[winner_idx][0]
                    state.trick.clear()
                    state.current_player = winner
                    state.leader = winner

                    if current_player == player:
                        break

                # Break if player's turn is done but trick not yet complete
                if current_player == player and len(state.trick) < 4:
                    break

            reward = self._rollout(state, player)

            # Backpropagate
            n = node
            while n:
                n.visits += 1
                n.wins += reward
                n = n.parent

        # Choose best move safely
        children_with_visits = [c for c in root.children if c.visits > 0]
        if children_with_visits:
            best_move = max(children_with_visits, key=lambda c: c.wins / c.visits).move
        else:
            best_move = random.choice(real_hand)

        # Print concise stats
        if self.debug:
            print("\nISMCTS stats for Player 0:")
            for child in root.children:
                print(f"  Card {child.move}: {child.wins}/{child.visits} wins, "
                      f"win rate = {child.wins/child.visits if child.visits else 0:.2f}")
            print(f"Chosen card: {best_move}\n")

        # Return actual card object from hand
        for c in real_hand:
            if c.suit == best_move.suit and c.rank == best_move.rank:
                return c
        return random.choice(real_hand)

    # ======================================================
    # ROLLOUT (play to end of hand)
    # ======================================================
    def _rollout(self, state, perspective_player):
        tricks_won = [0, 0]

        while any(state.hands):
            player = state.current_player
            hand = state.hands[player]
            if not hand:
                state.current_player = (state.current_player + 1) % 4
                continue

            legal = legal_moves(hand, state.trick, state.trump)
            if not legal:
                legal = hand[:]

            card = max(
                legal,
                key=lambda c: decide_card_heuristic(
                    c,
                    effective_suit(state.trick[0][1], state.trump) if state.trick else None,
                    state.trump,
                    [c2 for _, c2 in state.trick] if state.trick else None
                )
            )

            # Apply move safely
            hand.remove(card)
            state.trick.append((player, card))
            state.current_player = (state.current_player + 1) % 4

            # If trick complete
            if len(state.trick) == 4:
                winner_idx = trick_winner([c for _, c in state.trick], 0, state.trump)
                winner = state.trick[winner_idx][0]
                state.trick.clear()
                state.current_player = winner
                state.leader = winner
                tricks_won[winner % 2] += 1

        my_team = perspective_player % 2
        return 1 if tricks_won[my_team] >= 3 else 0