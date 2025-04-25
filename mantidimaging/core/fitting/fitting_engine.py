# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from typing_extensions import TYPE_CHECKING

from mantidimaging.core.fitting.fitting_functions import BaseFittingFunction

if TYPE_CHECKING:
    from mantidimaging.core.utility.sensible_roi import SensibleROI


class FittingEngine:

    def __init__(self, model: BaseFittingFunction):
        self.model = model

    def get_parameter_names(self) -> list[str]:
        return list(self.model.parameter_names)

    def get_init_params_from_roi(self, roi: SensibleROI) -> dict[str, float]:
        return {"mu": 2}
