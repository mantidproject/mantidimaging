NAME = 'Remove Outliers'

from .outliers import execute, modes, _cli_register  # noqa:F401
from .outliers_gui import _gui_register  # noqa: F401

from mantidimaging.core.utility.optional_imports import (  # noqa: F401
        tomopy_available as available)  # noqa:F821
