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
- [Future Enhancements](#future-enhancements)

---


## What is Euchre?

Euchre is a classic 4-player trick-taking card game played with a 24-card deck (9 through Ace in all four suits). It is popular in Germany and the Midwest USA. The game is played by two teams of two, sitting opposite each other.

---

## How to Play Euchre

### Setup
- **Players:** 4 (two teams of two)
- **Deck:** 24 cards (9, 10, J, Q, K, A of each suit)
- **Deal:** Each player is dealt 5 cards. The remaining 4 cards form the kitty; the top card is turned face up (the "upcard").

### Bidding (Making Trump)
1. Starting left of the dealer, each player can accept or pass on the upcard's suit as trump.
2. If accepted, the dealer picks up the upcard and discards one card.
3. If all pass, a second round allows players to name any other suit as trump (except the upcard's suit). If all pass again, the hand is re-dealt.
4. A player may "go alone" (play without their partner) for bonus points.

### Gameplay (Trick-Taking)
1. The player left of the dealer leads the first trick.
2. Players must follow suit if able; otherwise, they may play any card.
3. The highest card of the suit led wins the trick, unless a trump is played, in which case the highest trump wins.
4. The winner of each trick leads the next.

### Trump and Bowers
- **Trump suit**: Beats all other suits.
- **Right Bower**: Jack of trump suit (highest trump).
- **Left Bower**: Jack of the same color as trump (second highest trump, treated as trump suit).

### Scoring
- **Maker's team wins 3+ tricks:** 1 point
- **Maker's team wins all 5 tricks (a "march"):** 2 points
- **Maker goes alone and wins all 5 tricks:** 4 points
- **Defenders win 3+ tricks ("euchre" the makers):** 2 points
- First team to 10 points wins the game.

### Special Rules
- **Must follow suit** if possible.
- **No table talk** or signaling allowed.
- **Going Alone:** A player may play solo for extra points; their partner sits out the hand.

---

---

## Project Overview

This project implements a complete **Euchre game engine** with multiple AI bot strategies:

- **ISMCTS Bot**: Uses Monte Carlo Tree Search with information set handling to make optimal decisions under uncertainty
- **Heuristic Bot**: Uses rule-based logic for bidding and card selection (baseline for comparison)
- **Human Player**: Interactive mode allowing a human player to compete against AI opponents

### Key Achievements

✅ Full rule-enforcing game engine
✅ ISMCTS algorithm with void suit tracking and determinization
✅ Support for playing at multiple difficulty levels (via simulation count)
✅ Comprehensive testing framework comparing ISMCTS vs heuristic bots
✅ Game state management with proper card distribution

---

## How to Run

### Prerequisites

- Python 3.7+
- No external dependencies required (pure Python implementation)

### Running a Game

**Method 1: Interactive Mode (VS Code / PyCharm)**

1. Open `main.py` in your IDE
2. Press the "Run" button
3. Follow the on-screen prompts
4. You will play as Player 0 against 3 ISMCTS bots

**Method 2: Command Line**

```bash
cd /workspaces/Euchre_v1
python main.py
```

Follow the prompts to enter `dev` or `normal` mode:
- **Normal mode**: Standard gameplay with ISMCTS simulations
- **Dev mode**: Verbose debugging output showing bot decisions and game state

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

1. **Human vs AI**: Player 0 (human) vs Players 1, 2, 3 (ISMCTS)
2. **Simulation Mode**: All AI players (used for testing/training)
3. **Bot Matchups**: ISMCTS vs Heuristic bot comparisons

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

## The ISMCTS Algorithm

### Overview

**ISMCTS (Information Set Monte Carlo Tree Search)** is an extension of MCTS designed for games with **imperfect information** (hidden cards). Unlike perfect information games like Chess, Euchre players don't know:
- What cards are in opponents' hands
- What cards are in the undealt kitty
- What cards opponents will play

### Algorithm Steps

#### 1. **Determinization** (Handle Hidden Information)
The algorithm doesn't try to solve with true hidden information. Instead, it:
- Creates a complete game state by randomly assigning unknown cards to opponents
- Respects constraints: if a player couldn't follow suit, they don't have that suit
- Tracks "void suits" for each opponent based on played cards

```python
# If opponent didn't follow suit when leading, they're void in that suit
void_suits[player].add(led_suit)
```

#### 2. **Selection** (Tree Traversal)
Starting from the root node, select the most promising move paths using the **Upper Confidence Bound for Trees (UCT)** formula:

$$UCT = \frac{W_i}{N_i} + C \sqrt{\frac{\ln N}{N_i}}$$

Where:
- $W_i$ = wins from node $i$
- $N_i$ = visits to node $i$
- $N$ = visits to parent
- $C$ = exploration constant (typically ~1.4)

#### 3. **Expansion & Rollout** (Playout)
- If a node has untried moves, expand one randomly
- From there, play out the rest of the game with **heuristic moves**:
  - Bots use rule-based strategies (avoid waste cards when losing, etc.)
  - Each playout reaches a terminal game state

#### 4. **Backpropagation** (Update Statistics)
Walk back up the tree, incrementing visit counts and updating win statistics:

```
For each node on path:
    node.visits += 1
    if final_reward > threshold:
        node.wins += 1
```

### Why ISMCTS Works for Euchre

✅ **Handles uncertainty**: Doesn't require knowing opponent cards
✅ **Scales with computation**: More simulations = better decisions
✅ **Realistic play**: Learns from simulated outcomes without cheating
✅ **Fast decisions**: Makes moves in 1-5 seconds with ~600-1000 sims
✅ **Adaptable**: Can be tuned for different skill levels

### Implementation Details

**File**: [algorithm/ismcts.py](algorithm/ismcts.py)

Key features in our implementation:
- **Void suit tracking**: Candidates that don't follow suit lose access to that suit
- **Eligible visits heuristic**: Only counts visits when a move was actually available to play
- **Forced play optimization**: Skips simulation when only one legal move exists
- **State cloning**: Each simulation works with an independent game state copy

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

ISMCTS has proven highly effective in competitive game AI:
- Successfully used in poker AI (imperfect information benchmark)
- Extended variants used in games like Bridge and Hanabi
- More efficient than Deep Learning approaches for many card games
- Balances computation cost with decision quality

The algorithm essentially asks: "If I play this card, and randomly distribute the unknown cards, what's my average win rate across many simulated games?"

---

## Project Structure

```
Euchre_v1/
├── main.py                          # Entry point for interactive play
├── test.py                          # Basic game tests
├── test_ismcts_vs_heuristic.py     # Comparison benchmark (100+ games)
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
    ├── rules.py                    # Game rule enforcement
    └── tricks.py                   # Trick calculation logic
```

### Key Files

| File | Purpose |
|------|---------|
| `euchre_game.py` | Orchestrates game flow, manages players/bots, enforces rules |
| `ismcts.py` | ISMCTS algorithm - core AI decision making |
| `game_state.py` | Immutable game state: hands, tricks, scores, trump |
| `rules.py` | Legal move calculation, trick winners, suit tracking |
| `card.py` | Card representation with suit/rank and trump-aware comparison |

---

## Current Status

### ✅ Completed Features

- Full Euchre rules implementation
- ISMCTS algorithm with void suit optimization
- Interactive human play mode (command line)
- Heuristic baseline bot for comparison
- Comprehensive testing framework
- Design documentation

### 🚧 In Development / Planned

- **GUI**: Web-based or desktop interface for better UX
- **Game analysis**: Replay and analysis tools for specific scenarios
- **Bidding optimization**: Include bidding decisions in ISMCTS
- **Negative information tracking**: More sophisticated inference about opponent hands
- **Partnering AI**: Better cooperation between AI teammates
- **Solo/Loner mode**: Support for going alone (1v3) scenarios
- **Mobile deployment**: Optimize for smartphone CPUs

### ⚠️ Known Limitations

- **Bidding**: Currently uses heuristics only; ISMCTS doesn't optimize bid decisions
- **Partnering**: AI makes independent decisions without team coordination
- **Computation**: Requires reasonable CPU; phone performance untested
- **Randomness**: High-variance moves possible with similar win rates

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

- Algorithm & Core Implementation: Created as a research project in game AI

---

## Future Research Directions

1. **Bidding Integration**: Extend ISMCTS to handle bidding phase with better evaluation
2. **Deep Learning + MCTS**: Combine neural networks with ISMCTS for faster evaluation
3. **Information Theory**: Implement negative information tracking for smarter determinization
4. **Cooperative AI**: Develop partnership awareness and communication signaling
5. **Real-time Performance**: Optimize for mobile/cloud deployment

---

## License

This project is provided as-is for educational and research purposes.
