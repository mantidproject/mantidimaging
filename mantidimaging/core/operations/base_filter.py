# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, Any
from collections.abc import Callable
from enum import Enum, auto

import numpy as np

from mantidimaging.core.data import ImageStack

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QFormLayout, QWidget  # noqa: F401   # pragma: no cover
    from mantidimaging.gui.mvp_base import BaseMainWindowView  # pragma: no cover
    from mantidimaging.gui.widgets.dataset_selector import DatasetSelectorWidgetView


class FilterGroup(Enum):
    NoGroup = auto()
    Basic = auto()
    Advanced = auto()


class BaseFilter:
    filter_name = "Unnamed Filter"
    link_histograms = False
    show_negative_overlay = True
    operate_on_sinograms = False
    allow_for_180_projection = True

    SINOGRAM_FILTER_INFO = "This filter will work on a\nsinogram view of the data."

    __name__ = "BaseFilter"
    """
    The base class for filter algorithms, which should extend this class.

    All of this classes methods must be overridden, except sv_params and the do_before and do_after wrappers
    which are optional.
    """

    @staticmethod
    def filter_func(data: ImageStack) -> ImageStack:
        """
        Executes the filter algorithm on a given set of image data with the given parameters.

        :param data: the image data to apply the filter to
        :param kwargs: any additional arguments which the specific filter uses
        :return: the image data after applying the filter
        """
        raise_not_implemented("filter_func")
        return ImageStack(np.asarray([]))

    @staticmethod
    def execute_wrapper(args) -> partial:
        """
        Should construct a partial call to _filter_func using values taken from the widgets passed to this function
        as kwargs.
        :param kwargs: widgets which contain values required for _filter_func.
        :return: a partial call to _filter_func using parameters taken from the input widgets.
        """
        raise_not_implemented("execute_wrapper")
        return partial(lambda: None)

    @staticmethod
    def register_gui(form: QFormLayout, on_change: Callable, view: BaseMainWindowView) -> dict[str, QWidget]:
        """
        Adds any required input widgets to the given form and returns references to them.

        The return values should be in a dict which can be unpacked as kwargs for a call to
        the operations `execute_wrapper`.

        :param view:
        :param form: the layout to create input widgets in
        :param on_change: the filter view action to be bound to all created inputs
        :return: the widgets bound as kwargs which are needed to call execute_wrapper
        """
        raise_not_implemented("register_gui")
        return {}

    @staticmethod
    def sv_params() -> dict[str, Any]:
        """
        Any parameters required from the StackVisualizer ie. ROI
        :return: a map of parameters names
        """
        return {}

    @staticmethod
    def validate_execute_kwargs(kwargs: dict[str, Any]) -> bool:
        return True

    @staticmethod
    def group_name() -> FilterGroup:
        return FilterGroup.NoGroup

    @staticmethod
    def get_images_from_stack(widget: DatasetSelectorWidgetView, msg: str) -> ImageStack | None:
        stack_uuid = widget.current()
        if stack_uuid is None:
            raise ValueError(f"No stack for {msg}")
        try:
            stack = widget.main_window.get_stack(stack_uuid)
        except KeyError as exc:
            # Can happen if stack is closed while selected in the form
            raise ValueError(f"Selected stack for {msg} does not exist") from exc
        return stack


def raise_not_implemented(function_name):
    raise NotImplementedError(f"Required method '{function_name}' not implemented for filter")
