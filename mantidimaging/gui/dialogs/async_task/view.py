from __future__ import absolute_import, division, print_function

from mantidimaging.gui.mvp_base import BaseDialogView

from .presenter import AsyncTaskDialogPresenter


class AsyncTaskDialogView(BaseDialogView):
    def __init__(self, parent, auto_close=False):
        super(AsyncTaskDialogView, self).__init__(
                parent, 'gui/ui/async_task_dialog.ui')

        self.parent_view = parent
        self.presenter = AsyncTaskDialogPresenter(self)

        self.auto_close = auto_close

        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(1000)

        self.progress_text = self.infoText.text()

    def reject(self):
        # Do not close the dialog when processing is still ongoing
        if not self.presenter.task_is_running:
            super(AsyncTaskDialogView, self).reject()

    def handle_completion(self, successful):
        """
        Updates the UI after the task has been completed.

        :param successful: If the task was successful
        """
        # Set info text to "Complete"
        self.infoText.setText("Complete")

        # If auto close is enabled and the task was sucesfull then hide the UI
        if self.auto_close and successful:
            self.hide()

    def set_progress(self, progress, message):
        # Set status message
        if message:
            self.infoText.setText(message)

        # Update progress bar
        self.progressBar.setValue(progress * 1000)
