# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from typing import Union

from .astra_recon import AstraRecon
from .tomopy_recon import TomopyRecon


def get_reconstructor_for(algorithm: str) -> Union[AstraRecon, TomopyRecon]:
    if algorithm == "gridrec":
        return TomopyRecon()
    else:
        return AstraRecon()
