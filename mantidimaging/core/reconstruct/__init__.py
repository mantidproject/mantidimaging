# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from typing import TYPE_CHECKING

from .astra_recon import AstraRecon
from .tomopy_recon import TomopyRecon
from .cil_recon import CILRecon

if TYPE_CHECKING:
    from .base_recon import BaseRecon


def get_reconstructor_for(algorithm: str) -> BaseRecon:
    if algorithm == "gridrec":
        return TomopyRecon()
    if algorithm.startswith("CIL"):
        return CILRecon()
    else:
        return AstraRecon()
