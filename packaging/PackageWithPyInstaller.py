# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# File: packaging/PackageWithPyInstaller.py
import os
import pkgutil
import subprocess
import logging
import sys
from dataclasses import dataclass
from pathlib import Path

import imagecodecs
from PyInstaller.utils.hooks import conda_support, collect_data_files
import PyInstaller.__main__


@dataclass
class DataFilePattern:
    source: str
    destination: str
    description: str = ""

    def collect_files(self, base_path: Path) -> list[tuple[str, str]]:
        """
        Collects files matching the pattern relative to the base path.

        Args:
            base_path (Path): Root path to resolve the source pattern against.

        Returns:
            list[tuple[str, str]]: List of (absolute file path, destination path) tuples.
        """
        resolved_files = list((base_path / self.source).parent.glob((base_path / self.source).name))
        return [(str(f.resolve()), self.destination) for f in resolved_files]


class PackagingPatterns:
    """
    Holds static methods to retrieve all PyInstaller data file patterns.
    """

    @staticmethod
    def get_patterns() -> list[DataFilePattern]:
        return [
            DataFilePattern('../mantidimaging/gui/ui/*.ui', 'mantidimaging/gui/ui/', 'Qt UI files'),
            DataFilePattern('../mantidimaging/gui/ui/images/*', 'mantidimaging/gui/ui/images/', 'UI image resources'),
            DataFilePattern('../mantidimaging/core/gpu/*.cu', 'mantidimaging/core/gpu/', 'CUDA GPU code'),
            DataFilePattern('../mantidimaging/versions.py', 'mantidimaging/', 'Version file'),
            DataFilePattern('../mantidimaging/gui/windows/wizard/*.yml', 'mantidimaging/gui/windows/wizard/',
                            'Wizard YAML files'),
        ]


class DataFileCollector:

    def __init__(self, base_path: Path = Path("../mantidimaging")):
        self.base_path = base_path
        self.patterns = PackagingPatterns.get_patterns()

    def collect_pattern_files(self) -> list[tuple[str, str]]:
        """
        Collects all files matching defined patterns.

        Returns:
            list[tuple[str, str]]: Resolved (source, destination) file pairs for PyInstaller.
        """
        data_files = []
        for pattern in self.patterns:
            files = pattern.collect_files(self.base_path)
            if not files:
                logging.warning(f"No files matched for pattern: {pattern.source}")
            data_files.extend(files)
        return data_files


def create_run_options():
    """
    Creates the full list of PyInstaller options required to build the application.

    Returns:
        list[str]: Arguments to pass to PyInstaller.
    """
    run_options = [
        '../mantidimaging/__main__.py', '--name=MantidImaging', '--additional-hooks-dir=hooks', '--onedir',
        '--icon=../images/mantid_imaging_unstable_64px.ico'
    ]

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
    # COMPAT python 3.10 won't accept a Path: github.com/python/cpython/issues/88227
    for _, ops_module, _ in pkgutil.walk_packages([str(path_to_operations)]):
        # stop non-existent Hidden Imports
        # https://github.com/mantidproject/mantidimaging/issues/2298
        if "test.support" not in ops_module:
            imports.append(f'mantidimaging.core.operations.{ops_module}')

    imports.extend(["imagecodecs." + x for x in imagecodecs._extensions()] + ["imagecodecs._shared"])

    run_options.extend([f'--hidden-import={name}' for name in imports])

    # Adding dynamic libraries would usually be done via a hook, however when we need to collect them for hidden imports
    # the hook doesn't seem to be picked up by PyInstaller, so we do it here instead.
    run_options.extend(add_conda_dynamic_libs('tomopy', 'tomo'))
    run_options.extend(add_conda_dynamic_libs('mkl', 'mkl'))
    run_options.extend(add_conda_dynamic_libs('cupy', 'nvrtc'))
    run_options.extend(add_conda_dynamic_libs('libcurl', 'ssl'))
    run_options.extend(add_conda_dynamic_libs('libcurl', 'crypto'))


def add_missing_submodules(run_options):
    run_options.extend([f'--collect-submodules={name}' for name in ['cupy', 'cupy_backends']])


def add_data_files(run_options):
    """
    Add necessary data files to the PyInstaller build.

    This includes:
    - Running the version script to generate `versions.py`
    - Collecting all relevant static file patterns (e.g. .ui, .yml, images, .cu) using DataFileCollector
    - Collecting additional data files from the 'cupy' package
    - Extending the provided run_options with --add-data arguments for each resolved file pair
    """
    subprocess.check_call(["python", "../conda/make_versions.py", "pyinstaller"])
    collector = DataFileCollector()
    data_files = collector.collect_pattern_files()

    data_files += collect_data_files("cupy")
    run_options.extend([f'--add-data={src}{os.pathsep}{dest}' for src, dest in data_files])


def add_conda_dynamic_libs(module_name, pattern):
    options = []
    binaries = conda_support.collect_dynamic_libs(module_name)
    for src, dest in binaries:
        src_path = Path(src).resolve()
        if pattern in src_path.name:
            options.append(f'--add-binary={src_path}{os.pathsep}{dest}')
    return options


def add_optional_arguments(run_options):
    run_options.extend(['--noconfirm', '--clean'])


def add_exclude_modules(run_options):
    for exclude in ['matplotlib', 'dask', 'pandas', 'PySide6']:
        run_options.extend(['--exclude-module', exclude])


if __name__ == "__main__":
    # PyInstaller imports modules recursively. The structure of our module imports results in the nesting being so deep
    # that it hits Python's stack-limit. PyInstaller suggests increasing the recursion limit to work around this.
    # The default limit is 1000, meaning a recursion error would occur at around 115 nested imports.
    # A limit of 5000 means the error should occur at about 660 nested imports.
    sys.setrecursionlimit(sys.getrecursionlimit() * 5)
    PyInstaller.__main__.run(create_run_options())
