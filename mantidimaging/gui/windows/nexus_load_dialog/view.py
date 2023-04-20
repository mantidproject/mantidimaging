# Copyright (C) 2023 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations
from typing import Tuple

from PyQt5.QtCore import Qt, QEventLoop
from PyQt5.QtWidgets import QPushButton, QFileDialog, QLineEdit, QTreeWidget, QTreeWidgetItem, \
    QHeaderView, QCheckBox, QDialogButtonBox, QComboBox, QDoubleSpinBox, \
    QStackedWidget, QApplication, QWidget, QHBoxLayout, QLabel, QSpinBox

from mantidimaging.gui.mvp_base import BaseDialogView
from mantidimaging.gui.windows.nexus_load_dialog.presenter import NexusLoadPresenter, Notification

NEXUS_CAPTION = "NeXus"
NEXUS_FILTER = "NeXus (*.nxs *.hd5)"

FOUND_TEXT = {True: "✓", False: "✕"}

FOUND_COLUMN = 1
PATH_COLUMN = 2
SHAPE_COLUMN = 3
CHECKBOX_COLUMN = 4
TEXT_COLUMNS = [FOUND_COLUMN, PATH_COLUMN, SHAPE_COLUMN]


class NexusLoadDialog(BaseDialogView):
    tree: QTreeWidget
    chooseFileButton: QPushButton
    filePathLineEdit: QLineEdit
    buttonBox: QDialogButtonBox
    pixelDepthComboBox: QComboBox
    pixelSizeSpinBox: QDoubleSpinBox
    stackedWidget: QStackedWidget
    previewPushButton: QStackedWidget
    allPushButton: QStackedWidget
    presenter: NexusLoadPresenter

    def __init__(self, parent):
        super().__init__(parent, "gui/ui/nexus_load_dialog.ui")

        self.parent_view = parent
        self.presenter = NexusLoadPresenter(self)
        self.tree.expandItem(self.tree.topLevelItem(1))
        self.checkboxes = dict()

        self.tree.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.tree.header().setSectionResizeMode(2, QHeaderView.Stretch)

        self.chooseFileButton.clicked.connect(self.choose_nexus_file)
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)

        self.start_widget = QSpinBox()
        self.stop_widget = QSpinBox()
        self.step_widget = QSpinBox()

        self.start_widget.setMinimum(0)
        self.stop_widget.setMinimum(1)
        self.step_widget.setMinimum(1)

        self.increment_widget = QWidget()
        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel("Start"))
        h_layout.addWidget(self.start_widget)
        h_layout.addWidget(QLabel("Stop"))
        h_layout.addWidget(self.stop_widget)
        h_layout.addWidget(QLabel("Increment"))
        h_layout.addWidget(self.step_widget)
        self.increment_widget.setLayout(h_layout)
        self.increment_widget.setEnabled(False)

        section: QTreeWidgetItem = self.tree.topLevelItem(2)
        child = section.child(0).child(0)
        self.tree.setItemWidget(child, 2, self.increment_widget)
        self.tree.setItemWidget(child, 0, QLabel("Indices"))

        self.accepted.connect(self.parent_view.execute_nexus_load)

        self.previewPushButton.clicked.connect(self._set_preview_step)
        self.allPushButton.clicked.connect(self._set_all_step)
        self.n_proj = 0

        self.pixelBitDepthLabel.hide()
        self.pixelDepthComboBox.hide()

    def choose_nexus_file(self):
        """
        Select a NeXus file and attempt to load it. If a file is chosen, clear the information/widgets from the
        QTreeWidget and enable the OK button.
        """
        selected_file, _ = QFileDialog.getOpenFileName(caption=NEXUS_CAPTION,
                                                       filter=f"{NEXUS_FILTER};;All (*.*)",
                                                       initialFilter=NEXUS_FILTER)

        if selected_file:
            self.stackedWidget.setCurrentIndex(1)
            QApplication.instance().processEvents(QEventLoop.ProcessEventsFlag.AllEvents, 1)
            self.checkboxes.clear()
            self.clear_widgets()
            self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(True)
            self.filePathLineEdit.setText(selected_file)
            self.presenter.notify(Notification.NEXUS_FILE_SELECTED)
            self.stackedWidget.setCurrentIndex(0)

    def clear_widgets(self):
        """
        Remove text and checkbox widgets from the QTreeWidget when a new file has been selected.
        """
        for position in range(2):
            section: QTreeWidgetItem = self.tree.topLevelItem(position)
            for column in TEXT_COLUMNS:
                section.setText(column, "")

        data_section: QTreeWidgetItem = self.tree.topLevelItem(2)
        for position in range(5):
            child = data_section.child(position)
            for column in TEXT_COLUMNS:
                child.setText(column, "")
            self.tree.removeItemWidget(child, CHECKBOX_COLUMN)

    def set_data_found(self, position: int, found: bool, path: str, shape: Tuple[int, ...]):
        """
        Indicate on the QTreeWidget if the image key and data fields have been found or not.
        :param position: The row position for the data.
        :param found: Whether or not the data has been found.
        :param path: The data path in the NeXus file.
        :param shape: The shape of the data/image key array.
        """
        data_section: QTreeWidgetItem = self.tree.topLevelItem(position)
        self.set_found_status(data_section, found)

        # Nothing else to do if the data wasn't found
        if not found:
            return

        # Add the path and array shape information to the QTreeWidget
        data_section.setText(PATH_COLUMN, path)
        data_section.setText(SHAPE_COLUMN, str(shape))

    def set_images_found(self, position: int, found: bool, shape: Tuple[int, int, int]):
        """
        Indicate on the QTreeWidget if the projections and dark/flat before/after images were found in the data array.
        :param position: The row position for the image type.
        :param found: Whether or not the images were found.
        :param shape: The shape of the images array.
        """
        section: QTreeWidgetItem = self.tree.topLevelItem(2)
        child = section.child(position)
        self.set_found_status(child, found)

        # Nothing else to do if the images weren't found
        if not found:
            return

        # Set shape information and add a "Use?" checkbox
        child.setText(SHAPE_COLUMN, str(shape))
        checkbox = QCheckBox()
        checkbox.setChecked(True)
        if not position:
            checkbox.setEnabled(False)
        self.tree.setItemWidget(child, CHECKBOX_COLUMN, checkbox)
        self.checkboxes[child.text(0)] = checkbox

    def set_projections_increment(self, n_proj: int):
        """
        Set the properties of the indices spin boxes.
        :param n_proj: The number of projections that have been found in the NeXus file.
        """
        self.n_proj = n_proj
        self.tree.topLevelItem(2).child(0).setExpanded(True)

        self.stop_widget.setMaximum(n_proj)
        self.stop_widget.setValue(n_proj)
        self.step_widget.setMaximum(n_proj)

        self.increment_widget.setEnabled(True)

    def show_exception(self, msg: str, traceback):
        """
        Show an error about an exception.
        :param msg: The error message.
        :param traceback: The traceback.
        """
        self.parent_view.presenter.show_error(msg, traceback)

    def show_data_error(self, msg: str):
        """
        Show an error about missing required data or an unreadable file.
        :param msg: The error message.
        """
        self.parent_view.show_error_dialog(msg)

    def disable_ok_button(self):
        """
        Disable the OK button when the NeXus file isn't usable.
        """
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)

    @staticmethod
    def set_found_status(tree_widget_item: QTreeWidgetItem, found: bool):
        """
        Adds a tick or cross to the found column in the QTreeWidget to indicate if certain data could be found in the
        NeXus file.
        :param tree_widget_item: The QTreeWidgetItem that contains a found column.
        :param found: Whether or not the data was found.
        """
        tree_widget_item.setText(FOUND_COLUMN, FOUND_TEXT[found])
        tree_widget_item.setTextAlignment(FOUND_COLUMN, Qt.AlignHCenter)

    def _set_preview_step(self):
        """
        Set the spin boxes to load a preview of the projections.
        """
        self.start_widget.setValue(0)
        self.stop_widget.setValue(self.n_proj)
        self.step_widget.setValue(self.n_proj // 10)

    def _set_all_step(self):
        """
        Set the spin boxes to load all the projections.
        """
        self.start_widget.setValue(0)
        self.stop_widget.setValue(self.n_proj)
        self.step_widget.setValue(1)
