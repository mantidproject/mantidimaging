from __future__ import (absolute_import, division, print_function)
# Remove stripes in sinograms / ring artefacts in reconstructed volume
import helper as h


def cli_register(parser):
    parser.add_argument(
        "--pre-stripe-removal",
        nargs='*',
        required=False,
        type=str,
        default='wf',
        choices=methods(),
        help="Default: %(default)s\nStripe removal method and parameters.")


def gui_register(par):
    raise NotImplementedError("GUI doesn't exist yet")


def methods():
    return [
        'wf', 'wavelet-fourier', 'ti', 'titarenko', 'sf', 'smoothing-filter'
    ]


def execute(data, config, cores=None, chunksize=None):
    # get the first one, the rest will be processed
    meth = config.stripe_removal.pop().lower()
    if meth:
        from recon.tools import importer
        tomopy = importer.do_importing('tomopy')

        h.pstart(
            "Starting removal of stripes/ring artifacts using the method '{0}'...".
            format(meth))

        if meth in ['wavelet-fourier', 'wf']:
            _wf(data, config.stripe_removal, cores, chunksize)

        elif meth in ['titarenko', 'ti']:
            _ti(data, config.stripe_removal, cores, chunksize)

        elif meth in ['smoothing-filter', 'sf']:
            _sf(data, config.stripe_removal, cores, chunksize)

        h.pstop("Finished removal of stripes/ring artifacts.")

    return data


def _wf(data, params, cores, chunksize):
    kwargs = dict(
        level=None,
        wname=u'db5',
        sigma=2,
        pad=True,
        ncore=cores,
        nchunk=chunksize)

    data = tomopy.prep.stripe.remove_stripe_fw(data, kwargs)
    # TODO find where this is from? iprep?
    # data = iprep.filters.remove_stripes_ring_artifacts(
    #     data, 'wavelet-fourier')
    return data


def _ti(data, params, cores, chunksize):
    data = tomopy.prep.stripe.remove_stripe_fw(data)


def _sf(data, params, cores, chunksize):
    data = tomopy.prep.stripe.remove_stripe_sf(data)
