from __future__ import absolute_import, division, print_function

from isis_imaging import helper as h
from isis_imaging.core.filters import (circular_mask, clip_values, gaussian, median_filter,
                          outliers, ring_removal)


def execute(config, recon_data):
    if config.func.no_postproc:
        h.tomo_print_warning(
            "Post-processing steps have been skipped, because "
            "--no-postproc flag has been passed.")
        return recon_data

    cores = config.func.cores

    recon_data = outliers.execute(recon_data, config.args.outliers,
                                  config.args.outliers_radius,
                                  config.args.outliers_mode, cores)

    recon_data = ring_removal.execute(
        recon_data, config.args.ring_removal, config.args.ring_removal_x,
        config.args.ring_removal_y, config.args.ring_removal_thresh,
        config.args.ring_removal_thresh_max,
        config.args.ring_removal_thresh_min,
        config.args.ring_removal_theta_min, config.args.ring_removal_rwidth,
        cores, config.func.chunksize)

    recon_data = median_filter.execute(recon_data, config.args.median_size,
                                       config.args.median_mode, cores,
                                       config.func.chunksize)

    recon_data = gaussian.execute(
        recon_data, config.args.gaussian_size, config.args.gaussian_mode,
        config.args.gaussian_order, cores, config.func.chunksize)

    recon_data = circular_mask.execute(recon_data, config.args.circular_mask,
                                       config.args.circular_mask_val, cores)

    recon_data = clip_values.execute(recon_data, config.args.clip_min,
                                     config.args.clip_max)

    return recon_data
