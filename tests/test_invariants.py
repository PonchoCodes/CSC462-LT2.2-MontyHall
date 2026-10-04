"""Invariant and statistical tests for the Monty Hall simulation."""

import math

import numpy as np
import pytest

from monty import (
    knowingHost,
    makeBiasedHost,
    playGame,
    playGameWithPolicies,
    randomHost,
    stickStrategy,
    switchStrategy,
)

SEED = 2026
INVARIANT_GAMES = 20_000
STATISTICAL_TRIALS = 50_000


def threeStandardErrors(probability, sampleSize):
    # Standard error of a win rate measured over sampleSize independent games,
    # each won with the given probability:
    #     standardError = sqrt(probability * (1 - probability) / sampleSize)
    # The tolerance is 3 standard errors.
    return 3 * math.sqrt(probability * (1 - probability) / sampleSize)


def measureWinRate(hostPolicy, playerStrategy, numDoors, rng):
    """Return (winRate, effectiveSampleSize) over STATISTICAL_TRIALS games."""
    gameRecords = [playGameWithPolicies(hostPolicy, playerStrategy, rng, numDoors)
                   for _ in range(STATISTICAL_TRIALS)]
    keptResults = [gameRecord.won for gameRecord in gameRecords if gameRecord.won is not None]
    return sum(keptResults) / len(keptResults), len(keptResults)


# Guarantees the rule that defines the knowing host: the door he opens is a
# real door, is not the player's door, and is not the prize door. If a change
# to knowingHost or to the core game ever lets him reveal the prize or open the
# player's door, the win rates would silently be for a different problem.
@pytest.mark.parametrize("numDoors", [3, 4, 7])
def test_knowingHostNeverOpensPlayerDoorOrPrizeDoor(numDoors):
    rng = np.random.default_rng(SEED)
    for _ in range(INVARIANT_GAMES):
        gameRecord = playGameWithPolicies(knowingHost, stickStrategy, rng, numDoors)
        assert gameRecord.openedDoor != gameRecord.firstChoice
        assert gameRecord.openedDoor != gameRecord.prize
        assert 0 <= gameRecord.openedDoor < numDoors


# Guarantees that switching is a legal move for every host type: the player
# ends on a real door that is still closed and is different from the first
# choice. Catches a switchStrategy that "switches" to the opened door or stays
# on the original door.
@pytest.mark.parametrize("numDoors", [3, 4, 7])
@pytest.mark.parametrize("hostPolicy", [knowingHost, randomHost, makeBiasedHost(0.9)],
                         ids=["knowing", "random", "biased"])
def test_switchTargetIsUnopenedAndUnchosen(hostPolicy, numDoors):
    rng = np.random.default_rng(SEED)
    for _ in range(INVARIANT_GAMES):
        gameRecord = playGameWithPolicies(hostPolicy, switchStrategy, rng, numDoors)
        if gameRecord.won is None:
            # Discarded trial: the player never got to switch.
            continue
        assert gameRecord.finalChoice != gameRecord.openedDoor
        assert gameRecord.finalChoice != gameRecord.firstChoice
        assert 0 <= gameRecord.finalChoice < numDoors


# Guarantees that a game with fewer than 3 doors is rejected with ValueError
# by both entry points, instead of running a game where the host has no door
# to open. Catches the numDoors check being removed from either function.
@pytest.mark.parametrize("numDoors", [2, 1, 0, -1])
def test_fewerThanThreeDoorsRaisesValueError(numDoors):
    rng = np.random.default_rng(SEED)
    with pytest.raises(ValueError):
        playGame("stick", rng, numDoors=numDoors)
    with pytest.raises(ValueError):
        playGameWithPolicies(knowingHost, stickStrategy, rng, numDoors)


# Guarantees that sticking wins about 1/n of the time against the knowing
# host. This holds only if the prize and the first choice are both uniform
# over the doors and independent, so it catches a skewed or correlated draw.
@pytest.mark.parametrize("numDoors", [3, 4, 10])
def test_knowingHostStickWinRateIsOneOverN(numDoors):
    rng = np.random.default_rng(SEED)
    expectedWinRate = 1 / numDoors
    winRate, sampleSize = measureWinRate(knowingHost, stickStrategy, numDoors, rng)
    assert abs(winRate - expectedWinRate) <= threeStandardErrors(expectedWinRate, sampleSize)


# Guarantees that switching wins about (n-1)/(n(n-2)) of the time against the
# knowing host (2/3 for 3 doors). The player is wrong at first with probability
# (n-1)/n and then picks uniformly among the n-2 remaining closed doors, one of
# which has the prize. Catches a host that leaks or hides the wrong
# information, or a switch that is not uniform over the remaining doors.
@pytest.mark.parametrize("numDoors", [3, 4, 10])
def test_knowingHostSwitchWinRateMatchesTheory(numDoors):
    rng = np.random.default_rng(SEED)
    expectedWinRate = (numDoors - 1) / (numDoors * (numDoors - 2))
    winRate, sampleSize = measureWinRate(knowingHost, switchStrategy, numDoors, rng)
    assert abs(winRate - expectedWinRate) <= threeStandardErrors(expectedWinRate, sampleSize)


# Guarantees the Monty Fall result: when the host opens a random door and the
# trials where he reveals the prize are discarded, switching wins about 1/2 of
# the kept trials, not 2/3. Also checks that some trials really were discarded.
# Catches randomHost avoiding the prize, or discarded trials being counted.
def test_montyFallSwitchWinRateIsOneHalfForThreeDoors():
    rng = np.random.default_rng(SEED)
    expectedWinRate = 1 / 2
    # sampleSize here is the effective sample size: discarded trials are excluded.
    winRate, sampleSize = measureWinRate(randomHost, switchStrategy, 3, rng)
    assert sampleSize < STATISTICAL_TRIALS
    assert abs(winRate - expectedWinRate) <= threeStandardErrors(expectedWinRate, sampleSize)
