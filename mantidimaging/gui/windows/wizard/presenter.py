# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from logging import getLogger
from pathlib import Path
import yaml

from mantidimaging.gui.mvp_base.presenter import BasePresenter
from mantidimaging.gui.windows.wizard.view import WizardView

wizard_data_file = Path(__file__).parent / "wizard_steps.yml"
logger = getLogger(__name__)


class WizardPresenter(BasePresenter):
    def __init__(self, parent=None):
        self.view = WizardView(parent, self)
        super().__init__(self.view)

        self.main_window_presenter = parent.presenter
        self.wizard_data = yaml.safe_load(wizard_data_file.open())
        self.populate()
        parent.model_changed.connect(self.handle_stack_change)
        parent.filter_applied.connect(self.handle_stack_change)
        parent.recon_applied.connect(self.handle_stack_change)
        self.handle_stack_change()
        self.show()

    def show(self):
        self.view.show()

    def populate(self):
        for stage in self.wizard_data["stages"]:
            self.view.add_stage(stage["name"])
            for step in stage["steps"]:
                self.view.add_step(stage["name"], step)

    def run_action(self, action: str):
        if action == "load":
            self.main_window_presenter.wizard_action_load()

        elif action.startswith("operations"):
            operation_menu_name = action.partition(":")[2].strip()
            self.main_window_presenter.show_operation(operation_menu_name)

        elif action.startswith("reconstruction"):
            self.main_window_presenter.wizard_action_show_reconstruction()

        else:
            logger.error(f"Unknown action: '{action}'")

    def handle_stack_change(self):
        stack_history = None
        stack_list = self.main_window_presenter.stack_visualiser_list
        for uuid, name in stack_list:
            if "Tomo" not in name and "Recon" not in name:
                continue

            stack_history = self.main_window_presenter.get_stack_visualiser_history(uuid)
            break

        for stage in self.view.stages.values():
            stage.handle_stack_change(stack_history)
