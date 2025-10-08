# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import numpy as np
from scipy.optimize import minimize

from mantidimaging.core.fitting.fitting_functions import BaseFittingFunction, FittingRegion


class FittingEngine:

    def __init__(self, model: BaseFittingFunction) -> None:
        self.model = model

    def set_fitting_model(self, model: BaseFittingFunction) -> None:
        self.model = model

    def get_parameter_names(self) -> list[str]:
        return list(self.model.parameter_names)

    def get_init_params_from_roi(self, region: FittingRegion) -> dict[str, float]:
        return self.model.get_init_params_from_roi(region)

    def find_best_fit(self,
                      xdata: np.ndarray,
                      ydata: np.ndarray,
                      initial_params: list[float],
                      params_bounds: list[tuple[float | None, float | None]] | None = None) -> dict[str, float]:
        additional_params = self.model.prefitting(xdata, ydata, initial_params)
        if additional_params:
            params_to_fit = initial_params[:-len(additional_params)] + additional_params
        else:
            params_to_fit = initial_params

        def f(params_to_fit):
            return ((self.model.evaluate(xdata, params_to_fit) - ydata)**2).sum()

        result = minimize(f, params_to_fit, method="Nelder-Mead", bounds=params_bounds)

        all_param_names = self.model.get_parameter_names()
        all_params = list(result.x)
        return dict(zip(all_param_names, all_params, strict=True))
