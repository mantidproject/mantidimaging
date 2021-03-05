# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from __future__ import annotations
from PyQt5.QtWidgets import QLabel, QWidget, QVBoxLayout, QGroupBox, QPushButton, QStyle
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from typing import List

from mantidimaging.gui.mvp_base import BaseDialogView
from .model import EnablePredicateFactory


class WizardStage(QWidget):
    def __init__(self, name, parent=None):
        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.title_label = QLabel("Stage: " + name)
        self.layout.addWidget(self.title_label)
        self.steps: List[WizardStep] = []

    def add_step(self, wizard_step: WizardStep):
        self.steps.append(wizard_step)
        self.layout.addWidget(wizard_step)

    def handle_stack_change(self, stack_history: dict):
        for step in self.steps:
            step.handle_stack_change(stack_history)


class WizardStep(QWidget):
    def __init__(self, step: dict, wizard: WizardView, parent=None):
        super().__init__(parent)

        self.name = step["name"]
        self.layout = QVBoxLayout(self)
        self.title_label = QPushButton("Step: " + self.name)
        self.title_label.setLayoutDirection(Qt.RightToLeft)

        self.layout.addWidget(self.title_label)

        self.step_box = QGroupBox()
        self.step_box_layout = QVBoxLayout(self.step_box)
        self.description = QLabel(step["description"])

        self.step_box_layout.addWidget(self.description)

        if "action" in step:
            run_button = QPushButton("Run")
            self.step_box_layout.addWidget(run_button)
            run_button.clicked.connect(lambda: wizard.presenter.run_action(step["action"]))

        self.step_box.setVisible(False)
        self.layout.addWidget(self.step_box)

        self.title_label.clicked.connect(self.toggle_visible)

        self.enable_predicate = EnablePredicateFactory(step.get("enable_if", ""))
        self.done_predicate = EnablePredicateFactory(step.get("done_if", ""))

    def toggle_visible(self, event):
        self.step_box.setVisible(not self.step_box.isVisible())

    def handle_stack_change(self, stack_history: dict):
        enabled = self.enable_predicate(stack_history)

        if not enabled:
            self.step_box.setVisible(False)
        self.title_label.setEnabled(enabled)

        if self.done_predicate(stack_history):
            self.title_label.setIcon(self.style().standardIcon(QStyle.SP_DialogApplyButton))
        else:
            self.title_label.setIcon(QIcon())


class WizardView(BaseDialogView):
    def __init__(self, parent, presenter):
        super().__init__(parent, "gui/ui/wizard.ui")
        self.stages = {}
        self.presenter = presenter

    def add_stage(self, stage_name: str):
        new_stage = WizardStage(stage_name)
        self.stages[stage_name] = new_stage
        self.wizard_top_layout.addWidget(new_stage)

    def add_step(self, stage_name: str, step: dict):
        new_step = WizardStep(step, self)
        self.stages[stage_name].add_step(new_step)
