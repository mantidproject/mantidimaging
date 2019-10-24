import unittest

import mock
import numpy as np
from mantidimaging.core.data import Images
from mantidimaging.core.data import const as data_const
from mantidimaging.gui.windows.cor_tilt import CORTiltWindowPresenter, CORTiltWindowView
from mantidimaging.gui.windows.cor_tilt.presenter import Notification as PresNotification
from mantidimaging.gui.windows.stack_visualiser import StackVisualiserPresenter, StackVisualiserView


class CORTiltWindowPresenterTest(unittest.TestCase):
    def setUp(self):
        # Mock view
        self.view = mock.create_autospec(CORTiltWindowView)

        self.presenter = CORTiltWindowPresenter(self.view, None)

        # Mock stack
        self.stack = mock.create_autospec(StackVisualiserView)
        data = Images(sample=np.ndarray(shape=(128, 10, 128), dtype=np.float32))
        self.stack.presenter = StackVisualiserPresenter(self.stack, data)

    def test_data_selected(self):
        self.presenter.set_stack(self.stack)

        self.view.update_image_preview.assert_called_once()

    def test_set_slice_preview_index(self):
        self.presenter.set_stack(self.stack)

        self.presenter.set_preview_slice_idx(5)
        self.assertEquals(self.presenter.model.preview_slice_idx, 5)

    def test_set_projection_preview_index(self):
        self.presenter.set_stack(self.stack)

        self.presenter.set_preview_projection_idx(5)
        self.assertEquals(self.presenter.model.preview_projection_idx, 5)

    def test_do_add_manual_cor_table_row_no_last_result(self):
        self.presenter.model.selected_row = 0
        self.presenter.model.preview_slice_idx = 15
        self.presenter.notify(PresNotification.ADD_NEW_COR_TABLE_ROW)
        self.view.add_cor_table_row.assert_called_once_with(self.presenter.model.selected_row,
                                                            self.presenter.model.preview_slice_idx, 0)

    def test_do_add_manual_cor_table_row_with_last_result_cor(self):
        self.presenter.model.selected_row = 0
        self.presenter.model.preview_slice_idx = 15
        self.presenter.model.last_result = {data_const.COR_TILT_ROTATION_CENTRE: 4141}

        self.presenter.notify(PresNotification.ADD_NEW_COR_TABLE_ROW)
        self.view.add_cor_table_row.assert_called_once_with(
            self.presenter.model.selected_row, self.presenter.model.preview_slice_idx,
            self.presenter.model.last_result[data_const.COR_TILT_ROTATION_CENTRE])
