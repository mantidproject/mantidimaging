# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from abc import ABC, abstractmethod


class BaseFittingFunction(ABC):
    parameter_names: list[str]

    def get_parameter_names(self) -> list[str]:
        return list(self.parameter_names)

    @abstractmethod
    def get_init_params_from_roi(self, region: tuple[float, float, float, float]) -> dict[str, float]:
        ...


class ErfStepFunction(BaseFittingFunction):
    parameter_names = ["mu", "sigma", "h", "a"]

    def get_init_params_from_roi(self, region: tuple[float, float, float, float]) -> dict[str, float]:
        x1, x2, y1, y2 = region
        init_params = {
            "mu": (x1 + x2) / 2,
            "sigma": (x2 - x1) / 4,
            "h": y2 - y1,
            "a": y1,
        }
        return init_params
