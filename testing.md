# Testing Guide

This document explains the testing approach for the Euchre bot project and covers what we test.

---

## Running the Tests

### Unit & Integration Tests (`test.py`)

```bash
python -m unittest test.py
```

This runs the full suite of unit and integration tests using Python's built-in `unittest` framework.

### ISMCTS vs Heuristic Performance Test (`test_ismcts_vs_heuristic.py`)

```bash
python test_ismcts_vs_heuristic.py
```

This runs a 100-game simulation match (1000 simulations per move) and prints performance statistics. It takes several minutes to complete.

---

## What We Currently Test (`test.py`)

### 1. Full Hand Simulation (`test_simulate_one_hand_debug`)

Runs one complete hand from deal through scoring and asserts that:
- The upcard was dealt
- Trump was set after bidding
- All players have 5 cards going into play
- Exactly 5 tricks are played
- Each trick winner is a valid player index (0–3)
- The score change after the hand is one of the valid values: 0, 1, 2, or 4

### 2. Card Identity / Suit Logic

| Test | What it checks |
|------|----------------|
| `test_sister_suit` | Hearts ↔ Diamonds and Spades ↔ Clubs are correctly paired |
| `test_is_void_suit` | A hand void in a suit returns `True`; a hand holding that suit returns `False` |
| `test_num_void_suits` | Correctly counts void non-trump suits in a hand |
| `test_is_single_in_suit` | Detects when a card is the only one of its suit in the hand |

### 3. Card Selection Helpers

| Test | What it checks |
|------|----------------|
| `test_find_lowest_card` | Returns the card with the lowest `card_value` |
| `test_find_worst_card` | Does not return a trump card when non-trump cards are available |
| `test_remove_worst_card` | Upcard is added to the hand after removing the worst card |
| `test_throw_junk` | Returns a non-trump card to avoid wasting trump when discarding |

### 4. Trick & Move Logic

| Test | What it checks |
|------|----------------|
| `test_trick_winner` | A trump card beats a higher off-suit card |
| `test_cards_to_win_trick` | Identifies cards in the hand that beat the current trick |
| `test_decide_move` | Plays a card of the led suit when following suit is required |

### 5. Trump Selection (Bidding Heuristic)

| Test | What it checks |
|------|----------------|
| `test_choose_trump_basic` | A strong Hearts hand calls Hearts and goes alone |
| `test_choose_trump_pass` | A weak hand passes in round 1 |

### 6. Deterministic Bidding (`test_do_bidding_forced`)

Sets Player 0's hand to all aces of Hearts (very strong Hearts hand) and asserts that trump is set to Hearts and that makers_team is 0.

### 7. Trick Play Loop (`test_play_tricks_runs`)

Sets up a controlled hand where Player 0 has all Hearts trumps and runs `play_tricks`. Asserts exactly 5 trick winners are returned.

### 8. Scoring (`test_score_hand_all_cases`)

Verifies all scoring cases:
- Makers win 3 tricks → 1 point for makers
- Defenders win 3 tricks (euchre) → 2 points for defenders
- Makers win all 5 tricks (sweep) → 2 points for makers
- Maker goes alone and wins all 5 tricks → 4 points for makers
- Maker goes alone and fails → 0 points for makers

### 9. Bower Logic

| Test | What it checks |
|------|----------------|
| Left bower recognition | Jack of the sister suit is treated as trump in `effective_suit`, `legal_moves`, and `trick_winner` |
| Left bower leading | Left bower correctly leads as trump, not as its printed suit |
| Right bower | Jack of trump is always the highest card in `card_value` and wins every trick |
| `trick_winner` with multiple trump | Highest trump wins (right bower > left bower > ace > king > ...) |
| `legal_moves` with left bower | A hand with the left bower is forced to follow trump when trump is led |

### 10. Bidding – All Rounds

| Test | What it checks |
|------|----------------|
| Round 2 forbidden suit | `choose_trump` never returns the upcard suit in round 2 |
| Stick the dealer | A dealer with a weak hand is still assigned the best available suit in round 3 |
| Upcard pickup (dealer swap) | `remove_worst_card` gives the dealer the upcard and keeps the hand at 5 cards |

### 11. Hand Strength

Tests `hand_strength` directly with known hands to validate point totals for various trump suit and card combinations.

### 12. ISMCTS Correctness

| Test | What it checks |
|------|----------------|
| Determinization void suit constraints | Randomly generated opponent hands never include a suit the player is known to be void in |
| Alone play – skipped player | The maker's partner is correctly skipped during trick play in a lone hand |
| Node UCT formula | `best_child` in `node.py` selects the correct child given known visit and win values |

### 13. Game-Level Tests

| Test | What it checks |
|------|----------------|
| Full game to 10 points | `sim_game` exits when a team reaches 10 and the reported winner matches the scores |
| Deck integrity | After dealing, all 24 cards appear exactly once across the 4 hands plus the upcard |
| Player rotation | The dealer advances by 1 each hand; the player left of the dealer leads the first trick |

---

## ISMCTS vs Heuristic Performance Test

`test_ismcts_vs_heuristic.py` is a statistical benchmark, not a pass/fail unit test. It simulates 100 full games where one seat plays ISMCTS and the other three play heuristic bots. The ISMCTS seat rotates every game (seat = game index % 4) so all positions are covered.

**Output includes:**
- Win rate of ISMCTS team vs heuristic team
- Average score differential per game
- Standard deviation of score differentials
- Total runtime and average time per game
- ISMCTS call frequency (how often it chose to call trump)
- Win rate when ISMCTS called trump
- Euchre rate when ISMCTS called trump

This test is the primary tool for evaluating algorithm improvements. A baseline win rate of ~62% at 600 simulations vs. the heuristic bot has been established. A lightweight version (20 games, 200 sims) is also run as part of CI to catch performance regressions.
