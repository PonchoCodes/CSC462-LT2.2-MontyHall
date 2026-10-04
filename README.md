# Monty Hall Simulation

## What this is and how to run it

A Monte Carlo simulation of the Monty Hall problem. It plays many games with the "always stick" strategy and many with the "always switch" strategy, and prints the win count and win rate of each.

It supports:

- any number of doors, 3 or more (`--doors`)
- three host behaviors (`--host`):
  - `knowing`: the host knows where the prize is and opens one door that is neither the player's door nor the prize door
  - `random` (Monty Fall): the host opens a random door other than the player's; trials where he reveals the prize are discarded and the effective sample size is printed
  - `biased`: like `knowing`, but when he has more than one door to choose from he opens the lowest-numbered one with probability `--bias`

Requirements: Python 3.10 or newer and numpy. Developed with Python 3.13.0 and numpy 2.2.4.

Run it from the project folder (on systems without the `py` launcher, use `python` instead of `py`):

```
py monty.py                                  # 100,000 trials per strategy, 3 doors, knowing host
py monty.py --seed 42                        # reproducible run
py monty.py --trials 1000000 --seed 7        # more trials
py monty.py --doors 5                        # 5 doors
py monty.py --host random                    # Monty Fall
py monty.py --host biased --bias 0.9         # biased host
py monty.py --help                           # list all options
```

Output of `py monty.py --seed 42`:

```
 stick: 33215/100000 wins (0.3322)
switch: 66690/100000 wins (0.6669)
```

Output of `py monty.py --seed 42 --host random`:

```
 stick: 33422/66811 wins (0.5002)
        effective sample size: 66811 of 100000 trials (33189 discarded)
switch: 33651/66873 wins (0.5032)
        effective sample size: 66873 of 100000 trials (33127 discarded)
```

## How to run the tests and what each test file protects against

Requires pytest (`py -m pip install pytest`). From the project folder:

```
py -m pytest          # run everything
py -m pytest -v       # one line per test
```

`pytest.ini` adds the project folder to the import path so the tests can `import monty`, and points pytest at the `tests` folder.

### `tests/test_regression.py`

Protects against any change in the exact behavior of the classic game. With seed 42 and 100,000 trials per strategy it asserts exactly 33215 stick wins and 66690 switch wins, the counts recorded from the v1 code. It fails if the number or order of random draws in the default game changes, even when the new behavior would still be statistically correct. It does not show that the code is correct, only that it is unchanged.

### `tests/test_invariants.py`

Protects against the simulation breaking the rules of the game or drifting from the known probabilities.

| Test | What it guarantees |
|---|---|
| `test_knowingHostNeverOpensPlayerDoorOrPrizeDoor` | The knowing host's opened door is never the player's door or the prize door (3, 4 and 7 doors). |
| `test_switchTargetIsUnopenedAndUnchosen` | After switching, the player is on a closed door different from the first choice (all three hosts; 3, 4 and 7 doors). |
| `test_fewerThanThreeDoorsRaisesValueError` | `playGame` and `playGameWithPolicies` raise `ValueError` for 2, 1, 0 and -1 doors. |
| `test_knowingHostStickWinRateIsOneOverN` | Stick wins about 1/n of the time (3, 4 and 10 doors). |
| `test_knowingHostSwitchWinRateMatchesTheory` | Switch wins about (n-1)/(n(n-2)) of the time (3, 4 and 10 doors). |
| `test_montyFallSwitchWinRateIsOneHalfForThreeDoors` | With the random host and 3 doors, switch wins about 1/2 of the kept trials, and some trials are discarded. |

The statistical tests allow a difference of 3 standard errors, computed from the sample size as `3 * sqrt(p * (1 - p) / N)`, where `p` is the theoretical win rate and `N` is the number of kept trials. They use a fixed seed (2026), so their result is the same on every run.

## Architecture: the parts and how they connect

Everything is in `monty.py`.

