from __future__ import absolute_import, division, print_function

# Copyright &copy; 2017-2018 ISIS Rutherford Appleton Laboratory, NScD
# Oak Ridge National Laboratory & European Spallation Source
#
# This file is part of Mantid.
# Mantid is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# Mantid is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Author: Dimitar Tasev, Mantid Development Team
#
# File change history is stored at: <https://github.com/mantidproject/mantid>.
# Code Documentation is available at: <http://doxygen.mantidproject.org>

# packages part of public API, this will give direct access to the packages from
# isis_imaging.<package_name>
from isis_imaging.core import aggregate  # noqa: F401
from isis_imaging.core import algorithms  # noqa: F401
from isis_imaging.core import configs  # noqa: F401
from isis_imaging.core import configurations  # noqa: F401
from isis_imaging.core import convert  # noqa: F401
from isis_imaging.core import filters  # noqa: F401
from isis_imaging.core import io  # noqa: F401
from isis_imaging.core import imopr  # noqa: F401
from isis_imaging.core import parallel  # noqa: F401
from isis_imaging.core import process_list  # noqa: F401
from isis_imaging.core import tools  # noqa: F401

del absolute_import, division, print_function

"""
The gui package is not imported here, because it will pull in all of 
PyQt packages, which we do not want when using only the CLI. This
is both a speedup benefit and we do not have to deal if PyQt is missing 
(like on SCARF) when not using the GUI.
"""