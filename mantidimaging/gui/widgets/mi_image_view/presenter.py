from logging import getLogger


class MIImagePresenter:
    def __init__(self, view: 'MiImageView'):
        self.view = view

    def get_roi(self, image,roi_pos, roi_size, ensure_in_image):
        if ensure_in_image:
            # Don't allow negative point coordinates
            if roi_pos.x < 0 or roi_pos.y < 0:
                getLogger(__name__).info("Region of Interest starts outside the picture! Clipping to image bounds")
                roi_pos.x = max(roi_pos.x, 0)
                roi_pos.y = max(roi_pos.y, 0)

            if image.ndim == 2:
                image_height = image.shape[0]
                image_width = image.shape[1]
            else:
                image_height = image.shape[1]
                image_width = image.shape[2]

            roi_right = roi_pos.x + roi_size.x
            roi_bottom = roi_pos.y + roi_size.y

            if roi_right > image_width:
                roi_size.x -= roi_right - image_width
            if roi_bottom > image_height:
                roi_size.y -= roi_bottom - image_height
        return roi_pos, roi_size
