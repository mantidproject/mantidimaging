from pyqtgraph import ImageItem


class MantidImageItem(ImageItem):
    def __init__(self, image=None, **kwargs):
        super().__init__(image, **kwargs)

    def mouseMoveEvent(self, event):
        print(event)
