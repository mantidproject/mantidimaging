# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from multiprocessing.managers import SharedMemoryManager

memory_manager = SharedMemoryManager()


def start_memory_manager():
    memory_manager.start()


def shutdown_memory_manager():
    memory_manager.shutdown()


def reset_memory_manager():
    global memory_manager
    memory_manager = SharedMemoryManager()
