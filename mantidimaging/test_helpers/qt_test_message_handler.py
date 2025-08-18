# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from PyQt5 import QtCore


def qt_message_handler(mode, context, message):
    mode_map = {
        QtCore.QtInfoMsg: 'INFO',
        QtCore.QtWarningMsg: 'WARNING',
        QtCore.QtCriticalMsg: 'CRITICAL',
        QtCore.QtFatalMsg: 'FATAL'
    }

    # Get the string label for mode, otherwise default to 'DEBUG'
    mode_str = mode_map.get(mode, 'DEBUG')
    if mode == QtCore.QtWarningMsg and 'propagateSizeHints' in message:
        return
    print(f"qt_message_handler: line: {context.line}, func: {context.function}, file: {context.file}")
    print(f"{mode_str}: {message}\n")
