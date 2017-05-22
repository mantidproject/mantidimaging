from __future__ import absolute_import, division, print_function

import helper as h

from core.filters import (background_correction, contrast_normalisation,
                          crop_coords, cut_off, gaussian, median_filter,
                          minus_log, outliers, rebin, rotate_stack,
                          stripe_removal, value_scaling)


def execute(config, sample, flat, dark):
    if config.func.reuse_preproc:
        h.tomo_print_warning(
            "Pre-processing steps have been skipped, "
            "because --reuse-preproc or --only-postproc flag has been passed.")
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
    sample = contrast_normalisation.execute(sample, air, cores, chunksize)

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

    return sample, flat, dark
