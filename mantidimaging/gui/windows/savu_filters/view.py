import os
from typing import TYPE_CHECKING

from PyQt5 import Qt
from PyQt5.QtWidgets import QLabel, QMainWindow, QTextEdit, QSpinBox

from mantidimaging.core.configs.savu_backend_docker import RemoteConfig, RemoteConstants
from mantidimaging.gui.mvp_base import BaseMainWindowView
from mantidimaging.gui.windows.savu_filters.presenter import Notification as PresNotification
from mantidimaging.gui.windows.savu_filters.presenter import SavuFiltersWindowPresenter
from mantidimaging.gui.windows.savu_filters.remote_presenter import SavuFiltersRemotePresenter

if TYPE_CHECKING:
    from mantidimaging.gui.windows.main.view import MainWindowView  # noqa:F401


class SavuFiltersWindowView(BaseMainWindowView):
    new_output = Qt.pyqtSignal(str)
    savu_finished = Qt.pyqtSignal(str)
    info: QLabel
    description: QLabel
    startInput: QSpinBox
    endInput: QSpinBox

    def __init__(self, main_window: 'MainWindowView'):
        """
        TODO add Show plugins directory button
        Use qt/python/mantidqt/utils/show_in_explorer.py from Mantid
        :param main_window:
        :param cmap:
        """
        super(SavuFiltersWindowView, self).__init__(main_window, 'gui/ui/savu_filters_window.ui')

        self.remote_presenter = SavuFiltersRemotePresenter(self)
        self.presenter = SavuFiltersWindowPresenter(self, main_window, self.remote_presenter)
        self.main_window = main_window
        self.floating_output_window = QMainWindow(self)
        self.floating_output = QTextEdit(self.floating_output_window)
        self.floating_output_window.setCentralWidget(self.floating_output)
        self.floating_output_window.show()

        self.new_output.connect(self.append_output_text)
        self.savu_finished.connect(self.load_savu_stack)

        # Populate list of filters and handle filter selection
        self.filterSelector.addItems(self.presenter.model.filter_names)
        self.filterSelector.currentIndexChanged[int].connect(self.handle_filter_selection)
        self.handle_filter_selection()

        self.stackSelector.stack_selected_uuid.connect(self.presenter.set_stack_uuid)
        self.applyButton.clicked.connect(lambda: self.presenter.notify(PresNotification.APPLY_FILTER))
        self.applyListButton.clicked.connect(lambda: self.presenter.notify(PresNotification.APPLY_LIST))
        self.confirmPluginButton.clicked.connect(lambda: self.presenter.notify(PresNotification.CONFIRM_PLUGIN))

        self.stackSelector.subscribe_to_main_window(main_window)

    def cleanup(self):
        self.stackSelector.unsubscribe_from_main_window()
        self.main_window.savu_filters = None

    def show(self):
        super(SavuFiltersWindowView, self).show()

    def handle_filter_selection(self):
        self.presenter.notify(PresNotification.REGISTER_ACTIVE_FILTER)

    def set_description(self, info, desc):
        self.info.setText("\n".join([info, desc]))

    def append_output_text(self, text):
        self.floating_output.setText(self.floating_output.toPlainText() + "\n" + text)

    def clear_output_text(self):
        self.floating_output.setText("")

    def load_savu_stack(self, output: str):
        # replace remote output with the local output path equivalent
        local_output = os.path.expanduser(output.replace(RemoteConstants.OUTPUT_DIR, RemoteConfig.LOCAL_OUTPUT_DIR))
        # navigate to the first folder - that should be the folder created by the output plugin
        # TODO make more robust somehow, get output folder from Savu through Hebi?
        local_output = os.path.join(local_output, os.listdir(local_output)[0], "TiffSaver-tomo")
        kwargs = {
            'sample_path': local_output,
            'flat_path': '',
            'dark_path': '',
            'image_format': "tiff",
            'parallel_load': False,
            'indices': None,
            'custom_name': "apples",
            'in_prefix': '',
        }
        self.main_window.presenter.load_stack(**kwargs)

    def reset_indices_inputs(self, image_indices):
        self.startInput.setMaximum(image_indices[0])
        self.endInput.setMaximum(image_indices[0])
        self.stepInput.setMaximum(image_indices[0])
        self.startInput.setValue(0)
        self.endInput.setValue(image_indices[0])
