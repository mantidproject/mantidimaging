# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import inspect
import unittest

import numpy as np
from parameterized import parameterized

from mantidimaging.core.fitting import fitting_functions
from mantidimaging.core.fitting.fitting_functions import FittingRegion

# Collect all fitting functions from module
FUNCTIONS = [(name, obj) for name, obj in inspect.getmembers(fitting_functions)
             if inspect.isclass(obj) and issubclass(obj, fitting_functions.BaseFittingFunction)
             and obj is not fitting_functions.BaseFittingFunction]


class TestFittingFunction(unittest.TestCase):

    @parameterized.expand(FUNCTIONS)
    def test_has_string_param_names(self, _, fit_class: type[fitting_functions.BaseFittingFunction]):
        fit_func = fit_class()
        param_names = fit_func.get_parameter_names()
        for param_name in param_names:
            self.assertIsInstance(param_name, str)

    @parameterized.expand(FUNCTIONS)
    def test_evaluate_function(self, _, fit_class: type[fitting_functions.BaseFittingFunction]):
        fit_func = fit_class()
        param_names = fit_func.get_parameter_names()
        param_values = [1.0 for _ in param_names]
        xvals = np.linspace(0, 1, 10)

        yvals = fit_func.evaluate(xvals, param_values)
        self.assertEqual(xvals.shape, yvals.shape)

    @parameterized.expand(FUNCTIONS)
    def test_get_init_params(self, _, fit_class: type[fitting_functions.BaseFittingFunction]):
        fit_func = fit_class()
        param_names = fit_func.get_parameter_names()
        init_params = fit_func.get_init_params_from_roi(FittingRegion(1, 2, 3, 4))

        self.assertEqual(len(param_names), len(init_params))
        for param_name in param_names:
            self.assertIn(param_name, init_params)
