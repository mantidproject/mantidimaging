# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
import os
import uuid
from multiprocessing import shared_memory
from typing import List

import psutil
from psutil import NoSuchProcess, AccessDenied

MEM_PREFIX = 'MI'
MEM_DIR_LINUX = '/dev/shm'
CURRENT_PID = psutil.Process().pid


def generate_mi_shared_mem_name() -> str:
    return f'{MEM_PREFIX}_{CURRENT_PID}_{uuid.uuid4()}'


def clear_memory_from_current_process_linux() -> None:
    for mem_name in _get_shared_mem_names_linux():
        if _is_mi_memory_from_current_process(mem_name):
            free_shared_memory([mem_name])


def find_memory_from_previous_process_linux() -> List[str]:
    old_memory = []
    for mem_name in _get_shared_mem_names_linux():
        if _is_safe_to_remove(mem_name):
            old_memory.append(mem_name)
    return old_memory


def free_shared_memory(mem_names: List[str]) -> None:
    for mem_name in mem_names:
        shm = shared_memory.SharedMemory(name=mem_name)
        shm.close()
        shm.unlink()


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


def _get_shared_mem_names_linux() -> List[str]:
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
