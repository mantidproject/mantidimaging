import unittest

import numpy.testing as npt

from matplotlib.widgets import Slider

import mantidimaging.core.testing.unit_test_helper as th

from mantidimaging.core.utility.special_imports import import_mock

from mantidimaging.gui.stack_visualiser import (
        StackVisualiserPresenter, StackVisualiserView, ImageMode)
from mantidimaging.gui.stack_visualiser import \
        Notification as PresenterNotifications

mock = import_mock()


class StackVisualiserPresenterTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(StackVisualiserPresenterTest, self).__init__(*args, **kwargs)

    @classmethod
    def setUpClass(cls):
        cls.test_data = th.generate_images_class_random_shared_array()

    def setUp(self):
        # mock the view so it has the same methods
        self.view = mock.create_autospec(StackVisualiserView)
        self.view.slider = mock.create_autospec(Slider)
        self.presenter = StackVisualiserPresenter(
                self.view, self.test_data, data_traversal_axis=0)

    def test_getattr_and_clear(self):
        # empty class that inherits from object so that we can append
        # attributes to it
        class A:
            pass

        d = A()
        d.some_attr = 3
        result = self.presenter.getattr_and_clear(d, "some_attr")
        self.assertEqual(result, 3)
        self.assertTrue(d.some_attr is None)

    def test_get_image(self):
        index = 3

        test_data = self.test_data.sample

        img = self.presenter.get_image(index)
        npt.assert_equal(test_data[index], img)

        self.presenter.axis = 1
        img = self.presenter.get_image(index)
        npt.assert_equal(test_data[:, index, :], img)

        self.presenter.axis = 2
        img = self.presenter.get_image(index)
        npt.assert_equal(test_data[:, :, index], img)

        # make sure we reset it to default
        self.presenter.axis = 0
        self.assertEqual(self.presenter.axis, 0)

    def test_get_empty_fullpath(self):
        result = self.presenter.get_image_filename(3)
        # we expect an empty string as we have not set the filenames
        self.assertEqual(result, "")

    def test_do_rename_view(self):
        self.presenter.notify(PresenterNotifications.RENAME_WINDOW)
        self.view.update_title_event.assert_called_once()

    def test_do_histogram(self):
        self.presenter.notify(PresenterNotifications.HISTOGRAM)
        self.view.show_histogram_of_current_image.assert_called_once()

    def test_do_new_window_histogram(self):
        self.presenter.notify(PresenterNotifications.NEW_WINDOW_HISTOGRAM)
        self.view.show_histogram_of_current_image.assert_called_once()

    def test_show_error_message_forwarded_to_view(self):
        self.presenter.show_error("test message")
        self.view.show_error_dialog.assert_called_once_with("test message")

    def test_get_image_count_on_axis(self):
        self.assertEquals(
                self.presenter.get_image_count_on_axis(),
                self.test_data.sample.shape[self.presenter.axis])

    def test_scroll_stack(self):
        self.view.current_index = mock.MagicMock(return_value=3)
        self.presenter.do_scroll_stack(2)
        self.view.set_index.assert_called_once_with(5)

    def test_do_scroll_up(self):
        self.view.current_index = mock.MagicMock(return_value=3)
        self.presenter.notify(PresenterNotifications.SCROLL_UP)
        self.view.set_index.assert_called_once_with(4)

    def test_do_scroll_down(self):
        self.view.current_index = mock.MagicMock(return_value=3)
        self.presenter.notify(PresenterNotifications.SCROLL_DOWN)
        self.view.set_index.assert_called_once_with(2)

    def test_summed_image_creation(self):
        test_data = self.test_data.sample

        # No summed image by default
        self.assertEquals(self.presenter.image_mode, ImageMode.STACK)
        self.assertIsNone(self.presenter.summed_image)

        # Stack mode gets image from stack
        img = self.presenter.get_image(0)
        npt.assert_equal(test_data[0], img)

        # Summed image is created when first switching to summed mode
        self.presenter.image_mode = ImageMode.SUM
        self.assertEquals(self.presenter.image_mode, ImageMode.SUM)
        self.assertIsNotNone(self.presenter.summed_image)

        # Summed mode gets summed image
        img = self.presenter.get_image(0)
        npt.assert_equal(self.presenter.summed_image, img)

        # Summed image is not deleted when switching back to stack mode
        self.presenter.image_mode = ImageMode.STACK
        self.assertEquals(self.presenter.image_mode, ImageMode.STACK)
        self.assertIsNotNone(self.presenter.summed_image)

        # Stack mode gets image from stack
        img = self.presenter.get_image(0)
        npt.assert_equal(test_data[0], img)

    def test_summed_mode_disables_stack_scrolling(self):
        # Enable summed mode
        self.presenter.image_mode = ImageMode.SUM
        self.assertEquals(self.presenter.image_mode, ImageMode.SUM)

        # Ensure scroll stack events are not processed
        self.view.current_index = mock.MagicMock(return_value=3)
        self.presenter.notify(PresenterNotifications.SCROLL_UP)
        self.view.set_index.assert_not_called()


if __name__ == '__main__':
    unittest.main()
