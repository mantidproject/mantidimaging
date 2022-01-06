from typing import TYPE_CHECKING

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QComboBox

from mantidimaging.gui.widgets.dataset_selector.presenter import DatasetSelectorWidgetPresenter, Notification

if TYPE_CHECKING:
    from mantidimaging.gui.windows.main import MainWindowView


class DatasetSelectorWidgetView(QComboBox):
    datasets_updated = pyqtSignal()
    dataset_selected_uuid = pyqtSignal('PyQt_PyObject')

    main_window: 'MainWindowView'

    def __init__(self, parent):
        super().__init__(parent)

        self.presenter = DatasetSelectorWidgetPresenter(self)
        self.currentIndexChanged[int].connect(self.presenter.handle_selection)

    def subscribe_to_main_window(self, main_window: 'MainWindowView'):
        self.main_window = main_window

        # Initial population of dataset list
        self.presenter.notify(Notification.RELOAD_DATASETS)

        # Connect signal for auto update on stack change
        self.main_window.model_changed.connect(self._handle_loaded_datasets_changed)

    def unsubscribe_from_main_window(self):
        """
        Removes connections to main window.

        Must be called before the widget is destroyed.
        """
        if self.main_window:
            # Disconnect signal
            self.main_window.model_changed.disconnect(self._handle_loaded_datasets_changed)

    def _handle_loaded_datasets_changed(self):
        """
        Handle a change in loaded stacks.
        """
        self.presenter.notify(Notification.RELOAD_DATASETS)

    def current(self):
        return self.presenter.current_dataset

    # def try_to_select_relevant_stack(self, name: str) -> None:
    #     # Split based on whitespace
    #     name_parts = name.split()
    #     for i in range(self.count()):
    #         # If widget text contains all name parts
    #         if _string_contains_all_parts(self.itemText(i).lower(), name_parts):
    #             self.setCurrentIndex(i)
    #             break