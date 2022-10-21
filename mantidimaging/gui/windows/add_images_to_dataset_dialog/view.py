# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from mantidimaging.gui.mvp_base import BaseDialogView


class AddImagesToDatasetDialog(BaseDialogView):
    def __init__(self, parent):
        super().__init__(parent, 'gui/ui/add_to_dataset.ui')
