# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import numpy as np
from scipy.optimize import minimize

from mantidimaging.core.fitting.fitting_functions import BaseFittingFunction, FittingRegion


class FittingEngine:

    def __init__(self, model: BaseFittingFunction):
        self.model = model

    def get_parameter_names(self) -> list[str]:
        return list(self.model.parameter_names)

    def get_init_params_from_roi(self, region: FittingRegion) -> dict[str, float]:
        return self.model.get_init_params_from_roi(region)

    def find_best_fit(self, xdata: np.ndarray, ydata: np.ndarray, initial_params: list[float]) -> dict[str, float]:

        def f(params):
            return ((self.model.evaluate(xdata, params) - ydata)**2).sum()

        result = minimize(f, initial_params, method="Nelder-Mead")
        return dict(zip(self.model.get_parameter_names(), result.x, strict=True))
