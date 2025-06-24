# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from functools import partial
from logging import getLogger
from typing import Any
from collections.abc import Callable, Iterable

import numpy as np

from mantidimaging.core.operation_history.decorators import log_operation
from mantidimaging.core.operations.loader import load_filter_packages
from . import const

MODULE_NOT_FOUND = "Could not find module with name '{}'"


class ImageOperation:
    """
    A deserialized representation of an item in a stack's operation_history
    """

    def __init__(self, filter_name: str, filter_kwargs: dict[str, Any], display_name: str):
        self.filter_name = filter_name
        self.filter_kwargs = filter_kwargs
        self.display_name = display_name

    def to_partial(self, filter_funcs: dict[str, Callable]) -> partial:
        try:
            fn = filter_funcs[self.filter_name]
            return partial(fn, **self.filter_kwargs)
        except KeyError as exc:
            msg = MODULE_NOT_FOUND.format(self.filter_name)
            getLogger(__name__).error(msg)
            raise KeyError(msg) from exc

    @staticmethod
    def from_serialized(metadata_entry: dict[str, Any]) -> ImageOperation:
        return ImageOperation(filter_name=metadata_entry[const.OPERATION_NAME],
                              filter_kwargs=metadata_entry[const.OPERATION_KEYWORD_ARGS],
                              display_name=metadata_entry[const.OPERATION_DISPLAY_NAME])

    def serialize(self) -> dict[str, Any]:
        return {
            const.OPERATION_NAME: self.filter_name,
            const.OPERATION_KEYWORD_ARGS: self.filter_kwargs,
            const.OPERATION_DISPLAY_NAME: self.display_name,
        }

    def __str__(self):
        return f"{self.display_name if self.display_name else self.filter_name}, " \
               f"kwargs: {self.filter_kwargs}"


def deserialize_metadata(metadata: dict[str, Any]) -> list[ImageOperation]:
    return [ImageOperation.from_serialized(entry) for entry in metadata[const.OPERATION_HISTORY]] \
        if const.OPERATION_HISTORY in metadata else []


def ops_to_partials(filter_ops: Iterable[ImageOperation]) -> Iterable[partial]:
    raw_filters = {f.__name__: f.filter_func for f in load_filter_packages()}
    wrapped_filters = {name: log_operation(func) for name, func in raw_filters.items()}
    fixed_funcs = {
        const.OPERATION_NAME_AXES_SWAP: lambda img, **_: np.swapaxes(img, 0, 1),
    }
    wrapped_filters.update(fixed_funcs)
    return (op.to_partial(wrapped_filters) for op in filter_ops)
