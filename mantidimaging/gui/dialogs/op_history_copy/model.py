from typing import Iterable

from mantidimaging.core.data import Images
from mantidimaging.core.operation_history.operations import ops_to_partials, ImageOperation


class OpHistoryCopyDialogModel:
    def __init__(self, images):
        self.images: Images = images

    def apply_ops(self, ops: Iterable[ImageOperation], indices_to_apply: Iterable[bool]):
        # TODO: Preserve + append stack history - here and/or presenter?
        selected_ops = (op for op, i in zip(ops, indices_to_apply) if i)
        to_apply = ops_to_partials(selected_ops)
        image = self.images.sample
        for op in to_apply:
            image = op(image)
        return image
