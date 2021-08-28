from itertools import starmap, chain, tee, repeat
from typing import Optional, Callable


def repeatfunc(func: Callable, times: Optional[int] = None, *args):
    """Repeat calls to func with specified arguments.

    Example:  repeatfunc(random.random)
    """
    if times is None:
        return starmap(func, repeat(args))
    return starmap(func, repeat(args, times))


def pairwise(iterable):
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


def flatten(list_of_lists):
    """Flatten one level of nesting. """
    return chain.from_iterable(list_of_lists)


def grouper(iterable, n):
    """Collect data into fixed-length chunks or blocks."""

    # grouper('ABCDEFG', 3) --> ABC DEF
    args = [iter(iterable)] * n
    return zip(*args)
