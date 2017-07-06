from PyQt5 import Qt

# ISIS_IMAGING: Added to compile on runtime
from isis_imaging.core.algorithms import gui_compile_ui


class PlotOptionsDialog(Qt.QDialog):
    def __init__(self, current_config):
        super(PlotOptionsDialog, self).__init__()
        # ISIS_IMAGING: Added to compile on runtime
        gui_compile_ui.execute('gui/ui/plot_options.ui', self)

        if current_config.title is not None:
            self.lneFigureTitle.setText(current_config.title)
        if current_config.xlabel is not None:
            self.lneXAxisLabel.setText(current_config.xlabel)
        if current_config.ylabel is not None:
            self.lneYAxisLabel.setText(current_config.ylabel)
        if None not in current_config.x_range:
            self.lneXMin.setText(str(current_config.x_range[0]))
            self.lneXMax.setText(str(current_config.x_range[1]))
        if None not in current_config.y_range:
            self.lneYMin.setText(str(current_config.y_range[0]))
            self.lneYMax.setText(str(current_config.y_range[1]))
        if None not in current_config.colorbar_range:
            self.lneCMin.setText(str(current_config.colorbar_range[0]))
            self.lneCMax.setText(str(current_config.colorbar_range[1]))
            self.chkXLog.hide()
            self.chkYLog.hide()
        else:
            self.groupBox_4.hide()
        if current_config.logarithmic is not None:
            self.chkLogarithmic.setChecked(current_config.logarithmic)
        if current_config.xlog is not None:
            self.chkXLog.setChecked(current_config.xlog)
        if current_config.ylog is not None:
            self.chkYLog.setChecked(current_config.ylog)

        self._legend_widgets = []
        self.chkShowLegends.setChecked(current_config.legend.visible)
        if current_config.errorbar is None:
            self.chkShowErrorBars.hide()
        else:
            self.chkShowErrorBars.setChecked(current_config.errorbar)
        if not current_config.legend.applicable:
            self.groupBox.hide()
        else:
            self.chkShowLegends.setChecked(current_config.legend.visible)
            for legend in current_config.legend.all_legends():
                legend_widget = LegendSetter(
                    self, legend['text'], legend['handle'], legend['visible'])
                self.verticalLayout.addWidget(legend_widget)
                self._legend_widgets.append(legend_widget)

    @staticmethod
    def get_new_config(current_config):
        dialog = PlotOptionsDialog(current_config)
        dialog_accepted = dialog.exec_()
        if not dialog_accepted:
            return None
        try:
            xmin = float(str(dialog.lneXMin.text()))
            xmax = float(str(dialog.lneXMax.text()))
            x_range = (xmin, xmax)
        except ValueError:
            x_range = (None, None)

        try:
            ymin = float(str(dialog.lneYMin.text()))
            ymax = float(str(dialog.lneYMax.text()))
            y_range = (ymin, ymax)
        except ValueError:
            y_range = (None, None)

        try:
            cmin = float(str(dialog.lneCMin.text()))
            cmax = float(str(dialog.lneCMax.text()))
            colorbar_range = (cmin, cmax)
        except ValueError:
            colorbar_range = (None, None)

        logarithmic = dialog.chkLogarithmic.isChecked()
        legends = LegendDescriptor(visible=dialog.chkShowLegends.isChecked(),
                                   applicable=dialog.groupBox.isHidden())
        for legend_widget in dialog._legend_widgets:
            legends.set_legend_text(handle=legend_widget.handle,
                                    text=legend_widget.get_text(),
                                    visible=legend_widget.is_visible())

        return PlotConfig(title=dialog.lneFigureTitle.text(),
                          xlabel=dialog.lneXAxisLabel.text(),
                          ylabel=dialog.lneYAxisLabel.text(),
                          legend=legends,
                          errorbar=dialog.chkShowErrorBars.isChecked(),
                          x_range=x_range, xlog=dialog.chkXLog.isChecked(),
                          y_range=y_range, ylog=dialog.chkYLog.isChecked(),
                          colorbar_range=colorbar_range,
                          logarithmic=logarithmic)


class LegendSetter(Qt.QWidget):
    """This is a widget that consists of a checkbox and a lineEdit that will control exactly one legend entry

    This widget has a concrete reference to the artist and modifies it"""

    def __init__(self, parent, text, handle, is_enabled):
        super(LegendSetter, self).__init__(parent)
        self.isEnabled = Qt.QCheckBox(self)
        self.isEnabled.setChecked(is_enabled)
        self.legendText = Qt.QLineEdit(self)
        self.legendText.setText(text)
        self.handle = handle
        layout = Qt.QHBoxLayout(self)
        layout.addWidget(self.isEnabled)
        layout.addWidget(self.legendText)

    def is_visible(self):
        return self.isEnabled.checkState()

    def get_text(self):
        return str(self.legendText.text())


class LegendDescriptor(object):
    """This is a class that describes the legends on a plot"""

    def __init__(self, visible=False, applicable=True, handles=None):
        self.visible = visible
        self.applicable = applicable
        if handles:
            self.handles = list(handles)
        else:
            self.handles = []
        self._labels = {}

    def all_legends(self):
        """
        An iterator which yields a dictionary description of legends containing the handle, text and if visible or not
        """
        for handle in self.handles:
            yield self.get_legend_descriptor(handle)

    def set_legend_text(self, handle, text, visible=True):
        if handle not in self.handles:
            self.handles.append(handle)
        if not visible:
            text = '_' + text
        self._labels[handle] = text

    def get_legend_descriptor(self, handle):
        if handle in self._labels.keys():
            # If a new value has been set for a handle return that
            label = self._labels[handle]
        else:
            label = handle.get_label()   # Else get the value from the plot
        if label.startswith('_'):
            x = {'text': label[1:], 'visible': False, 'handle': handle}
        else:
            x = {'text': label, 'visible': True, 'handle': handle}
        return x

    def get_legend_text(self, handle):
        if handle in self._labels.keys():
            return self._labels[handle]
        return handle.get_label()


class PlotConfig(object):
    def __init__(self, **kwargs):
        # Define default values for all options
        self.title = None
        self.xlabel = None
        self.ylabel = None
        self.xlog = None
        self.ylog = None
        self.legend = LegendDescriptor()
        self.errorbar = None
        self.x_range = None
        self.y_range = None
        self.colorbar_range = None
        self.logarithmic = None
        # Populates fields from keyword arguments
        for (argname, value) in kwargs.items():
            if value is not None:
                setattr(self, argname, value)

    @property
    def title(self):
        if self._title is not None:
            return self._title
        return ""

    @title.setter
    def title(self, value):
        if value is None:
            self._title = None
        else:
            try:
                self._title = str(value)
            except ValueError:
                raise ValueError(
                    "Plot title must be a string or castable to string")

    @property
    def xlabel(self):
        if self._xlabel is not None:
            return self._xlabel
        return ""

    @xlabel.setter
    def xlabel(self, value):
        if value is None:
            self._xlabel = None
        else:
            try:
                self._xlabel = str(value)
            except ValueError:
                raise ValueError(
                    "Plot xlabel must be a string or castable to string")

    @property
    def ylabel(self):
        if self._ylabel is not None:
            return self._ylabel
        return ""

    @ylabel.setter
    def ylabel(self, value):
        if value is None:
            self._ylabel = None
        else:
            try:
                self._ylabel = str(value)
            except ValueError:
                raise ValueError(
                    "Plot ylabel must be a string or castable to string")
