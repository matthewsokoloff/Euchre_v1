import random
import copy
from algorithm.node import ISMCTSNode
from game.rules import legal_moves, decide_move, trick_winner, effective_suit


class ISMCTS:
    def __init__(self, simulations=300, debug=False):
        self.simulations = simulations
        self.debug = debug

    # player advancement
    def _advance_player(self, state):
        for _ in range(4):
            state.current_player = (state.current_player + 1) % 4

            # if alone, skip the lone maker's partner
            if getattr(state, "alone", False):
                maker = state.maker_index
                team = state.makers_team
                if state.current_player != maker and state.current_player % 2 == team:
                    continue
            return

    # ISMCTS entry point
    def choose_card(self, game, player):
        if player != 0:
            raise ValueError("ISMCTS currently only used for player 0")

        real_hand = list(game.state.hands[player])
        root = ISMCTSNode()

        for _ in range(self.simulations):
            # determinization
            state = copy.deepcopy(game.state) # copy the game state, randomizes opponents' hands but keeps real hand intact

            deck = [c for h in state.hands for c in h if h is not None]
            random.shuffle(deck)

            for p in range(4):
                if p != player:
                    n = len(state.hands[p])
                    state.hands[p] = deck[:n]
                    deck = deck[n:]

            state.hands[player] = list(real_hand)
            state.trick = list(state.trick)

            # selection / expansion
            node = root
            steps = 0
            # loop through moves til game end or 100 steps
            while any(state.hands) and steps < 100:
                steps += 1
                current = state.current_player
                hand = state.hands[current]
                # empty hand -> advance player
                if not hand:
                    self._advance_player(state)
                    continue
                legal = legal_moves(hand, state.trick, state.trump) or hand[:]

                # if our player, choose an untried move and expand the tree, or pick the best child node
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
                # if not our player, use heuristic instead of simulating moves
                else:
                    move = decide_move(hand, state.trick, state.trump, player)

                # apply the move
                hand.remove(move)
                state.trick.append((current, move))
                self._advance_player(state)

                # Resolve trick if full
                if len(state.trick) == 4:
                    trick_cards = [c for _, c in state.trick]
                    winner_idx = trick_winner(trick_cards, state.leader, state.trump)
                    winner = state.trick[winner_idx][0]
                    state.trick.clear()
                    state.current_player = winner
                    state.leader = winner

                # stop after first expansion
                if node.parent and node.visits == 0:
                    break

            # simulation of the rest of the game
            reward = self._rollout(state, player)

            # backpropagation (updates the statistics up the tree)
            while node:
                node.visits += 1
                node.wins += reward
                node = node.parent

        # choose the final move
        best = max(root.children, key=lambda c: c.wins / c.visits)
        return next(c for c in real_hand if c.suit == best.move.suit and c.rank == best.move.rank)

    # rollout
    def _rollout(self, state, perspective_player):
        tricks_won = [0, 0]
        steps = 0

        # loops until all players' hands are empty or 200 steps have passed (avoid infinite looping)
        while any(state.hands) and steps < 200:
            steps += 1
            player = state.current_player
            hand = state.hands[player]

            if not hand:
                self._advance_player(state)
                continue

            # decide the card using heuristics
            card = decide_move(hand, state.trick, state.trump, player)

            hand.remove(card)
            state.trick.append((player, card))
            self._advance_player(state)

            # trick resolution
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
