from __future__ import absolute_import, division, print_function

from PyQt5 import Qt

from mantidimaging.core.utility import gui_compile_ui

from .atd_presenter import AsyncTaskDialogPresenter


class AsyncTaskDialogView(Qt.QDialog):
    def __init__(self, parent, auto_close=False):
        super(AsyncTaskDialogView, self).__init__(parent)
        gui_compile_ui.execute('gui/ui/async_task_dialog.ui', self)

        self.parent_view = parent
        self.presenter = AsyncTaskDialogPresenter(self)

        self.cancelButton.clicked.connect(self.cancel_clicked)

        self.auto_close = auto_close

    def cancel_clicked(self):
        """
        Handles the user clicking the Cancel button.
        """
        # TODO: actually handle cancellation
        self.parent_view.presenter.show_error("I've been cancelled")

    def handle_completion(self, successful):
        """
        Updates the UI after the task has been completed.

        :param successful: If the task was successful
        """
        # Set info text to "Complete"
        self.infoText.setText("Complete")

        # Set the progress bar to full
        finalProgress = self.progressBar.maximum() if successful \
            else self.progressBar.minimum()
        self.progressBar.setValue(finalProgress)

        # Disable the cancel button
        self.cancelButton.setEnabled(False)

        # If auto close is enabled and the task was sucesfull then hide the UI
        if self.auto_close and successful:
            self.hide()
