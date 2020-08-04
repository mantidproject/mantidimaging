from mantidimaging.core.data import Images
from mantidimaging.core.operation_history import const


def update_image_operations(images: Images, model):
    """
    TODO: remove this function / integrate in recon GUI
    Updates the image operation history with the results in the given model.
    """
    images.record_operation(const.OPERATION_NAME_COR_TILT_FINDING,
                            display_name="Calculated COR/Tilt",
                            **model.stack_properties)
