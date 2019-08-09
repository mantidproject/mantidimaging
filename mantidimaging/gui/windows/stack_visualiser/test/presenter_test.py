import unittest

import numpy.testing as npt
from matplotlib.widgets import Slider
from mock import mock

import mantidimaging.core.testing.unit_test_helper as th
from mantidimaging.gui.windows.stack_visualiser import StackVisualiserPresenter, StackVisualiserView


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

    def test_get_image(self):
        index = 3

        test_data = self.test_data.sample

        img = self.presenter.get_image(index)
        npt.assert_equal(test_data[index], img)


if __name__ == '__main__':
    unittest.main()
