from __future__ import absolute_import, division, print_function

from isis_imaging import helper as h
from isis_imaging.core.tools import importer


def _cli_register(parser):
    parser.add_argument(
        "--stripe-removal-wf",
        nargs='*',
        required=False,
        type=str,
        help="Stripe removal using wavelett-fourier method. "
        "Available parameters:\n"
        "level (default: None, int, optional) "
        "Number of discrete wavelet transform levels.\n"
        "wname (default: 'db5', str, optional) "
        "Type of the wavelet filter. 'haar', 'db5', 'sym5', etc.\n"
        "sigma (default: 2, float, optional) "
        "Damping parameter in Fourier space.\n"
        "pad (default: True, bool, optional) "
        "If True, extend the size of the sinogram by padding with zeros.")

    parser.add_argument(
        "--stripe-removal-ti",
        nargs='*',
        required=False,
        type=str,
        help="Stripe removal using Titarenko's approach. "
        "Available parameters:\n"
        "nblock (default: 0, int, optional) Number of blocks.\n"
        "alpha (default: 1.5, float, optional) Damping factor.")

    parser.add_argument(
        "--stripe-removal-sf",
        nargs='*',
        required=False,
        type=str,
        help="Stripe removal using smoothing-filter method. "
        "Available parameters:\n"
        "size (default:5, int, optional) Size of the smoothing filter.")

    return parser


def _gui_register(dialog):
    # TODO will probably be best to separate into multiple algs
    from isis_imaging.core.algorithms import gui_compile_ui as gcu

    if dialog is None:
        dialog = gcu.execute("gui/ui/alg_dialog.ui")
    return dialog


def methods():
    return [
        'wf', 'wavelet-fourier', 'ti', 'titarenko', 'sf', 'smoothing-filter'
    ]


def execute(data, wf, ti, sf, cores=None, chunksize=None):
    """
    Execute stripe removal filters.
    Multiple filters can be executed, if they are specified on the command line.

    The order for that execution will always be:
        wavelett-fourier, titarenko, smoothing-filter.

    :param data: Sample data which is to be processed. Expected in radiograms

    :param wf: Specify parameters for the wavelett-fourier filter.
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

    :param ti: Specify parameters for the titarenko filter.
               Acceptable keywords are:

                    nblock (default:0, int, optional) Number of blocks.

                    alpha (default: 1.5, int, optional) Damping factor.

    :param sf: Specify parameters for the smoothing-filter.
               Acceptable keywords are:

                    size (default: 5, int, optional)
                        Size of the smoothing filter.

    Example command line:

    isis_imaging -i /some/data --stripe-removal-wf level=1

    isis_imaging -i /some/data --stripe-removal-wf level=3 pad=False

    isis_imaging -i /some/data
                    --stripe-removal-wf level=3 pad=False wname=db5

    isis_imaging -i /some/data
                    --stripe-removal-wf level=3 pad=False wname=db5 sigma=2

    isis_imaging -i /some/data --stripe-removal-ti nblock=3

    isis_imaging -i /some/data --stripe-removal-ti nblock=3 alpha=2

    isis_imaging -i /some/data --stripe-removal-sf size=3
    """
    # get the first one, the rest will be processed
    msg = "Starting removal of stripes/ring artifacts using method '{0}'..."
    if wf:
        h.pstart(msg.format('Wavelett-Fourier'))
        data = _wf(data, wf, cores, chunksize)
        h.pstop("Finished removal of stripes/ring artifacts.")

    elif ti:
        h.pstart(msg.format('Titarenko'))
        data = _ti(data, ti, cores, chunksize)
        h.pstop("Finished removal of stripes/ring artifacts.")

    elif sf:
        h.pstart(msg.format('Smoothing-Filter'))
        data = _sf(data, sf, cores, chunksize)
        h.pstop("Finished removal of stripes/ring artifacts.")

    return data


def _wf(data, params, cores, chunksize):
    tomopy = importer.do_importing('tomopy')
    # creating a dictionary with all possible params for this func
    kwargs = dict(
        level=None,
        wname=u'db5',
        sigma=2,
        pad=True,
        ncore=cores,
        nchunk=chunksize)

    # process the input parameters
    params = dict(map(lambda p: p.split('='), params))

    # dict.get returns a None if the keyword arg is not found
    # this means if the user hasn't passed anything that matches the string
    # then the default is used
    kwargs['level'] = int(
        params.get('level')) if params.get('level') else kwargs['level']
    kwargs['wname'] = str(
        params.get('wname')) if params.get('wname') else kwargs['wname']
    kwargs['sigma'] = int(
        params.get('sigma')) if params.get('sigma') else kwargs['sigma']
    kwargs['pad'] = bool(
        params.get('pad')) if params.get('pad') else kwargs['pad']

    return tomopy.prep.stripe.remove_stripe_fw(data, **kwargs)
    # TODO find where this is from? iprep?
    # data = iprep.filters.remove_stripes_ring_artifacts(
    #     data, 'wavelet-fourier')


def _ti(data, params, cores, chunksize):
    tomopy = importer.do_importing('tomopy')

    # creating a dictionary with all possible params for this func
    kwargs = dict(nblock=0, alpha=1.5, ncore=cores, nchunk=chunksize)
    # process the input parameters
    params = dict(map(lambda p: p.split('='), params))

    # dict.get returns a None if the keyword arg is not found
    # this means if the user hasn't passed anything that matches the string
    # then the default is used
    kwargs['nblock'] = int(
        params.get('nblock')) if params.get('nblock') else kwargs['nblock']
    kwargs['alpha'] = float(
        params.get('alpha')) if params.get('alpha') else kwargs['alpha']

    return tomopy.prep.stripe.remove_stripe_ti(data, **kwargs)


def _sf(data, params, cores, chunksize):
    tomopy = importer.do_importing('tomopy')

    # creating a dictionary with all possible params for this func
    kwargs = dict(size=5, ncore=cores, nchunk=chunksize)
    # process the input parameters
    params = dict(map(lambda p: p.split('='), params))

    # dict.get returns a None if the keyword arg is not found
    # this means if the user hasn't passed anything that matches the string
    # then the default is used
    kwargs['size'] = int(
        params.get('size')) if params.get('size') else kwargs['size']
    return tomopy.prep.stripe.remove_stripe_sf(data, **kwargs)
