from logging import getLogger

import numpy as np

from mantidimaging import helper as h
from mantidimaging.core.utility.progress_reporting import Progress
from mantidimaging.core.utility.value_scaling import apply_factors


LOG = getLogger(__name__)


def _cli_register(parser):
    return parser


def execute(data,
            flat=None,
            dark=None,
            air_region=None,
            cores=None,
            chunksize=None,
            progress=None):
    """

    :param data: Sample data which is to be processed. Expected in radiograms
    :param flat: Flat (open beam) image to use in normalization
    :param dark: Dark image to use in normalization
    :param air_region: Open beam region used for calcualtion of normalisation
                       factors.
    :param cores: The number of cores that will be used to process the data.
    :param chunksize: The number of chunks that each worker will receive.
    :return: Filtered data (stack of images)
    """
    h.check_data_stack(data)

    def check_corr_stack(name, stack):
        if stack is None:
            raise ValueError('{} image stack is None'.format(name))

        if not isinstance(stack, np.ndarray):
            raise ValueError('{} must be an ndarray'.format(name))

        if stack.ndim != 3:
            raise ValueError('{} must be 3 dimensional'.format(name))

    check_corr_stack('flat', flat)
    check_corr_stack('dark', dark)

    _execute_seq(data.sample, flat, dark, air_region, progress)

    h.check_data_stack(data)

    return data


def _execute_seq(sample,
                 flat=None,
                 dark=None,
                 air_region=None,
                 progress=None):
    progress = Progress.ensure_instance(
            progress, task_name='Background Correction and Normalisation')

    with progress:
        left, top, right, bottom = air_region

        # Calculate sample normalisation factors
        sample_factors = sample[:, top:bottom, left:right].sum(axis=(1, 2))
        np.divide(sample_factors,
                  sample_factors.max(),
                  out=sample_factors)
        np.divide(1.0,
                  sample_factors,
                  out=sample_factors)

        # Calculate flat field normalisation factors
        flat_factors = flat[:, top:bottom, left:right].sum(axis=(1, 2))
        np.divide(flat_factors,
                  flat_factors.max(),
                  out=flat_factors)
        np.divide(1.0,
                  flat_factors,
                  out=flat_factors)

        # Normalise sample
        apply_factors(sample, sample_factors)

        # Normalise flat field
        apply_factors(flat, flat_factors)

        # Average flat field
        average_flat_field = np.average(flat, axis=0)
        LOG.info('Flat field sum: {}'.format(average_flat_field.sum()))

        # Average dark field
        average_dark_field = np.average(dark, axis=0)
        LOG.info('Dark field sum: {}'.format(average_dark_field.sum()))

        # Subtract dark field from sample
        np.subtract(sample,
                    average_dark_field,
                    out=sample)

        # Subtract dark field from flat field
        np.subtract(average_flat_field,
                    average_dark_field,
                    out=average_flat_field)

        # Divide sample by flat field
        average_flat_field[average_flat_field == 0] = 1e-9
        np.true_divide(sample,
                       average_flat_field,
                       out=sample)
