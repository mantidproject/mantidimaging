# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import numpy as np
from scipy.optimize import minimize

from mantidimaging.core.fitting.fitting_functions import BaseFittingFunction, FittingRegion
from mantidimaging.gui.widgets.spectrum_widgets.fitting_param_form_widget import BoundType


class FittingEngine:

    def __init__(self, model: BaseFittingFunction) -> None:
        self.model = model

    def set_fitting_model(self, model: BaseFittingFunction) -> None:
        self.model = model

    def get_parameter_names(self) -> list[str]:
        return list(self.model.parameter_names)

    def get_init_params_from_roi(self, region: FittingRegion) -> dict[str, float]:
        return self.model.get_init_params_from_roi(region)

    def find_best_fit(
        self,
        xdata: np.ndarray,
        ydata: np.ndarray,
        initial_params: list[float],
        params_bounds: list[BoundType] | None = None,
    ) -> tuple[dict[str, float], float, float]:
        """
        Fit the model to the given spectrum using unweighted least squares.

        Returns:
            - fit_params: dictionary of parameter names → fitted values
            - rss: residual sum of squares (Σ(residual²))
            - reduced_rss: rss / degrees of freedom, where DoF = N - p

        Notes:
            Uses the Nelder–Mead minimizer on the unweighted residuals.
        """

        additional_params = self.model.prefitting(xdata, ydata, initial_params)

        if additional_params:
            params_to_fit = initial_params[:-len(additional_params)] + additional_params
        else:
            params_to_fit = initial_params

        def residual_sum_squares(params_subset):
            residuals = self.model.evaluate(xdata, params_subset) - ydata
            return np.sum(residuals**2)

        result = minimize(residual_sum_squares, params_to_fit, method="Nelder-Mead", bounds=params_bounds)

        all_param_names = self.model.get_parameter_names()
        all_params = list(result.x)
        fit_params = dict(zip(all_param_names, all_params, strict=True))

        rss = float(result.fun)
        n_points = ydata.size
        dof = max(n_points - len(all_params), 1)
        reduced_rss = rss / dof

        return fit_params, rss, reduced_rss
