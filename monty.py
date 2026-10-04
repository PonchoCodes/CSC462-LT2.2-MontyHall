"""Monty Hall simulation: compare "stick" vs "switch" win rates.

Host behaviors and player strategies are policy functions that are passed
into the core game function, playGameWithPolicies.

A host policy has the signature
    hostPolicy(doors, choice, prize, rng) -> openedDoor
A player strategy has the signature
    playerStrategy(doors, choice, openedDoor, rng) -> finalChoice
"""

import argparse
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class GameRecord:
    """What happened in one game.

    If the host revealed the prize the trial is discarded: finalChoice and
    won are both None.
    """
    prize: int
    firstChoice: int
    openedDoor: int
    finalChoice: int | None
    won: bool | None


# Host policies

def knowingHost(doors, choice, prize, rng):
    # The host knows where the prize is and opens a door that is
    # neither the player's choice nor the prize.
    openableDoors = [door for door in doors if door != choice and door != prize]
    return int(rng.choice(openableDoors))


def randomHost(doors, choice, prize, rng):
    # Monty Fall: the host does not know where the prize is and opens
    # any door other than the player's choice.
    openableDoors = [door for door in doors if door != choice]
    return int(rng.choice(openableDoors))


def makeBiasedHost(lowerDoorProbability):
    """Build a host policy that, when more than one door can be opened,
    opens the lowest-numbered one with probability lowerDoorProbability."""
    if not 0 <= lowerDoorProbability <= 1:
        raise ValueError(f"lowerDoorProbability must be between 0 and 1, got {lowerDoorProbability}")

    def biasedHost(doors, choice, prize, rng):
        openableDoors = [door for door in doors if door != choice and door != prize]
        if len(openableDoors) == 1:
            return openableDoors[0]
        elif rng.random() < lowerDoorProbability:
            return openableDoors[0]
        else:
            # With exactly two openable doors this is the higher-numbered one.
            return int(rng.choice(openableDoors[1:]))

    return biasedHost


# Player strategies

def stickStrategy(doors, choice, openedDoor, rng):
    return choice


def switchStrategy(doors, choice, openedDoor, rng):
    switchTargets = [door for door in doors if door != choice and door != openedDoor]
    if len(switchTargets) == 1:
        # With 3 doors, exactly one door is left that is neither chosen nor opened.
        return switchTargets[0]
    else:
        return int(rng.choice(switchTargets))


PLAYER_STRATEGIES = {"stick": stickStrategy, "switch": switchStrategy}
HOST_TYPES = ("knowing", "random", "biased")


def makeHostPolicy(hostType, lowerDoorProbability=0.5):
    """Return the host policy function for a host type name."""
    if hostType == "knowing":
        return knowingHost
    elif hostType == "random":
        return randomHost
    elif hostType == "biased":
        return makeBiasedHost(lowerDoorProbability)
    raise ValueError(f"unknown hostType: {hostType!r}")


# Core game

def playGameWithPolicies(hostPolicy, playerStrategy, rng, numDoors=3):
    """Play one game with the given policies and return a GameRecord."""
    if numDoors < 3:
        raise ValueError(f"numDoors must be at least 3, got {numDoors}")

    doors = list(range(numDoors))
    prize = int(rng.integers(numDoors))
    choice = int(rng.integers(numDoors))

    openedDoor = hostPolicy(doors, choice, prize, rng)
    if openedDoor == prize:
        # The prize was revealed, so this trial is discarded.
        return GameRecord(prize, choice, openedDoor, None, None)

    finalChoice = playerStrategy(doors, choice, openedDoor, rng)
    return GameRecord(prize, choice, openedDoor, finalChoice, finalChoice == prize)


def playGame(strategy, rng, numDoors=3, hostType="knowing", lowerDoorProbability=0.5):
    """Play one game, choosing the policies by name.

    Return True if the player wins the prize, False if not, and None if the
    trial is discarded because the host revealed the prize.
    """
    if strategy not in PLAYER_STRATEGIES:
        raise ValueError(f"unknown strategy: {strategy!r}")
    if numDoors < 3:
        raise ValueError(f"numDoors must be at least 3, got {numDoors}")
    if hostType not in HOST_TYPES:
        raise ValueError(f"unknown hostType: {hostType!r}")
    if not 0 <= lowerDoorProbability <= 1:
        raise ValueError(f"lowerDoorProbability must be between 0 and 1, got {lowerDoorProbability}")

    hostPolicy = makeHostPolicy(hostType, lowerDoorProbability)
    playerStrategy = PLAYER_STRATEGIES[strategy]
    return playGameWithPolicies(hostPolicy, playerStrategy, rng, numDoors).won


def main():
    parser = argparse.ArgumentParser(description="Monty Hall simulation")
    parser.add_argument("-n", "--trials", type=int, default=100_000,
                        help="number of trials per strategy (default: 100000)")
    parser.add_argument("--seed", type=int, default=None,
                        help="seed for reproducible results")
    parser.add_argument("--doors", type=int, default=3,
                        help="number of doors, at least 3 (default: 3)")
    parser.add_argument("--host", choices=HOST_TYPES, default="knowing",
                        help="host behavior; 'random' is Monty Fall (default: knowing)")
    parser.add_argument("--bias", type=float, default=0.5,
                        help="biased host: probability of opening the lowest-numbered "
                             "openable door (default: 0.5)")
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)
    hostPolicy = makeHostPolicy(args.host, args.bias)

    for strategyName, playerStrategy in PLAYER_STRATEGIES.items():
        gameRecords = [playGameWithPolicies(hostPolicy, playerStrategy, rng, args.doors)
                       for _ in range(args.trials)]
        # Discarded Monty Fall trials have won set to None and do not count.
        keptResults = [gameRecord.won for gameRecord in gameRecords if gameRecord.won is not None]
        wins = sum(keptResults)
        effectiveSampleSize = len(keptResults)
        winRate = wins / effectiveSampleSize
        print(f"{strategyName:>6}: {wins}/{effectiveSampleSize} wins ({winRate:.4f})")
        if args.host == "random":
            print(f"        effective sample size: {effectiveSampleSize} of {args.trials} trials "
                  f"({args.trials - effectiveSampleSize} discarded)")


if __name__ == "__main__":
    main()
