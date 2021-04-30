# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from functools import partial
from typing import Callable, Dict

from PyQt5.QtWidgets import QFormLayout

from mantidimaging.core.data import Images
from mantidimaging.core.operations.base_filter import BaseFilter


class ArithmeticFilter(BaseFilter):

    filter_name = "Arithmetic"
    link_histograms = True

    @staticmethod
    def filter_func(data: Images, mult_val: float, add_val: float) -> Images:
        pass

    @staticmethod
    def register_gui(form: 'QFormLayout', on_change: Callable, view: 'BaseMainWindowView') -> Dict[str, 'QWidget']:
        pass

    @staticmethod
    def execute_wrapper(args) -> partial:
        pass