"""Glyph-set membership on screen arrays (numba): isin and any_in, moved out of utils.py (speed-up 261117-lkz).

The (min, max, mask) of an element set is memoized; the kernels test each cell against it. any_in stops at the
first match instead of building the boolean array that isin returns."""
import functools
from itertools import chain

import numba as nb
import numpy as np


@nb.njit('b1[:,:](i2[:,:],i2,i2,b1[:])', cache=True)
def _isin_kernel(array, mi, ma, mask):
    ret = np.zeros(array.shape, dtype=nb.b1)
    for y in range(array.shape[0]):
        for x in range(array.shape[1]):
            if array[y, x] < mi or array[y, x] > ma:
                continue
            ret[y, x] = mask[array[y, x] - mi]
    return ret


@functools.lru_cache(1024)
def _isin_mask(elems):
    elems = np.array(list(chain(*elems)), np.int16)
    return _isin_mask_kernel(elems)


@nb.njit('Tuple((i2,i2,b1[:]))(i2[:])', cache=True)
def _isin_mask_kernel(elems):
    mi: i2 = 32767
    ma: i2 = -32768
    for i in range(elems.shape[0]):
        if mi > elems[i]:
            mi = elems[i]
        if ma < elems[i]:
            ma = elems[i]
    ret = np.zeros(ma - mi + 1, dtype=nb.b1)
    for i in range(elems.shape[0]):
        ret[elems[i] - mi] = True
    return mi, ma, ret


def _mask(array, elems):
    assert array.dtype == np.int16
    try:  # the mask is memoized on elems; they are nearly always hashable already (frozensets, tuples)
        return _isin_mask(elems)
    except TypeError:  # a list or set among them: make it hashable (same elements, same mask)
        return _isin_mask(tuple(tuple(e) if isinstance(e, list) else
                                frozenset(e) if isinstance(e, set) else e for e in elems))


def isin(array, *elems):
    return _isin_kernel(array, *_mask(array, elems))


@nb.njit('b1(i2[:,:],i2,i2,b1[:])', cache=True)
def _any_in_kernel(array, mi, ma, mask):
    for y in range(array.shape[0]):
        for x in range(array.shape[1]):
            if mi <= array[y, x] <= ma and mask[array[y, x] - mi]:
                return True
    return False


def any_in(array, *elems):
    """isin(array, *elems).any() without building the boolean array; stops at the first match."""
    return bool(_any_in_kernel(array, *_mask(array, elems)))
