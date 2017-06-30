from __future__ import absolute_import, division, print_function


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
    for i, curr_shape in enumerate(shape):
        if i == axis:
            continue
        single *= curr_shape

    return single


def _determine_dtype_size(dtype=None):
    if '16' in str(dtype):
        return 16
    elif '32' in str(dtype):
        return 32
    elif '64' in str(dtype):
        return 64


def full_size(shape=None, axis=None, dtype=None):
    """
    Compute the full size of the data and return in Megabytes.

    :param shape: The shape of the data for which the size will be calculated

    :param axis: The axis on which the shape is going to be traversed

    :param dtype: The data type


    :returns: The size as a float in Megabytes

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
