from mantidimaging.core.data import Images
from mantidimaging.core.operation_history import const

from .auto import auto_find_cors


def run_auto_finding_on_images(images: Images, model, roi, projections=None, cores=None, progress=None):
    """
    Performs automatic COR/Tilt finding on an image stack.
    """
    auto_find_cors(images.sample, roi, model, projections, cores, progress)
    model.linear_regression()
    update_image_operations(images, model)


def update_image_operations(images: Images, model):
    """
    Updates the image operation history with the results in the given model.
    """
    images.record_operation(
        const.OPERATION_NAME_COR_TILT_FINDING,
        **model.stack_properties)
