import unittest

import mock
import numpy.testing as npt

import mantidimaging.test_helpers.unit_test_helper as th
from mantidimaging.gui.windows.stack_visualiser import StackVisualiserPresenter, StackVisualiserView, SVNotification, \
    SVImageMode


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

    def test_notify_refresh_image_normal_image_mode(self):
        self.presenter.image_mode = SVImageMode.NORMAL
        self.presenter.notify(SVNotification.REFRESH_IMAGE)
        self.assertIs(self.view.image,
                      self.presenter.images.sample,
                      "Image should have been set as sample images")

    def test_notify_refresh_image_averaged_image_mode(self):
        self.presenter.image_mode = SVImageMode.AVERAGED
        self.presenter.notify(SVNotification.REFRESH_IMAGE)
        self.assertIs(self.view.image,
                      self.presenter.averaged_image,
                      "Image should have been set as averaged image")


if __name__ == '__main__':
    unittest.main()
