import itertools
from bisect import bisect
from operator import itemgetter

# tuples of bounds provided as problem parameters
Bound = tuple[int | None, int | None]
Bounds = tuple[Bound, ...]
# solution table mapping space to (x, rate) pairs
SolutionKeys = tuple[int, ...]
SolutionValues = tuple[tuple[int, int], ...]

# TODO: solve integer allocation problem starting from continuous solution
class SpaceAllocator:
    """Solver for the even allocation of a budget of integers under constraints."""

    def __init__(self, bounds: Bounds, n_unconstrained: int):
        # store problem parameters
        self.bounds = bounds
        self.n_unconstrained = n_unconstrained
        # construct lookup table
        self._table = _solve_table(bounds, n_unconstrained)

    def _solve_x(self, space: int):
        """Compute the (non-integer) solution to x."""
        # get ref to solution table
        keys, values = self._table
        # find region with binary search
        space_key = bisect(keys, space) - 1
        if space_key < 0:
            raise ValueError("Space is out of range of solution space.")
        # min_space + dx * rate = space <=> dx = (space - min_space) / rate
        x, rate = values[space_key]
        min_space = keys[space_key]
        dx = (space - min_space) / rate
        return x + dx

    def evaluate(self, x: int):
        """Evaluate the bounded distribution for the specified value of x."""
        return tuple(
            itertools.chain(
                (
                    # lower bound if x is above it
                    b[0] if b[0] is not None and x < b[0]
                    # upper bound if x is below it
                    else b[1] if b[1] is not None and x > b[1] else x
                    for b in self.bounds
                ),
                # unconstrained items
                (x for _ in range(self.n_unconstrained)),
            )
        )

    def solve(self, space: int):
        """Solve the allocation problem and return the bounded items."""
        x = self._solve_x(space)
        return self.evaluate(x)  # type: ignore


def _flatten_bounds(bounds: Bounds) -> list[tuple[int, bool]]:
    """Return (lower, upper) bounds flattened into sorted tuples of (value, is-upper-bound)."""
    lower_bounds = ((b[0], False) for b in bounds if b[0] is not None)
    upper_bounds = ((b[1], True) for b in bounds if b[1] is not None)
    return sorted(itertools.chain(lower_bounds, upper_bounds), key=itemgetter(0))


def _solve_table(bounds: Bounds, n_unconstrained: int) -> tuple[SolutionKeys, SolutionValues]:
    """Compute space |-> (x, rate) solution table of linear regions for bounds."""
    # construct lookup table
    flat_bounds = _flatten_bounds(bounds)

    # initialize vars
    min_space_total = 0  # min constraints are accumulated in loop
    rate = sum(b[0] is None for b in bounds) + n_unconstrained  # initial rate is 1 per non-lower-bounded element

    # construct intermediary table mapping values of x to rates of space allocation
    x_table: dict[int, int] = {0: rate}
    for b, is_upper in flat_bounds:
        if is_upper:
            # if upper bound: rate decreases
            rate -= 1
        else:
            # if lower bound: rate and total min increases
            rate += 1
            min_space_total += b
        x_table[b] = rate

    # construct final table mapping space to x-value and rates on linear sections
    # NOTE: since bounds are pre-sorted, ansertion order guarantees that keys are sorted
    keys: list[int] = []
    values: list[tuple[int, int]] = []
    min_space = min_space_total
    prev_x, prev_rate = 0, 0

    for x, rate in x_table.items():
        # accumulate the mapping from regions of space to values of x
        min_space += (x - prev_x) * prev_rate
        keys.append(min_space)
        values.append((x, rate))
        prev_x, prev_rate = x, rate

    return tuple(keys), tuple(values)
