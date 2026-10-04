"""Monty Hall simulation: compare "stick" vs "switch" win rates."""

import argparse

import numpy as np


def playGame(strategy, rng, numDoors=3, hostType="knowing", lowerDoorProbability=0.5):
    """Play one game. Return True if the player wins the prize, False if not.

    hostType "knowing": the host opens one non-prize, non-chosen door.
    hostType "random" (Monty Fall): the host opens a random non-chosen door;
        if that door reveals the prize the trial is discarded and None is returned.
    hostType "biased": like "knowing", but when more than one door can be
        opened, the host opens the lowest-numbered one with probability
        lowerDoorProbability.
    """
    if strategy not in ("stick", "switch"):
        raise ValueError(f"unknown strategy: {strategy!r}")
    if numDoors < 3:
        raise ValueError(f"numDoors must be at least 3, got {numDoors}")
    if hostType not in ("knowing", "random", "biased"):
        raise ValueError(f"unknown hostType: {hostType!r}")
    if not 0 <= lowerDoorProbability <= 1:
        raise ValueError(f"lowerDoorProbability must be between 0 and 1, got {lowerDoorProbability}")

    doors = list(range(numDoors))
    prize = int(rng.integers(numDoors))
    choice = int(rng.integers(numDoors))

    if hostType == "knowing":
        # The host knows where the prize is and opens a door that is
        # neither the player's choice nor the prize.
        openableDoors = [door for door in doors if door != choice and door != prize]
        openedDoor = int(rng.choice(openableDoors))
    elif hostType == "random":
        # The host does not know where the prize is and opens any door
        # other than the player's choice.
        openableDoors = [door for door in doors if door != choice]
        openedDoor = int(rng.choice(openableDoors))
        if openedDoor == prize:
            # The prize was revealed, so this trial is discarded.
            return None
    elif hostType == "biased":
        openableDoors = [door for door in doors if door != choice and door != prize]
        if len(openableDoors) == 1:
            openedDoor = openableDoors[0]
        elif rng.random() < lowerDoorProbability:
            openedDoor = openableDoors[0]
        else:
            # With exactly two openable doors this is the higher-numbered one.
            openedDoor = int(rng.choice(openableDoors[1:]))

    if strategy == "switch":
        switchTargets = [door for door in doors if door != choice and door != openedDoor]
        if len(switchTargets) == 1:
            # With 3 doors, exactly one door is left that is neither chosen nor opened.
            choice = switchTargets[0]
        else:
            choice = int(rng.choice(switchTargets))

    return choice == prize


def main():
    parser = argparse.ArgumentParser(description="Monty Hall simulation")
    parser.add_argument("-n", "--trials", type=int, default=100_000,
                        help="number of trials per strategy (default: 100000)")
    parser.add_argument("--seed", type=int, default=None,
                        help="seed for reproducible results")
    parser.add_argument("--doors", type=int, default=3,
                        help="number of doors, at least 3 (default: 3)")
    parser.add_argument("--host", choices=("knowing", "random", "biased"), default="knowing",
                        help="host behavior; 'random' is Monty Fall (default: knowing)")
    parser.add_argument("--bias", type=float, default=0.5,
                        help="biased host: probability of opening the lowest-numbered "
                             "openable door (default: 0.5)")
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)

    for strategy in ("stick", "switch"):
        gameResults = [playGame(strategy, rng, args.doors, args.host, args.bias)
                       for _ in range(args.trials)]
        # Discarded Monty Fall trials are None and do not count.
        keptResults = [result for result in gameResults if result is not None]
        wins = sum(keptResults)
        effectiveSampleSize = len(keptResults)
        winRate = wins / effectiveSampleSize
        print(f"{strategy:>6}: {wins}/{effectiveSampleSize} wins ({winRate:.4f})")
        if args.host == "random":
            print(f"        effective sample size: {effectiveSampleSize} of {args.trials} trials "
                  f"({args.trials - effectiveSampleSize} discarded)")


if __name__ == "__main__":
    main()
