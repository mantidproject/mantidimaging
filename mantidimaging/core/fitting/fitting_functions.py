# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from abc import ABC, abstractmethod
from math import sqrt
from typing import NamedTuple

import numpy as np
from scipy.optimize import curve_fit
from scipy.special import erf, erfc


class FittingRegion(NamedTuple):
    x_min: float
    x_max: float
    y_min: float
    y_max: float


class BaseFittingFunction(ABC):
    parameter_names: list[str]
    additional_parameter_names: list[str]
    additional_params: list[float]
    function_name: str

    def get_parameter_names(self) -> list[str]:
        return list(self.parameter_names)

    def get_additional_parameter_names(self) -> list[str]:
        return list(self.additional_parameter_names)

    @abstractmethod
    def get_additional_params(self) -> dict[str, float]:
        ...

    @abstractmethod
    def get_init_params_from_roi(self, region: FittingRegion) -> dict[str, float]:
        ...

    @abstractmethod
    def evaluate(self, xdata: np.ndarray, params: list[float]) -> np.ndarray:
        ...

    @abstractmethod
    def fitting_setup(self, xdata: np.ndarray, ydata: np.ndarray, params: list[float]) -> None:
        ...

    @abstractmethod
    def fitting_setup_reset(self) -> None:
        ...


class ErfStepFunction(BaseFittingFunction):
    parameter_names = ["mu", "sigma", "h", "a"]
    function_name = "Error function"
    additional_params = []
    additional_parameter_names = []

    def fitting_setup(self, _, __, ___) -> None:
        return

    def fitting_setup_reset(self) -> None:
        return

    def get_additional_params(self) -> dict[str, float]:
        return {}

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
    parameter_names = ["t_hkl", "sigma", "tau", "h", "a"]
    additional_parameter_names = ["a_0", "b_0", "a_hkl", "b_hkl"]
    function_name = "Santisteban"
    additional_params = [0, 0, 0, 0]
    x_B_eq_zero_tolerance = 1.1
    x_B_eq_one_tolerance = 0.9

    def calculate_line_profile(self, xdata: np.ndarray, params: list[float]) -> np.ndarray:
        t_hkl, sigma, tau, h, a = params
        B = 0.5 * (erfc(-(xdata - t_hkl) / (sqrt(2) * sigma)) - np.exp(-((xdata - t_hkl) / tau) +
                                                                       (sigma**2 /
                                                                        (2 * tau**2))) * erfc(-((xdata - t_hkl) /
                                                                                                (sqrt(2) * sigma)) +
                                                                                              (sigma / tau)))
        return B

    def fitting_setup(self, xdata: np.ndarray, ydata: np.ndarray, params: list[float]) -> None:
        B = self.calculate_line_profile(xdata, params)

        x_B_eq_zero_ind = np.argwhere(B <= self.x_B_eq_zero_tolerance * np.min(B))[-1][0]
        x_B_eq_one_ind = np.argwhere(B >= self.x_B_eq_one_tolerance * np.max(B))[0][0]

        try:
            a_0, b_0 = self.right_side_fitting(xdata[x_B_eq_one_ind:], ydata[x_B_eq_one_ind:])
            a_hkl, b_hkl = self.left_side_fitting(xdata[:x_B_eq_zero_ind], ydata[:x_B_eq_zero_ind], a_0, b_0)
            self.additional_params = [a_0, b_0, a_hkl, b_hkl]
        except TypeError:
            self.x_B_eq_one_tolerance -= 0.1
            self.x_B_eq_zero_tolerance += 0.1
            self.fitting_setup(xdata, ydata, params)

    def fitting_setup_reset(self) -> None:
        self.additional_params = [0, 0, 0, 0]

    def evaluate(self, xdata: np.ndarray, params: list[float]) -> np.ndarray:
        t_hkl, sigma, tau, h, a = params
        a_0, b_0, a_hkl, b_hkl = self.additional_params
        B = self.calculate_line_profile(xdata, params)
        if self.additional_params == [0, 0, 0, 0]:
            y = h + (a * B)
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
        }
        return init_params

    def get_additional_params(self) -> dict[str, float]:
        add_params = {
            "a_0": self.additional_params[0],
            "b_0": self.additional_params[1],
            "a_hkl": self.additional_params[2],
            "b_hkl": self.additional_params[3]
        }
        return add_params

    def right_side_fitting(self, xdata, ydata):

        def f(t, a_0, b_0):
            return np.exp(-(a_0 + b_0 * t))

        popt, pcov = curve_fit(f, xdata, ydata)
        return popt

    def left_side_fitting(self, xdata, ydata, a_0, b_0):

        def f(t, a_hkl, b_hkl):
            return np.exp(-(a_0 + b_0 * t)) * np.exp(-(a_hkl + b_hkl * t))

        popt, pcov = curve_fit(f, xdata, ydata)
        return popt
