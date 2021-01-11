# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import unittest
from unittest import mock
from unittest.mock import DEFAULT, MagicMock, Mock, patch
from uuid import uuid4

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.gui.windows.stack_choice.presenter import StackChoicePresenter
from mantidimaging.gui.windows.stack_choice.view import Notification


class StackChoicePresenterTest(unittest.TestCase):
    def setUp(self):
        self.original_stack = th.generate_images()
        self.new_stack = th.generate_images()
        self.v = mock.MagicMock()
        self.op_p = mock.MagicMock()
        self.uuid = uuid4()
        self.p = StackChoicePresenter(original_stack=self.original_stack,
                                      new_stack=self.new_stack,
                                      operations_presenter=self.op_p,
                                      stack_uuid=self.uuid,
                                      view=self.v)

    def test_presenter_doesnt_raise_lists_for_original_stack(self):
        single_stack_uuid = uuid4()
        original_stack = [(th.generate_images(), single_stack_uuid), (th.generate_images(), uuid4())]
        StackChoicePresenter(original_stack, mock.MagicMock(), mock.MagicMock(), single_stack_uuid, mock.MagicMock())

    @mock.patch("mantidimaging.gui.windows.stack_choice.presenter.StackChoiceView")
    def test_presenter_throws_if_uuid_is_not_in_stack(self, _):
        original_stack = [(th.generate_images(), uuid4()), (th.generate_images(), uuid4())]
        with self.assertRaises(RuntimeError):
            StackChoicePresenter(original_stack, mock.MagicMock(), mock.MagicMock(), uuid4(), None)

    def test_show_calls_show_in_the_view(self):
        self.p.show()

        self.v.show.assert_called_once()

    def test_notify_choose_original(self):
        self.p.do_reapply_original_data = mock.MagicMock()

        self.p.notify(Notification.CHOOSE_ORIGINAL)

        self.p.do_reapply_original_data.assert_called_once()

    @patch.multiple("mantidimaging.gui.windows.stack_choice.presenter.StackChoicePresenter",
                    do_reapply_original_data=MagicMock(side_effect=RuntimeError),
                    show_error=DEFAULT)
    def test_notify_handles_exceptions(self, _: Mock = Mock(), show_error: Mock = Mock()):
        self.p.notify(Notification.CHOOSE_ORIGINAL)

        show_error.assert_called_once()

    def test_notify_choose_new_data(self):
        self.p.do_clean_up_original_data = mock.MagicMock()

        self.p.notify(Notification.CHOOSE_NEW_DATA)

        self.p.do_clean_up_original_data.assert_called_once()

    def test_clean_up_original_images_stack(self):
        self.op_p.original_images_stack = [(1, self.uuid), (2, uuid4())]

        self.p._clean_up_original_images_stack()

        self.assertEqual(1, len(self.op_p.original_images_stack))
        self.assertEqual(2, self.op_p.original_images_stack[0][0])

        self.p._clean_up_original_images_stack()

        self.assertEqual(None, self.op_p.original_images_stack)

    def test_do_reapply_original_data(self):
        self.p._clean_up_original_images_stack = mock.MagicMock()
        self.p.close_view = mock.MagicMock()
        self.p.stack = 1

        self.p.do_reapply_original_data()

        self.op_p.main_window.presenter.model.set_images_in_stack.assert_called_once_with(self.uuid, 1)
        self.p._clean_up_original_images_stack.assert_called_once()
        self.assertTrue(self.v.choice_made)
        self.p.close_view.assert_called_once()

    def test_do_clean_up_original_data(self):
        self.p.stack = mock.MagicMock()
        self.p._clean_up_original_images_stack = mock.MagicMock()
        self.p.close_view = mock.MagicMock()

        self.p.do_clean_up_original_data()

        self.p._clean_up_original_images_stack.assert_called_once()
        self.assertTrue(self.v.choice_made)
        self.p.close_view.assert_called_once()

    def test_close_view_calls_close_on_view(self):
        self.p.close_view()

        self.v.close.assert_called_once()

    def test_close_view_sets_done_true(self):
        self.p.close_view()

        self.assertTrue(self.p.done)

    def test_do_toggle_lock_histograms(self):
        self.v.lockHistograms.isChecked.return_value = True
        self.p.notify(Notification.TOGGLE_LOCK_HISTOGRAMS)
        self.v.connect_histogram_changes.assert_called_once()

        self.v.lockHistograms.isChecked.return_value = False
        self.p.notify(Notification.TOGGLE_LOCK_HISTOGRAMS)
        self.v.disconnect_histogram_changes.assert_called_once()
