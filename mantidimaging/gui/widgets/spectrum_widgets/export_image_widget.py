from PyQt5.QtWidgets import QWidget, QVBoxLayout
from pyqtgraph import ImageView, ROI, mkPen
import numpy as np

class ExportImageViewWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.image_view = ImageView(self)
        layout.addWidget(self.image_view)

        self.roi_overlays = []

    def update_image(self, image: np.ndarray):
        """Set image to display."""
        self.image_view.setImage(image, autoLevels=True)
        self.clear_rois()

    def add_roi_overlay(self, roi_data):
        """Draw ROI rectangle on top of the image."""
        roi = ROI(pos=(roi_data.x, roi_data.y), size=(roi_data.width, roi_data.height), pen=mkPen((0,255,0), width=2))
        self.image_view.addItem(roi)
        self.roi_overlays.append(roi)

    def clear_rois(self):
        for roi in self.roi_overlays:
            self.image_view.removeItem(roi)
        self.roi_overlays.clear()
