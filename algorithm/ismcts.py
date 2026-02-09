import random
import copy
from algorithm.node import ISMCTSNode
from game.rules import legal_moves, decide_move, trick_winner, effective_suit


class ISMCTS:
    def __init__(self, simulations=300, debug=False):
        self.simulations = simulations
        self.debug = debug

    # -------------------------
    # Player advancement helper
    # -------------------------
    def _advance_player(self, state):
        for _ in range(4):
            state.current_player = (state.current_player + 1) % 4

            # Skip lone maker's partner if alone
            if getattr(state, "alone", False):
                maker = state.maker_index
                team = state.makers_team
                if state.current_player != maker and state.current_player % 2 == team:
                    continue

            return

    # -------------------------
    # Main ISMCTS entry point
    # -------------------------
    def choose_card(self, game, player):
        if player != 0:
            raise ValueError("ISMCTS currently only used for player 0")

        real_hand = list(game.state.hands[player])
        root = ISMCTSNode()

        for _ in range(self.simulations):
            # -------- Determinization --------
            state = copy.deepcopy(game.state)

            deck = [c for h in state.hands for c in h if h is not None]
            random.shuffle(deck)

            for p in range(4):
                if p != player:
                    n = len(state.hands[p])
                    state.hands[p] = deck[:n]
                    deck = deck[n:]

            state.hands[player] = list(real_hand)
            state.trick = list(state.trick)

            node = root

            # -------- Selection + Expansion --------
            steps = 0
            while any(state.hands) and steps < 100:
                steps += 1
                current = state.current_player
                hand = state.hands[current]

                if not hand:
                    self._advance_player(state)
                    continue

                legal = legal_moves(hand, state.trick, state.trump) or hand[:]

                if current == player:
                    untried = node.untried_moves(legal)
                    if untried:
                        move = random.choice(untried)
                        node = node.add_child(move)
                    else:
                        if not node.children:
                            break
                        node = node.best_child()
                        move = node.move
                else:
                    move = decide_move(hand, state.trick, state.trump, player)

                # Apply move
                hand.remove(move)
                state.trick.append((current, move))
                self._advance_player(state)

                # Resolve trick if full
                if len(state.trick) == 4:
                    trick_cards = [c for _, c in state.trick]
                    winner_idx = trick_winner(trick_cards, 0, state.trump)
                    winner = state.trick[winner_idx][0]
                    state.trick.clear()
                    state.current_player = winner
                    state.leader = winner

                # Stop after first expansion
                if node.parent and node.visits == 0:
                    break

            # -------- Simulation --------
            reward = self._rollout(state, player)

            # -------- Backpropagation --------
            while node:
                node.visits += 1
                node.wins += reward
                node = node.parent

        # -------- Final move selection --------
        best = max(root.children, key=lambda c: c.wins / c.visits)
        return next(c for c in real_hand if c.suit == best.move.suit and c.rank == best.move.rank)

    # -------------------------
    # Rollout (safe, bounded)
    # -------------------------
    def _rollout(self, state, perspective_player):
        tricks_won = [0, 0]
        steps = 0

        while any(state.hands) and steps < 200:
            steps += 1
            player = state.current_player
            hand = state.hands[player]

            if not hand:
                self._advance_player(state)
                continue

            legal = legal_moves(hand, state.trick, state.trump) or hand[:]

            card = decide_move(hand, state.trick, state.trump, player)

            hand.remove(card)
            state.trick.append((player, card))
            self._advance_player(state)

            # Resolve trick
            if len(state.trick) == 4:
                trick_cards = [c for _, c in state.trick]
                winner_idx = trick_winner(trick_cards, 0, state.trump)
                winner = state.trick[winner_idx][0]
                state.trick.clear()
                state.current_player = winner
                state.leader = winner
                tricks_won[winner % 2] += 1

        my_team = perspective_player % 2
        return 1 if tricks_won[my_team] >= 3 else 0