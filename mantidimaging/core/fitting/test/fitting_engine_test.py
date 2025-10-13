# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import unittest

import numpy as np

from ..fitting_engine import FittingEngine, BaseFittingFunction, FittingRegion


class MockFittingFunction(BaseFittingFunction):
    parameter_names = ['a', 'b']

    def get_init_params_from_roi(self, region: FittingRegion) -> dict[str, float]:
        return {'a': 1, 'b': 2}

    def evaluate(self, xdata: np.ndarray, params: list[float]) -> np.ndarray:
        a, b = params
        return a * xdata + b

    def prefitting(self, xdata: np.ndarray, ydata: np.ndarray, params: list[float]) -> list[float]:
        return []


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

    def test_find_best_fit_with_fixed_bounds(self):
        xvals = np.linspace(1, 10, 20)
        yvals = 3.1 * xvals + 2.7
        bounds = [(0.8, 0.8), (0.99, 0.99)]

        result = self.engine.find_best_fit(xvals, yvals, [1, 1], params_bounds=bounds)
        self.assertEqual(result['a'], bounds[0][0])
        self.assertEqual(result['b'], bounds[1][0])

    def test_find_best_fit_with_range_bounds(self):
        xvals = np.linspace(1, 10, 20)
        yvals = 3.1 * xvals + 2.7
        bounds = [(0.8, 0.85), (0.9, 0.99)]

        result = self.engine.find_best_fit(xvals, yvals, [1, 1], params_bounds=bounds)
        self.assertTrue(bounds[0][0] <= result['a'] <= bounds[0][1])
        self.assertTrue(bounds[1][0] <= result['b'] <= bounds[1][1])
