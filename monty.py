"""Monty Hall simulation: compare "stick" vs "switch" win rates."""

import argparse

import numpy as np


def playGame(strategy, rng):
    """Play one 3-door game. Return True if the player wins the prize."""
    if strategy not in ("stick", "switch"):
        raise ValueError(f"unknown strategy: {strategy!r}")

    doors = [0, 1, 2]
    prize = int(rng.integers(3))
    choice = int(rng.integers(3))

    # The host knows where the prize is and opens a door that is
    # neither the player's choice nor the prize.
    openableDoors = [door for door in doors if door != choice and door != prize]
    openedDoor = int(rng.choice(openableDoors))

    if strategy == "switch":
        # Exactly one door is left that is neither chosen nor opened.
        choice = [door for door in doors if door != choice and door != openedDoor][0]

    return choice == prize


def main():
    parser = argparse.ArgumentParser(description="Monty Hall simulation")
    parser.add_argument("-n", "--trials", type=int, default=100_000,
                        help="number of trials per strategy (default: 100000)")
    parser.add_argument("--seed", type=int, default=None,
                        help="seed for reproducible results")
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)

    for strategy in ("stick", "switch"):
        wins = sum(playGame(strategy, rng) for _ in range(args.trials))
        winRate = wins / args.trials
        print(f"{strategy:>6}: {wins}/{args.trials} wins ({winRate:.4f})")


if __name__ == "__main__":
    main()
