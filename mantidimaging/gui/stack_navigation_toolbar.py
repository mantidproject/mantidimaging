from __future__ import absolute_import, division, print_function

from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT


class StackNavigationToolbar(NavigationToolbar2QT):

    toolitems = [t for t in NavigationToolbar2QT.toolitems if
                 t[0] in ('Home', 'Pan', 'Zoom', 'Subplots', 'Save', None)]
