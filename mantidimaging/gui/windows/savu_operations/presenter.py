import json
import traceback
from enum import Enum, auto
from logging import getLogger
from typing import TYPE_CHECKING, List
from uuid import UUID

from PyQt5.QtWidgets import QWidget
from requests import Response

from mantidimaging.gui.mvp_base import BasePresenter
from mantidimaging.gui.utility import BlockQtSignals, add_property_to_form
from mantidimaging.gui.utility.qt_helpers import delete_all_widgets_from_layout
from mantidimaging.gui.windows.savu_operations.job_run_response import JobRunResponseContent
from mantidimaging.gui.windows.savu_operations.model import (CurrentFilterData, SavuFiltersWindowModel)
from mantidimaging.gui.windows.savu_operations.process_list.view import ProcessListView
from mantidimaging.gui.windows.savu_operations.remote_presenter import SavuFiltersRemotePresenter
from mantidimaging.gui.windows.stack_visualiser import StackVisualiserView

if TYPE_CHECKING:
    from mantidimaging.gui.windows.savu_operations.view import SavuFiltersWindowView  # noqa: F401
    from mantidimaging.gui.windows.main.view import MainWindowView  # noqa: F401


class Notification(Enum):
    REGISTER_ACTIVE_FILTER = auto()
    APPLY_FILTER = auto()
    APPLY_LIST = auto()
    CONFIRM_PLUGIN = auto()


class Mode(Enum):
    """To determine if a new plugin is being configured, or one in the process list is being edited.

    The presenter is initially in ADDING mode. When the parameters of a plugin are loaded from the process list,
    it switches to EDITING mode. If a new filter is selected from the dropdown, or the
    """
    ADDING = auto()
    EDITING = auto()


class SavuFiltersWindowPresenter(BasePresenter):
    def __init__(self, view: 'SavuFiltersWindowView', main_window: 'MainWindowView'):
        super(SavuFiltersWindowPresenter, self).__init__(view)

        # handles socketio events coming from the remote backend
        self.remote_presenter = SavuFiltersRemotePresenter(view)
        self.model = SavuFiltersWindowModel(self, self.remote_presenter.retrieve_plugins_json())
        self.main_window = main_window

        self.process_list_view = ProcessListView(self.view)
        self.view.processListLayout.insertWidget(0, self.process_list_view)
        self.process_list_view.plugin_change_request.connect(self.load_plugin_from_list)

        self.current_filter: CurrentFilterData = ()
        self.mode: Mode = Mode.ADDING

    def disconnect(self):
        self.remote_presenter.disconnect()

    def notify(self, signal):
        try:
            if signal == Notification.REGISTER_ACTIVE_FILTER:
                self.do_register_active_filter()
            elif signal == Notification.APPLY_FILTER:
                self.do_apply_filter()
            elif signal == Notification.APPLY_LIST:
                self.apply_list()
            elif signal == Notification.CONFIRM_PLUGIN:
                self.confirm_plugin()

        except Exception as e:
            self.show_error(e, traceback.format_exc())
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

        self.model.stack = stack

    def handle_roi_selection(self, roi):
        # TODO used to check  and self.filter_uses_auto_property(SVParameters.ROI): but disabled for now
        pass
        # if roi:
        # self.view.auto_update_triggered.emit()

    def do_register_active_filter(self):
        self.set_mode(Mode.ADDING)
        filter_idx = self.view.filterSelector.currentIndex()
        self.load_filter(filter_idx)

    def load_filter(self, filter_idx, plugin_parameters=None):
        delete_all_widgets_from_layout(self.view.filterPropertiesLayout)
        savu_filter = self.model.filter(filter_idx)

        parameters_widgets: List[QWidget] = []
        for parameter in savu_filter.visible_parameters():
            value = plugin_parameters.get(parameter.name, parameter.value) if plugin_parameters \
                else parameter.value

            label, widget = add_property_to_form(
                parameter.name,
                parameter.type,
                value,
                tooltip=parameter.description,
                form=self.view.filterPropertiesLayout,
            )
            parameters_widgets.append(widget)

        self.current_filter = (savu_filter, parameters_widgets)
        self.view.set_description(savu_filter.synopsis, savu_filter.info)

        # TODO then trigger self.view.auto_update_triggered.emit to update the view

        # we do not have to do this for SAVU operations as they are all the same #notallfilters
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
        er = json.loads(error_response.text)
        msg = f"Error response from hebi:\n{error_response.status_code}: {error_response.reason}\n{er['message']}"
        self.view.show_output_text(msg)
        raise NotImplementedError(msg)

    def confirm_plugin(self):
        entry = SavuFiltersWindowModel.create_plugin_entry_from(self.current_filter)
        if self.mode == Mode.ADDING:
            self.process_list_view.add_plugin(entry)
        elif self.mode == Mode.EDITING:
            self.process_list_view.save_edited_plugin(entry)

    def load_plugin_from_list(self):
        self.set_mode(Mode.EDITING)
        to_load = self.process_list_view.plugin_to_edit
        filter_idx = [f.name for f in self.model.filters].index(to_load.name.decode('utf-8'))
        parameters = {k: str(v) for k, v in json.loads(to_load.data).items()}
        with BlockQtSignals([self.view.filterSelector]):
            self.view.filterSelector.setCurrentIndex(filter_idx)
            self.load_filter(filter_idx, parameters)

    def set_mode(self, mode: Mode):
        self.mode = mode
        message = "Add To Process List" if mode == Mode.ADDING else \
            f"Confirm Changes To Filter {self.process_list_view.to_edit + 1}"  # type: ignore
        self.view.confirmPluginButton.setText(message)
