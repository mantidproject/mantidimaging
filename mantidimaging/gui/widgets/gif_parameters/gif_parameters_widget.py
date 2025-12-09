# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QDoubleSpinBox, QPushButton

from mantidimaging.gui.utility.gif_utils import estimate_gif_size


class GifParametersWidget(QDialog):
    """
    Dialog for GIF export parameters: frame step size and Gif duration

    The dialog provides estimated GIF size in MB based on selected parameters.
    The estimation is based on LWZ compression testing with a IMAT00010675 flower dataset.
    """

    def __init__(self, parent, image_stack, optimal_skip: int):
        super().__init__(parent)
        self.setWindowTitle("GIF Parameters")
        self.image_stack = image_stack
        self._build_ui(optimal_skip)

    def _build_ui(self, optimal_skip: int) -> None:
        """Build the UI components"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(12)

        # Frame skip and duration inputs
        inputs_layout = self._create_inputs_layout(optimal_skip)
        main_layout.addLayout(inputs_layout)

        # GIF size estimation label and buttons
        self.size_label = QLabel()
        self.size_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        main_layout.addWidget(self.size_label)
        button_layout = self._create_button_layout()
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)
        self.frame_skip_spinbox.valueChanged.connect(self._update_size_estimate)
        self._update_size_estimate()

    def _create_inputs_layout(self, optimal_skip: int) -> QHBoxLayout:
        """Create frame skip and duration input controls"""
        inputs_layout = QHBoxLayout()
        inputs_layout.setSpacing(30)

        # Frame step size
        frame_skip_layout = QHBoxLayout()
        frame_skip_layout.setSpacing(8)
        frame_skip_label = QLabel("Frame Step:")
        self.frame_skip_spinbox = QSpinBox()
        self.frame_skip_spinbox.setMinimum(1)
        self.frame_skip_spinbox.setMaximum(max(1, self.image_stack.num_projections))
        self.frame_skip_spinbox.setValue(optimal_skip)
        self.frame_skip_spinbox.setMinimumWidth(80)
        self.frame_skip_spinbox.setToolTip("Show every Nth frame (e.g., 2 = show every 2nd frame). "
                                           "Increase to reduce GIF size and frame count.")
        frame_skip_layout.addWidget(frame_skip_label)
        frame_skip_layout.addWidget(self.frame_skip_spinbox)
        inputs_layout.addLayout(frame_skip_layout)

        # Gif duration
        duration_layout = QHBoxLayout()
        duration_layout.setSpacing(8)
        duration_label = QLabel("Duration (sec):")
        self.duration_spinbox = QDoubleSpinBox()
        self.duration_spinbox.setMinimum(0.1)
        self.duration_spinbox.setMaximum(3600.0)
        self.duration_spinbox.setValue(3.0)
        self.duration_spinbox.setDecimals(2)
        self.duration_spinbox.setMinimumWidth(80)
        self.duration_spinbox.setToolTip("Total time in seconds for the complete animation rotation. "
                                         "Shorter = faster animation, longer = slower animation.")
        duration_layout.addWidget(duration_label)
        duration_layout.addWidget(self.duration_spinbox)
        inputs_layout.addLayout(duration_layout)

        inputs_layout.addStretch()
        return inputs_layout

    def _create_button_layout(self) -> QHBoxLayout:
        """Create OK and Cancel buttons"""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        ok_button.setMinimumWidth(120)
        cancel_button.setMinimumWidth(120)
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        return button_layout

    def _update_size_estimate(self) -> None:
        """
        Update the estimated GIF size based on current frame skip spinbox value.

        Displays:
        - Estimated compressed GIF size with current frame skip
        - Full stack size without frame skip
        - Size difference from frame skip to show compression savings
        """
        frame_skip = self.frame_skip_spinbox.value()
        total_frames = self.image_stack.num_projections
        selected_frames = total_frames // frame_skip

        compressed_size_with_skip_mb = estimate_gif_size(selected_frames, self.image_stack.height,
                                                         self.image_stack.width)
        compressed_size_no_skip_mb = estimate_gif_size(total_frames, self.image_stack.height, self.image_stack.width)
        size_reduction_mb = compressed_size_no_skip_mb - compressed_size_with_skip_mb

        size_text = (f"Estimated size: {selected_frames} frames, ~{compressed_size_with_skip_mb:.1f} MB\n"
                     f"Without frame skip: {total_frames} frames, ~{compressed_size_no_skip_mb:.1f} MB\n"
                     f"Size reduction: {size_reduction_mb:.1f} MB")
        self.size_label.setText(size_text)

    def get_frame_skip(self) -> int:
        """Get the selected frame skip value"""
        return self.frame_skip_spinbox.value()

    def get_duration(self) -> float:
        """Get the selected duration value"""
        return self.duration_spinbox.value()
