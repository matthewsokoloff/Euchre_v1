import random
import copy
from algorithm.node import ISMCTSNode
from game.rules import legal_moves, decide_move, trick_winner

class ISMCTS:
    def __init__(self, simulations=300, debug=False):
        self.simulations = simulations
        self.debug = debug

    def _advance_player(self, state):
        # Advance to the next player, skipping a lone maker's partner
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

    def choose_card(self, game, player):
        real_hand = list(game.state.hands[player])
        root = ISMCTSNode()

        for _ in range(self.simulations):
            # --- lightweight copy of game state ---
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

            # --- determinization: shuffle unknown hands ---
            full_deck = [c for h in state.hands if h for c in h]
            random.shuffle(full_deck)
            for p in range(4):
                if p != player:
                    n = len(state.hands[p])
                    state.hands[p] = full_deck[:n]
                    full_deck = full_deck[n:]
            state.hands[player] = list(real_hand)

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
                    # --- expand tree using canonical moves (rank, suit) only ---
                    canonical_legal = [(c.rank, c.suit) for c in legal]

                    untried = node.untried_moves(canonical_legal)
                    if untried:
                        move = random.choice(untried)
                        node = node.add_child(move)
                    else:
                        if not node.children:
                            break
                        node = node.best_child()
                        move = node.move  # move is (rank, suit)

                    # pick actual card from determinized hand matching canonical move
                    candidates = [c for c in legal if (c.rank, c.suit) == move]
                    if not candidates:
                        # fallback in rare cases
                        move_card = random.choice(legal)
                    else:
                        move_card = candidates[0]
                else:
                    # opponent uses decide_move (already respects legal_moves)
                    move_card = decide_move(hand, state.trick, state.trump, current)

                # --- play the card ---
                hand.remove(move_card)
                state.trick.append((current, move_card))
                self._advance_player(state)

                # --- resolve trick ---
                if len(state.trick) == 4:
                    trick_cards = [c for _, c in state.trick]
                    winner_idx = trick_winner(trick_cards, state.leader, state.trump)
                    winner = state.trick[winner_idx][0]
                    state.trick.clear()
                    state.current_player = winner
                    state.leader = winner

                if current == player and node.visits == 0:
                    break

            # --- rollout from leaf ---
            reward = self._rollout(state, player)

            # --- backpropagate ---
            while node:
                node.visits += 1
                node.wins += reward
                node = node.parent

        # --- pick best move from tree ---
        best = max(root.children, key=lambda c: c.wins / c.visits)

        # --- map canonical move back to actual legal card in real hand ---
        legal_in_hand = legal_moves(real_hand, game.state.trick, game.state.trump)
        matching_cards = [c for c in legal_in_hand if (c.rank, c.suit) == best.move]
        if not matching_cards:
            # fallback: choose random legal card
            card_to_play = random.choice(legal_in_hand)
        else:
            card_to_play = matching_cards[0]

        if self.debug:
            print("\n- ISMCTS thinking -")
            for child in root.children:
                wr = child.wins / child.visits if child.visits else 0
                print(f"{child.move}: winrate={wr:.3f} visits={child.visits}")
            print(f"Chosen move: {card_to_play}\n")

        return card_to_play

    def _rollout(self, state, perspective_player):
        # Simulate a playout from the current state using only legal moves.
        tricks_won = [0, 0]
        steps = 0
        max_steps = 50  # cap rollout for speed

        while any(state.hands) and steps < max_steps:
            steps += 1
            player = state.current_player
            hand = state.hands[player]

            if not hand:
                self._advance_player(state)
                continue

            # Compute legal moves first
            legal = legal_moves(hand, state.trick, state.trump)
            if not legal:
                legal = hand[:]  # fallback (should rarely happen)

            # Pick a move using decide_move but only from legal cards
            card = decide_move(hand, state.trick, state.trump, player)

            hand.remove(card)
            state.trick.append((player, card))
            self._advance_player(state)

            # resolve trick
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
