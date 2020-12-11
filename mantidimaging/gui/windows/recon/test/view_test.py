import unittest
from unittest import mock

from mantidimaging.gui.windows.main import MainWindowView
from mantidimaging.gui.windows.recon import ReconstructWindowView
from mantidimaging.test_helpers import start_qapplication

from mantidimaging.core.utility.version_check import versions
versions._use_test_values()


@start_qapplication
class ReconstructWindowViewTest(unittest.TestCase):
    def setUp(self) -> None:
        # mock the view so it has the same methods
        with mock.patch("mantidimaging.gui.windows.main.view.WelcomeScreenPresenter"):
            with mock.patch("mantidimaging.gui.windows.main.view.has_other_shared_arrays", return_value=False):
                self.main_window = MainWindowView()
        self.view = ReconstructWindowView(self.main_window)
        self.view.presenter = self.presenter = mock.MagicMock()

    def test_test(self):
        pass
