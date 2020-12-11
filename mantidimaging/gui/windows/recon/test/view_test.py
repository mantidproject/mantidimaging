import unittest
from unittest import mock

from mantidimaging.core.utility.data_containers import ScalarCoR, Degrees, Slope
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

    def test_on_row_change(self):
        pass

    def test_check_stack_for_invalid_180_deg_proj(self):
        pass

    @mock.patch("mantidimaging.gui.windows.recon.view.QMessageBox")
    def test_warn_user(self, qmessagebox_mock):
        warning_title = "warning title"
        warning_message = "warning message"
        self.view.warn_user(warning_title, warning_message)
        qmessagebox_mock.warning.assert_called_once_with(self.view, warning_title, warning_message)

    def test_remove_selected_cor(self):
        self.view.tableView = table_view_mock = mock.Mock()
        assert self.view.remove_selected_cor() == table_view_mock.removeSelectedRows.return_value

    def test_clear_cor_table(self):
        self.view.tableView = table_view_mock = mock.Mock()
        assert self.view.clear_cor_table() == table_view_mock.model.return_value.removeAllRows.return_value

    def test_cor_table_model(self):
        pass

    def test_set_results(self):
        cor_val = 20
        tilt_val = 30
        slope_val = 40
        cor = ScalarCoR(cor_val)
        tilt = Degrees(tilt_val)
        slope = Slope(slope_val)

        self.view.image_view = image_view_mock = mock.Mock()
        self.view.set_results(cor, tilt, slope)
        assert self.view.rotation_centre == cor_val
        assert self.view.tilt == tilt_val
        assert self.view.slope == slope_val
        image_view_mock.set_tilt.assert_called_once_with(tilt)
