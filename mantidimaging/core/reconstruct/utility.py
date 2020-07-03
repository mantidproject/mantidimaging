from logging import getLogger
from typing import Optional, Tuple, Dict, Any

from mantidimaging.core.data import Images
from mantidimaging.core.operation_history import const

LOG = getLogger(__name__)


def get_last_cor_tilt_find(images: Images) -> Tuple[Optional[Dict[str, Any]], Optional[int]]:
    """
    Gets the properties from the last instance of COR/Tilt finding that was run
    on a given image stack.
    """
    if not images.has_history:
        return None, None

    # Copy the history and reverse it
    history = images.metadata[const.OPERATION_HISTORY][:]
    history.reverse()

    # Iterate over history and find the first instance of COR/Tilt finding
    # (which is the last given that the history was reversed)
    for i, e in enumerate(history):
        if const.OPERATION_NAME_COR_TILT_FINDING in e[const.OPERATION_NAME]:
            return e[const.OPERATION_KEYWORD_ARGS], len(history) - 1 - i

    return None, None


def get_crop_operations(images: Images, start=None, end=None):
    """
    Gets a list of crop operations that happened between two points in the
    image operation history.
    """
    if not images.has_history:
        return []

    history = images.metadata[const.OPERATION_HISTORY][start:end]
    crops = [e for e in history if const.OPERATION_NAME_CROP in e[const.OPERATION_NAME]]
    return crops


def get_crop(images, axis, start=None, end=None):
    """
    Gets a sum along a given axis of all crop operations that happened between
    two points in the image operation history.
    """
    total_crop = 0.0
    for crop in get_crop_operations(images, start, end):
        total_crop += crop[const.OPERATION_KEYWORD_ARGS][const.CROP_REGION_OF_INTEREST][axis]
    return total_crop


def get_cor_tilt_from_images(images: Images) -> Tuple[int, float, float]:
    """
    Gets rotation centre at top of image and gradient with which to calculate
    rotation centre arrays for reconstruction.
    """
    # If there is no stack history
    if not images or not images.has_history:
        return 0, 0.0, 0.0

    last_find, last_find_idx = get_last_cor_tilt_find(images)
    # If the stack history does not contain a COR/Tilt finding step
    if not last_find:
        return 0, 0.0, 0.0

    cor = last_find[const.COR_TILT_ROTATION_CENTRE]
    tilt = last_find[const.COR_TILT_TILT_ANGLE_DEG]
    gradient = last_find[const.COR_TILT_FITTED_GRADIENT]

    cor -= get_crop(images, 0, start=last_find_idx)

    # Get total offset from linear regression origin from total crop length on
    # top edge
    top = get_crop(images, 1, start=last_find_idx)
    LOG.debug('Total top crop: {}'.format(top))

    # Calculate new rotation centre at new top of image
    new_cor = (top * gradient) + cor
    LOG.debug('New COR corrected for top crop: {}'.format(new_cor))

    return new_cor, tilt, gradient
