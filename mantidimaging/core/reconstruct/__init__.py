from typing import Union

from .astra_recon import AstraRecon
from .tomopy_recon import TomopyRecon


def get_reconstructor_for(algorithm: str) -> Union[AstraRecon, TomopyRecon]:
    if algorithm == "gridrec":
        return TomopyRecon()
    else:
        return AstraRecon()
