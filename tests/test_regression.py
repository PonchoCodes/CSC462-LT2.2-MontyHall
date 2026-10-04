"""Regression test: seeded win counts of the classic 3-door game must not change."""

import numpy as np

from monty import playGame

SEED = 42
TRIALS = 100_000

# Recorded from the Phase 1 version of monty.py (numpy 2.2.4).
EXPECTED_STICK_WINS = 33215
EXPECTED_SWITCH_WINS = 66690


def test_seededWinCountsAreUnchanged():
    # Same order as main(): one generator, all stick games, then all switch games.
    rng = np.random.default_rng(SEED)
    stickWins = sum(playGame("stick", rng) for _ in range(TRIALS))
    switchWins = sum(playGame("switch", rng) for _ in range(TRIALS))

    assert stickWins == EXPECTED_STICK_WINS
    assert switchWins == EXPECTED_SWITCH_WINS
