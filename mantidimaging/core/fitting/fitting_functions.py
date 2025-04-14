# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from abc import ABC


class BaseFittingFunction(ABC):
    parameter_names: list[str]

    def get_parameter_names(self) -> list[str]:
        return list(self.parameter_names)


class ErfStepFunction(BaseFittingFunction):
    parameter_names = ["mu", "sigma", "h", "a"]
