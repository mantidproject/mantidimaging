# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import json

from PyQt5.QtWidgets import (QWidget, QTreeWidget, QTreeWidgetItem, QDialogButtonBox, QVBoxLayout, QShortcut,
                             QPushButton)
from PyQt5.QtGui import QKeySequence, QGuiApplication

from mantidimaging.core.data import ImageStack
from mantidimaging.core.operation_history import const
from mantidimaging.gui.mvp_base import BaseDialogView


class MetadataDialog(BaseDialogView):
    """
    Dialog used to show a pretty formatted version of the image metadata.
    """

    def __init__(self, parent: QWidget, images: ImageStack):
        super().__init__(parent)

        self.setWindowTitle('Image Metadata')
        self.setSizeGripEnabled(True)
        self.resize(600, 300)

        self.metadata = images.metadata
        main_widget = MetadataDialog.build_metadata_tree(images.metadata)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(self.accept)

        copy_button = QPushButton("Copy")
        buttons.addButton(copy_button, QDialogButtonBox.ActionRole)
        copy_button.clicked.connect(self.copy_metadata_to_clipboard)

        layout = QVBoxLayout()
        layout.addWidget(main_widget)
        layout.addWidget(buttons)
        self.setLayout(layout)

        shortcut = QShortcut(QKeySequence("Ctrl+C"), self)
        shortcut.activated.connect(self.copy_metadata_to_clipboard)

    @staticmethod
    def build_metadata_tree(metadata):
        """
        Builds a QTreeWidget from the 'operation_history' metadata of an image.

        The top level items are operations, and each has any args and/or kwargs as child nodes.
        """
        main_widget = QTreeWidget()
        main_widget.setHeaderLabel("Operation history")
        if len(metadata) != 0:
            for key, value in metadata.items():
                if key == const.OPERATION_HISTORY:
                    MetadataDialog._build_operation_history(main_widget, metadata)
                else:
                    item = QTreeWidgetItem(main_widget)
                    item.setText(0, f"{key}: {str(value)}")
                    main_widget.insertTopLevelItem(0, item)

        return main_widget

    @staticmethod
    def _build_operation_history(main_widget, metadata):
        for i, op in enumerate(metadata[const.OPERATION_HISTORY]):
            operation_item = QTreeWidgetItem(main_widget)
            if const.OPERATION_DISPLAY_NAME in op and op[const.OPERATION_DISPLAY_NAME]:
                operation_item.setText(0, op[const.OPERATION_DISPLAY_NAME])
            else:
                operation_item.setText(0, op[const.OPERATION_NAME])

            main_widget.insertTopLevelItem(i, operation_item)

            if op.get(const.TIMESTAMP, False):
                date_item = QTreeWidgetItem(operation_item)
                date_item.setText(0, f"Date: {op[const.TIMESTAMP]}")

            if op.get(const.OPERATION_KEYWORD_ARGS, False):
                kwargs_list_item = QTreeWidgetItem(operation_item)
                kwargs_list_item.setText(0, "Keyword arguments")
                # Note: Items must be added to the tree before they can expanded.
                # Nodes are added as they are created so these can be expanded by default
                kwargs_list_item.setExpanded(True)
                for kw, val in op[const.OPERATION_KEYWORD_ARGS].items():
                    kwargs_item = QTreeWidgetItem(kwargs_list_item)
                    kwargs_item.setText(0, f"{kw}: {val}")

    def copy_metadata_to_clipboard(self):
        meta_data_as_text = json.dumps(self.metadata, indent=4)
        QGuiApplication.clipboard().setText(meta_data_as_text)
