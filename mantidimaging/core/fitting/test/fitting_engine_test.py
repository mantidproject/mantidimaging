# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import unittest

import numpy as np

from ..fitting_engine import FittingEngine, BaseFittingFunction, FittingRegionType


class MockFittingFunction(BaseFittingFunction):
    parameter_names = ['a', 'b']

    def get_init_params_from_roi(self, region: FittingRegionType) -> dict[str, float]:
        return {'a': 1, 'b': 2}

    def evaluate(self, xdata: np.ndarray, params: list[float]) -> np.ndarray:
        a, b = params
        return a * xdata + b


class FittingEngineTest(unittest.TestCase):

    def setUp(self):
        self.model = MockFittingFunction()
        self.engine = FittingEngine(self.model)

    def test_get_param_names(self):
        self.assertListEqual(self.engine.get_parameter_names(), ['a', 'b'])

    def test_get_init_params(self):
        init_params = self.engine.get_init_params_from_roi((1, 2, 3, 4))
        self.assertEqual(init_params['a'], 1)
        self.assertEqual(init_params['b'], 2)

    def test_find_best_fit(self):
        xvals = np.linspace(1, 10, 20)
        yvals = 3.1 * xvals + 2.7

        result = self.engine.find_best_fit(xvals, yvals, [1, 1])
        self.assertAlmostEqual(result['a'], 3.1, 4)
        self.assertAlmostEqual(result['b'], 2.7, 4)
