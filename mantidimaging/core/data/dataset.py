from dataclasses import dataclass
from typing import Optional

from mantidimaging.core.data import Images


@dataclass
class Dataset:
    sample: Images
    flat_before: Optional[Images] = None
    flat_after: Optional[Images] = None
    dark_before: Optional[Images] = None
    dark_after: Optional[Images] = None
