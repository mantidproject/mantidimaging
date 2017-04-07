from __future__ import absolute_import, division, print_function

import unittest

import mock
from mock import call

from gui.mw import mw_presenter, mw_view_interface
from core.configs.recon_config import ReconstructionConfig


class MainWindowPresenterTest(unittest.TestCase):
    def setUp(self):
        self.view = mock.create_autospec(mw_view_interface.ImgpyMainWindowView)
        self.config = ReconstructionConfig.empty_init()
        self.presenter = mw_presenter.ImgpyMainWindowPresenter(self.view,
                                                               self.config)

    def test_median_filter_clicked(self):
        self.view.set_value = mock.Mock(return_value=None)
        self.presenter.notify(mw_presenter.Notification.MEDIAN_FILTER_CLICKED)
        self.view.set_value.assert_called_once_with(5)


if __name__ == '__main__':
    unittest.main()
