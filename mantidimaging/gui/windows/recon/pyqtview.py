from typing import TYPE_CHECKING

from PyQt5.QtWidgets import QAbstractItemView, QWidget, QDoubleSpinBox, QComboBox, QSpinBox
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from mantidimaging.gui.mvp_base import BaseMainWindowView
from mantidimaging.gui.widgets import NavigationToolbarSimple
from mantidimaging.gui.windows.recon.point_table_model import CorTiltPointQtModel, Column
from mantidimaging.gui.windows.recon.presenter import Notification as PresNotification
from mantidimaging.gui.windows.recon.presenter import ReconstructWindowPresenter

if TYPE_CHECKING:
    from mantidimaging.gui.windows.main import MainWindowView  # noqa:F401


class ReconstructWindowView(BaseMainWindowView):
    inputTab: QWidget
    resultTab: QWidget
    reconTab: QWidget

    # part of the Reconstruct tab
    algorithmName: QComboBox
    filterName: QComboBox
    numIter: QSpinBox
    maxProjAngle: QDoubleSpinBox
    resultCor: QDoubleSpinBox
    resultTilt: QDoubleSpinBox

    def __init__(self, main_window: 'MainWindowView', cmap='Greys_r'):
        super().__init__(main_window, 'gui/ui/recon_window.ui')
        self.main_window = main_window
        self.presenter = ReconstructWindowPresenter(self, main_window)

        self.stackSelector.stack_selected_uuid.connect(self.presenter.set_stack_uuid)

        # Handle preview image selection
        self.previewProjectionIndex.valueChanged[int].connect(self.presenter.set_preview_projection_idx)
        self.previewSliceIndex.valueChanged[int].connect(self.presenter.set_preview_slice_idx)

        # Handle calculation parameters
        self.projectionCountReset.clicked.connect(self.reset_projection_count)
    @property
    def slice_count(self):
        """
        The number of slices/sinograms the user has selected for automatic
        COR/Tilt finding.
        """
        return self.sliceCount.value()

    @property
    def projection_count(self):
        """
        The number of projections the user has selected for automatic COR/Tilt
        finding.
        """
        return self.projectionCount.value()

    @property
    def rotation_centre(self):
        return self.resultCor.value()

    @rotation_centre.setter
    def rotation_centre(self, value):
        self.resultCor.setValue(value)

    @property
    def tilt(self):
        return self.resultTilt.value()

    @tilt.setter
    def tilt(self, value):
        self.resultTilt.setValue(value)

    @property
    def max_proj_angle(self):
        return self.maxProjAngle.value()

    @property
    def algorithm_name(self):
        return self.algorithmName.currentText()

    @property
    def filter_name(self):
        return self.filterName.currentText()

    @property
    def num_iter(self):
        return self.numIter.value() if self.numIter.isVisible() else None
