from __future__ import (absolute_import, division, print_function)
import numpy as np


def single_size(shape=None, axis=None):
    """
    Size of a single unit across the axis we are traversing.
    This does not take into account data type, it returns the pure size.

    To get bits from this, multiply by the data size.
    To get bytes, divide the bits by 8.
    To get the size of the whole dataset, multiply by the length axis (the one that we are traversing across).
    To get kilobytes, divide by 1024.
    To get megabytes, divide by 1024 again.
    """
    single = 1
    for i in range(len(shape)):
        if i == axis:
            continue
        single *= shape[i]

    return single


def _determine_dtype_size(dtype=None):
    if dtype in ['int16', 'float16', 'np.int16', 'np.float16', '16']\
            or isinstance(dtype, np.int16) \
            or isinstance(dtype, np.float16) \
            or dtype is np.int16 \
            or dtype is np.float16:

        return 16
    elif dtype in ['int32', 'float32', 'np.int32', 'np.float32', '32'] \
            or isinstance(dtype, np.int32) \
            or isinstance(dtype, np.float32) \
            or dtype is np.int32 \
            or dtype is np.float32:
        return 32
    elif dtype in ['int64', 'float64', 'np.int64', 'np.float64', '64'] \
            or isinstance(dtype, np.int64) \
            or isinstance(dtype, np.float64) \
            or dtype is np.int64 \
            or dtype is np.float64:
        return 64


def full_size(shape=None, axis=None, dtype=None):
    """
    Compute the full size of the data and return in Megabytes.

    If a parameter is not specified on call, the one provided at the class initialisation will be used!

    :param shape: The shape of the data for which the size will be calculated
    :param axis: The axis on which the shape is going to be traversed
    :param dtype: The data type

    """
    mul = _determine_dtype_size(dtype)

    single = single_size(shape, axis)

    # get the bits
    single_bits = single * mul

    # get the bytes
    single_bytes = single_bits / 8

    full_size_bytes = shape[axis] * single_bytes
    # convert to MB
    return full_size_bytes / 1024 / 1024
