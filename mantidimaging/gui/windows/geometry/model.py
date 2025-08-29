# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from cil.utilities.display import show_geometry

from mantidimaging.core.data import ImageStack


class GeometryWindowModel:

    def generate_figure(self, stack: ImageStack) -> Figure | None:
        geometry = stack.geometry

        if geometry is None:
            return None

        # Apply dark styling
        plt.style.use("dark_background")
        figure: Figure = show_geometry(geometry, show=False).figure
        figure.set_facecolor("black")

        return figure
