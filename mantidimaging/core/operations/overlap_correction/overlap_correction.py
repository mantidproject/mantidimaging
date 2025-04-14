# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
from dataclasses import dataclass

from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, Any
from collections.abc import Callable

import numpy
import numpy as np

from mantidimaging.core.operations.base_filter import BaseFilter
from mantidimaging.core.parallel import utility as pu, shared as ps

if TYPE_CHECKING:
    from mantidimaging.core.data import ImageStack
    from mantidimaging.gui.mvp_base import BaseMainWindowView
    from PyQt5.QtWidgets import QFormLayout, QWidget


class OverlapCorrection(BaseFilter):
    """
    Overlap correction is a post-experimental data correction performed when the input fluxes are periodic,
    accurately restoring the input flux up to a very large fraction of pixels (up to ~90%) occupied by the end of the
    acquisition shutter which leads to large distortions of measured timing characteristics of the input flux.

    Intended to be used on: Projections

    When: As a pre-processing step, to correct the observed spectrum and clarify its characteristics.
    """
    filter_name = "Overlap Correction"
    link_histograms = True
    allow_for_180_projection = False

    @staticmethod
    def filter_func(images: ImageStack, progress=None) -> ImageStack:
        """
        :return: The ImageStack object which has been corrected using the supplied shutter information.
        """
        if images.shutter_count_file:
            shutters_dir = images.shutter_count_file.source_file.parent
            shutter_breaks = OverlapCorrection.get_shutters_breaks(shutters_dir)
        else:
            raise RuntimeError("No loaded Shutter Count file for this stack.")

        params = {'shutter_breaks': shutter_breaks}
        output = pu.create_array(images.data.shape, images.dtype)
        ps.run_compute_func(OverlapCorrection._compute_overlap_correction, images.data.shape[0],
                            [images.shared_array, output], params, progress)
        images.shared_array = output
        return images

    @staticmethod
    def _compute_overlap_correction(i: int, arrays: list[np.ndarray], params: dict[str, np.ndarray]):
        array = arrays[0]
        output = arrays[1]
        for sb in params['shutter_breaks']:
            if i == sb[0] or i == sb[1]:
                output[i] = array[i]
            elif sb[0] < i < sb[1]:
                ss = sb[0]
                counts = sb[2]
                prob_occupied = numpy.sum(array[ss:i], axis=0) / counts
                output[i] = array[i] / (1 - prob_occupied)

    @staticmethod
    def register_gui(form: QFormLayout, on_change: Callable, view: BaseMainWindowView) -> dict[str, QWidget]:
        return {}

    @staticmethod
    def execute_wrapper(*args) -> partial:
        return partial(OverlapCorrection.filter_func)

    @staticmethod
    def validate_execute_kwargs(kwargs: dict[str, Any]) -> bool:
        return True

    @staticmethod
    def get_shutters_breaks(data_dir: Path) -> list[tuple]:
        shuter_count_file = sorted(data_dir.glob("*ShutterCount.txt"))[0]
        shutter_times_file = sorted(data_dir.glob("*ShutterTimes.txt"))[0]
        spectra_file = sorted(data_dir.glob("*Spectra.txt"))[0]

        shuter_count = numpy.loadtxt(shuter_count_file, dtype=int)
        shutter_times = numpy.loadtxt(shutter_times_file)
        spectra = numpy.loadtxt(spectra_file)

        @dataclass
        class ShutterInfo:
            number: int
            count: int
            start_time: float = 0
            end_time: float = 0
            start_index: int = 0
            end_index: int = 0

        shutter_breaks = []
        prev_time = 0.0
        for number, count in shuter_count:
            if count == 0:
                break

            this_shutter = ShutterInfo(number, count)
            delay = shutter_times[number, 1]
            duration = shutter_times[number, 2]

            this_shutter.start_time = prev_time + delay
            this_shutter.end_time = this_shutter.start_time + duration
            prev_time = this_shutter.end_time
            this_shutter.start_index = int(numpy.searchsorted(spectra[:, 0], this_shutter.start_time))
            this_shutter.end_index = int(numpy.searchsorted(spectra[:, 0], this_shutter.end_time))
            shutter_breaks.append((this_shutter.start_index, this_shutter.end_index, this_shutter.count))
            print(this_shutter)

        return shutter_breaks
