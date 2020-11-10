# This file is part of Mantid Imaging
#
# Mantid Imaging is a graphical toolkit for performing 3D reconstruction of neutron tomography data.
# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
#
#   Mantid Imaging is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.

import fileinput
import os
import sys

for root, dirs, files in os.walk('.'):
    for line in fileinput.input(
            (os.path.join(root, name) for name in files if name.endswith('.py')),
            inplace=True,
            # backup='.bak' # uncomment this if you want backups
            ):
        if fileinput.isfirstline() and line != "# This file is part of Mantid Imaging\n":
            sys.stdout.write('# This file is part of Mantid Imaging\n#\n# Mantid Imaging is a graphical toolkit for '
                             'performing 3D reconstruction of neutron tomography data.\n# Copyright (C) 2020 ISIS '
                             'Rutherford Appleton Laboratory UKRI\n#\n#   Mantid Imaging is free software: you can '
                             'redistribute it and/or modify\n#   it under the terms of the GNU General Public License '
                             'as published by\n#   the Free Software Foundation, either version 3 of the License, or\n#'
                             '   (at your option) any later version.\n#\n#   This program is distributed in the hope'
                             ' that it will be useful,\n#   but WITHOUT ANY WARRANTY; without even the implied warranty'
                             ' of\n#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the\n#   GNU General '
                             'Public License for more details.\n#\n#   You should have received a copy of the GNU '
                             'General Public License\n#   along with this program.  If not, see '
                             '<https://www.gnu.org/licenses/>.\n')
            sys.stdout.write(line)
        else:
            sys.stdout.write(line)