| Part | Responsibility |
|---|---|
| `GameRecord` | Frozen dataclass describing one game: `prize`, `firstChoice`, `openedDoor`, `finalChoice`, `won`. For a discarded trial `finalChoice` and `won` are `None`. |
| `knowingHost`, `randomHost` | Host policies. Signature `(doors, choice, prize, rng) -> openedDoor`. |
| `makeBiasedHost(lowerDoorProbability)` | Validates the probability and returns a host policy with the same signature that remembers that probability. |
| `stickStrategy`, `switchStrategy` | Player strategies. Signature `(doors, choice, openedDoor, rng) -> finalChoice`. |
| `PLAYER_STRATEGIES` | Dictionary mapping `"stick"` and `"switch"` to the strategy functions. |
| `HOST_TYPES` | Tuple of the valid host names; also the choices for `--host`. |
| `makeHostPolicy(hostType, lowerDoorProbability)` | Maps a host name to a host policy function. Raises `ValueError` for an unknown name. |
| `playGameWithPolicies(hostPolicy, playerStrategy, rng, numDoors=3)` | The core game. Contains no host-specific or strategy-specific logic. Returns a `GameRecord`. |
| `playGame(strategy, rng, numDoors=3, hostType="knowing", lowerDoorProbability=0.5)` | Wrapper with the v2 signature. Validates its arguments, looks up the policies by name, calls `playGameWithPolicies`, and returns only `won` (`True`, `False` or `None`). Used by the regression test. |
| `main()` | Command-line entry point. |

Data flow for one run:

1. `main()` parses the command line with argparse into `args`.
2. It creates one generator, `np.random.default_rng(args.seed)`, which is used for every random draw in the run.
3. It calls `makeHostPolicy(args.host, args.bias)` once to get the host policy function.
4. For each entry in `PLAYER_STRATEGIES` (stick, then switch) it calls `playGameWithPolicies(hostPolicy, playerStrategy, rng, args.doors)` `args.trials` times.
5. Inside `playGameWithPolicies`, in this order:
   1. check `numDoors >= 3`
   2. draw the prize door with `rng.integers(numDoors)`
   3. draw the player's first choice with `rng.integers(numDoors)`
   4. call `hostPolicy(doors, choice, prize, rng)` to get the opened door
   5. if the opened door is the prize, return a discarded `GameRecord`
   6. call `playerStrategy(doors, choice, openedDoor, rng)` to get the final choice
   7. return a `GameRecord` with `won = (finalChoice == prize)`
6. `main()` drops the records whose `won` is `None`, counts the wins among the rest, and prints wins, kept trials and win rate. For `--host random` it also prints the effective sample size and the number of discarded trials.

To add a host or strategy, write a function with the matching signature and add it to `makeHostPolicy` / `HOST_TYPES` or to `PLAYER_STRATEGIES`. `playGameWithPolicies` is not edited.

## Why this structure

- **What problem did the Phase 2 version have?** The Phase 2 version was harder to add new features to. I noticed this when trying to add the biased host, so I switched to a function approach.
- **What options did you consider?** I considered using classes but decided that was overkill for the purposes of this project.
- **Why this one?** I picked functions inside of functions because it didn't need much more code and it solved my problem.

## Decision log

- **RNG choice (`default_rng` vs. the `random` module).** I used numpy.random over the random module because I was already going to use numpy's `choice` to pick between doors, so I decided I might as well use numpy's random module. Moreover, if I needed to, I can generate hundreds of random numbers at once with numpy, whereas with random I'd need a loop.
- **Fixed seed in the tests.** We use a fixed seed for tests because it removes the randomness and allows us to focus only on keeping the behavior the same.

## Known limitations

- **Monte Carlo error.** Results are estimates. The error of a win rate shrinks in proportion to 1/sqrt(N): about 0.0015 standard error for a rate near 1/3 at the default N = 100,000. Ten times the precision needs 100 times the trials.
- **Uniform choices assumed.** The prize position, the player's first choice, the knowing and random hosts' choice among their openable doors, and the switch choice among the remaining doors are all uniform. The only non-uniform behavior is the biased host.
- **Monty Fall shrinks the effective sample size.** Trials where the random host reveals the prize are discarded. With 3 doors about 1/3 of trials are lost, so the error is larger than `--trials` suggests. The stick and switch runs keep different numbers of trials.
- **The bias does not show in the output.** The program reports only overall win rates, which are the same for every value of `--bias`. The bias changes the win rate conditional on which door was opened, and that is not reported.
- **The host opens exactly one door**, for any number of doors.
- **More than 3 doors: switching** picks uniformly at random among the closed doors other than the first choice.
- **More than 3 doors: biased host.** When more than two doors can be opened, he opens the lowest-numbered one with probability p and otherwise a uniformly random one of the rest. With exactly two openable doors this is "lower with probability p, higher otherwise".
- **Speed.** Games are played one at a time in a Python loop, and all `GameRecord`s of a strategy are held in memory before counting. Very large `--trials` values are slow and memory-heavy.
- **Command-line input errors are tracebacks.** `--doors 2` and `--bias 2` end with a `ValueError` traceback, and `--trials 0` ends with `ZeroDivisionError`, rather than a usage message.
- **Stick and switch share one generator.** The stick games run first and the switch games continue from the same random stream, so the two strategies are not played on the same sequence of games.

