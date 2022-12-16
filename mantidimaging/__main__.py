#!/usr/bin/env python
# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

if __name__ == '__main__':
    from multiprocessing import freeze_support
    # freeze_support adds support for multiprocessing when the application has been frozen to produce a Windows
    # executable. It is only required for Windows and will have no effect when invoked on any other OS.
    # It will also have no effect when the script is run normally by the Python interpreter.
    freeze_support()

    from mantidimaging import main
    main.main()
