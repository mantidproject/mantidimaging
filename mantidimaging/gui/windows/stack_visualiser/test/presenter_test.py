import unittest

import mock
import numpy.testing as npt

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.gui.windows.stack_visualiser import StackVisualiserPresenter, StackVisualiserView, SVNotification


class StackVisualiserPresenterTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(StackVisualiserPresenterTest, self).__init__(*args, **kwargs)

    @classmethod
    def setUpClass(cls):
        cls.test_data = th.generate_images_class_random_shared_array()

    def setUp(self):
        # mock the view so it has the same methods
        self.view = mock.create_autospec(StackVisualiserView)
        self.presenter = StackVisualiserPresenter(self.view, self.test_data)

    def test_get_image(self):
        index = 3

        test_data = self.test_data.sample

        img = self.presenter.get_image(index)
        npt.assert_equal(test_data[index], img)

    def test_delete_data(self):
        self.presenter.delete_data()
        self.assertIsNone(self.presenter.images, None)

    def test_notify_refresh_image(self):
        self.presenter.notify(SVNotification.REFRESH_IMAGE)
        self.view.show_current_image.assert_called_once_with()


if __name__ == '__main__':
    unittest.main()
