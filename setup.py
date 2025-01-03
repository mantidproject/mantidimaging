#!/usr/bin/env python
# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from __future__ import annotations

import fnmatch
import importlib
import os
import platform
import subprocess
from distutils.core import Command
from collections import defaultdict
from pathlib import Path
import tempfile
import shutil
from importlib.machinery import SourceFileLoader

from setuptools import find_packages, setup

THIS_PATH = os.path.dirname(__file__)

versions = SourceFileLoader('versions', 'mantidimaging/__init__.py').load_module()


class GenerateReleaseNotes(Command):
    description = "Generate release notes"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        spec = importlib.util.spec_from_file_location('release_notes', 'docs/ext/release_notes.py')
        release_notes = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(release_notes)

        print("\nNew Features\n------------")
        for line in release_notes.ReleaseNotes.make_rst("feature"):
            print(line)
        print("\nFixes\n-----")
        for line in release_notes.ReleaseNotes.make_rst("fix"):
            print(line)
        print("\nDeveloper Changes\n-----------------")
        for line in release_notes.ReleaseNotes.make_rst("dev"):
            print(line)


class CompilePyQtUiFiles(Command):
    description = "Compiles any PyQt .ui files found in the source tree"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    @staticmethod
    def compile_single_file(ui_filename):
        from PyQt5 import uic

        py_filename = os.path.splitext(ui_filename)[0] + ".py"
        with open(py_filename, "w") as py_file:
            uic.compileUi(ui_filename, py_file)

    @staticmethod
    def find_ui_files():
        matches = []
        for root, _, filenames in os.walk("./mantidimaging/"):
            for filename in fnmatch.filter(filenames, "*.ui"):
                matches.append(os.path.join(root, filename))
        return matches

    def run(self):
        ui_files = self.find_ui_files()
        for f in ui_files:
            self.compile_single_file(f)


class CreateDeveloperEnvironment(Command):
    description = "Install the dependencies needed to develop Mantid Imaging"
    user_options = [("conda=", None, "path to conda or mamba command")]

    def initialize_options(self):
        mamba_path = shutil.which("mamba")
        conda_path = shutil.which("conda")
        if mamba_path is not None:
            self.conda = mamba_path
        elif conda_path is not None:
            self.conda = conda_path
        else:
            self.conda = None

    def finalize_options(self):
        if self.conda is None:
            raise ValueError("Could not find conda or mamba")

    def count_indent(self, line):
        leading_spaces = len(line) - len(line.lstrip(" "))
        return leading_spaces // 2

    def get_package_depends(self):
        # Parse the metafile manually, do avoid needing a nonstandard library
        meta_file = Path(__file__).parent / "conda" / "meta.yaml"
        with meta_file.open() as meta_file_fh:
            section = []
            parsed_values = defaultdict(list)
            for line in meta_file_fh:
                # ignore templating
                if line.strip() == "" or "{%" in line:
                    continue
                if platform.system() != "Linux" and "[linux]" in line:
                    continue
                if line.strip().endswith(":"):
                    indent = self.count_indent(line)
                    section = section[:indent]
                    section.append(line.strip(" :\n"))
                else:
                    parsed_values[".".join(section)].append(line.strip(" -\n"))
        return parsed_values["requirements.run"]

    def make_environment_file(self, extra_deps):
        dev_env_file = Path(__file__).parent / "environment-dev.yml"
        output_env_file = tempfile.NamedTemporaryFile("wt", delete=False, suffix=".yaml")
        in_dependencies_section = False
        with dev_env_file.open() as dev_env_file_fh:
            for line in dev_env_file_fh:
                if line.startswith("dependencies:"):
                    in_dependencies_section = True

                if in_dependencies_section and line.strip().startswith("- mantidimaging"):
                    for extra_dep in extra_deps:
                        output_env_file.write(f"  - {extra_dep}\n")
                else:
                    output_env_file.write(line)
        output_env_file.close()
        print("Created environment file:", output_env_file.name)
        return output_env_file.name

    def run(self):
        existing_envs_output = subprocess.check_output([self.conda, "env", "list"], encoding="utf8")
        if any(line.startswith("mantidimaging-dev ") for line in existing_envs_output.split("\n")):
            print("Removing existing mantidimaging-dev environment")
            command_conda_env_remove = [self.conda, "env", "remove", "-n", "mantidimaging-dev"]
            subprocess.check_call(command_conda_env_remove)
        extra_deps = self.get_package_depends()
        env_file_path = self.make_environment_file(extra_deps)
        print("Creating conda environment for development")
        command_conda_env = [self.conda, "env", "create", "-f", env_file_path]
        subprocess.check_call(command_conda_env)
        os.remove(env_file_path)


setup(
    name="mantidimaging",
    version=versions.__version__,
    packages=find_packages(),
    package_data={
        "mantidimaging.gui": ["ui/*.ui", "ui/images/*.png", "windows/wizard/*.yml"],
        "mantidimaging.core": ["gpu/*.cu"],
    },
    entry_points={
        "console_scripts":
        ["mantidimaging-ipython = mantidimaging.ipython:main", "mantidimaging = mantidimaging.main:main"],
    },
    url="https://github.com/mantidproject/mantidimaging",
    license="GPL-3.0",
    description="Graphical toolkit for neutron imaging",
    long_description=open("README.md").read(),
    test_suite="nose.collector",
    classifiers=[
        "Programming Language :: Python :: 3.10",
        "Natural Language :: English",
        "Intended Audience :: Science/Research",
        "Operating System :: POSIX :: Linux",
        "Topic :: Scientific/Engineering",
    ],
    cmdclass={
        "compile_ui": CompilePyQtUiFiles,
        "create_dev_env": CreateDeveloperEnvironment,
        "release_notes": GenerateReleaseNotes,
    },
)
