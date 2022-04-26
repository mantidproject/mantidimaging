# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

from functools import partial

from mantidimaging.core.operations.base_filter import BaseFilter, FilterGroup
from mantidimaging.core.tools import importer
from mantidimaging.core.utility.progress_reporting import Progress
from mantidimaging.gui.utility.qt_helpers import Type


class StripeRemovalFilter(BaseFilter):
    """Stripe and ring artifact removal operations wrapped from TomoPy.

    Source: https://tomopy.readthedocs.io/en/latest/api/tomopy.prep.stripe.html

    Intended to be used on: Sinograms

    When: If stripes artifacts are present that have not been
    removed with outliers + flat-fielding the projections

    Caution: Horizontal stripes caused by changes in image intensity (pixel values)
    should be fixed by ROI Normalisation instead!
    """
    filter_name = "Stripe Removal"
    link_histograms = True

    @staticmethod
    def filter_func(images, wf=None, ti=None, sf=None, progress=None):
        """
        Execute stripe removal operations.

        Multiple operations can be executed, if they are specified on the command
        line.

        The order for that execution will always be: wavelet-fourier, Titarenko,
        smoothing-filter.

        :param images: Sample data which is to be processed. Expected in radiograms

        :param wf: Specify parameters for the wavelet-fourier filter.
                   Acceptable keywords are:

                        level (default None, type int, optional parameter)
                                Number of discrete wavelet transform levels.

                        wname (default 'db5', type str, optional parameter)
                                Type of the wavelet filter. 'haar', 'db5', 'sym5'.

                        sigma (default 2, type float, optional parameter)
                                Damping parameter in Fourier space.

                        pad (default True, type bool, optional parameter)
                                If True, extend the size of the sinogram by
                                padding with zeros.

        :param ti: Specify parameters for the Titarenko filter.
                   Acceptable keywords are:

                        nblock (default:0, int, optional) Number of blocks.

                        alpha (default: 1.5, int, optional) Damping factor.

        :param sf: Specify parameters for the smoothing-filter.
                   Acceptable keywords are:

                        size (default: 5, int, optional)
                            Size of the smoothing filter.

        :return: Processed data
        """
        progress = Progress.ensure_instance(progress, task_name='Stripe Removal')

        # get the first one, the rest will be processed
        msg = "Starting removal of stripes/ring artifacts using method '{0}'..."

        with progress:
            if wf:
                progress.update(msg=msg.format('Fourier-wavelet'))
                func = partial(_wf, images.data, wf)
            elif sf:
                progress.update(msg=msg.format('Smoothing-Filter'))
                func = partial(_sf, images.data, sf)

            images.data = func()

        return images

    @staticmethod
    def register_gui(form, on_change, view):
        from mantidimaging.gui.utility import add_property_to_form

        label, _ = add_property_to_form("This filter requires sinograms\nto produce a sensible result.",
                                        Type.LABEL,
                                        form=form,
                                        on_change=on_change)
        # Filter type option
        _, value_filter_type = add_property_to_form('Filter Type',
                                                    Type.CHOICE,
                                                    form=form,
                                                    on_change=on_change,
                                                    tooltip="Which filter to use in the operation.")

        # Wavelet options
        _, value_wf_level = add_property_to_form('Level',
                                                 Type.INT,
                                                 default_value=1,
                                                 valid_values=(0, 100),
                                                 form=form,
                                                 on_change=on_change,
                                                 tooltip="Number of discrete wavelet transform levels.")

        _, value_wf_wname = add_property_to_form('Wavelet Filter',
                                                 Type.CHOICE,
                                                 valid_values=wavelet_names(),
                                                 form=form,
                                                 on_change=on_change,
                                                 tooltip="Type of the wavelet filter. 'haar', 'db5', 'sym5'.")

        _, value_wf_sigma = add_property_to_form('Sigma',
                                                 Type.FLOAT,
                                                 2.0, (0.0, 100.0),
                                                 form=form,
                                                 on_change=on_change,
                                                 tooltip="Damping parameter in Fourier space.")

        # Titarenko options
        # _, value_ti_nblock = add_property_to_form('Number of Blocks',
        #                                           Type.INT,
        #                                           0, (0, 100),
        #                                           form=form,
        #                                           on_change=on_change)
        #
        # _, value_ti_alpha = add_property_to_form('Alpha', Type.FLOAT, 1.5, form=form, on_change=on_change)

        # Smoothing filter options
        _, value_sf_size = add_property_to_form('Size',
                                                Type.INT,
                                                5, (0, 100),
                                                form=form,
                                                on_change=on_change,
                                                tooltip="Size of the smoothing filter.")
        # ('titarenko', [value_ti_nblock, value_ti_alpha])
        filters = [('fourier-wavelet', [value_wf_level, value_wf_wname, value_wf_sigma]),
                   ('smoothing-filter', [value_sf_size])]

        def on_filter_type_change(name):
            for f in filters:
                enabled = name == f[0]
                for ui_item in f[1]:
                    ui_item.setEnabled(enabled)
            on_change()

        value_filter_type.addItems([f[0] for f in filters])
        value_filter_type.currentIndexChanged[str].connect(on_filter_type_change)
        on_filter_type_change(value_filter_type.currentText())

        return {
            "value_filter_type": value_filter_type,
            "value_wf_level": value_wf_level,
            "value_wf_wname": value_wf_wname,
            "value_wf_sigma": value_wf_sigma,
            "value_sf_size": value_sf_size,
        }

    @staticmethod
    def execute_wrapper(value_filter_type=None,
                        value_wf_level=None,
                        value_wf_wname=None,
                        value_wf_sigma=None,
                        value_ti_nblock=None,
                        value_ti_alpha=None,
                        value_sf_size=None):
        filter_type = value_filter_type.currentText()
        wf = None
        ti = None
        sf = None

        if filter_type == 'fourier-wavelet':
            wf = {
                'level': value_wf_level.value(),
                'wname': value_wf_wname.currentText(),
                'sigma': value_wf_sigma.value(),
                'pad': False
            }
        elif filter_type == 'titarenko':
            ti = {'nblock': value_ti_nblock.value(), 'alpha': value_ti_alpha.value()}
        elif filter_type == 'smoothing-filter':
            sf = {'size': value_sf_size.value()}

        return partial(StripeRemovalFilter.filter_func, wf=wf, ti=ti, sf=sf)

    @staticmethod
    def group_name() -> FilterGroup:
        return FilterGroup.Advanced


