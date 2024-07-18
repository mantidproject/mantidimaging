# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import math

import numpy
from typing import TYPE_CHECKING
from collections.abc import Iterable

if TYPE_CHECKING:
    import numpy.typing as npt


def _determine_dtype_size(dtype: npt.DTypeLike) -> int:
    try:
        return numpy.dtype(dtype).itemsize
    except TypeError as exc:
        raise ValueError(f"Can't get size of {dtype}, ({type(dtype)=})") from exc


def full_size(shape: Iterable[int]) -> int:
    """
    Compute the full size of the data, i.e. the number of elements

    :param shape: The shape of the data for which the size will be calculated
    :returns: The size
    """

    return math.prod(shape)


def full_size_bytes(shape: Iterable[int], dtype: npt.DTypeLike) -> int:
    return full_size(shape) * _determine_dtype_size(dtype)


def full_size_KB(shape: Iterable[int], dtype: npt.DTypeLike) -> float:
    return full_size_bytes(shape, dtype) / 1024


def full_size_MB(shape: Iterable[int], dtype: npt.DTypeLike) -> float:
    return full_size_KB(shape, dtype) / 1024


def number_of_images_from_indices(start: int, end: int, increment: int) -> int:
    return int((end - start) / increment) if increment != 0 else 0
