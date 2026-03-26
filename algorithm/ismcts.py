import random
from algorithm.node import ISMCTSNode
from game.rules import legal_moves, decide_move, trick_winner, effective_suit
from game.card import Card, Suit, Rank


class ISMCTS:
    def __init__(self, simulations=600, debug=False):
        self.simulations = simulations
        self.debug = debug

    def _advance_player(self, state):
        while True:
            state.current_player = (state.current_player + 1) % 4
            if not getattr(state, "alone", False):
                return

            maker = state.maker_index
            team = state.makers_team

            if state.current_player != maker and state.current_player % 2 == team:
                continue
            return

    def choose_card(self, game, player):
        real_hand = list(game.state.hands[player])
        root = ISMCTSNode()

        for _ in range(self.simulations):
            # --- Copy state ---
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

            # --- Track void suits ---
            void_suits = [set() for _ in range(4)]

            # --- Build full Euchre deck ---
            ALL_CARDS = [
                Card(suit, rank)
                for suit in [Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS, Suit.SPADES]
                for rank in [Rank.NINE, Rank.TEN, Rank.JACK, Rank.QUEEN, Rank.KING, Rank.ACE]
            ]

            # --- Known cards ---
            known_cards = set(real_hand)
            known_cards.update(card for _, card in state.trick)

            # --- Unknown pool (includes kitty) ---
            unknown_cards = [c for c in ALL_CARDS if c not in known_cards]
            random.shuffle(unknown_cards)

            # --- Assign opponent hands with constraints ---
            for p in range(4):
                if p == player:
                    continue

                needed = len(state.hands[p])
                new_hand = []

                i = 0
                while i < len(unknown_cards) and len(new_hand) < needed:
                    card = unknown_cards[i]
                    eff = effective_suit(card, state.trump)

                    if eff in void_suits[p]:
                        i += 1
                        continue

                    new_hand.append(card)
                    unknown_cards.pop(i)

                # fallback fill
                while len(new_hand) < needed and unknown_cards:
                    new_hand.append(unknown_cards.pop())

                state.hands[p] = new_hand

            state.hands[player] = list(real_hand)

            # --- MCTS traversal ---
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
                    move = decide_move(hand, state.trick, state.trump, current)

                # --- VOID SUIT UPDATE (CRITICAL FIX) ---
                if state.trick:
                    lead_card = state.trick[0][1]
                    lead_suit = effective_suit(lead_card, state.trump)

                    if effective_suit(move, state.trump) != lead_suit:
                        void_suits[current].add(lead_suit)

                # apply move
                hand.remove(move)
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

            reward = self._rollout(state, player)

            # backprop
            while node:
                node.visits += 1
                node.wins += reward
                node = node.parent

        # --- Choose best move ---
        best = max(root.children, key=lambda c: c.wins / c.visits)

        if self.debug:
            print("\n[ISMCTS Debug]")
            print(f"Simulations run: {self.simulations}")

            for child in root.children:
                win_rate = child.wins / child.visits if child.visits > 0 else 0
                print(f"{child.move} -> {win_rate:.2f} ({child.visits})")

        return next(
            c for c in real_hand
            if c.suit == best.move.suit and c.rank == best.move.rank
        )

    def _rollout(self, state, perspective_player):
        tricks_won = [0, 0]
        steps = 0

        while any(state.hands) and steps < 50:
            steps += 1
            player = state.current_player
            hand = state.hands[player]

            if not hand:
                self._advance_player(state)
                continue

            legal = legal_moves(hand, state.trick, state.trump)
            card = random.choice(legal)

            hand.remove(card)
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
        reward = (tricks_won[my_team] - tricks_won[1 - my_team]) / 5.0
        # normalize to -1..1 (Safety clamp in case of edge cases)
        reward = max(-1.0, min(1.0, reward))
        return reward