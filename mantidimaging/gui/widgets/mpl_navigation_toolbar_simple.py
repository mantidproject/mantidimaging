# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT


class NavigationToolbarSimple(NavigationToolbar2QT):

    # See [Matplotlib]/lib/matplotlib/backend_bases.py
    toolitems = (
        ('Home', 'Reset original view', 'home', 'home'),
        ('Pan', 'Pan axes with left mouse, zoom with right', 'move', 'pan'),
        ('Zoom', 'Zoom to rectangle', 'zoom_to_rect', 'zoom'),
    )
