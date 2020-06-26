from typing import Iterable

from mantidimaging.core.data import Images
from mantidimaging.core.operation_history.operations import ops_to_partials, ImageOperation


class OpHistoryCopyDialogModel:
    def __init__(self, images):
        self.images: Images = images

    def apply_ops(self, ops: Iterable[ImageOperation]):
        to_apply = ops_to_partials(ops)
        for op in to_apply:
            op(self.images)
