from __future__ import (absolute_import, division, print_function)
# Remove stripes in sinograms / ring artefacts in reconstructed volume
import helper as h


def methods():
    return [
        'wf', 'wavelet-fourier', 'ti', 'titarenko', 'sf', 'smoothing-filter'
    ]


def execute(data, config):
    if config.stripe_removal_method:
        from recon.tools import importer
        tomopy = importer.do_importing('tomopy')
        if 'wavelet-fourier' == config.post.stripe_removal_method.lower():
            h.pstart(
                "Starting removal of stripes/ring artifacts using the method '{0}'...".
                format(config.stripe_removal_method))

            # data = tomopy.prep.stripe.remove_stripe_fw(data)
            data = iprep.filters.remove_stripes_ring_artifacts(
                data, 'wavelet-fourier')

            h.pstop("Finished removal of stripes/ring artifacts.")

        elif 'titarenko' == config.stripe_removal_method.lower():
            h.pstart(
                "Starting removal of stripes/ring artifacts, using the method '{0}'...".
                format(config.stripe_removal_method))

            data = tomopy.prep.stripe.remove_stripe_ti(data)

            h.pstop("Finished removal of stripes/ring artifacts.")

    return data