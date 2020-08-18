from typing import Optional, Tuple

from PyQt5 import Qt
from PyQt5.QtWidgets import QComboBox, QCheckBox, QTreeWidget, QTreeWidgetItem, QPushButton, QSizePolicy, \
    QHeaderView, QDoubleSpinBox

from mantidimaging.core.utility.data_containers import LoadingParameters
from mantidimaging.gui.utility import (compile_ui)
from mantidimaging.gui.windows.main.load_dialog.field import Field
from mantidimaging.gui.windows.main.load_dialog.presenter import LoadPresenter, Notification


class MWLoadDialog(Qt.QDialog):
    tree: QTreeWidget
    pixel_bit_depth: QComboBox
    images_are_sinograms: QCheckBox

    pixelSize: QDoubleSpinBox

    step_preview: QPushButton
    step_all: QPushButton

    _sample_path: Optional[QTreeWidgetItem] = None
    _flat_path: Optional[QTreeWidgetItem] = None
    _dark_path: Optional[QTreeWidgetItem] = None
    _proj_180deg_path: Optional[QTreeWidgetItem] = None
    _sample_log_path: Optional[QTreeWidgetItem] = None
    _flat_log_path: Optional[QTreeWidgetItem] = None

    def __init__(self, parent):
        super(MWLoadDialog, self).__init__(parent)
        compile_ui('gui/ui/load_dialog.ui', self)

        self.parent_view = parent
        self.presenter = LoadPresenter(self)

        self.tree.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.tree.header().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tree.header().setStretchLastSection(False)
        self.tree.setTabKeyNavigation(True)

        self.sample, self.select_sample = self.create_file_input(0)
        self.select_sample.clicked.connect(lambda: self.presenter.notify(Notification.UPDATE_ALL_FIELDS))

        self.flat, self.select_flat = self.create_file_input(1)
        self.select_flat.clicked.connect(
            lambda: self.presenter.notify(Notification.UPDATE_OTHER, field=self.flat, name="Flat"))

        self.dark, self.select_dark = self.create_file_input(2)
        self.select_dark.clicked.connect(
            lambda: self.presenter.notify(Notification.UPDATE_OTHER, field=self.dark, name="Dark"))

        self.proj_180deg, self.select_proj_180deg = self.create_file_input(3)
        self.sample_log, self.select_sample_log = self.create_file_input(4)
        self.flat_log, self.select_flat_log = self.create_file_input(5)

        self.step_all.clicked.connect(self._set_all_step)
        self.step_preview.clicked.connect(self._set_preview_step)
        # if accepted load the stack
        self.accepted.connect(self.parent_view.execute_load)

        # remove the placeholder text from QtCreator
        self.expectedResourcesLabel.setText("")

    def create_file_input(self, position: int) -> Tuple[Field, QPushButton]:
        section: QTreeWidgetItem = self.tree.topLevelItem(position)

        use = QCheckBox(self)
        self.tree.setItemWidget(section, 2, use)

        select_button = QPushButton("Select", self)
        select_button.setMaximumWidth(100)
        select_button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)

        self.tree.setItemWidget(section, 3, select_button)
        field = Field(self, self.tree, section, use)

        return field, select_button

    @staticmethod
    def select_file(caption: str) -> Optional[str]:
        """
        :param caption: Title of the file browser window that will be opened
        :return: True: If a file has been selected, False otherwise
        """
        images_filter = "Images (*.png *.jpg *.tif *.tiff *.fit *.fits)"
        selected_file, accepted = Qt.QFileDialog.getOpenFileName(caption=caption,
                                                                 filter=f"{images_filter};;All (*.*)",
                                                                 initialFilter=images_filter)

        if accepted:
            return selected_file
        else:
            return None

    def _set_all_step(self):
        self.sample.set_step(1)

    def _set_preview_step(self):
        self.sample.set_step(self.presenter.last_shape[0] // 10)

    def get_parameters(self) -> LoadingParameters:
        return self.presenter.get_parameters()

    def show_error(self, msg, traceback):
        self.parent_view.presenter.show_error(msg, traceback)
