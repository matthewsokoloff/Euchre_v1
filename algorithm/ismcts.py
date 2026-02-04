import random
import copy
from algorithm.node import ISMCTSNode
from game.rules import legal_moves, decide_card, trick_winner, effective_suit
from game.card import Card, Suit, Rank


class ISMCTS:
    def __init__(self, simulations=300, debug=False):
        self.simulations = simulations
        self.debug = debug

    def choose_card(self, game, player):
        if player != 0:
            raise ValueError("ISMCTS currently only used for player 0")

        real_hand = list(game.state.hands[player])
        root = ISMCTSNode()

        for _ in range(self.simulations):
            # --- Determinization ---
            state = copy.deepcopy(game.state)
            deck = [c for h in state.hands for c in h]
            random.shuffle(deck)

            for p in range(4):
                if p != player:
                    needed = len(state.hands[p])
                    state.hands[p] = deck[:needed]
                    deck = deck[needed:]

            state.hands[player] = list(real_hand)
            state.trick = list(state.trick)

            node = root

            # =======================
            # SELECTION + EXPANSION
            # =======================
            while True:
                current = state.current_player
                hand = state.hands[current]

                if not hand:
                    state.current_player = (current + 1) % 4
                    continue

                legal = legal_moves(hand, state.trick, state.trump) or hand[:]

                if current == player:
                    # EXPAND
                    untried = node.untried_moves(legal)
                    if untried:
                        move = random.choice(untried)
                        node = node.add_child(move)
                    else:
                        node = node.select_child()  # UCT
                        move = node.move
                else:
                    # Opponent heuristic
                    move = max(
                        legal,
                        key=lambda c: decide_card(
                            c,
                            effective_suit(state.trick[0][1], state.trump) if state.trick else None,
                            state.trump,
                            [c2 for _, c2 in state.trick] if state.trick else None
                        )
                    )

                # Apply move
                hand.remove(move)
                state.trick.append((current, move))
                state.current_player = (current + 1) % 4

                # Finish trick
                if len(state.trick) == 4:
                    winner_idx = trick_winner([c for _, c in state.trick], 0, state.trump)
                    winner = state.trick[winner_idx][0]
                    state.trick.clear()
                    state.current_player = winner
                    state.leader = winner

                # Stop expansion after one new node
                if node.parent and node.visits == 0:
                    break

            # =======================
            # SIMULATION
            # =======================
            reward = self._rollout(state, player)

            # =======================
            # BACKPROPAGATION
            # =======================
            while node:
                node.visits += 1
                node.wins += reward
                node = node.parent

        # =======================
        # FINAL MOVE SELECTION
        # =======================
        best = max(root.children, key=lambda c: c.wins / c.visits)
        return next(c for c in real_hand if c == best.move)

    # play to end of hand
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
                key=lambda c: decide_card(
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