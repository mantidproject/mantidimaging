from PyQt5 import Qt

from mantidimaging.gui.utility import (BlockQtSignals, compile_ui)


class ImageSelectorWidget(Qt.QWidget):

    def __init__(self, parent, stack_view):
        super(ImageSelectorWidget, self).__init__(parent)
        compile_ui('gui/ui/image_selector_widget.ui', self)

        self.stack_view = stack_view

        self.imageIndex.valueChanged[int].connect(self.on_user_changes_image)

    @property
    def max_index(self):
        return self.imageIndex.maximum()

    @max_index.setter
    def max_index(self, idx):
        with BlockQtSignals([self.imageIndex]):
            self.imageIndex.setValue(0)
            self.imageIndex.setMaximum(idx)

    @property
    def index(self):
        return self.imageIndex.value()

    @index.setter
    def index(self, idx):
        with BlockQtSignals([self.imageIndex]):
            self.imageIndex.setValue(idx)

    def on_user_changes_image(self, idx):
        self.stack_view.presenter.current_image_index = idx
