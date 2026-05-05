# Testing Guide

This document explains the testing approach for the Euchre bot project, covering what tests currently exist and what still needs to be tested.

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

Verifies two scoring cases:
- Makers win 3 tricks → 1 point for makers
- Defenders win 3 tricks (euchre) → 2 points for defenders

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

This test is the primary tool for evaluating algorithm improvements. A baseline win rate of ~62% at 600 simulations vs. the heuristic bot has been established.

---

## What Still Needs to Be Tested

### High Priority

- **Left Bower recognition**: Confirm the Jack of the sister suit is treated as trump in `effective_suit`, `legal_moves`, and `trick_winner`. Edge cases like the left bower leading a trick or following suit rules involving the left bower are not currently tested.
- **Right Bower**: Confirm the Jack of trump is always the highest card in `card_value` and always wins in `trick_winner`.
- **Bidding – round 2 (forbidden suit)**: The second round of bidding, where the upcard suit is forbidden, has no dedicated test. Verify that `choose_trump` never returns the forbidden suit.
- **Stick the dealer**: No test covers the forced dealer pick in round 3. A dealer with a weak hand should still be assigned the best available suit.
- **Going alone scoring**: The 4-point lone hand win and the 0-point lone hand loss paths in `score_hand` are not tested.
- **Upcard pickup (dealer swap)**: Verify that `remove_worst_card` correctly gives the dealer the upcard and reduces their hand back to 5 cards.

### Medium Priority

- **`legal_moves` with left bower**: A hand containing the Jack of the sister suit should be forced to follow trump if trump is led.
- **`trick_winner` with multiple trump**: When several trump cards are played, confirm the highest trump (right bower > left bower > ace > ...) wins.
- **`hand_strength` function**: No tests currently cover the hand strength scoring used to decide whether to call trump. Test it directly with known hands to validate point totals.
- **`cards_to_win_trick` edge cases**: The current implementation returns the full legal play list rather than the filtered winning subset (possible bug). This should be verified and tested.
- **ISMCTS determinization**: Unit tests to check that the randomly generated opponent hands respect void suit constraints (i.e., a player flagged as void in spades is never assigned a spades card).
- **Alone play – skipped player**: In a lone hand, the maker's partner should be skipped during trick play. `play_tricks` and `play_tricks_human` both have this logic but it is not covered by a test.

### Lower Priority

- **Full game to 10 points (`sim_game`)**: Confirm the game exits when a team reaches 10 and that the reported winning team matches the scores.
- **Deck integrity**: Confirm after dealing that all 24 cards appear exactly once across the 4 hands plus the upcard.
- **Player rotation**: Confirm the dealer advances by 1 each hand and that the player left of the dealer leads the first trick.
- **ISMCTS node UCT formula**: The `best_child` selection in `node.py` should be unit tested with known visit/win values to confirm it selects the correct child.
- **Performance regression**: Add a lightweight version of `test_ismcts_vs_heuristic.py` (e.g., 20 games, 200 sims) that can be run as part of CI to catch regressions in algorithm quality.
