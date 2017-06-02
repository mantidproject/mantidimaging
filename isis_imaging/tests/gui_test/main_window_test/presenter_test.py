from __future__ import absolute_import, division, print_function

import unittest

import mock

from isis_imaging.core.configs.recon_config import ReconstructionConfig
from gui.main_window import mw_presenter, mw_view


class MainWindowPresenterTest(unittest.TestCase):
    def setUp(self):
        # spec_set forbids addings new parameters
        self.view = mock.create_autospec(
            mw_view.ImgpyMainWindowView, spec_set=True)
        self.config = ReconstructionConfig.empty_init()
        self.presenter = mw_presenter.ImgpyMainWindowPresenter(self.view,
                                                               self.config)

    def test_median_filter_clicked(self):
        self.view.set_value = mock.Mock(return_value=None)
        self.presenter.notify(mw_presenter.Notification.MEDIAN_FILTER_CLICKED)
        self.view.set_value.assert_called_once_with(5)


if __name__ == '__main__':
    unittest.main()
