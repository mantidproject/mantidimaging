# Copyright (C) 2024 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import time
from multiprocessing import get_context
import os
import uuid
from logging import getLogger
from typing import TYPE_CHECKING

import psutil
from psutil import NoSuchProcess, AccessDenied

from mantidimaging.core.operations.loader import load_filter_packages

if TYPE_CHECKING:
    from multiprocessing.pool import Pool

MEM_PREFIX = 'MI'
MEM_DIR_LINUX = '/dev/shm'
CURRENT_PID = psutil.Process().pid

LOG = getLogger(__name__)
perf_logger = getLogger("perf." + __name__)

cores: int = 1
pool: Pool | None = None


def create_and_start_pool(process_count: int) -> None:
    t0 = time.monotonic()
    context = get_context('spawn')
    global cores
    if process_count == 0:
        cores = context.cpu_count()
    else:
        cores = process_count
    global pool
    LOG.info(f'Creating process pool with {cores} processes')
    pool = context.Pool(cores, initializer=worker_setup)

    if perf_logger.isEnabledFor(1):
        perf_logger.info(f"Process pool started in {time.monotonic() - t0}")


def worker_setup():
    # Required to import modules for running operations
    load_filter_packages()


def end_pool():
    if pool:
        pool.close()
        pool.terminate()


def generate_mi_shared_mem_name() -> str:
    return f'{MEM_PREFIX}_{CURRENT_PID}_{uuid.uuid4()}'


def clear_memory_from_current_process_linux() -> None:
    for mem_name in _get_shared_mem_names_linux():
        if _is_mi_memory_from_current_process(mem_name):
            free_shared_memory_linux([mem_name])


def find_memory_from_previous_process_linux() -> list[str]:
    old_memory = []
    for mem_name in _get_shared_mem_names_linux():
        if _is_safe_to_remove(mem_name):
            old_memory.append(mem_name)
    return old_memory


def free_shared_memory_linux(mem_names: list[str]) -> None:
    for mem_name in mem_names:
        os.remove(f'{MEM_DIR_LINUX}/{mem_name}')


def _is_safe_to_remove(mem_name: str) -> bool:
    process_start = psutil.Process().create_time()
    if _is_mi_shared_mem(mem_name) and os.path.getmtime(f'{MEM_DIR_LINUX}/{mem_name}') < process_start:
        try:
            pid = int(mem_name.split('_')[1])
            _lookup_process(pid)
        except NoSuchProcess:
            # The process that owns the memory has ended
            return True
        except AccessDenied:
            # The process that owns the memory still exists
            return False
    return False


def _get_shared_mem_names_linux() -> list[str]:
    return os.listdir(MEM_DIR_LINUX)


def _lookup_process(pid) -> None:
    psutil.Process(pid)


def _is_mi_shared_mem(mem_name: str) -> bool:
    split_name = mem_name.split('_')

    try:
        int(split_name[1])
    except (IndexError, ValueError):
        return False

    return len(split_name) == 3 and split_name[0] == MEM_PREFIX


def _is_mi_memory_from_current_process(mem_name: str) -> bool:
    return _is_mi_shared_mem(mem_name) and int(mem_name.split('_')[1]) == CURRENT_PID
