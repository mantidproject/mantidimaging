from PyQt5 import Qt

from .presenter import ProcessListPresenter, Notification


class ProcessListView(Qt.QGroupBox):
    def __init__(self, parent):
        super(Qt.QGroupBox, self).__init__("Process List", parent)
        self.setLayout(Qt.QVBoxLayout(self))
        self.processing_plugins_layout = Qt.QVBoxLayout()

        self.layout().addWidget(
            PluginDisplayWidget(parent=self, plugin_name="ImageLoader", fixed=True))
        self.layout().addLayout(self.processing_plugins_layout)
        self.layout().addWidget(
            PluginDisplayWidget(parent=self, plugin_name="TiffSaver", fixed=True))

        self.presenter = ProcessListPresenter(self)
        self.order_change_request = None
        self.to_remove = None

        self.plugin_widgets = []

    def add_plugin(self, plugin):
        self.presenter.add_plugin(plugin)

    def display_plugin(self, plugin_name, fixed=False):
        widget = PluginDisplayWidget(parent=self, plugin_name=plugin_name, fixed=fixed)
        self.processing_plugins_layout.addWidget(widget)
        self.plugin_widgets.append(widget)

        self._correct_movement_button_states()

    def _correct_movement_button_states(self):
        for i, widget in enumerate(self.plugin_widgets):
            widget.up_button.setEnabled(True)
            widget.down_button.setEnabled(True)

            if i == 0:
                widget.up_button.setEnabled(False)
            if i == len(self.plugin_widgets) - 1:
                widget.down_button.setEnabled(False)

    def change_order(self, old_index, new_index):
        self.order_change_request = (old_index, new_index)
        self.presenter.notify(Notification.CHANGE_ORDER)

    def signal_remove_plugin(self, index):
        self.to_remove = index
        self.presenter.notify(Notification.REMOVE_PLUGIN)

    def remove_plugin(self, index):
        to_remove = self.plugin_widgets.pop(index)
        self.processing_plugins_layout.removeWidget(to_remove)
        to_remove.deleteLater()
        self._correct_movement_button_states()

    def swap(self, index_1, index_2):
        to_move = self.plugin_widgets[index_1]

        self.processing_plugins_layout.removeWidget(to_move)
        self.processing_plugins_layout.insertWidget(index_2, to_move)

        self.plugin_widgets[index_1], self.plugin_widgets[index_2] = \
            self.plugin_widgets[index_2], self.plugin_widgets[index_1]

        self._correct_movement_button_states()

    @property
    def plugin_entries(self):
        return self.presenter.model.plugins


class PluginDisplayWidget(Qt.QWidget):
    def __init__(self, parent, plugin_name, fixed=False):
        super(Qt.QWidget, self).__init__(parent)
        self.setLayout(Qt.QHBoxLayout(self))

        plugin_button = Qt.QPushButton(plugin_name, self)
        build_icon = self.style().standardIcon
        self.up_button = Qt.QPushButton(build_icon(self.style().SP_ArrowUp), "", self)
        self.down_button = Qt.QPushButton(build_icon(self.style().SP_ArrowDown), "", self)
        remove_button = Qt.QPushButton(build_icon(self.style().SP_DialogCancelButton), "", self)
        buttons = [plugin_button, self.up_button, self.down_button, remove_button]

        self.up_button.clicked.connect(lambda: self.parent().change_order(self.index, self.index - 1))
        self.down_button.clicked.connect(lambda: self.parent().change_order(self.index, self.index + 1))
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
