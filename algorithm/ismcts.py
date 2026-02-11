import random
from algorithm.node import ISMCTSNode
from game.rules import legal_moves, decide_move, trick_winner


class ISMCTS:
    def __init__(self, simulations=300, debug=False):
        self.simulations = simulations
        self.debug = debug

    # player advancement
    def _advance_player(self, state):
        while True:
            state.current_player = (state.current_player + 1) % 4

            if not getattr(state, "alone", False):
                return

            maker = state.maker_index
            team = state.makers_team

            # skip lone maker's partner
            if state.current_player != maker and state.current_player % 2 == team:
                continue

            return

    # entry point
    def choose_card(self, game, player):
        real_hand = list(game.state.hands[player])
        root = ISMCTSNode()

        # precompute deck
        full_deck = [c for h in game.state.hands if h for c in h]

        for _ in range(self.simulations):
            # shallow copy for speed
            state = type(game.state)(
                hands=[list(h) for h in game.state.hands],
                dealer=game.state.dealer,
                trump=game.state.trump,
                trick=list(game.state.trick),
                scores=list(game.state.scores),
                current_player=game.state.current_player,
                leader=game.state.leader
            )
            state.maker_index = getattr(game.state, "maker_index", None)
            state.makers_team = getattr(game.state, "makers_team", None)
            state.alone = getattr(game.state, "alone", False)

            # determinization: shuffle unknown hands
            deck = full_deck[:]
            random.shuffle(deck)

            for p in range(4):
                if p != player:
                    n = len(state.hands[p])
                    state.hands[p] = deck[:n]
                    deck = deck[n:]

            state.hands[player] = list(real_hand)

            # selection / expansion
            node = root
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
                    # increment eligible_visits
                    for child in node.children:
                        if child.move in legal:
                            child.eligible_visits += 1

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

                # apply move (faster removal)
                hand.pop(hand.index(move))
                state.trick.append((current, move))
                self._advance_player(state)

                # resolve trick
                if len(state.trick) == 4:
                    trick_cards = [c for _, c in state.trick]
                    winner_idx = trick_winner(trick_cards, state.leader, state.trump)
                    winner = state.trick[winner_idx][0]
                    state.trick.clear()
                    state.current_player = winner
                    state.leader = winner

                if current == player and node.visits == 0:
                    break

            # rollout
            reward = self._rollout(state, player)

            # backpropagation
            while node:
                node.visits += 1
                node.wins += reward
                node = node.parent

        # choose best move
        best = max(root.children, key=lambda c: c.wins / c.visits)
        return next(c for c in real_hand if c.suit == best.move.suit and c.rank == best.move.rank)

    # rollout (faster, shorter)
    def _rollout(self, state, perspective_player):
        tricks_won = [0, 0]
        steps = 0
        max_steps = 40  # short rollout limit

        while any(state.hands) and steps < max_steps:
            steps += 1
            player = state.current_player
            hand = state.hands[player]

            if not hand:
                self._advance_player(state)
                continue

            card = decide_move(hand, state.trick, state.trump, player)
            hand.pop(hand.index(card))
            state.trick.append((player, card))
            self._advance_player(state)

            if len(state.trick) == 4:
                trick_cards = [c for _, c in state.trick]
                winner_idx = trick_winner(trick_cards, state.leader, state.trump)
                winner = state.trick[winner_idx][0]
                state.trick.clear()
                state.current_player = winner
                state.leader = winner
                tricks_won[winner % 2] += 1

        my_team = perspective_player % 2
        return tricks_won[my_team] - tricks_won[1 - my_team]
