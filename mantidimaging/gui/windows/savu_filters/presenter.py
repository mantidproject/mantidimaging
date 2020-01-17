from enum import Enum, auto
from logging import getLogger
from typing import List, TYPE_CHECKING
from uuid import UUID

from PyQt5.QtWidgets import QWidget
from requests import Response

from mantidimaging.gui.mvp_base import BasePresenter
from mantidimaging.gui.utility import add_property_to_form
from mantidimaging.gui.windows.savu_filters.job_run_response import JobRunResponseContent
from mantidimaging.gui.windows.savu_filters.model import SavuFiltersWindowModel, CurrentFilterData
from mantidimaging.gui.windows.savu_filters.process_list.view import ProcessListView
from mantidimaging.gui.windows.savu_filters.remote_presenter import SavuFiltersRemotePresenter
from mantidimaging.gui.windows.stack_visualiser import StackVisualiserView

if TYPE_CHECKING:
    from mantidimaging.gui.windows.savu_filters.view import SavuFiltersWindowView  # noqa:F401
    from mantidimaging.gui.windows.main.view import MainWindowView  # noqa:F401


class Notification(Enum):
    REGISTER_ACTIVE_FILTER = auto()
    APPLY_FILTER = auto()
    APPLY_LIST = auto()
    ADD_PLUGIN = auto()


class SavuFiltersWindowPresenter(BasePresenter):
    def __init__(self, view: 'SavuFiltersWindowView',
                 main_window: 'MainWindowView',
                 remote_presenter: SavuFiltersRemotePresenter):
        super(SavuFiltersWindowPresenter, self).__init__(view)

        self.model = SavuFiltersWindowModel(self)
        self.remote_presenter = remote_presenter
        self.main_window = main_window

        self.process_list_view = ProcessListView(self.view)
        self.view.processListLayout.insertWidget(0, self.process_list_view)

        self.current_filter: CurrentFilterData = ()

    def notify(self, signal):
        try:
            if signal == Notification.REGISTER_ACTIVE_FILTER:
                self.do_register_active_filter()
            elif signal == Notification.APPLY_FILTER:
                self.do_apply_filter()
            elif signal == Notification.APPLY_LIST:
                self.apply_list()
            elif signal == Notification.ADD_PLUGIN:
                self.add_plugin()

        except Exception as e:
            self.show_error(e)
            getLogger(__name__).exception("Notification handler failed")

    def set_stack_uuid(self, uuid: UUID):
        self.set_stack(self.main_window.get_stack_visualiser(uuid) if uuid is not None else None)

    def set_stack(self, stack: StackVisualiserView):
        # Disconnect ROI update signal from previous stack
        if self.model.stack:
            self.model.stack.roi_updated.disconnect(self.handle_roi_selection)

        self.model.stack = stack

        # Connect ROI update signal to newly selected stack
        if stack:
            stack.roi_updated.connect(self.handle_roi_selection)
            self.view.reset_indices_inputs(self.model.image_shape)

    def handle_roi_selection(self, roi):
        if roi:
            # TODO used to check  and self.filter_uses_auto_property(SVParameters.ROI): but disabled for now
            self.view.auto_update_triggered.emit()

    def do_register_active_filter(self):
        # clear the fields of the previous filter

        filter_idx = self.view.filterSelector.currentIndex()

        savu_filter = self.model.filter(filter_idx)

        parameters_widgets: List[QWidget] = []
        for parameters in savu_filter.visible_parameters():
            label, widget = add_property_to_form(
                parameters.name,
                parameters.type,
                parameters.value,
                tooltip=parameters.description,
                form=self.view.filterPropertiesLayout,
            )
            parameters_widgets.append(widget)

        self.current_filter = (savu_filter, parameters_widgets)
        self.view.set_description(savu_filter.synopsis, savu_filter.info)

        # TODO then trigger self.view.auto_update_triggered.emit to update the view

        # we do not have to do this for SAVU filters as they are all the same #notallfilters
        # Register new filter (adding it's property widgets to the properties layout)
        # TODO set up the filter further if necessary
        # self.model.setup_filter(None)

    def filter_uses_auto_property(self, prop):
        if self.model.parameters_from_stack is not None:
            return prop in self.model.parameters_from_stack.values()
        else:
            return False

    def do_apply_filter(self):
        self.view.clear_output_text()
        indices = [self.view.startInput.value(), self.view.endInput.value(), self.view.stepInput.value()]
        self.model.do_apply_filter(self.current_filter, indices)

    def apply_list(self):
        self.view.clear_output_text()
        entries = self.process_list_view.plugin_entries
        indices = [self.view.startInput.value(), self.view.endInput.value(), self.view.stepInput.value()]
        self.model.apply_process_list(entries, indices)

    def do_job_submission_success(self, response_content: JobRunResponseContent):
        self.remote_presenter.do_job_submission_success(response_content)

    def do_job_submission_failure(self, error_response: Response):
        raise NotImplementedError(f"(Unhandled) error response from hebi:\n{error_response.reason}")

    def add_plugin(self):
        entry = SavuFiltersWindowModel.create_plugin_entry_from(self.current_filter)
        self.process_list_view.add_plugin(entry)
