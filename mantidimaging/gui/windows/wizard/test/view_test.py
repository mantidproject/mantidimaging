# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import unittest
from unittest import mock

from mantidimaging.gui.windows.wizard.view import WizardView, WizardStep, WizardStage
from mantidimaging.gui.windows.main import MainWindowView
from mantidimaging.test_helpers import start_qapplication, mock_versions

STEP_DATA = {'name': 'Loading files', 'description': 'desc'}


@mock_versions
@start_qapplication
class WizardViewTest(unittest.TestCase):
    def setUp(self) -> None:
        with mock.patch("mantidimaging.gui.windows.main.view.WelcomeScreenPresenter"):
            self.main_window = MainWindowView()
        self.view = WizardView(self.main_window, mock.Mock())

    def test_add_stage(self):
        self.view.add_stage("loading")
        self.assertIn("loading", self.view.stages)

    def test_add_step(self):
        self.view.add_stage("loading")
        self.view.add_step("loading", STEP_DATA)
        self.assertIn("loading", self.view.stages)
        self.assertEqual(len(self.view.stages["loading"].steps), 1)


@start_qapplication
class WizardStepTest(unittest.TestCase):
    def setUp(self) -> None:
        self.step = WizardStep(STEP_DATA, mock.Mock())

    def test_show_step(self):
        self.step.step_box = mock.Mock()
        self.step.show_step()
        self.step.step_box.setVisible.assert_called_once_with(True)

    def test_hide_step(self):
        self.step.step_box = mock.Mock()
        self.step.hide_step()
        self.step.step_box.setVisible.assert_called_once_with(False)

    def test_handle_stack_change(self):
        self.step.enable_predicate = mock.Mock(return_value=True)
        self.step.step_box = mock.Mock()
        self.step.title_label = mock.Mock()
        self.step.handle_stack_change({})
        self.step.title_label.setEnabled.assert_called_once_with(True)


@start_qapplication
class WizardStageTest(unittest.TestCase):
    def setUp(self) -> None:
        self.stage = WizardStage("loading")

    def test_add_step(self):
        self.stage.layout = mock.Mock()
        step = mock.Mock()
        self.stage.add_step(step)
        self.stage.layout.addWidget.assert_called_once_with(step)
        self.assertIn(step, self.stage.steps)

    def test_handle_stack_change(self):
        self.stage.layout = mock.Mock()
        step = mock.Mock()
        hist = {'a': 'b'}
        self.stage.add_step(step)
        self.stage.handle_stack_change(hist)
        step.handle_stack_change.assert_called_once_with(hist)
