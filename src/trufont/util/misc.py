import itertools


def grouper(iterable, n, fillvalue=None):
    """Collect data into fixed-length chunks or blocks.

    grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx.

    Lifted from itertool's recipes.
    """
    args = [iter(iterable)] * n
    return itertools.zip_longest(*args, fillvalue=fillvalue)


def pairwise(iterable):
    """s -> (s0,s1), (s1,s2), (s2, s3), ...

    Lifted from itertool's recipes.
    """
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)
