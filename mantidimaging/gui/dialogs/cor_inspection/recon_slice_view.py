# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from pyqtgraph import GraphicsLayoutWidget

from mantidimaging.gui.dialogs.cor_inspection.types import ImageType
from mantidimaging.gui.widgets.mi_mini_image_view.view import MIMiniImageView

if TYPE_CHECKING:
    from mantidimaging.gui.dialogs.cor_inspection import CORInspectionDialogView  # pragma: no cover


class CompareSlicesView(GraphicsLayoutWidget):

    def __init__(self, parent: 'CORInspectionDialogView'):
        super().__init__(parent)
        self.parent = parent

        self.imageview_less = MIMiniImageView(name="less", parent=parent, recon_mode=True)
        self.imageview_current = MIMiniImageView(name="current", parent=parent, recon_mode=True)
        self.imageview_more = MIMiniImageView(name="more", parent=parent, recon_mode=True)
        self.all_imageviews = [self.imageview_less, self.imageview_current, self.imageview_more]
        MIMiniImageView.set_siblings(self.all_imageviews, axis=True, hist=True)

        self.imageview_less.link_sibling_axis()
        self.imageview_less.link_sibling_histogram()

        self.less_label = self.addLabel("", 0, 0)
        self.current_label = self.addLabel("", 0, 1)
        self.more_label = self.addLabel("", 0, 2)

        sub_layout = self.addLayout(1, 0, colspan=3)
        sub_layout.addItem(self.imageview_less)
        sub_layout.addItem(self.imageview_current)
        sub_layout.addItem(self.imageview_more)

        self.less_sumsq = self.addLabel("", 2, 0)
        self.current_sumsq = self.addLabel("", 2, 1)
        self.more_sumsq = self.addLabel("", 2, 2)

        self.sumsqs = [0, 0, 0]

        # Work around for https://github.com/mantidproject/mantidimaging/issues/565
        self.scene().contextMenu = [item for item in self.scene().contextMenu if "export" not in item.text().lower()]

    def set_image(self, image_type: ImageType, recon_data: np.ndarray, title: str):
        sumsq = np.sum(recon_data**2)
        if image_type == ImageType.LESS:
            self.imageview_less.clear()
            self.imageview_less.setImage(recon_data)
            self.less_label.setText(title)
            self.less_sumsq.setText(f"Sum of SQ: {sumsq:.6f}")
            self.sumsqs[0] = sumsq
        elif image_type == ImageType.CURRENT:
            self.imageview_current.clear()
            self.imageview_current.setImage(recon_data, autoLevels=False)
            self.current_label.setText(title)
            self.current_sumsq.setText(f"Sum of SQ: {sumsq:.6f}")
            self.sumsqs[1] = sumsq
        elif image_type == ImageType.MORE:
            self.imageview_more.clear()
            self.imageview_more.setImage(recon_data)
            self.more_label.setText(title)
            self.more_sumsq.setText(f"Sum of SQ: {sumsq:.6f}")
            self.sumsqs[2] = sumsq

        self.parent.mark_best_recon(self.sumsqs)
