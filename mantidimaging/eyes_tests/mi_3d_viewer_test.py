# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import numpy as np
import pytest
import os
from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication
from mantidimaging.core.data.dataset import Dataset
from mantidimaging.test_helpers.qt_test_helpers import wait_until
from mantidimaging.test_helpers.unit_test_helper import generate_zeroed_images

from mantidimaging.eyes_tests.base_eyes import BaseEyesTest


@pytest.mark.skipif(os.environ.get("CI") == "true",
                    reason="VTK cannot initialise OpenGL on headless Windows CI runners.")
class MI3DViewerTest(BaseEyesTest):

    def _create_3d_object(self, shape=(30, 30, 30), cube_size=12, dtype=np.float32):
        """
        Create a 3D volume containing a cube and a sphere placed side-by-side.
        @param shape: The (Z, Y, X) dimensions of the volume.
        @param cube_size: Side length of the cube in voxels.
        @param dtype: Numpy dtype for the output volume.
        @return: A numpy array encoding the cube and sphere.
        """
        volume = np.zeros(shape, dtype=dtype)
        z_size, y_size, x_size = shape
        z, y, x = np.indices(shape)

        cube_z0 = (z_size - cube_size) // 2
        cube_y0 = (y_size - cube_size) // 2
        cube_x0 = x_size // 4 - cube_size // 2
        volume[cube_z0:cube_z0 + cube_size, cube_y0:cube_y0 + cube_size, cube_x0:cube_x0 + cube_size] = 250

        radius = cube_size / 2
        sphere_cx = cube_x0 + cube_size + radius
        sphere_cy = y_size / 2
        sphere_cz = z_size / 2
        sphere_mask = (x - sphere_cx)**2 + (y - sphere_cy)**2 + (z - sphere_cz)**2 <= radius**2
        volume[sphere_mask] = 250

        return volume

    def _generate_3d_dataset(self) -> Dataset:
        """
        Generate and register a Dataset containing the cube & sphere 3D volume.
        @return: The created Dataset.
        """
        shape = (30, 30, 30)

        volume = self._create_3d_object(shape=shape, cube_size=12)

        sample_stack = generate_zeroed_images(shape=shape, dtype=np.float32)
        sample_stack.data[:] = volume
        sample_stack.name = "3D Cube & Sphere Stack"

        dataset = Dataset(sample=sample_stack)
        self.imaging.presenter.model.add_dataset_to_model(dataset)

        QApplication.sendPostedEvents()

        return dataset

    def test_3d_viewer_opens_without_data(self):
        """
        Verify that the 3D viewer window opens correctly when no data is loaded.
        """
        self.imaging.open_3d_viewer()
        viewer_window = self.imaging.viewer3d

        wait_until(lambda: viewer_window.isVisible(), delay=0.1)

        assert viewer_window.isVisible(), "3D viewer did not open without data."

    def test_3d_viewer_renders_3d_object(self):
        """
        Verify that the 3D viewer correctly renders the generated 3D object.
        """
        self._generate_3d_dataset()

        self.imaging.open_3d_viewer()
        viewer_window = self.imaging.viewer3d

        wait_until(lambda: viewer_window.isVisible(), delay=0.1)

        QTest.keyClick(viewer_window.vtk_widget, Qt.Key_V)
