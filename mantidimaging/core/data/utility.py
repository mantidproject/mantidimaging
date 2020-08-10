from typing import TYPE_CHECKING

from mantidimaging.core.utility.sensible_roi import SensibleROI

if TYPE_CHECKING:
    from mantidimaging.core.data import Images


def mark_cropped(images: 'Images', roi: SensibleROI):
    # avoids circular import error
    from mantidimaging.core.filters.crop_coords import CropCoordinatesFilter
    # not ideal.. but it will allow to replicate the result accurately
    images.record_operation(CropCoordinatesFilter.__name__, CropCoordinatesFilter.filter_name, region_of_interest=roi)
