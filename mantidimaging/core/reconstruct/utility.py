from mantidimaging.core.data import const


def get_roi_left_shift(images):
    if const.OPERATION_HISTORY not in images.properties:
        return 0

    history = images.properties[const.OPERATION_HISTORY]
    rois = [e['kwargs']['region_of_interest'] for e in history
            if 'crop_coords' in e['name']]

    roi_offset = 0
    for r in rois:
        roi_offset += r[0]

    return roi_offset


def get_cor_tilt_from_images(images):
    if not images or const.AUTO_COR_TILT not in images.properties:
        return (0, 0.0, 0.0)

    auto_cor_tilt = images.properties[const.AUTO_COR_TILT]

    cor = auto_cor_tilt['rotation_centre']
    tilt = auto_cor_tilt['tilt_angle_rad']
    m = auto_cor_tilt['fitted_gradient']

    cor -= get_roi_left_shift(images)

    return (cor, tilt, m)
