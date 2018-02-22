NAME = 'Minus Log'

from .minus_log import execute, _cli_register  # noqa:F401
from .minus_log_gui import _gui_register  # noqa:F401

from mantidimaging.core.utility.optional_imports import (  # noqa: F401
        tomopy_available as available)  # noqa:F821
