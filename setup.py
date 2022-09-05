#!/usr/bin/env python
# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import fnmatch
import os
import subprocess
from distutils.core import Command
import sys
from collections import defaultdict
from pathlib import Path
import tempfile
import shutil

from setuptools import find_packages, setup
try:
    from sphinx.setup_command import BuildDoc
except ModuleNotFoundError:
    print("Warning: sphinx needed for building documentation")
    BuildDoc = False

THIS_PATH = os.path.dirname(__file__)


class PublishDocsToGitHubPages(Command):
    description = "Deploy built documentation to GitHub Pages"
    user_options = [
        ("repo=", "r", "Repository URL"),
        ("docs-dir=", "d", "Directory of documentation to publish"),
        ("commit-msg=", "m", "Commit message"),
    ]

    def initialize_options(self):
        self.repo = None
        self.docs_dir = None
        self.commit_msg = None

    def finalize_options(self):
        self.repo = "https://github.com/mantidproject/mantidimaging" if self.repo is None else self.repo

        self.docs_dir = "docs/build/html" if self.docs_dir is None else self.docs_dir

        self.commit_msg = "Publish documentation" if self.commit_msg is None else self.commit_msg

    def run(self):
        git_dir = os.path.join(self.docs_dir, ".git")
        if os.path.exists(git_dir):
            import shutil

            shutil.rmtree(git_dir)

        from git import Git

        g = Git(self.docs_dir)
        g.init()
        g.checkout(b="main")
        g.add(".")
        g.commit("-m {}".format(self.commit_msg))
        g.push("--force", self.repo, "main:gh-pages")


class GenerateSphinxApidoc(Command):
    description = "Generate API documentation with sphinx-apidoc"
    user_options = []

    def initialize_options(self):
        self.sphinx_options = []
        self.module_dir = None
        self.out_dir = None

    def finalize_options(self):
        self.sphinx_options.append("sphinx-apidoc")
        self.sphinx_options.extend(["-f", "-M", "-e", "-T"])

        self.sphinx_options.extend(["-d", "10"])

        self.module_dir = "mantidimaging"
        self.sphinx_options.append(self.module_dir)
        self.sphinx_options.append("**/test")
        self.sphinx_options.append("**/test_helpers")
        self.sphinx_options.append("**/gui")
        self.sphinx_options.append("**/core/utility")
        self.sphinx_options.append("**/core/tools")

        self.out_dir = "docs/api/"
        self.sphinx_options.extend(["-o", self.out_dir])

    def run(self):
        print("Running: {}".format(" ".join(self.sphinx_options)))
        subprocess.call(self.sphinx_options)


class GenerateSphinxVersioned(Command):
    description = "Generate API documentation with versions in directories"
    user_options = []

    def initialize_options(self):
        self.sphinx_multiversion_executable = None
        self.sphinx_multiversion_options = None

    def finalize_options(self):
        self.sphinx_multiversion_executable = "sphinx-multiversion"
        self.sphinx_multiversion_options = ["docs", "docs/build/html"]

    def run(self):
        print("Running setup.py internal_docs_api")
        command_docs_api = [sys.executable, "setup.py", "internal_docs_api"]
        subprocess.check_call(command_docs_api)
        print("Running setup.py internal_docs")
        command_docs = [sys.executable, "setup.py", "internal_docs"]
        subprocess.check_call(command_docs)
        print("Running sphinx-multiversion")
        command_sphinx_multiversion = [self.sphinx_multiversion_executable]
        command_sphinx_multiversion.extend(self.sphinx_multiversion_options)
        subprocess.check_call(command_sphinx_multiversion)


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
        for root, dirnames, filenames in os.walk("./mantidimaging/"):
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
        # Parse the metefile manually, do avoid needing an nonstandard library
        meta_file = Path(__file__).parent / "conda" / "meta.yaml"
        with meta_file.open() as meta_file_fh:
            section = []
            parsed_values = defaultdict(list)
            for line in meta_file_fh:
                # ignore templating
                if line.strip() == "" or "{%" in line:
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
        with dev_env_file.open() as dev_env_file_fh:
            for line in dev_env_file_fh:
                if line.strip() == "- mantidimaging":
                    for extra_dep in extra_deps:
                        output_env_file.write(f"  - {extra_dep}\n")
                else:
                    output_env_file.write(line)
        output_env_file.close()
        print("Created environment file:", output_env_file.name)
        return output_env_file.name

    def run(self):
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
    version="2.5.0a1",
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
        "Programming Language :: Python :: 3.9",
        "Natural Language :: English",
        "Intended Audience :: Science/Research",
        "Operating System :: POSIX :: Linux",
        "Topic :: Scientific/Engineering",
    ],
    cmdclass={
        "internal_docs_api": GenerateSphinxApidoc,
        **({
            "internal_docs": BuildDoc
        } if BuildDoc else {}),
        "docs": GenerateSphinxVersioned,
        "docs_publish": PublishDocsToGitHubPages,
        "compile_ui": CompilePyQtUiFiles,
        "create_dev_env": CreateDeveloperEnvironment,
    },
)
