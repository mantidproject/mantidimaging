from functools import partial

from . import execute, wavelet_names, NAME


def _gui_register(main_window):
    from mantidimaging.gui.algorithm_dialog import AlgorithmDialog

    dialog = AlgorithmDialog(main_window)
    dialog.setWindowTitle(NAME)

    # Filter type option
    _, value_filter_type = dialog.add_property('Filter Type', 'list')

    # Wavelet options
    _, value_wf_level = dialog.add_property(
            'Level', 'int', valid_values=(0, 100))
    _, value_wf_wname = dialog.add_property(
            'Wavelet Filter', 'list',
            valid_values=wavelet_names())
    _, value_wf_sigma = dialog.add_property(
            'Sigma', 'float', 2.0, (0.0, 100.0))

    # Titarenko options
    _, value_ti_nblock = dialog.add_property(
            'Number of Blocks', 'int', 0, (0, 100))
    _, value_ti_alpha = dialog.add_property('Alpha', 'float', 1.5)

    # Smoothing filter options
    _, value_sf_size = dialog.add_property('Size', 'int', 5, (0, 100))

    filters = [
            ('wavelet-fourier',
                [value_wf_level, value_wf_wname, value_wf_sigma]),
            ('titarenko',
                [value_ti_nblock, value_ti_alpha]),
            ('smoothing-filter',
                [value_sf_size])
            ]

    def on_filter_type_change(name):
        for f in filters:
            enabled = name == f[0]
            for ui_item in f[1]:
                ui_item.setEnabled(enabled)

    value_filter_type.addItems([f[0] for f in filters])
    value_filter_type.currentIndexChanged[str].connect(on_filter_type_change)
    on_filter_type_change(value_filter_type.currentText())

    def custom_execute():
        filter_type = value_filter_type.currentText()
        wf = None
        ti = None
        sf = None

        if filter_type == 'wavelett-fourier':
            wf = {'level': value_wf_level.value(),
                  'wname': value_wf_wname.currentText(),
                  'sigma': value_wf_sigma.value(),
                  'pad': False}
        elif filter_type == 'titarenko':
            ti = {'nblock': value_ti_nblock.value(),
                  'alpha': value_ti_alpha.value()}
        elif filter_type == 'smoothing-filter':
            sf = {'size': value_sf_size.value()}

        return partial(execute, wf=wf, ti=ti, sf=sf)

    dialog.set_execute(custom_execute)

    return dialog
