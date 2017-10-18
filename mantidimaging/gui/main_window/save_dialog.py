from __future__ import absolute_import, division, print_function

from PyQt5 import Qt

from mantidimaging.core.io.loader import supported_formats
from mantidimaging.core.io.utility import DEFAULT_IO_FILE_FORMAT
from mantidimaging.core.utility import gui_compile_ui


def select_directory(field, caption):
    assert isinstance(field, Qt.QLineEdit), (
            "The passed object is of type {0}. This function only works with "
            "QLineEdit".format(type(field)))

    # open file dialogue and set the text if file is selected
    field.setText(Qt.QFileDialog.getExistingDirectory(caption=caption))


class MWSaveDialog(Qt.QDialog):
    def __init__(self, parent, stack_list):
        super(MWSaveDialog, self).__init__(parent)
        gui_compile_ui.execute('gui/ui/save_dialog.ui', self)

        self.browseButton.clicked.connect(
            lambda: select_directory(self.savePath, "Browse"))

        self.buttonBox.button(Qt.QDialogButtonBox.SaveAll).clicked.connect(
            self.save_all)

        # dynamically add all the supported formats
        formats = supported_formats()
        self.formats.addItems(formats)

        # set the default to tiff
        self.formats.setCurrentIndex(formats.index(DEFAULT_IO_FILE_FORMAT))

        if stack_list:  # we will just show an empty drop down if no stacks
            self.stack_uuids, user_friendly_names = zip(*stack_list)
            # the stacklist is created in the main windows presenter and has
            # format [(uuid, title)...], doing zip(*stack_list) unzips the
            # tuples into separate lists
            self.stackNames.addItems(user_friendly_names)

        self.selected_stack = None

    def save_all(self):
        self.selected_stack = self.stack_uuids[self.stackNames.currentIndex()]
        self.parent().execute_save()

    def save_path(self):
        """
            :return: The directory of the path as a Python string
        """
        return str(self.savePath.text())

    def name_prefix(self):
        """
            :return: The directory of the path as a Python string
        """
        return str(self.namePrefix.text())

    def swap_axes(self):
        return self.swapAxes.isChecked()

    def overwrite(self):
        return self.overwriteAll.isChecked()

    def image_format(self):
        return str(self.formats.currentText())
