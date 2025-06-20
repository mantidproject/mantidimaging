# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from abc import ABC, abstractmethod
from math import sqrt
from typing import NamedTuple

import numpy as np
from scipy.optimize import curve_fit
from scipy.special import erf, erfc


class LeftSideFittingException(Exception):

    def __init__(self, source_err):
        print("LeftSideFittingException:", source_err)


class RightSideFittingException(Exception):

    def __init__(self, source_err):
        print("RightSideFittingException:", source_err)


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

        ydata_max_ind = np.argmax(ydata)
        ydata_min_ind = np.argmin(ydata)

        if ydata_max_ind == len(xdata) or ydata_min_ind == 0:
            raise BadFittingRoiError()

        percentile_right = np.percentile(ydata, 95)
        p_r = np.argwhere(ydata < percentile_right)
        percentile_right_threshold = np.extract(p_r > ydata_max_ind, p_r)
        if percentile_right_threshold.size == 0:
            raise BadFittingRoiError()
        percentile_right_ind = percentile_right_threshold[0]

        percentile_left = np.percentile(ydata[:ydata_min_ind], 10)
        p_l = np.argwhere(ydata > percentile_left)
        percentile_left_threshold = np.extract(p_l < ydata_min_ind, p_l)
        if percentile_left_threshold.size == 0:
            raise BadFittingRoiError()
        percentile_left_ind = percentile_left_threshold[-1]

        try:
            a_0, b_0 = self.right_side_fitting(xdata[percentile_right_ind:], ydata[percentile_right_ind:])
            a_hkl, b_hkl = self.left_side_fitting(xdata[:percentile_left_ind], ydata[:percentile_left_ind], a_0, b_0)
        except LeftSideFittingException:
            raise BadFittingRoiError(message='A fit could not be found for the left side of the Bragg Edge, '
                                     'please adjust the ROI on the left.') from None
        except RightSideFittingException:
            raise BadFittingRoiError(message='A fit could not be found for the right side of the Bragg Edge, '
                                     'please adjust the ROI on the right.') from None

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

        try:
            popt, pcov = curve_fit(f, xdata, ydata, [0, 0])
            return popt
        except (TypeError, ValueError) as err:
            raise RightSideFittingException(err) from err

    def left_side_fitting(self, xdata, ydata, a_0, b_0) -> list[float]:

        def f(t, a_hkl, b_hkl):
            return np.exp(-(a_0 + b_0 * t)) * np.exp(-(a_hkl + b_hkl * t))

        try:
            popt, pcov = curve_fit(f, xdata, ydata, [0, 0])
            return popt
        except (TypeError, ValueError) as err:
            raise LeftSideFittingException(err) from err
