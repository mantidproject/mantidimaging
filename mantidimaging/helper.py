"""
Module for commonly used functions across the modules.
"""

import logging
import os
import sys
import time

from time import gmtime, strftime
from logging import getLogger

import numpy as np

_log_file_handler = None
_log_formatter = None

_time_start = None


def initialise_logging(default_level=logging.DEBUG):
    global _log_formatter
    _log_formatter = logging.Formatter(
            "%(asctime)s [%(name)s] %(levelname)s: %(message)s")

    # Add a very verbose logging level
    logging.addLevelName(5, 'TRACE')

    # Capture all warnings
    logging.captureWarnings(True)

    # Remove default handlers
    root_logger = logging.getLogger()
    root_logger.handlers = []

    # Stdout handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(_log_formatter)
    root_logger.addHandler(console_handler)

    # Default log level
    root_logger.setLevel(default_level)

    # Don't ever print all the debug logging from Qt
    logging.getLogger('PyQt5').setLevel(logging.INFO)


def set_logging_from_func_config(config):
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.getLevelName(config.log_level))

    getLogger(__name__).debug('Log level set to {}'.format(config.log_level))


def check_config_class(config):
    from mantidimaging.core.configs.recon_config import ReconstructionConfig
    assert isinstance(config, ReconstructionConfig), \
        "The provided config is not of type ReconstructionConfig and cannot \
        be used!"


def initialise(config, saver=None):
    root_logger = logging.getLogger()

    set_logging_from_func_config(config.func)

    # File handler
    global _log_file_handler
    if _log_file_handler is not None:
        root_logger.removeLogger(_log_file_handler)

    # Generate log file filename
    output_path = saver.get_output_path()
    if output_path is None:
        # If no output path is provided then output the log in the current
        # working directory with the filename log_DATE.txt
        log_path = '.'
        log_name_prefix = 'log'
    else:
        # If an output path was provided then output the log in the same
        # directory as the output directory with the filename OUTDIR_DATE.txt
        # For example: "-o out" would give the log filename "out_DATE.txt"
        log_path = output_path
        log_name_prefix = output_path
    log_name_suffix = strftime("_%d_%b_%Y_%H_%M_%S", gmtime()) + ".txt"
    log_fullpath = os.path.join(log_path, log_name_prefix + log_name_suffix)
    _log_file_handler = logging.FileHandler(log_fullpath, mode='w')
    _log_file_handler.setFormatter(_log_formatter)
    root_logger.addHandler(_log_file_handler)

    # Start global execution timer
    global _time_start

    if not _time_start:
        _time_start = time.time()

    # Output run log header
    log = logging.getLogger(__name__)

    log.info('Time now (run begin): ' + time.ctime(_time_start))

    alg_hdr = ("\n"
               "--------------------------\n"
               "Tool/Algorithm\n"
               "--------------------------\n")
    alg_hdr += str(config.func)
    log.info(alg_hdr)

    preproc_hdr = ("\n"
                   "--------------------------\n"
                   "Filter parameters\n"
                   "--------------------------\n")
    preproc_hdr += str(config.args)
    log.info(preproc_hdr)

    cmd_hdr = ("\n"
               "--------------------------\n"
               "Command line\n"
               "--------------------------\n")
    cmd_hdr += config.cmd_line
    log.info(cmd_hdr)

    log.debug("Run initialised")


def check_config_integrity(config):
    check_config_class(config)

    if not config.func.output_path:
        logging.getLogger(__name__).warning(
            "No output path specified, no output will be produced!")


def check_data_stack(data, expected_dims=3, expected_class=np.ndarray):
    if data is None:
        raise ValueError("Data is a None type.")

    if isinstance(data, expected_class):
        to_check = data
    else:
        to_check = data.sample

    # the data must be a np array, otherwise most functionality won't work
    if not isinstance(to_check, expected_class):
        raise ValueError(
            "Invalid data type. It is not a Numpy ndarray: {0}".
            format(to_check))

    # the scripts are designed to work with a 3 dimensional dataset
    # in the case of 4 dimensional data, it's typically reduced to 3 dimensions
    # via the aggregate functionality
    if expected_dims != to_check.ndim:
        raise ValueError(
            "Invalid data format. It does not have 3 dimensions. "
            "Shape: {0}".format(to_check.shape))


def run_import_checks(config):
    """
    Run the import checks to notify the user which features are available in
    the execution.
    """
    from mantidimaging.core.parallel import utility as pu

    log = logging.getLogger(__name__)
    if not pu.multiprocessing_available():
        log.info("Multiprocessing not available.")
    else:
        log.info("Running process on {0} cores.".format(config.func.cores))
