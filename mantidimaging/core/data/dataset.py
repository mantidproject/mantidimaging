from dataclasses import dataclass
from typing import Optional

from mantidimaging.core.data import Images


@dataclass
class Dataset:
    sample: Images
    flat: Optional[Images] = None
    dark: Optional[Images] = None
