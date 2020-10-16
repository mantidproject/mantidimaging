def to_KB(size, dtype=None):
    return to_bytes(to_bits(size, dtype)) / 1024


def to_MB(size, dtype=None):
    return to_KB(size, dtype) / 1024


def to_GB(size, dtype=None):
    return to_MB(size, dtype) / 1024


def single_size(shape=None, axis=None):
    """
    Size of a single unit across the axis we are traversing.
    This does not take into account data type, it returns the pure size.

    - To get bits from this, multiply by the data size.
    - To get bytes, divide the bits by 8.
    - To get the size of the whole dataset, multiply by the length axis (the
      one that we are traversing across).
    - To get kilobytes, divide by 1024.
    - To get megabytes, divide by 1024 again.
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
    return 1


def to_bytes(bits):
    return bits / 8


def to_bits(size, dtype=None):
    if dtype:
        mul = _determine_dtype_size(dtype)
    else:
        mul = 1
    return size * mul


def full_size(shape=None, axis=None):
    """
    Compute the full size of the data and return in Megabytes.

    :param shape: The shape of the data for which the size will be calculated

    :param axis: The axis on which the shape is going to be traversed

    :param dtype: The data type

    :returns: The size as a float in Megabytes

    """
    single = single_size(shape, axis)
    return single * shape[axis]


def full_size_MB(shape=None, axis=None, dtype=None):
    return to_MB(full_size(shape, axis), dtype)


def full_size_KB(shape=None, axis=None, dtype=None):
    return to_KB(full_size(shape, axis), dtype)


def number_of_images_from_indices(start, end, increment):
    return int((end - start) / increment) if increment != 0 else 0
