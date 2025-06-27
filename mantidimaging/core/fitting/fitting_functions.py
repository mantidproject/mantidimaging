# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from abc import ABC, abstractmethod
from math import sqrt
from typing import NamedTuple

import numpy as np
from scipy.optimize import curve_fit
from scipy.special import erf, erfc


class BadFittingRoiError(Exception):

    def __init__(self, message: str = 'A fit could not be found within the given ROI, please try widening the ROI.'):
        self.message = message
        super().__init__(self.message)


class FittingRegion(NamedTuple):
    x_min: float
    x_max: float
    y_min: float
    y_max: float


class BaseFittingFunction(ABC):
    parameter_names: list[str]
    function_name: str

    def get_parameter_names(self) -> list[str]:
        return list(self.parameter_names)

    @abstractmethod
    def get_init_params_from_roi(self, region: FittingRegion) -> dict[str, float]:
        ...

    @abstractmethod
    def evaluate(self, xdata: np.ndarray, params: list[float]) -> np.ndarray:
        ...

    @abstractmethod
    def prefitting(self, xdata: np.ndarray, ydata: np.ndarray, params: list[float]) -> list[float]:
        ...


class ErfStepFunction(BaseFittingFunction):
    parameter_names = ["mu", "sigma", "h", "a"]
    function_name = "Error function"

    def prefitting(self, _, __, ___) -> list[float]:
        return []

    def evaluate(self, xdata: np.ndarray, params: list[float]) -> np.ndarray:
        mu, sigma, h, a = params
        y = h * 0.5 * (1 + erf((xdata - mu) / (sigma * sqrt(2)))) + a
        return y

    def get_init_params_from_roi(self, region: FittingRegion) -> dict[str, float]:
        x1, x2, y1, y2 = region
        init_params = {
            "mu": (x1 + x2) / 2,
            "sigma": (x2 - x1) / 4,
            "h": y2 - y1,
            "a": y1,
        }
        return init_params


class SantistebanFunction(BaseFittingFunction):
    """
    Fitting algorithm for fitting Bragg Edges to the forumulas given by Santisteban:
    https://www.researchgate.net/publication/42793067_Time-of-flight_Neutron_Transmission_Diffraction
    """
    parameter_names = ["t_hkl", "sigma", "tau", "h", "a", "a_0", "b_0", "a_hkl", "b_hkl"]
    function_name = "Santisteban"

    def calculate_line_profile(self, xdata: np.ndarray, params: list[float]) -> np.ndarray:
        t_hkl, sigma, tau, h, a, _, __, ___, ____ = params
        B = 0.5 * (erfc(-(xdata - t_hkl) / (sqrt(2) * sigma)) - np.exp(-((xdata - t_hkl) / tau) +
                                                                       (sigma**2 /
                                                                        (2 * tau**2))) * erfc(-((xdata - t_hkl) /
                                                                                                (sqrt(2) * sigma)) +
                                                                                              (sigma / tau)))
        return B

    def prefitting(self, xdata: np.ndarray, ydata: np.ndarray, params: list[float]) -> list[float]:
        _, __, ___, ____, _____, a_0, b_0, a_hkl, b_hkl = params

        if ydata.shape[0] < 5:
            raise BadFittingRoiError("Fitting region too narrow to find fit")

        right_percentile_mean = int(np.mean(np.argwhere(ydata > np.percentile(ydata, 95))))
        left_percentile_mean = int(np.mean(np.argwhere(ydata < np.percentile(ydata, 5))))

        # ensure there are enough points for fit to run
        right_percentile_mean = min(ydata.shape[0] - 3, right_percentile_mean)
        left_percentile_mean = max(3, left_percentile_mean)

        a_0, b_0 = self.right_side_fitting(xdata[right_percentile_mean:], ydata[right_percentile_mean:])
        a_hkl, b_hkl = self.left_side_fitting(xdata[:left_percentile_mean], ydata[:left_percentile_mean], a_0, b_0)

        if (np.array([a_0, b_0, a_hkl, b_hkl]) == 0).any():
            raise BadFittingRoiError()
        return [a_0, b_0, a_hkl, b_hkl]

    def evaluate(self, xdata: np.ndarray, params: list[float]) -> np.ndarray:
        t_hkl, sigma, tau, h, a, a_0, b_0, a_hkl, b_hkl = params
        B = self.calculate_line_profile(xdata, params)
        if [a_0, b_0, a_hkl, b_hkl] == [0, 0, 0, 0]:
            y = a + (h * B)
        else:
            y = (np.exp(-(a_0 + b_0 * xdata)) * (np.exp(-(a_hkl + b_hkl * xdata)) +
                                                 (1 - np.exp(-(a_hkl + b_hkl * xdata))) * B))
        return y

    def get_init_params_from_roi(self, region: FittingRegion) -> dict[str, float]:
        x1, x2, y1, y2 = region
        init_params = {
            "t_hkl": (x1 + x2) / 2,
            "sigma": (x2 - x1) / 4,
            "tau": (x2 - x1) / 8,
            "h": y2 - y1,
            "a": y1,
            "a_0": 0,
            "b_0": 0,
            "a_hkl": 0,
            "b_hkl": 0
        }
        return init_params

    def right_side_fitting(self, xdata, ydata) -> list[float]:

        def f(t, a_0, b_0):
            return np.exp(-(a_0 + b_0 * t))

        popt, pcov = curve_fit(f, xdata, ydata, [0, 0])
        return popt

    def left_side_fitting(self, xdata, ydata, a_0, b_0) -> list[float]:

        def f(t, a_hkl, b_hkl):
            return np.exp(-(a_0 + b_0 * t)) * np.exp(-(a_hkl + b_hkl * t))

        popt, pcov = curve_fit(f, xdata, ydata, [0, 0])
        return popt
