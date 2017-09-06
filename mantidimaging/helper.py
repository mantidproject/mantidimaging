from __future__ import (absolute_import, division, print_function)

import logging
import os
import sys
import time
from time import gmtime, strftime

import numpy as np

"""
Class for commonly used functions across the modules
"""

_log_file_handler = None
_log_formatter = None

_time_start = None

_whole_exec_timer = None
_timer_running = False
_timer_start = None

_progress_bar = None


def initialise_logging():
    global _log_formatter
    _log_formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

    root_logger = logging.getLogger()
    root_logger.handlers = []

    # Stdout handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(_log_formatter)
    root_logger.addHandler(console_handler)

    # Default log level
    root_logger.setLevel(logging.DEBUG)

    logging.getLogger(__name__).debug("Logging initialised")


def check_config_class(config):
    from mantidimaging.core.configs.recon_config import ReconstructionConfig
    assert isinstance(
        config, ReconstructionConfig
    ), "The provided config is not of type ReconstructionConfig and cannot be used!"


def initialise(config, saver=None):
    root_logger = logging.getLogger()

    # File handler
    global _log_file_handler
    if _log_file_handler is not None:
        root_logger.removeLogger(_log_file_handler)

    output_path = saver.get_output_path()
    log_name_prefix = output_path if output_path is not None else "log"
    log_name_suffix = strftime("_%d_%b_%Y_%H_%M_%S", gmtime()) + ".txt"
    log_fullpath = os.path.join(output_path, log_name_prefix + log_name_suffix)
    _log_file_handler = logging.FileHandler(log_fullpath, mode='w')
    _log_file_handler.setFormatter(_log_formatter)
    root_logger.addHandler(_log_file_handler)

    # Log level
    # config.func.verbosity

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
        to_check = data.get_sample()

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


def debug_print_memory_usage_linux(message=""):
    try:
        # Windows doesn't seem to have resource package, so this will
        # silently fail
        import resource as res
        print(" >> Memory usage", res.getrusage(res.RUSAGE_SELF).ru_maxrss,
              "KB, ", int(res.getrusage(res.RUSAGE_SELF).ru_maxrss) / 1024,
              "MB", message)
    except ImportError:
        res = None
        pass


def progress_available():
    try:
        from tqdm import tqdm
        return tqdm
    except ImportError:
        logging.getLogger(__name__).info(
                "Progress bar library TQDM not available. "
                "To install locally please use pip install tqdm. "
                "Falling back to ASCII progress bar.")


def run_import_checks(config):
    """
    Run the import checks to notify the user which features are available in the execution.
    """
    from mantidimaging.core.parallel import utility as pu
    progress_available()

    log = logging.getLogger(__name__)
    if not pu.multiprocessing_available():
        log.info("Multiprocessing not available.")
    else:
        log.info("Running process on {0} cores.".format(config.func.cores))


def get_memory_usage_linux(kb=False, mb=False):
    """
    :param kb: Return the value in Kilobytes
    :param mb: Return the value in Megabytes
    """
    try:
        # Windows doesn't seem to have resource package, so this will
        # silently fail
        import resource as res
    except ImportError:
        return " <not available on Windows> "

    tuple_to_return = tuple()  # start with empty tuple
    if kb:
        tuple_to_return += (int(res.getrusage(res.RUSAGE_SELF).ru_maxrss),)

    if mb:
        tuple_to_return += (int(res.getrusage(res.RUSAGE_SELF).ru_maxrss) /
                            1024,)
    return tuple_to_return


def get_memory_usage_linux_str():

    memory_in_kbs, memory_in_mbs = get_memory_usage_linux(kb=True, mb=True)
    # handle caching
    memory_string = "{0} KB, {1} MB".format(memory_in_kbs, memory_in_mbs)

    # use an attribute to this function only, instead a global variable visible outside
    if not hasattr(get_memory_usage_linux_str, 'last_memory_cache'):
        get_memory_usage_linux_str.last_memory_cache = memory_in_kbs
    else:
        # get memory difference in Megabytes
        delta_memory = (
            memory_in_kbs - get_memory_usage_linux_str.last_memory_cache) / 1024

        # remove cached memory, del removes the reference so that hasattr will work correctly
        del get_memory_usage_linux_str.last_memory_cache
        memory_string += ". Memory change: {0} MB".format(delta_memory)

    return memory_string


def pstart(message):
    """
    Print the message and start the execution timer.

    :param message: Message to be printed
    """
    global _timer_running
    global _timer_start

    if not _timer_running:
        _timer_running = True

    _timer_start = time.time()

    log = logging.getLogger(__name__)

    log.info(message)
    log.debug("Memory usage before execution: " + get_memory_usage_linux_str())


def pstop(message):
    """
    Print the message and stop the execution timer.

    :param message: Message to be printed
    """
    global _timer_running

    if not _timer_running:
        raise ValueError("helper.pstart(...) was not called previously!")

    _timer_running = False

    log = logging.getLogger(__name__)

    timer_string = str(time.time() - _timer_start)
    log.info(str(message) + " Elapsed time: " + timer_string + " sec.")

    log.debug("Memory usage after execution: " + get_memory_usage_linux_str())


def total_execution_timer(message="Total execution time was "):
    """
    This will ONLY be used to time the WHOLE execution time.
    The first call to this will be in tomo_reconstruct.py and it will start it.
    The last call will be at the end of find_center or do_recon.
    """
    global _whole_exec_timer

    if not _whole_exec_timer:
        # change type from bool to timer
        _whole_exec_timer = time.time()
    else:
        # change from timer to string
        _whole_exec_timer = str(time.time() - _whole_exec_timer)
        message += _whole_exec_timer + " sec"
        logging.getLogger(__name__).info(message)


def prog_init(total, desc="Progress", ascii=False, unit='images'):
    """
    Initialises and returns the progress bar if the tqdm library is available.

    Otherwise does nothing, and Helper's progress update and close function will also do nothing.

    :param total: the total number of iterations of the progress bar
    :param desc: the label in front of the progress bar
    :param ascii: to use ascii # (True) or utf-8 blocks (False)
    :param unit: the unit for loading. Default is 'images'
    """
    global _progress_bar
    if logging.getLogger(__name__).isEnabledFor(logging.INFO):
        try:
            from tqdm import tqdm
            if _progress_bar:
                raise ValueError(
                    "Timer was not closed previously. Please do prog_close()!")
            _progress_bar = tqdm(
                total=total, desc=desc, ascii=ascii, unit=unit)
        except ImportError:
            try:
                from custom_timer import CustomTimer
                _progress_bar = CustomTimer(total, desc)
            except ImportError:
                _progress_bar = None


def prog_update(value=1):
    """
    This function will print a simple ascii bar if tqdm is not present.
    """
    global _progress_bar
    if _progress_bar:
        _progress_bar.update(value)


def prog_close():
    """
    This function will do nothing if the tqdm library is not present.
    """
    global _progress_bar
    if _progress_bar:
        _progress_bar.close()

    _progress_bar = None


def output_log_footers():
    """
    """
    global _time_start
    if _time_start is not None:
        logging.getLogger(__name__).info(
                "Total execution time:" + str(time.time() - _time_start))
    _time_start = None
