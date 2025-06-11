# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from abc import ABC, abstractmethod
from math import sqrt
from typing import NamedTuple

import numpy as np
from scipy.special import erf, erfc


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


class ErfStepFunction(BaseFittingFunction):
    parameter_names = ["mu", "sigma", "h", "a"]
    function_name = "Error function"

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
    function_name = "Santisteban"

    def calculate_line_profile(self, xdata: np.ndarray, params: list[float]) -> np.ndarray:
        t_hkl, sigma, tau, h, a = params
        B = 0.5 * (erfc(-(xdata - t_hkl) / (sqrt(2) * sigma)) - np.exp(-((xdata - t_hkl) / tau) + (sigma ** 2 / (2 * tau ** 2))) * erfc(-((xdata - t_hkl) / (sqrt(2) * sigma)) + (sigma / tau)))
        return B

    def evaluate(self, xdata: np.ndarray, params: list[float]) -> np.ndarray:
        t_hkl, sigma, tau, h, a = params
        B = self.calculate_line_profile(xdata, params)
        y = h + (a * B)
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
