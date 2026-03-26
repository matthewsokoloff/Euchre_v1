import random
import copy
from algorithm.node import ISMCTSNode
from game.rules import legal_moves, decide_move, trick_winner
from game.card import Card, Suit, Rank


class ISMCTS:
    def __init__(self, simulations=600, debug=False):
        """Initialize the ISMCTS agent. simulations (int): Number of Information Set
        Monte Carlo simulations to run when selecting a move. debug (bool): If True,
        prints detailed debugging information about the MCTS tree and move statistics."""
        self.simulations = simulations
        self.debug = debug

    # player advancement
    def _advance_player(self, state):
        """Advance the turn to the next valid player. Handles the special Euchre rule
        where a player may go alone. If a player is going alone, their partner must be
        skipped when advancing turns. state: The current simulated game state."""
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
        """ Returns the card from the real hand corresponding to the best move found by the search.
        Select the best card to play using Information Set MCTS.

        The algorithm performs repeated simulations of the game from the
        current state. hidden/unknown information (opponent hands) is randomized
        in each simulation (determinization). The tree tracks statistics
        about moves available to the current player and uses those
        statistics to choose the best action.

        Steps:
        1. copy current game state.
        2. randomly assign hidden cards to opponents. (determinization)
        3. run MCTS selection/expansion +  simulation + backpropagation.
        4. choose move w/ best win rate.

        game: the real game instance.
        player (int): index of the current player."""

        real_hand = list(game.state.hands[player])
        root = ISMCTSNode()

        for _ in range(self.simulations):
            # deep copy hands but nothing else (reduce computing power necessary)
            state = type(game.state)(hands=[list(h) for h in game.state.hands], dealer=game.state.dealer, trump=game.state.trump, trick=list(game.state.trick), scores=list(game.state.scores), current_player=game.state.current_player, leader=game.state.leader)
            state.maker_index = getattr(game.state, "maker_index", None)
            state.makers_team = getattr(game.state, "makers_team", None)
            state.alone = getattr(game.state, "alone", False)

            # determinization: shuffle unknown hands
            # --- Build full Euchre deck ---
            ALL_CARDS = [
                Card(suit, rank)
                for suit in [Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS, Suit.SPADES]
                for rank in [Rank.NINE, Rank.TEN, Rank.JACK, Rank.QUEEN, Rank.KING, Rank.ACE]
            ]

            # --- Collect known cards (what we are allowed to know) ---
            known_cards = set(real_hand)

            # cards already played in current trick
            known_cards.update(card for _, card in state.trick)

            # OPTIONAL: if your game tracks upcard / discard, include them here
            # example:
            # if hasattr(state, "upcard") and state.upcard:
            #     known_cards.add(state.upcard)

            # --- Build unknown pool (this now correctly includes the kitty) ---
            full_deck = [c for c in ALL_CARDS if c not in known_cards]

            random.shuffle(full_deck)

            # --- Reassign opponent hands ---
            for p in range(4):
                if p != player:
                    n = len(state.hands[p])
                    state.hands[p] = full_deck[:n]
                    full_deck = full_deck[n:]

            # --- Restore our real hand ---
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
                    # increment eligible visits
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

            # backpropagation
            while node:
                node.visits += 1
                node.wins += reward
                node = node.parent

        # choose best move
        best = max(root.children, key=lambda c: c.wins / c.visits)
        if self.debug:
            print("\n[ISMCTS Debug]")
            print(f"Simulations run: {self.simulations}")

            if root.children:
                print("Move statistics:")
                for child in root.children:
                    win_rate = child.wins / child.visits if child.visits > 0 else 0
                    print(
                        f"  Move {child.move}: "
                        f"Wins={child.wins:.2f}, "
                        f"Visits={child.visits}, "
                        f"Eligible={child.eligible_visits}, "
                        f"Win rate={win_rate:.2f}"
                    )

                best_win_rate = best.wins / best.visits if best.visits > 0 else 0
                print(f"Chosen move: {best.move} with win rate {best_win_rate:.2f}")

                # traversal path
                node = root
                path = []
                while node.children:
                    node = node.best_child()
                    path.append(node.move)
                if path:
                    print("Traversal path in MCTS tree:", " -> ".join(str(m) for m in path))
                else:
                    print("Traversal path in MCTS tree: (no moves expanded)")
            else:
                print("No children nodes to display (early exit in MCTS).")

        # return the actual card from the real hand
        return next(c for c in real_hand if c.suit == best.move.suit and c.rank == best.move.rank)

    # rollout with the copy retained
    def _rollout(self, state, perspective_player):
        """ Returns a float of the normalized reward in the range [-1, 1]
        Performs a random simulation (rollout) from the current state.

        The rollout continues until either all cards are played or
        the step limit of 50 is reached. During the rollout, players
        choose random legal moves.

        The result is converted into a normalized reward between
        -1 and 1 from the perspective of the specified player.

        state: simulated game state.
        perspective_player (int): the player whose perspective the reward is calculated from."""
        tricks_won = [0, 0]  # [team0, team1]
        steps = 0
        max_steps = 50  # cap rollout for speed

        while any(state.hands) and steps < max_steps:
            steps += 1
            player = state.current_player
            hand = state.hands[player]

            if not hand:
                self._advance_player(state)
                continue

            # Choose a card to play in rollout
            legal = legal_moves(hand, state.trick, state.trump)
            card = random.choice(legal)
            hand.remove(card)
            state.trick.append((player, card))
            self._advance_player(state)

            # Resolve trick if full
            if len(state.trick) == 4:
                trick_cards = [c for _, c in state.trick]
                winner_idx = trick_winner(trick_cards, state.leader, state.trump)
                winner = state.trick[winner_idx][0]
                state.trick.clear()
                state.current_player = winner
                state.leader = winner
                tricks_won[winner % 2] += 1

        # Compute normalized reward
        my_team = perspective_player % 2
        reward = (tricks_won[my_team] - tricks_won[1 - my_team]) / 5.0  # normalize to -1..1

        # Safety clamp in case of edge cases
        reward = max(-1.0, min(1.0, reward))
        return reward
