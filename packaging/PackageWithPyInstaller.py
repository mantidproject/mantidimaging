# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

# Package the application using PyInstaller
#
import os
import pkgutil
import sys
from pathlib import Path
from PyInstaller.utils.hooks import conda_support
import PyInstaller.__main__


def create_run_options():
    run_options = ['../mantidimaging/__main__.py', '--name=MantidImaging', '--additional-hooks-dir=hooks']

    add_hidden_imports(run_options)
    add_missing_submodules(run_options)
    add_data_files(run_options)
    add_optional_arguments(run_options)
    add_exclude_modules(run_options)

    return run_options


def add_hidden_imports(run_options):
    imports = [
        'astra.utils', 'tomopy', 'cupy_backends.cuda.api._runtime_enum', 'cupy_backends.cuda.api._driver_enum',
        'cupy_backends.cuda.stream', 'fastrlock', 'fastrlock.rlock'
    ]

    # Operations modules must be added as hidden imports because most are imported programmatically in MantidImaging
    path_to_operations = Path(__file__).parent.parent.joinpath('mantidimaging/core/operations')
    for _, ops_module, _ in pkgutil.walk_packages([path_to_operations]):
        imports.append(f'mantidimaging.core.operations.{ops_module}')

    run_options.extend([f'--hidden-import={name}' for name in imports])

    # Adding dynamic libraries would usually be done via a hook, however when we need to collect them for hidden imports
    # the hook doesn't seem to be picked up by PyInstaller, so we do it here instead.
    run_options.extend(add_conda_dynamic_libs('tomopy', 'tomo'))
    run_options.extend(add_conda_dynamic_libs('mkl', 'mkl'))


def add_missing_submodules(run_options):
    imports = ['cupy']
    run_options.extend([f'--collect-submodules={name}' for name in imports])


def add_data_files(run_options):
    # Each tuple in the list should give the location of the data files to copy and the destination to copy them to in
    # the package
    data_files = [('../mantidimaging/gui/ui/*.ui', 'mantidimaging/gui/ui/'),
                  ('../mantidimaging/gui/ui/images/*', 'mantidimaging/gui/ui/images/'),
                  ('../mantidimaging/gui/windows/wizard/*.yml', 'mantidimaging/gui/windows/wizard/')]

    run_options.extend([f'--add-data={src}{os.pathsep}{dest}' for src, dest in data_files])


def add_conda_dynamic_libs(module_name, pattern):
    options = []
    binaries = conda_support.collect_dynamic_libs(module_name)
    for src, dest in binaries:
        if pattern in Path(src).name:
            options.append(f'--add-binary={src}{os.pathsep}{dest}')

    return options


def add_optional_arguments(run_options):
    optional_args = ['--noconfirm', '--clean']
    run_options.extend(optional_args)


def add_exclude_modules(run_options):
    excludes = ['matplotlib', 'dask', 'pandas']
    for exclude in excludes:
        run_options.extend(['--exclude-module', exclude])


if __name__ == "__main__":
    # PyInstaller imports modules recursively. The structure of our module imports results in the nesting being so deep
    # that it hits Python's stack-limit. PyInstaller suggests increasing the recursion limit to work around this.
    # The default limit is 1000, meaning a recursion error would occur at around 115 nested imports.
    # A limit of 5000 means the error should occur at about 660 nested imports.
    sys.setrecursionlimit(sys.getrecursionlimit() * 5)

    PyInstaller.__main__.run(create_run_options())
