from __future__ import absolute_import, division, print_function

from logging import getLogger

from mantidimaging.core.filters import (
        background_correction, roi_normalisation, crop_coords, cut_off,
        gaussian, median_filter, minus_log, outliers, rebin, rotate_stack,
        stripe_removal, circular_mask, clip_values, ring_removal)
from mantidimaging.core.utility import value_scaling


def execute(config, sample, flat, dark):
    getLogger(__name__).info("Running the default filtering.")

    if config.func.skip_preproc:
        getLogger(__name__).warning(
            "Pre-processing steps have been skipped, "
            "because --skip-preproc flag has been passed.")
        return sample, flat, dark

    cores = config.func.cores
    chunksize = config.func.chunksize
    roi = config.args.region_of_interest

    # sample = mcp_corrections.execute(sample)
    # if (flat is not None and dark is not None):
    #     flat = mcp_corrections.execute(flat)
    #     dark = mcp_corrections.execute(dark)

    sample, flat, dark = rotate_stack.execute(sample, config.args.rotation,
                                              flat, dark, cores, chunksize)

    air = config.args.air_region
    # we scale up if either a background correction is performed
    # or contrast normalisation (air region)
    if (flat is not None and dark is not None) or air is not None:
        scale_factors = value_scaling.create_factors(sample, roi, cores,
                                                     chunksize)

    sample = background_correction.execute(
        sample, flat, dark, cores=cores, chunksize=chunksize)

    # removes the contrast difference between the stack of images
    sample = roi_normalisation.execute(sample, air, cores, chunksize)

    # scale up the data to a nice int16 range while keeping the effects
    # from the flat/dark and air normalisations
    if (flat is not None and dark is not None) or air is not None:
        sample = value_scaling.apply_factor(sample, scale_factors, cores,
                                            chunksize)

    if flat is not None and dark is not None:
        sample, flat, dark = crop_coords.execute(sample, roi, flat, dark)
    else:
        sample, flat, dark = crop_coords.execute(
            sample, roi)  # flat and dark will be None

    sample = rebin.execute(sample, config.args.rebin, config.args.rebin_mode,
                           cores, chunksize)

    sample = stripe_removal.execute(
        sample, config.args.stripe_removal_wf, config.args.stripe_removal_ti,
        config.args.stripe_removal_sf, cores, chunksize)

    sample = outliers.execute(sample, config.args.outliers,
                              config.args.outliers_radius,
                              config.args.outliers_mode, cores)

    sample = median_filter.execute(sample, config.args.median_size,
                                   config.args.median_mode, cores, chunksize)

    sample = gaussian.execute(sample, config.args.gaussian_size,
                              config.args.gaussian_mode,
                              config.args.gaussian_order, cores, chunksize)

    sample = cut_off.execute(sample, config.args.cut_off)
    # this should be last because the other filters
    # do not expect to work in -log data
    sample = minus_log.execute(sample, config.args.minus_log)

    sample = outliers.execute(sample, config.args.outliers,
                              config.args.outliers_radius,
                              config.args.outliers_mode, cores)

    sample = ring_removal.execute(
        sample, config.args.ring_removal, config.args.ring_removal_x,
        config.args.ring_removal_y, config.args.ring_removal_thresh,
        config.args.ring_removal_thresh_max,
        config.args.ring_removal_thresh_min,
        config.args.ring_removal_theta_min, config.args.ring_removal_rwidth,
        cores, config.func.chunksize)

    sample = circular_mask.execute(sample, config.args.circular_mask,
                                   config.args.circular_mask_val, cores)

    sample = clip_values.execute(sample, config.args.clip_min,
                                 config.args.clip_max,
                                 config.args.clip_min_new_value,
                                 config.args.clip_max_new_value)

    return sample, flat, dark
