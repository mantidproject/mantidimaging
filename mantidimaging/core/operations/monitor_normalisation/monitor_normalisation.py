# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from functools import partial
from typing import Callable, Dict, Any

import numpy as np
from PyQt5.QtWidgets import QFormLayout, QWidget

from mantidimaging.core.data import Images
from mantidimaging.core.operations.base_filter import BaseFilter
from mantidimaging.core.parallel import shared as ps
from mantidimaging.gui.mvp_base import BaseMainWindowView


def _divide_by_counts(data=None, counts=None):
    data[:] = np.true_divide(data, counts)


class MonitorNormalisation(BaseFilter):
    """Normalises the values of the data by the monitor counts read from the Sample log file.

    Intended to be used on: Projections

    When: As a pre-processing step to normalise the value ranges of the data.
    """
    filter_name = "Monitor Normalisation"

    @staticmethod
    def filter_func(images: Images, cores=None, chunksize=None, progress=None) -> Images:
        if images.num_projections == 1:
            # we can't really compute the preview as the image stack copy
            # passed in doesn't have the logfile in it
            return images
        counts = images.counts()

        if counts is None:
            raise RuntimeError("No loaded log values for this stack.")

        counts_val = counts.value / counts.value[0]
        do_division = ps.create_partial(_divide_by_counts, fwd_function=ps.inplace2)
        ps.shared_list = [images.data, counts_val]
        ps.execute(do_division, images.num_projections, progress, cores=cores)
        return images

    @staticmethod
    def register_gui(form: 'QFormLayout', on_change: Callable, view: 'BaseMainWindowView') -> Dict[str, 'QWidget']:
        return {}

    @staticmethod
    def execute_wrapper(*args) -> partial:
        return partial(MonitorNormalisation.filter_func)

    @staticmethod
    def validate_execute_kwargs(kwargs: Dict[str, Any]) -> bool:
        return True