def methods():
    return ['wf', 'fourier-wavelet', 'ti', 'titarenko', 'sf', 'smoothing-filter']


def wavelet_names():
    return ['haar', 'db5', 'sym5']


def _get_params(params):
    if isinstance(params, dict):
        return params
    else:
        return dict(map(lambda p: p.split('='), params))


def _wf(data, params):
    tomopy = importer.do_importing('tomopy')

    # creating a dictionary with all possible params for this func
    kwargs = dict(level=None, wname=u'db5', sigma=2, pad=True)

    # process the input parameters
    params = _get_params(params)

    # dict.get returns a None if the keyword arg is not found
    # this means if the user hasn't passed anything that matches the string
    # then the default is used
    kwargs['level'] = int(params.get('level')) if params.get('level') else kwargs['level']
    kwargs['wname'] = str(params.get('wname')) if params.get('wname') else kwargs['wname']
    kwargs['sigma'] = int(params.get('sigma')) if params.get('sigma') else kwargs['sigma']
    kwargs['pad'] = bool(params.get('pad')) if params.get('pad') else kwargs['pad']

    return tomopy.prep.stripe.remove_stripe_fw(data, **kwargs)


# FIXME takes a huge amount of time even for preview
# so currently disabled. Might not be needed after
# integration of more stripe removal methods from
# def _ti(data, params, cores, chunksize):
#     tomopy = importer.do_importing('tomopy')
#
#     # creating a dictionary with all possible params for this func
#     kwargs = dict(nblock=0, alpha=1.5, ncore=cores, nchunk=chunksize)
#
#     # process the input parameters
#     params = _get_params(params)
#
#     # dict.get returns a None if the keyword arg is not found
#     # this means if the user hasn't passed anything that matches the string
#     # then the default is used
#     kwargs['nblock'] = int(params.get('nblock')) if params.get('nblock') else kwargs['nblock']
#     kwargs['alpha'] = float(params.get('alpha')) if params.get('alpha') else kwargs['alpha']
#
#     return tomopy.prep.stripe.remove_stripe_ti(data, **kwargs)


def _sf(data, params):
    tomopy = importer.do_importing('tomopy')

    # creating a dictionary with all possible params for this func
    kwargs = dict(size=5)

    # process the input parameters
    params = _get_params(params)

    # dict.get returns a None if the keyword arg is not found
    # this means if the user hasn't passed anything that matches the string
    # then the default is used
    kwargs['size'] = int(params.get('size')) if params.get('size') else kwargs['size']
    return tomopy.prep.stripe.remove_stripe_sf(data, **kwargs)