## Likely points of future breakage

- **Seeded outputs depend on numpy.** The regression test's exact counts (33215 and 66690) were recorded with numpy 2.2.4. They depend on the bit stream of `default_rng` and on how `integers` and `choice` consume it. A numpy release that changes any of these would fail the regression test without any change to this code.
- **Order and number of random draws.** The regression test also fails if the default game draws in a different order (currently prize, first choice, host's door) or makes an extra draw. For example, `switchStrategy` takes the single remaining door without a draw when there are 3 doors; replacing that with an unconditional `rng.choice` may change the stream.
- **Fixed seed in the statistical tests.** They pass with seed 2026 and `STATISTICAL_TRIALS = 50_000`. A different seed or trial count gives a different sample, and a 3-standard-error check fails by chance roughly 0.3% of the time per test.
- **Assumption that `numDoors >= 3`.** It is checked in `playGameWithPolicies` and `playGame`. The policy functions do not check it themselves; called directly with fewer doors they can receive an empty list of openable doors.
- **Policy signatures are a convention, not enforced.** A new host must accept `(doors, choice, prize, rng)` and return a door other than the player's choice; a new strategy must accept `(doors, choice, openedDoor, rng)`. Nothing validates what a policy returns.
- **Discard rule lives in the core.** `playGameWithPolicies` discards any trial where the opened door is the prize. A future host that is meant to reveal the prize without discarding would need that rule changed.
- **`playGame` and `makeHostPolicy` list hosts by name.** A new host type has to be added to `HOST_TYPES` and `makeHostPolicy`, and a host needing a new setting needs a new parameter and command-line option.
- **`pytest.ini` is needed for imports.** The tests import `monty` from the project root through `pythonpath = .`. Moving `monty.py` into a package or removing `pytest.ini` breaks the imports.
- **Python version.** The `int | None` annotations in `GameRecord` require Python 3.10 or newer.

## Sources

YouTube tutorials on the tools and ideas used in this project:

- **pytest:** [Learn Pytest: The Complete Guide for Beginners](https://www.youtube.com/watch?v=Q8ZmQCzO9pA) and [Python pytest Tutorial: Beginner's Guide to Writing Simple & Scalable Tests](https://www.youtube.com/watch?v=c5NxPksbLOc)
- **numpy's random generator (`default_rng`):** [NumPy Random Generator Tutorial - Modern Random Number Generation in Python](https://www.youtube.com/watch?v=bg3aSAKkLMM) and [NumPy Random default_rng() and its Seed Argument in Python](https://www.youtube.com/watch?v=zdF86daJNiA)
- **`.ini` files:** [Config Files & Parsing in Python](https://www.youtube.com/watch?v=OYUqpJxjII4) and [Create and Read Configuration .ini file](https://www.youtube.com/watch?v=Su1olGdKlSM)
- **Regression testing:** [What is Regression Testing? Software Testing Tutorial](https://www.youtube.com/watch?v=aeu5zacsHsI)
- **Invariant (property-based) testing:** [Shai Geva - Property Based Testing with Hypothesis: Stronger Tests, Less Work](https://www.youtube.com/watch?v=jhhpdzkHyqU) and [Emma Saroyan - Property-Based Testing the Python Way](https://www.youtube.com/watch?v=SYXzqYXP04o)
- **Closures (a function defined inside a function that remembers a value):** [Python Closures](https://www.youtube.com/watch?v=CHo-orWR8PI) and [Closures - Python Concepts (what, how to and why)](https://www.youtube.com/watch?v=JxXy2ehmpjI)

### AI use
I used an AI assistant (Claude) to help format this README. 
