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

    def find_best_fit(self, xdata: np.ndarray, ydata: np.ndarray,
                      initial_params: list[float]) -> tuple[dict[str, float], float]:
        """
        Perform a model fit and return the fitted parameters and chi-squared value.

        :param xdata: TOF data (independent variable)
        :param ydata: Spectrum data (dependent variable)
        :param initial_params: Initial parameter estimates
        :return: (fit_params, chi_squared)
        """
        additional_params: list[float] = self.model.prefitting(xdata, ydata, initial_params)
        fit_param_count = len(initial_params) - len(additional_params)
        params_to_fit: np.ndarray = np.array(initial_params[:fit_param_count])

        def chi_squared(params_subset: list[float]) -> float:
            full_params = list(params_subset) + additional_params
            residuals = self.model.evaluate(xdata, full_params) - ydata
            return float(np.sum(residuals**2))

        result = minimize(chi_squared, params_to_fit, method="Nelder-Mead")
        all_param_names = self.model.get_parameter_names()
        all_params: list[float] = list(result.x) + additional_params
        fit_params: dict[str, float] = dict(zip(all_param_names, all_params, strict=True))
        final_residuals = self.model.evaluate(xdata, all_params) - ydata
        chi2: float = float(np.sum(final_residuals**2))
        return fit_params, chi2
