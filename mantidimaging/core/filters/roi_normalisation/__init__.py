NAME = 'ROI Normalisation'

from .roi_normalisation import execute, _cli_register  # noqa:F401
from .roi_normalisation_gui import _gui_register  # noqa:F401

del absolute_import, division, print_function  # noqa:F821
