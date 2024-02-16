# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from typing import Dict, List, TYPE_CHECKING
import unittest
from unittest import mock

import numpy

from mantidimaging.core.operations.loader import load_filter_packages
import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.core.utility.data_containers import Counts
from mantidimaging.core.gpu import utility as gpu

if TYPE_CHECKING:
    from mantidimaging.core.operations.loader import BaseFilterClass

GPU_NOT_AVAIL = not gpu.gpu_available()


def get_filter_func_args():
    filter_func_args = {
        "Clip Values": {"clip_min": 0.1, "clip_max": 0.5},
        "Crop Coordinates": {"region_of_interest": [0, 0, 5, 5]},
        "Divide": {"value": 2},
        "Flat-fielding": {"flat_before": th.generate_images(), "dark_before": th.generate_images(),
                          "selected_flat_fielding": "Only Before", "use_dark": False},
        "Gaussian": {"size": 2.0, "order": 1, "mode": "nearest"},
        "Median": {"size": 3, "mode": "nearest", "force_cpu": GPU_NOT_AVAIL},
        "Remove Outliers": {"diff": 0.1},
        "Rebin": {"mode": "constant"},
        "Remove all stripes": {"sm_size": 25},
        "Ring Removal": {"theta_min": 2},
        "ROI Normalisation": {"region_of_interest": [0, 0, 5, 5]},
        "Rotate Stack": {"angle": 10}
    }  # yapf: disable
    return filter_func_args


class OperationsTest(unittest.TestCase):
    filters: List[BaseFilterClass]
    filter_args: Dict

    @classmethod
    def setUpClass(cls) -> None:
        cls.filters = load_filter_packages()
        cls.filter_args = get_filter_func_args()

    def test_load_filters(self):
        self.assertGreater(len(self.filters), 10)

    def test_operation_works_inplace(self):
        for filter in self.filters:
            filter_name = filter.filter_name
            filter_args = self.filter_args.get(filter_name, {})

            images = th.generate_images()
            if filter_name == "Monitor Normalisation":
                counts = Counts(numpy.ones(images.num_images))
                images._log_file = mock.Mock(counts=lambda counts=counts: counts)

            returned = filter.filter_func(images, **filter_args)
            self.assertEqual(id(images), id(returned))
