from typing import Optional, List, Union, Tuple

from PyQt5 import Qt
from mantidimaging.core.utility.savu_interop.plugin_list import SAVUPluginListEntry

from .presenter import ProcessListPresenter, Notification


class ProcessListView(Qt.QGroupBox):
    """The view of the process list in the savu filters window.

    A fixed loader and saver plugin are represented by non-interactive widgets.
    Processing plugins are laid out in between, and can be edited, removed, and have their positions changed.
    """
    plugin_change_request = Qt.pyqtSignal()

    def __init__(self, parent):
        super(Qt.QGroupBox, self).__init__("Process List", parent)
        self.setLayout(Qt.QVBoxLayout(self))
        self.processing_plugins_layout = Qt.QVBoxLayout()

        self.layout().addWidget(PluginDisplayWidget(parent=self, pos="First", plugin_name="ImageLoader", fixed=True))
        self.layout().addLayout(self.processing_plugins_layout)
        self.layout().addWidget(PluginDisplayWidget(parent=self, pos="Last", plugin_name="TiffSaver", fixed=True))

        self.presenter: ProcessListPresenter = ProcessListPresenter(self)
        self.order_change_request: Optional[Tuple[int, int]] = None
        self.to_remove: Optional[int] = None
        self.to_edit: Optional[int] = None

        self.plugin_widgets: List[PluginDisplayWidget] = []

    def add_plugin(self, plugin: SAVUPluginListEntry):
        self.presenter.add_plugin(plugin)

    def display_plugin(self, plugin_name: str, fixed=False):
        widget = PluginDisplayWidget(parent=self,
                                     pos=len(self.plugin_entries) + 1,
                                     plugin_name=plugin_name,
                                     fixed=fixed)
        self.processing_plugins_layout.addWidget(widget)
        self.plugin_widgets.append(widget)

        self._correct_display_widget_states()

    def signal_order_change(self, old_index: int, new_index: int):
        self.order_change_request = (old_index, new_index)
        self.presenter.notify(Notification.CHANGE_ORDER)

    def signal_remove_plugin(self, index: int):
        self.to_remove = index
        self.presenter.notify(Notification.REMOVE_PLUGIN)

    def signal_edit_plugin(self, index: int):
        self.to_edit = index
        self.plugin_change_request.emit()

    def swap(self, index_1: int, index_2: int):
        to_move = self.plugin_widgets[index_1]

        self.processing_plugins_layout.removeWidget(to_move)
        self.processing_plugins_layout.insertWidget(index_2, to_move)

        self.plugin_widgets[index_1], self.plugin_widgets[index_2] = \
            self.plugin_widgets[index_2], self.plugin_widgets[index_1]

        self._correct_display_widget_states()

    def remove_plugin(self, index: int):
        to_remove = self.plugin_widgets.pop(index)
        self.processing_plugins_layout.removeWidget(to_remove)
        to_remove.deleteLater()
        self._correct_display_widget_states()

    def _correct_display_widget_states(self):
        """ Sets the correct position label and up/down button states for every plugin display widget."""

        if not self.plugin_widgets:
            return

        for i, widget in enumerate(self.plugin_widgets):
            widget.pos_label.setText(str(i + 1))
            widget.up_button.setEnabled(True)
            widget.down_button.setEnabled(True)
        self.plugin_widgets[0].up_button.setEnabled(False)
        self.plugin_widgets[-1].down_button.setEnabled(False)

    @property
    def plugin_entries(self):
        return self.presenter.model.plugins

    @property
    def plugin_to_edit(self):
        return self.plugin_entries[self.to_edit]

    def save_edited_plugin(self, entry: SAVUPluginListEntry):
        if self.to_edit is None:
            raise RuntimeError("Process list view 'to_edit' was unexpectedly unset.")
        self.presenter.overwrite_plugin(self.to_edit, entry)


class PluginDisplayWidget(Qt.QWidget):
    """ Widget representing a plugin in the process list.

    Each widget is laid out horizontally and consists (in order) of:
     1. A label with the plugins position in the process list
     2. A button with the plugins name. Clicking this makes the parameters of the plugin editable.
     3. Up/Down arrows to change the plugins position in the process list
     4. A remove button.

    All elements except the plugin button are fixed size, taking up as little (horizontal) space as possible.
    The plugin button fills the remaining space, which will be determined by the width of the largest
    name of any plugin in the parent layout.
    """
    def __init__(self, parent: Qt.QWidget, pos: Union[int, str], plugin_name: str, fixed: bool = False):
        super(Qt.QWidget, self).__init__(parent)
        self.setLayout(Qt.QHBoxLayout(self))
        self.pos_label = Qt.QLabel(str(pos))
        self.pos_label.setSizePolicy(Qt.QSizePolicy.Fixed, Qt.QSizePolicy.Maximum)
        self.layout().addWidget(self.pos_label)

        plugin_button = Qt.QPushButton(plugin_name, self)
        build_icon = self.style().standardIcon
        self.up_button = Qt.QPushButton(build_icon(self.style().SP_ArrowUp), None, self)
        self.down_button = Qt.QPushButton(build_icon(self.style().SP_ArrowDown), None, self)
        remove_button = Qt.QPushButton(build_icon(self.style().SP_DialogCancelButton), None, self)
        buttons = [plugin_button, self.up_button, self.down_button, remove_button]

        plugin_button.clicked.connect(lambda: self.parent().signal_edit_plugin(self.index))
        self.up_button.clicked.connect(lambda: self.parent().signal_order_change(self.index, self.index - 1))
        self.down_button.clicked.connect(lambda: self.parent().signal_order_change(self.index, self.index + 1))
        remove_button.clicked.connect(lambda: self.parent().signal_remove_plugin(self.index))

        for btn in buttons:
            btn.setSizePolicy(Qt.QSizePolicy.Fixed, Qt.QSizePolicy.Maximum)
            self.layout().addWidget(btn)
        plugin_button.setSizePolicy(Qt.QSizePolicy.Expanding, Qt.QSizePolicy.Maximum)

        if fixed:
            for btn in buttons:
                btn.setEnabled(False)

    @property
    def index(self):
        return self.parent().plugin_widgets.index(self)
