# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from abc import ABC, abstractmethod
from math import sqrt
from typing import NamedTuple

import numpy as np
from scipy.special import erf


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
    parameter_names = ["t_hkl", "sigma", "tau"]
    function_name = "Santisteban"

    def evaluate(self, xdata: np.ndarray, params: list[float]) -> np.ndarray:
        t_hkl, sigma, tau = params
        y = xdata
        return y

    def get_init_params_from_roi(self, region: FittingRegion) -> dict[str, float]:
        x1, x2, y1, y2 = region
        init_params = {
            "t_hkl": 0.00,
            "sigma": 0.00,
            "tau": 0.00,
        }
        return init_params
