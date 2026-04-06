# Euchre Bot with ISMCTS

Implementation of **Information Set Monte Carlo Tree Search (ISMCTS)** algorithm-based opponent for Euchre.

## Table of Contents

- [What is Euchre?](#what-is-euchre)
- [Project Overview](#project-overview)
- [How to Run](#how-to-run)
- [Game Modes](#game-modes)
- [The ISMCTS Algorithm](#the-ismcts-algorithm)
- [Project Structure](#project-structure)
- [Current Status](#current-status)

---


## What is Euchre?

Euchre is a classic 4-player trick-taking card game played with a 24-card deck (9 through Ace in all four suits). It is popular in Germany and the Midwest USA. The game is played by two teams of two, sitting opposite each other.

---

## How to Play Euchre

### Setup
- **Players:** 4 (two teams of two)
- **Deck:** 24 cards (9, 10, J, Q, K, A of each suit)
- **Deal:** Each player is dealt 5 cards. The remaining 4 cards form the kitty. The top card in the kitty is turned face up (this is the upcard). The three cards under the upcard will remain unknown.

### Bidding (with Stick the Dealer)
1. Starting left of the dealer, each player can accept or pass on the upcard's suit as trump.
2. If accepted, the dealer picks up the upcard and discards one card.
3. If all pass, a second round allows players to name any other suit as trump (except the upcard's suit). If all players left of the dealer pass in the second round, the dealer is "stuck" and must choose trump.
4. A player may "go alone" (play without their partner) for bonus points.

### Gameplay (Tricks)
1. The player left of the dealer leads the first trick.
2. Players must follow the led suit if possible; otherwise, they may play any card.
3. The highest card of the suit led wins the trick, unless trump is played, in which case the highest trump wins.
4. The person who took the trick (trick winner) leads the next trick.

### Trump and Bowers
- **Trump suit**: Beats all other suits.
- **Right Bower**: Jack of trump suit (highest trump).
- **Left Bower**: Jack of the sister suit (same color suit) of trump (second highest trump, acts as trump for the round and not its original suit).

### Scoring
- **Maker's team wins 3 or 4 tricks:** 1 point
- **Maker's team wins all 5 tricks (a sweep):** 2 points
- **Maker goes alone and wins all 5 tricks:** 4 points
- **Defenders win 3+ tricks (a euchre):** 2 points
- First team to 10 points wins the game.

### Special Rules
- **Must follow suit** if possible.
- **Going Alone:** If a player goes alone, their partner sits out the hand.

---

---

## Project Overview

This project implements a complete **Euchre game engine** with multiple bot strategies:

- **ISMCTS Bot**: Uses Information Set Monte Carlo Tree Search to make optimal decisions under uncertainty (the opponents' hands are hidden)
- **Heuristic Bot**: Uses rule-based logic for bidding and card selection (baseline for comparison)
- **Human Player**: Interactive mode allowing a human player to compete against bot opponents running ISMCTS

### Key Achievements

Full rule-enforcing game engine
ISMCTS algorithm with void suit tracking and determinization (world-building based on current information)
Comprehensive testing framework comparing ISMCTS vs heuristic bots
Game state management with proper card distribution (shuffling + dealing)

---

## How to Run

### Prerequisites

- Python 3.7+
- No external dependencies required

### Running a Game

**Method 1: Interactive Mode (VS Code / PyCharm)**

1. Open `main.py` in your IDE
2. Press the "Run" button
3. Follow the on-screen prompts to enter `dev` or `normal` mode
4. You will play as Player 0 against 3 ISMCTS bots

**Method 2: Command Line**

```bash
cd /workspaces/Euchre_v1
python main.py
```

Follow the prompts to enter `dev` or `normal` mode:
- **Normal mode**: Standard gameplay with ISMCTS simulations
- **Dev mode**: Verbose debugging output showing bot decision-making process and game state

### Running Tests

**Run a match between ISMCTS and heuristic bots:**

```bash
python test_ismcts_vs_heuristic.py
```

This runs 100 games with 1000 simulations per move, providing statistics on:
- Win rate of ISMCTS bot
- Calling/bidding success rate
- Average score differences
- Performance metrics

**Run basic game tests:**

```bash
python test.py
```

---

## Game Modes

The current implementation supports:

1. **Human vs ISMCTS Bots**: Player 0 (human) vs Players 1, 2, 3 (ISMCTS Bots) with `dev` and `normal` mode
2. **Simulation Mode**: Simulates ISMCTS vs 3 heuristic players (used for testing/training)

Configuration in `main.py`:
```python
bots = ["human", "ismcts", "ismcts", "ismcts"]  # Player types
human_player = 0  # Which seat is human (0-3)
```

To adjust difficulty, modify the simulations parameter:
```python
# Easy: ~100 simulations per move
# Medium: ~600 simulations per move
# Hard: ~2000+ simulations per move
```

---

## ISMCTS Algorithm

### Overview

**ISMCTS (Information Set Monte Carlo Tree Search)** is an extension of MCTS designed for games with **imperfect information** (hidden cards). Unlike perfect information games like Chess, Euchre players don't know:
- What cards are in opponents' hands
- What cards are in the kitty (the 3 hidden cards after dealing)
- What cards opponents will play or can play

### Algorithm Steps

#### 1. **Determinization** (How Hidden Information is Handled)
The algorithm doesn't try to solve with true hidden information. Instead, it:
- Creates a complete game state by randomly assigning unknown cards to opponents
- Respects constraints: if a player didn't follow suit, they don't have that suit, and they will not be assigned cards of that suit (this is void suit tracking)

```python
# If opponent didn't follow suit when leading, they're void in that suit
void_suits[player].add(led_suit)
```

#### 2. **Selection** (Tree Traversal)
Starting from the root node, select the most promising move paths using the **Upper Confidence Bound for Trees (UCT)** formula:

$$UCT = \frac{W_i}{N_i} + C \sqrt{\frac{\ln N}{N_i}}$$

Where:
- $W_i$ = wins from node $i$
- $N_i$ = eligible visits to node $i$
- $\frac{W_i}{N_i}$ = win rate
- $N$ = total eligible visits
- $C$ = exploration constant (usually, and in this case, $\sqrt{2}$)

#### 3. **Expansion & Rollout** (Simulation)
- If a node has untried moves, expand one randomly
- From there, play out the rest of the game with **heuristic moves**:
  - Bots use rule-based strategies (avoid waste cards when losing, etc.)
  - Each playout reaches a terminal game state

#### 4. **Backpropagation** (Update Statistics)
After a simulation ends, walk back up the tree, incrementing visit counts and updating win statistics:

```
For each node on path:
    node.visits += 1
    if final_reward > threshold:
        node.wins += 1
```

### Why ISMCTS Works for Euchre

- **Handles uncertainty**: Doesn't require knowing opponent cards
- **Scales with computation**: More simulations = better decisions
- **Realistic play**: Learns from simulated outcomes without cheating
- **Fast decisions**: Makes moves quickly, even at high simulation numbers
- **Adaptable**: Can preform at different skill levels based on number of simulations ran

### Implementation Details

**File**: [algorithm/ismcts.py](algorithm/ismcts.py)

Key features in our implementation:
- **Void suit tracking**: Candidates that don't follow suit lose access to that suit
- **Eligible visits heuristic**: Only counts visits on legal moves (does not waste resources calculating win probabilities for illegal moves)
- **Forced play optimization**: Skips simulation when only one legal move exists
- **State cloning**: Each simulation works with an independent game state copy so the true game state remains intact

```python
# Central ISMCTS function
def choose_card(self, game, player):
    real_hand = list(game.state.hands[player])
    root = ISMCTSNode()
    
    for _ in range(self.simulations):  # Run N iterations
        # 1. Determinization
        state = self._determinize_game(game, player, void_suits)
        
        # 2 & 3. Selection/Expansion/Rollout
        node = self._tree_traversal(root, state, player)
        reward = self._rollout(state, player)
        
        # 4. Backpropagation
        self._backpropagate(node, reward)
    
    # Return best move based on visit counts
    return root.best_child().move
```

### Research Context

ISMCTS has proven highly effective and is widely used in many competitive games:
- Successfully used in poker AI (imperfect information benchmark)
- Extended variants used in games like Bridge and Hanabi
- More efficient than Deep Learning approaches for many games, especially those with hidden information
- Balances computation cost with decision quality

The algorithm finds and plays what it thinks is the best legal card (this is, the card with the highest win rate across many simulations of random distributions of the unknown cards).

---

## Project Structure

```
Euchre_v1/
├── main.py                          # Entry point for interactive play
├── test.py                          # Rule tests
├── test_ismcts_vs_heuristic.py      # Comparison of ISMCTS vs Heuristic Bots (100+ games)
├── design.md                        # Project design document
├── README.md                        # This file
│
├── algorithm/
│   ├── ismcts.py                   # ISMCTS algorithm implementation
│   └── node.py                     # MCTS tree node structure
│
└── game/
    ├── euchre_game.py              # Main game engine & controller
    ├── game_state.py               # Game state representation
    ├── card.py                     # Card data structure
    ├── deck.py                     # Deck management
    └── rules.py                    # Game rule enforcement
```

### Key Files

| File | Purpose                                                          |
|------|------------------------------------------------------------------|
| `euchre_game.py` | Game engine. Manages game flow, players/bots, and enforces rules |
| `ismcts.py` | ISMCTS algorithm - core decision making                          |
| `game_state.py` | Immutable game state: hands, tricks, scores, trump               |
| `rules.py` | Establishes the legal moves and other helpful methods for Euchre |
| `card.py` | Card creation with Suits and Ranks.                              |

---

## Current Status

### Completed Features

- Full Euchre rules implementation
- ISMCTS algorithm with void suit and forced play optimization
- Interactive human play mode (in command line)
- Heuristic baseline bot for comparison
- Comprehensive testing framework
- Design documentation

### In Development / Planned

- **GUI**: Web-based or desktop interface for better UX
- **Game analysis**: Replay and analysis tools for specific scenarios
- **Bidding optimization**: Include bidding decisions in ISMCTS
- **Negative information tracking**: More sophisticated inference about opponent hands
- **Mobile deployment**: Optimize for smartphone CPUs

### Known Limitations

- **Bidding**: Currently uses heuristics only; ISMCTS doesn't optimize bid decisions
- **Partnering**: Bots make independent decisions without using much of the known information about the partner's hand
- **Computation**: Phone performance untested, and preforming many or in-depth simulations requires a reasonable CPU
- **Randomness**: High-variance moves are possible from similar simulated win rates

---

## Performance Benchmarks

Based on `test_ismcts_vs_heuristic.py` runs:

| Simulations per Move | Time per Move | Estimated Win Rate vs Heuristic |
|---------------------|---------------|--------------------------------|
| 100                 | ~0.2 seconds  | ~55%                          |
| 600                 | ~1 second     | ~62%                          |
| 1000                | ~2 seconds    | ~65%                          |
| 2000+               | ~4-5 seconds  | ~68%+                         |

*Note: Exact numbers vary by hardware. Use `test_ismcts_vs_heuristic.py` to benchmark on your system.*

---

## Development Notes

### Game State Management

The project uses immutable-style game states:
```python
state.hands       # List[List[Card]] - Each player's hand
state.trump       # Suit - Current trump suit
state.trick       # List[Tuple[player, Card]] - Current trick cards
state.scores      # List[int] - Team scores
state.current_player  # int - Whose turn (0-3)
```

### Making Legal Moves

```python
from game.rules import legal_moves

hand = state.hands[player]
legal = legal_moves(hand, state.trick, state.trump)
# Returns list of cards that don't break suit-following rules
```

### Debugging

Run with dev mode for verbose output:
```bash
python main.py
# Then enter: dev
```

This prints:
- Game state after each action
- Bot decision-making process
- Simulation statistics
- Void suit tracking

---

## Contributors

- Algorithm & Core Implementation: Created as a research project in game AI (specifically for Euchre) by Matthew Sokoloff
- Clusters: Built to increase computing power (interconnected networks of GPUs to increase computing power for large tasks) by Samuel Mayle

---
