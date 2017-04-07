from __future__ import absolute_import, division, print_function

import numpy as np

import helper as h
from core.filters import (
    circular_mask, crop_coords, cut_off, gaussian, median_filter, minus_log,
    normalise_by_air_region, normalise_by_flat_dark, outliers, rebin,
    ring_removal, rotate_stack, stripe_removal, value_scaling)
from core.imgdata import loader
from core.imgdata import saver
from core.tools import importer
from readme import Readme


def execute(config):
    """
    Run the whole reconstruction. The steps in the process are:
        - load the data
        - do pre_processing on the data
        - (optional) save out pre_processing images
        - do the reconstruction with the appropriate tool
        - save out reconstruction images

    The configuration for pre_processing and reconstruction are read from 
    the config parameter.

    :param config: A ReconstructionConfig with all the necessary parameters to
                   run a reconstruction.
    :param cmd_line: The full command line text if running from the CLI.
    """

    saver_class = saver.Saver(config)

    h.initialise(config, saver_class)
    h.run_import_checks(config)
    h.check_config_integrity(config)

    # import early to check if tool is available
    tool = importer.timed_import(config)

    # create directory, or throw if not empty and no --overwrite-all
    # we get the output path from the saver, because
    # that expands variables and gets the absolute path
    saver.make_dirs_if_needed(saver_class.get_output_path(),
                              saver_class._overwrite_all)

    readme = Readme(config, saver_class)
    readme.begin(config.cmd_line, config)
    h.set_readme(readme)

    sample, flat, dark = loader.load_data(config)

    sample, flat, dark = pre_processing(config, sample, flat, dark)

    # Save pre-proc images, print inside
    saver_class.save_preproc_images(sample)
    if config.func.only_preproc is True:
        h.tomo_print_note("Only pre-processing run, exiting.")
        readme.end()
        return sample

    if not config.func.only_postproc:
        sample = tool.run_reconstruct(sample, config)
    else:
        h.tomo_print_note("Only post-processing run, skipping reconstruction.")

    sample = post_processing(config, sample)

    # TODO only for testing purposes
    # this seems to crop out most of the noise from the reconstructions
    # but it might crop out data too!
    np.clip(sample, 1e-9, 5, sample)

    saver_class.save_recon_output(sample)
    readme.end()
    return sample


def pre_processing(config, sample, flat, dark):
    if config.func.reuse_preproc:
        h.tomo_print_warning(
            "Pre-processing steps have been skipped, "
            "because --reuse-preproc or --only-postproc flag has been passed.")
        return sample, flat, dark

    cores = config.func.cores
    chunksize = config.func.chunksize
    roi = config.args.region_of_interest
    sample, flat, dark = rotate_stack.execute(sample, config.args.rotation,
                                              flat, dark, cores, chunksize)

    air = config.args.air_region
    if (flat is not None and dark is not None) or air is not None:
        scale_factors = value_scaling.create_factors(sample, roi, cores,
                                                     chunksize)

    sample = normalise_by_flat_dark.execute(sample, flat, dark, cores,
                                            chunksize)

    # removes the contrast difference between the stack of images
    sample = normalise_by_air_region.execute(sample, air, cores, chunksize)

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


def post_processing(config, recon_data):
    if config.func.no_postproc:
        h.tomo_print_warning(
            "Post-processing steps have been skipped, because "
            "--no-postproc flag has been passed.")
        return recon_data

    cores = config.func.cores

    recon_data = outliers.execute(recon_data, config.args.outliers_threshold,
                                  config.args.outliers_radius, cores)

    recon_data = ring_removal.execute(
        recon_data, config.args.ring_removal,
        config.args.ring_removal_center_x, config.args.ring_removal_center_y,
        config.args.ring_removal_thresh, config.args.ring_removal_thresh_max,
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

    return recon_data
