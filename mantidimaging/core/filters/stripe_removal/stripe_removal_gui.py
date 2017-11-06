from functools import partial

from . import execute, wavelet_names


def _gui_register(form):
    from mantidimaging.gui.filters_window import add_property_to_form

    # Filter type option
    _, value_filter_type = add_property_to_form(
            'Filter Type', 'list', form=form)

    # Wavelet options
    _, value_wf_level = add_property_to_form(
            'Level', 'int', valid_values=(0, 100), form=form)

    _, value_wf_wname = add_property_to_form(
            'Wavelet Filter', 'list',
            valid_values=wavelet_names(), form=form)

    _, value_wf_sigma = add_property_to_form(
            'Sigma', 'float', 2.0, (0.0, 100.0), form=form)

    # Titarenko options
    _, value_ti_nblock = add_property_to_form(
            'Number of Blocks', 'int', 0, (0, 100), form=form)

    _, value_ti_alpha = add_property_to_form(
            'Alpha', 'float', 1.5, form=form)

    # Smoothing filter options
    _, value_sf_size = add_property_to_form(
            'Size', 'int', 5, (0, 100), form=form)

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

    return (None, None, custom_execute, None)
