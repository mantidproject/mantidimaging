# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from .astra_recon import AstraRecon
from .tomopy_recon import TomopyRecon
from .cil_recon import CILRecon
from .base_recon import BaseRecon


def get_reconstructor_for(algorithm: str) -> BaseRecon:
    if algorithm == "gridrec":
        return TomopyRecon()
    if algorithm.startswith("CIL"):
        return CILRecon()
    else:
        return AstraRecon()
