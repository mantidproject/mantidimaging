# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from PyQt5 import QtCore, QtWidgets


class ExperimentSetupFormWidget(QtWidgets.QGroupBox):
    """
    A custom Qt widget for setting up experiment properties related to Time of Flight (ToF).

    This widget contains input fields for flight path and time delay.

    Attributes:
        timeDelayLabel: Label for the time delay input field.
        flightPathSpinBox: Spin box for inputting the flight path value.
        flightPathLabel: Label for the flight path input field.
        timeDelaySpinBox: Spin box for inputting the time delay value.

    """

    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(parent)
        self.setupUi()

    def setupUi(self):
        self.setObjectName("experimentSetupGroupBox")

        self.resize(300, 94)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())

        target = self.parent() if self.parent() else self
        target.setSizePolicy(sizePolicy)
        target.setMinimumSize(QtCore.QSize(300, 94))
        target.setContextMenuPolicy(QtCore.Qt.DefaultContextMenu)

        layout = QtWidgets.QGridLayout(self)

        self.flightPathLabel = QtWidgets.QLabel(self)
        self.flightPathLabel.setObjectName("flightPathLabel")
        self.flightPathLabel.setText("Flight path: ")
        layout.addWidget(self.flightPathLabel, 0, 0)

        self.flightPathSpinBox = QtWidgets.QDoubleSpinBox(self)
        self.flightPathSpinBox.setSuffix(" m")
        self.flightPathSpinBox.setMinimum(0)
        self.flightPathSpinBox.setMaximum(1e10)
        self.flightPathSpinBox.setDecimals(3)
        self.flightPathSpinBox.setObjectName("flightPathSpinBox")
        layout.addWidget(self.flightPathSpinBox, 0, 1)

        self.timeDelayLabel = QtWidgets.QLabel(self)
        self.timeDelayLabel.setObjectName("timeDelayLabel")
        self.timeDelayLabel.setText("Time delay: ")
        layout.addWidget(self.timeDelayLabel, 1, 0)

        self.timeDelaySpinBox = QtWidgets.QDoubleSpinBox(self)
        self.timeDelaySpinBox.setSuffix(" \u03BCs")
        self.timeDelaySpinBox.setMaximum(1e10)
        self.timeDelaySpinBox.setDecimals(3)
        self.timeDelaySpinBox.setObjectName("timeDelaySpinBox")
        layout.addWidget(self.timeDelaySpinBox, 1, 1)

        self.setWindowTitle("Time of Flight Properties")
        self.setTitle("Time of Flight Properties")

        QtCore.QMetaObject.connectSlotsByName(self)

    @property
    def flight_path(self) -> float:
        return self.flightPathSpinBox.value()

    @flight_path.setter
    def flight_path(self, value: float) -> None:
        self.flightPathSpinBox.setValue(value)

    @property
    def time_delay(self) -> float:
        return self.timeDelaySpinBox.value()

    @time_delay.setter
    def time_delay(self, value: float):
        self.timeDelaySpinBox.setValue(value)

    def connect_value_changed(self, handler: QtCore.pyqtSlot):
        self.flightPathSpinBox.valueChanged.connect(handler)
        self.timeDelaySpinBox.valueChanged.connect(handler)
