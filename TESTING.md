# Testing Guide

## Test Strategy

This project uses Python's built-in `unittest` framework. The tests focus on simple Euchre core logic such as card ranking, legal moves, and trick winners.

Run the tests locally with:

```bash
python -m unittest -v
```

GitHub Actions runs the same command on pushes to `main` and pull requests.

## Manual Test Table

| Manual test | Why it is manual |
| --- | --- |
| Terminal output is easy to read | This is a visual/user experience check. |
| AI moves seem reasonable | Strategy quality needs human judgment. |
| Game pacing feels okay | Speed is subjective. |

## Automated Test Suite

- `card_value`: checks a success state where the right bower is strongest.
- `legal_moves`: checks that a player follows suit when possible.
- `trick_winner`: checks that trump wins a trick.
- `find_lowest_card`: checks an error state for empty input.
