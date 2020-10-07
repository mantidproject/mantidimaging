import unittest
from functools import partial

import mock

from mantidimaging.gui.windows.main import MainWindowView
from mantidimaging.gui.windows.operations import FiltersWindowPresenter
from mantidimaging.test_helpers.unit_test_helper import assert_called_once_with, generate_images


class FiltersWindowPresenterTest(unittest.TestCase):
    def setUp(self) -> None:
        self.main_window = mock.create_autospec(MainWindowView)
        self.view = mock.MagicMock()
        self.presenter = FiltersWindowPresenter(self.view, self.main_window)
        self.view.presenter = self.presenter

    @mock.patch('mantidimaging.gui.windows.operations.presenter.FiltersWindowModel.filter_registration_func')
    def test_register_active_filter(self, filter_reg_mock: mock.Mock):
        reg_fun_mock = mock.Mock()
        filter_reg_mock.return_value = reg_fun_mock
        self.view.filterSelector.currentIndex.return_value = 0
        self.presenter.do_register_active_filter()

        reg_fun_mock.assert_called_once()
        filter_reg_mock.assert_called_once()

    @mock.patch('mantidimaging.gui.windows.operations.presenter.FiltersWindowModel.do_apply_filter')
    def test_apply_filter(self, apply_filter_mock: mock.Mock):
        stack = mock.Mock()
        presenter = mock.Mock()
        stack.presenter = presenter
        presenter.images.has_proj180deg.return_value = False
        self.presenter.stack = stack
        self.presenter.do_apply_filter()
        self.view.clear_previews.assert_called_once()

        expected_apply_to = [stack]
        assert_called_once_with(apply_filter_mock, expected_apply_to,
                                partial(self.presenter._post_filter, expected_apply_to))

    @mock.patch('mantidimaging.gui.windows.operations.presenter.FiltersWindowModel.do_apply_filter')
    def test_apply_filter_with_180degree_proj_stack(self, apply_filter_mock: mock.Mock):
        stack = mock.Mock()
        stack_proj180 = mock.Mock()
        presenter = mock.Mock()
        stack.presenter = presenter

        presenter.images.has_proj180deg.return_value = True
        presenter.images.proj180deg = stack_proj180
        self.view.main_window.get_stack_with_images.return_value = stack_proj180

        self.presenter.stack = stack
        self.presenter.do_apply_filter()

        self.view.clear_previews.assert_called_once()
        self.view.main_window.get_stack_with_images.assert_called_once_with(stack_proj180)

        expected_apply_to = [stack, stack_proj180]
        assert_called_once_with(apply_filter_mock, expected_apply_to,
                                partial(self.presenter._post_filter, expected_apply_to))

    @mock.patch('mantidimaging.gui.windows.operations.presenter.FiltersWindowModel.do_apply_filter')
    def test_apply_filter_to_all(self, apply_filter_mock: mock.Mock):
        self.view.ask_confirmation.return_value = False
        self.presenter.do_apply_filter_to_all()

        self.view.ask_confirmation.assert_called_once()

        self.view.ask_confirmation.reset_mock()
        self.view.ask_confirmation.return_value = True
        mock_stack_visualisers = [mock.Mock(), mock.Mock()]
        self.presenter.main_window = mock.Mock()
        self.presenter.main_window.get_all_stack_visualisers = mock.Mock()
        self.presenter.main_window.get_all_stack_visualisers.return_value = mock_stack_visualisers

        self.presenter.do_apply_filter_to_all()

        assert_called_once_with(apply_filter_mock, mock_stack_visualisers,
                                partial(self.presenter._post_filter, mock_stack_visualisers))

    @mock.patch('mantidimaging.gui.windows.operations.presenter.FiltersWindowPresenter.do_update_previews')
    def test_post_filter(self, update_previews_mock):
        mock_stack_visualisers = [mock.Mock(), mock.Mock()]
        self.presenter._post_filter(mock_stack_visualisers, None)

        for i, msv in enumerate(mock_stack_visualisers):
            assert msv.presenter.images == self.view.main_window.update_stack_with_images.call_args_list[i].args[0]
        update_previews_mock.assert_called_once()
        self.view.show_operation_completed.assert_called_once_with("Circular Mask")

    def test_update_previews_no_stack(self):
        self.presenter.do_update_previews()
        self.view.clear_previews.assert_called_once()

    @mock.patch('mantidimaging.gui.windows.operations.presenter.FiltersWindowPresenter._update_preview_image')
    @mock.patch('mantidimaging.gui.windows.operations.presenter.FiltersWindowModel.apply_to_images')
    def test_update_previews_apply_throws_exception(self, apply_mock: mock.Mock, update_preview_image_mock: mock.Mock):
        apply_mock.side_effect = Exception
        stack = mock.Mock()
        presenter = mock.Mock()
        stack.presenter = presenter
        images = generate_images()
        presenter.get_image.return_value = images
        self.presenter.stack = stack

        self.presenter.do_update_previews()

        presenter.get_image.assert_called_once_with(self.presenter.model.preview_image_idx)
        self.view.clear_previews.assert_called_once()
        update_preview_image_mock.assert_called_once()
        apply_mock.assert_called_once()

    @mock.patch('mantidimaging.gui.windows.operations.presenter.FiltersWindowPresenter._update_preview_image')
    @mock.patch('mantidimaging.gui.windows.operations.presenter.FiltersWindowModel.apply_to_images')
    def test_update_previews(self, apply_mock: mock.Mock, update_preview_image_mock: mock.Mock):
        stack = mock.Mock()
        presenter = mock.Mock()
        stack.presenter = presenter
        images = generate_images()
        presenter.get_image.return_value = images
        self.presenter.stack = stack
        self.presenter.do_update_previews()

        presenter.get_image.assert_called_once_with(self.presenter.model.preview_image_idx)
        self.view.clear_previews.assert_called_once()
        self.view.previews.auto_range.assert_called_once()
        self.assertEqual(3, update_preview_image_mock.call_count)
        apply_mock.assert_called_once()

    def test_get_filter_module_name(self):
        self.presenter.model.filters = mock.MagicMock()

        module_name = self.presenter.get_filter_module_name(0)

        self.assertEqual("mock.mock", module_name)
