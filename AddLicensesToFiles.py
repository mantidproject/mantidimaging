# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import fileinput
import os
import sys

for root, dirs, files in os.walk('.'):
    for line in fileinput.input(
            (os.path.join(root, name) for name in files if name.endswith('.py')),
            inplace=True,
            # backup='.bak' # uncomment this if you want backups
            ):
        if fileinput.isfirstline() and line != "# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI\n":
            sys.stdout.write('# Copyright (C) 2020 ISIS Rutherford Appleton Laboratory UKRI\n# SPDX - License - '
                             'Identifier: GPL-3.0-or-later\n\n')
            sys.stdout.write(line)
        else:
            sys.stdout.write(line)
