from pyqtgraph import GraphicsLayoutWidget, ImageItem, PlotItem

histogram_axes_labels = {'left': 'Frequency', 'bottom': 'Value'}


class FilterPreviews(GraphicsLayoutWidget):
    image_before: ImageItem
    image_after: ImageItem
    histogram_before: PlotItem
    histogram_after: PlotItem

    def __init__(self, parent=None, **kwargs):
        super(FilterPreviews, self).__init__(parent, **kwargs)

        self.addLabel("Image before:")
        self.addLabel("Pixel values before:")
        self.nextRow()

        self.image_before = ImageItem()
        self.image_before_vb = self.addViewBox(invertY=True)
        self.image_before_vb.addItem(self.image_before)
        self.histogram_before = self.addPlot(labels=histogram_axes_labels)

        self.nextRow()
        self.addLabel("Image after:")
        self.addLabel("Pixel values after:")
        self.nextRow()

        self.image_after = ImageItem()
        self.image_after_vb = self.addViewBox(invertY=True)
        self.image_after_vb.addItem(self.image_after)
        self.histogram_after = self.addPlot(labels=histogram_axes_labels)

    def clear_items(self):
        self.image_before.setImage()
        self.image_after.setImage()
        self.histogram_before.clear()
        self.histogram_after.clear()
